"""Gemini API 클라이언트 — 시장 분석 + 임베딩 생성

Gemini 2.5 Pro로 시장 상황을 분석하고,
gemini-embedding-001로 분석 결과를 3072차원 벡터로 변환한다.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from rl_hybrid.config import config
from rl_hybrid.rag.prompts import MARKET_ANALYSIS_PROMPT, EMBEDDING_TEXT_TEMPLATE

logger = logging.getLogger("rag.gemini")


class GeminiClient:
    """Gemini API 래퍼 — 분석 + 임베딩"""

    def __init__(self):
        self.cfg = config.gemini
        if not self.cfg.api_key:
            raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다")

        genai.configure(api_key=self.cfg.api_key)
        self.analysis_model = genai.GenerativeModel(self.cfg.analysis_model)

        # Rate limiting
        self._request_times: list[float] = []

        # C2: 일일 LLM 호출 카운터 (KST 날짜 기준, 프로세스 재시작 시 파일 기반 복구)
        self._daily_counter_file = Path(
            os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parent.parent.parent))
        ) / "data" / "gemini_daily_counter.json"
        self._c2_today: str = ""
        self._c2_count: int = 0
        self._load_daily_counter()

    def _kst_today(self) -> str:
        return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")

    def _load_daily_counter(self):
        today = self._kst_today()
        try:
            if self._daily_counter_file.exists():
                data = json.loads(self._daily_counter_file.read_text(encoding="utf-8"))
                if data.get("date") == today:
                    self._c2_today = today
                    self._c2_count = int(data.get("count", 0))
                    return
        except Exception:
            pass
        self._c2_today = today
        self._c2_count = 0

    def _save_daily_counter(self):
        try:
            self._daily_counter_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._daily_counter_file.with_suffix(".tmp")
            tmp.write_text(
                json.dumps({"date": self._c2_today, "count": self._c2_count}, ensure_ascii=False),
                encoding="utf-8",
            )
            import os as _os
            _os.replace(str(tmp), str(self._daily_counter_file))
        except Exception as e:
            logger.debug(f"C2 카운터 저장 실패: {e}")

    def _increment_daily_counter(self):
        today = self._kst_today()
        if self._c2_today != today:
            self._c2_today = today
            self._c2_count = 0
        self._c2_count += 1
        self._save_daily_counter()

    def get_daily_call_count(self) -> int:
        """텔레그램 일일 요약용 LLM 호출 카운트 반환."""
        today = self._kst_today()
        if self._c2_today != today:
            self._load_daily_counter()
        return self._c2_count

    def _heuristic_fallback(self, market_data: dict, reason: str) -> dict:
        """C2 degrade — LLM 대신 단순 휴리스틱으로 관망 반환.

        H14: 매수 degrade 시 abstain(보수) 원칙에 따라 관망.
        """
        logger.warning(f"C2 서킷브레이커 발동 → 휴리스틱 폴백: {reason}")
        return {
            "market_regime": "unknown",
            "confidence": 0.0,
            "key_signals": [],
            "risk_assessment": "circuit_breaker",
            "recommended_action": "hold",
            "reasoning": f"C2 서킷브레이커 발동: {reason}",
            "_c2_degraded": True,
            "_c2_reason": reason,
        }

    def _rate_limit(self):
        """RPM 제한 준수"""
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= self.cfg.rpm_limit:
            sleep_time = 60 - (now - self._request_times[0]) + 1
            logger.info(f"Rate limit 대기: {sleep_time:.1f}초")
            time.sleep(sleep_time)
        self._request_times.append(time.time())

    def analyze_market(
        self,
        market_data: dict,
        external_data: dict,
        rag_context: str = "없음",
    ) -> Optional[dict]:
        """시장 데이터를 Gemini에게 분석 요청 → 구조화된 JSON 반환

        Returns:
            {
                "market_regime": str,
                "confidence": float,
                "key_signals": list[str],
                "risk_assessment": str,
                "recommended_action": str,
                "reasoning": str,
                "time_horizon": str,
                "danger_score_adjustment": int,
                "opportunity_score_adjustment": int,
            }
        """
        # C2: 일일 호출 캡 초과 시 휴리스틱 폴백
        today = self._kst_today()
        if self._c2_today != today:
            self._load_daily_counter()
        if self._c2_count >= self.cfg.daily_call_cap:
            return self._heuristic_fallback(
                market_data, f"일일 호출 캡 초과({self._c2_count}/{self.cfg.daily_call_cap})"
            )

        self._rate_limit()

        prompt = MARKET_ANALYSIS_PROMPT.format(
            market_data=json.dumps(market_data, ensure_ascii=False, indent=2)[:2000],
            external_data=json.dumps(external_data, ensure_ascii=False, indent=2)[:2000],
            rag_context=rag_context[:1000],
        )

        for attempt in range(self.cfg.max_retries):
            try:
                # C2: 지연 예산 초과 시 휴리스틱 직행
                _call_start = time.time()
                response = self.analysis_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.cfg.temperature,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )
                _latency = time.time() - _call_start
                if _latency > self.cfg.latency_budget_seconds:
                    logger.warning(f"C2: 지연 예산 초과 ({_latency:.1f}s > {self.cfg.latency_budget_seconds}s)")
                    self._increment_daily_counter()
                    return self._heuristic_fallback(
                        market_data, f"지연 예산 초과({_latency:.1f}s)"
                    )

                text = response.text.strip()
                # JSON 블록 추출 (```json ... ``` 감싸기 대응)
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                result = json.loads(text)
                # B3: 결정성 추적 — model_id/prompt_hash/temperature 기록
                result["_model_id"] = self.cfg.analysis_model
                result["_prompt_hash"] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:32]
                result["_temperature"] = self.cfg.temperature
                # C2: 성공 호출 카운트
                self._increment_daily_counter()
                logger.info(
                    f"Gemini 분석 완료: regime={result.get('market_regime')}, "
                    f"action={result.get('recommended_action')}, "
                    f"confidence={result.get('confidence')}, "
                    f"model={self.cfg.analysis_model}, temp={self.cfg.temperature}"
                )
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패 (시도 {attempt+1}): {e}")
            except Exception as e:
                logger.error(f"Gemini API 호출 실패 (시도 {attempt+1}): {e}")
                if attempt < self.cfg.max_retries - 1:
                    time.sleep(2 ** attempt)

        logger.error("Gemini 분석 실패 — 모든 재시도 소진")
        return None

    def generate_embedding(self, text: str) -> Optional[list[float]]:
        """텍스트를 3072차원 임베딩 벡터로 변환

        Args:
            text: 임베딩할 텍스트 (분석 결과 요약)

        Returns:
            3072차원 float 리스트, 실패 시 None
        """
        self._rate_limit()

        try:
            result = genai.embed_content(
                model=f"models/{self.cfg.embedding_model}",
                content=text,
                task_type="retrieval_document",
            )
            embedding = result["embedding"]
            logger.debug(f"임베딩 생성 완료: dim={len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None

    def build_embedding_text(self, analysis: dict, market_snapshot: dict = None) -> str:
        """분석 결과를 임베딩용 텍스트로 변환"""
        return EMBEDDING_TEXT_TEMPLATE.format(
            timestamp=time.strftime("%Y-%m-%d %H:%M"),
            market_regime=analysis.get("market_regime", "unknown"),
            confidence=analysis.get("confidence", 0),
            key_signals=", ".join(analysis.get("key_signals", [])),
            risk_assessment=analysis.get("risk_assessment", "unknown"),
            recommended_action=analysis.get("recommended_action", "hold"),
            reasoning=analysis.get("reasoning", ""),
            btc_price=market_snapshot.get("btc_price", "N/A") if market_snapshot else "N/A",
            rsi=market_snapshot.get("rsi", "N/A") if market_snapshot else "N/A",
            fgi=market_snapshot.get("fgi", "N/A") if market_snapshot else "N/A",
        )
