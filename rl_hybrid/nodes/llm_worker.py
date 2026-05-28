"""LLM/RAG 워커 노드 — Gemini 분석 + pgvector RAG 전담

역할:
  - Main Brain의 analyze_market 요청 → Gemini API 분석 → 결과 반환
  - rag_query 요청 → pgvector 유사 검색 → 결과 반환
  - embed_and_store 요청 → 임베딩 생성 + 저장
  - PUB 채널 구독하여 시장 데이터 캐시
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import jsonschema
import zmq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rl_hybrid.nodes.base_node import BaseNode
from rl_hybrid.config import config
from rl_hybrid.protocol import (
    ZMQMessage, Action, make_heartbeat,
)
from rl_hybrid.rag.rag_pipeline import RAGPipeline
from core.brain.llm_provider import LLMRouter

KST = timezone(timedelta(hours=9))

logger = logging.getLogger("node.llm_worker")

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "schemas" / "decision_result.json"
_DECISION_SCHEMA: Optional[dict] = None


_SCHEMA_LOAD_ERROR: Optional[str] = None
_DECISION_VALIDATOR: Optional[jsonschema.Draft7Validator] = None


def _load_decision_schema() -> tuple[Optional[dict], Optional[str]]:
    """스키마 로드 + Validator 1회 생성. 반환: (schema_dict, error_msg)."""
    global _DECISION_SCHEMA, _SCHEMA_LOAD_ERROR, _DECISION_VALIDATOR
    if _DECISION_SCHEMA is None and _SCHEMA_LOAD_ERROR is None:
        try:
            _DECISION_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
            _DECISION_VALIDATOR = jsonschema.Draft7Validator(_DECISION_SCHEMA)
        except jsonschema.SchemaError as e:
            _SCHEMA_LOAD_ERROR = f"SchemaError: {e}"
            logger.error(_SCHEMA_LOAD_ERROR)
        except Exception as e:
            _SCHEMA_LOAD_ERROR = f"decision_result.json 로드 실패: {e}"
            logger.error(_SCHEMA_LOAD_ERROR)
    return _DECISION_SCHEMA, _SCHEMA_LOAD_ERROR


def _validate_decision(analysis: dict) -> tuple[bool, str]:
    """jsonschema 로 decision_result.json 스키마 강제 검증.

    반환: (valid: bool, error_message: str)
    스키마 로드 실패 / SchemaError → fail-closed: (False, 사유)
    캐싱된 Draft7Validator 재사용으로 반복 파싱 제거.
    """
    schema, load_err = _load_decision_schema()
    if load_err or schema is None or _DECISION_VALIDATOR is None:
        return False, load_err or "스키마 로드 실패 (unknown)"
    try:
        _DECISION_VALIDATOR.validate(analysis)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, e.message
    except jsonschema.SchemaError as e:
        logger.error(f"스키마 자체 오류: {e}")
        return False, f"SchemaError: {e}"


def _log_near_miss_veto(cycle_id: str, reason: str, raw: object):
    """B1 검증 실패 이벤트를 near_miss_veto.jsonl 에 기록."""
    log_dir = _SCHEMA_PATH.parent.parent.parent / "logs" / "executions"
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "event": "near_miss_veto",
        "cycle_id": cycle_id,
        "reason": reason,
        "raw_snippet": str(raw)[:300],
        "timestamp": datetime.now(KST).isoformat(),
    }
    with (log_dir / "near_miss_veto.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class LLMWorkerNode(BaseNode):
    """LLM/RAG 워커 — DEALER + SUB

    SO-6: gemini_client 직접호출 → LLMRouter 경유.
    평상시=Qwen(quick), 트리거=Claude(deep). ZMQ 계약 유지. B1 하드게이트 보존.
    """

    def __init__(self, llm_router: Optional[LLMRouter] = None):
        super().__init__("llm_worker")
        self.dealer: Optional[zmq.Socket] = None
        self.sub: Optional[zmq.Socket] = None
        self.pipeline: Optional[RAGPipeline] = None
        self.latest_market_data: dict = {}
        self._llm_router: LLMRouter = llm_router or LLMRouter()

    def _setup_sockets(self):
        # DEALER → Main Brain ROUTER
        self.dealer = self.ctx.socket(zmq.DEALER)
        self.dealer.setsockopt_string(zmq.IDENTITY, self.node_name)
        self.dealer.connect(self.zmq_config.router_addr)
        self.logger.info(f"DEALER 연결: {self.zmq_config.router_addr}")

        # SUB → Main Brain PUB (시장 데이터 수신)
        self.sub = self.ctx.socket(zmq.SUB)
        self.sub.connect(self.zmq_config.pub_addr)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")  # 모든 토픽 구독
        self.logger.info(f"SUB 연결: {self.zmq_config.pub_addr}")

        # RAG 파이프라인 초기화
        try:
            self.pipeline = RAGPipeline()
            self.logger.info("RAG 파이프라인 초기화 완료")
        except Exception as e:
            self.logger.error(f"RAG 파이프라인 초기화 실패: {e}")

    def _send_heartbeat(self):
        """Main Brain에 하트비트 전송"""
        msg = make_heartbeat(self.node_name, status="alive", uptime=self.uptime)
        try:
            self.dealer.send(b"" + msg.serialize())
        except Exception:
            pass

    def _main_loop(self):
        """메시지 수신 루프"""
        poller = zmq.Poller()
        poller.register(self.dealer, zmq.POLLIN)
        poller.register(self.sub, zmq.POLLIN)

        self.logger.info("LLM Worker 메인 루프 시작")

        while self._running:
            events = dict(poller.poll(100))

            # DEALER: Main Brain 요청 처리
            if self.dealer in events:
                self._handle_dealer_message()

            # SUB: 시장 데이터 캐시
            if self.sub in events:
                self._handle_sub_message()

    def _handle_dealer_message(self):
        """Main Brain 요청 처리"""
        try:
            frames = self.dealer.recv_multipart(zmq.NOBLOCK)
            # DEALER는 빈 프레임 제거 후 데이터 프레임만
            data = frames[-1] if frames else None
            if not data:
                return

            msg = ZMQMessage.deserialize(data)
        except Exception as e:
            self.logger.error(f"메시지 수신 에러: {e}")
            return

        self.logger.info(f"요청 수신: action={msg.action}, req_id={msg.request_id}")

        handlers = {
            Action.ANALYZE_MARKET.value: self._handle_analyze,
            Action.RAG_QUERY.value: self._handle_rag_query,
            Action.EMBED_AND_STORE.value: self._handle_embed_store,
        }

        handler = handlers.get(msg.action)
        if handler:
            response = handler(msg)
            if response:
                response.sender = self.node_name
                self.dealer.send(b"" + response.serialize())
        else:
            self.logger.warning(f"알 수 없는 액션: {msg.action}")

    def _handle_sub_message(self):
        """PUB 채널 시장 데이터 캐시"""
        try:
            data = self.sub.recv(zmq.NOBLOCK)
            msg = ZMQMessage.deserialize(data)
            if msg.action == Action.MARKET_UPDATE.value:
                self.latest_market_data = msg.payload
                self.logger.debug("시장 데이터 캐시 갱신")
        except Exception:
            pass

    def _handle_analyze(self, msg: ZMQMessage) -> Optional[ZMQMessage]:
        """시장 분석 요청 처리 — LLMRouter 경유 (gemini_client 직접호출 제거).

        라우팅: 평상시=Qwen(quick), 트리거(급락/레짐전환/고위험)=Claude(deep).
        ZMQ 계약(reply payload 형식) 유지. B1 스키마 하드게이트 보존.
        """
        try:
            market_data = msg.payload.get("market_data", {})
            external_data = msg.payload.get("external_data", {})
            context = msg.payload.get("context", {})
            cycle_id = context.get("cycle_id", f"cycle_{int(time.time())}")

            # 외부 데이터가 비어있으면 자체 수집
            if not external_data:
                external_data = self._collect_external_data()

            # LLMRouter 라우팅 트리거 신호 추출
            price_change_24h = float(
                market_data.get("change_rate_24h")
                or (market_data.get("current_price") or {}).get("signed_change_rate", 0.0)
                or 0.0
            ) * 100  # signed_change_rate 는 소수(예: -0.05 = -5%)
            regime_switch = bool(context.get("regime_switch", False))
            high_risk = bool(context.get("high_risk", False))

            prompt = self._build_analysis_prompt(market_data, external_data, cycle_id)
            raw_text, tier = self._llm_router.route(
                prompt,
                price_change_24h=price_change_24h,
                regime_switch=regime_switch,
                high_risk=high_risk,
                max_tokens=1024,
            )
            self.logger.info(f"LLMRouter tier={tier}, cycle={cycle_id}")

            analysis = self._parse_llm_response(raw_text, cycle_id, tier)

            # B1: 스키마 하드게이트 — risk 경계로 넘기기 전 강제 검증
            valid, err_msg = _validate_decision(analysis)
            if not valid:
                _log_near_miss_veto(cycle_id, err_msg, analysis)
                logger.warning(f"B1 스키마 검증 실패 → 관망 강제: {err_msg}")
                hold_result = {
                    "decision": "관망",
                    "confidence": 0.0,
                    "reason": f"B1 스키마 검증 실패로 관망 강제: {err_msg[:100]}",
                    "b1_veto": True,
                    "b1_error": err_msg,
                }
                return msg.reply(hold_result)
            return msg.reply(analysis)

        except Exception as e:
            self.logger.error(f"분석 처리 에러: {e}", exc_info=True)
            return msg.reply({}, error="LLM 분석 처리 중 오류 (상세는 서버 로그 참조)")

    def _build_analysis_prompt(
        self,
        market_data: dict,
        external_data: dict,
        cycle_id: str,
    ) -> str:
        """LLMRouter 용 분석 프롬프트 생성."""
        cp = market_data.get("current_price", {})
        btc_price = cp.get("trade_price", "N/A") if isinstance(cp, dict) else cp
        rsi = market_data.get("indicators", {}).get("rsi_14", "N/A")
        fgi = external_data.get("fgi", {})
        fgi_val = fgi.get("value", "N/A") if isinstance(fgi, dict) else "N/A"
        change = cp.get("signed_change_rate", 0.0) if isinstance(cp, dict) else 0.0
        return (
            f"[cycle={cycle_id}] BTC 시장 분석 요청.\n"
            f"BTC 가격: {btc_price}원, RSI: {rsi}, FGI: {fgi_val}, 24h변동: {change:.2%}\n"
            "JSON 형식으로 decision(매수/매도/관망), confidence(0.0~1.0), "
            "reason, market_regime 을 반환하라."
        )

    def _parse_llm_response(self, raw: str, cycle_id: str, tier: str) -> dict:
        """LLM 텍스트 응답 → 분석 dict 파싱.

        JSON 블록 추출 실패 시 관망 heuristic fallback.
        """
        import re
        # JSON 블록 추출 시도
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                result = json.loads(m.group())
                result.setdefault("cycle_id", cycle_id)
                result.setdefault("llm_tier", tier)
                return result
            except json.JSONDecodeError:
                pass

        # heuristic fallback: 관망
        logger.warning(f"LLM 응답 JSON 파싱 실패 → heuristic 관망: {raw[:100]}")
        return {
            "decision": "관망",
            "confidence": 0.0,
            "reason": f"LLM 응답 파싱 실패(heuristic fallback): {raw[:80]}",
            "market_regime": "unknown",
            "cycle_id": cycle_id,
            "llm_tier": tier,
        }

    def _handle_rag_query(self, msg: ZMQMessage) -> Optional[ZMQMessage]:
        """RAG 유사 검색 요청 처리"""
        if not self.pipeline:
            return msg.reply({"results": []}, error="RAG 파이프라인 미초기화")

        try:
            query_text = msg.payload.get("query_text", "")
            top_k = msg.payload.get("top_k", 5)

            results = self.pipeline.query_similar(query_text, top_k)

            # 직렬화를 위해 embedding 필드 제거
            for r in results:
                r.pop("embedding", None)

            return msg.reply({"results": results})

        except Exception as e:
            return msg.reply({"results": []}, error=str(e))

    def _handle_embed_store(self, msg: ZMQMessage) -> Optional[ZMQMessage]:
        """임베딩 생성 + 저장 요청 처리"""
        if not self.pipeline:
            return msg.reply({}, error="RAG 파이프라인 미초기화")

        try:
            cycle_id = msg.payload.get("cycle_id", "")
            analysis = msg.payload.get("analysis", {})
            market_state = msg.payload.get("market_state", {})
            decision_id = msg.payload.get("decision_id")

            embed_text = self.pipeline.gemini.build_embedding_text(analysis, market_state)
            embedding = self.pipeline.gemini.generate_embedding(embed_text)

            if embedding:
                record_id = self.pipeline.store.store_analysis(
                    cycle_id=cycle_id,
                    analysis_text=embed_text,
                    analysis_json=analysis,
                    embedding=embedding,
                    decision_id=decision_id,
                )
                return msg.reply({"embedding_id": record_id, "success": True})

            return msg.reply({"success": False}, error="임베딩 생성 실패")

        except Exception as e:
            return msg.reply({"success": False}, error=str(e))

    def _collect_external_data(self) -> dict:
        """외부 데이터 자체 수집 (FGI, 뉴스 등)"""
        external = {}
        try:
            import subprocess
            from scripts.hide_console import subprocess_kwargs
            # FGI 수집
            result = subprocess.run(
                [sys.executable, "scripts/collect_fear_greed.py"],
                capture_output=True, text=True, timeout=15,
                cwd=config.project_root,
                **subprocess_kwargs(),
            )
            if result.returncode == 0:
                external["fgi"] = json.loads(result.stdout)
        except Exception as e:
            self.logger.debug(f"외부 데이터 수집 에러: {e}")

        return external


if __name__ == "__main__":
    node = LLMWorkerNode()
    node.start()
