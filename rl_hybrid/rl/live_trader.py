"""LiveTrader — 실시간 매매 봇 (기존 파이프라인 완전 통합)

기존 run_agents.py의 6 Phase 파이프라인에 RL + LLM 분석을 삽입하여,
세 소스의 융합 결정으로 매매를 실행한다.

실행 흐름:
  1. 시장 데이터 수집 (기존 스크립트)
  2. 외부 데이터 수집 (ExternalDataAgent)
  3. 에이전트 판단 (Orchestrator)
  4. RL 추론 (DistributedTrainer)
  5. LLM 분석 (RAG Pipeline, 선택)
  6. 결정 융합 (DecisionBlender)
  7. 매매 실행 + DB 기록 + 알림
"""

import json
import logging
import os
import subprocess
from scripts.hide_console import subprocess_kwargs
import sys
import time
from typing import Optional


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rl_hybrid.config import config
from rl_hybrid.rl.state_encoder import StateEncoder
from rl_hybrid.rl.decision_blender import DecisionBlender
from scripts.execute_trade import make_auth_header as _make_auth_header

logger = logging.getLogger("rl.live_trader")

try:
    from rl_hybrid.rl.distributed_trainer import DistributedTrainer
    from rl_hybrid.rl.continuous_learner import ContinuousLearner
    from rl_hybrid.rl.model_registry import ModelRegistry
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LiveTrader:
    """실시간 매매 봇 — 분산 시스템의 최종 통합 포인트"""

    def __init__(
        self,
        enable_rl: bool = True,
        enable_llm: bool = False,
        enable_continuous_learning: bool = True,
        dry_run: bool = None,
    ):
        """
        Args:
            enable_rl: RL 추론 활성화
            enable_llm: Gemini LLM 분석 활성화
            enable_continuous_learning: 백그라운드 재학습 활성화
            dry_run: DRY_RUN 오버라이드 (None이면 .env 따름)
        """
        self.project_root = config.project_root
        self.encoder = StateEncoder()
        self.blender = DecisionBlender()

        # RL 구성요소
        self.enable_rl = enable_rl and TORCH_AVAILABLE
        self.trainer: Optional[DistributedTrainer] = None
        self.learner: Optional[ContinuousLearner] = None
        self.registry: Optional[ModelRegistry] = None

        if self.enable_rl:
            self.trainer = DistributedTrainer(obs_dim=42)
            self.registry = ModelRegistry()
            self.trainer.load_model()

            if enable_continuous_learning:
                self.learner = ContinuousLearner(
                    trainer=self.trainer,
                    retrain_interval_hours=6,
                )
                self.learner.start_background()

        # LLM 구성요소
        self.enable_llm = enable_llm
        self.llm_analysis: Optional[dict] = None

        # DRY_RUN
        if dry_run is not None:
            os.environ["DRY_RUN"] = str(dry_run).lower()

        self._cycle_count = 0

    def run_cycle(self) -> dict:
        """단일 매매 사이클 실행

        Returns:
            {
                "cycle_id": str,
                "blended_decision": dict,
                "agent_result": dict,
                "rl_prediction": dict,
                "trade_result": dict,
                "timestamp": str,
            }
        """
        self._cycle_count += 1
        cycle_id = f"live_{int(time.time())}_{self._cycle_count}"
        logger.info(f"=== 매매 사이클 #{self._cycle_count} ({cycle_id}) ===")

        result = {
            "cycle_id": cycle_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "blended_decision": None,
            "agent_result": None,
            "rl_prediction": None,
            "llm_analysis": None,
            "trade_result": None,
            "errors": [],
        }

        try:
            # Phase 1: 데이터 수집
            market_data = self._run_script("scripts/collect_market_data.py")
            portfolio = self._run_script("scripts/get_portfolio.py")

            if not market_data or not portfolio:
                result["errors"].append("데이터 수집 실패")
                return result

            # R2: 잔고 reconciliation — drift 감지 시 halt
            drift_result = self._check_portfolio_drift(portfolio)
            result["drift_check"] = drift_result
            if drift_result.get("halt"):
                result["errors"].append(f"R2 drift halt: {drift_result.get('reason')}")
                self._log_execution({"event": "r2_drift_halt", **drift_result})
                logger.warning(f"R2 drift halt — 매매 중단: {drift_result.get('reason')}")
                return result

            # Phase 2: 에이전트 파이프라인 (기존 Orchestrator)
            agent_result = self._run_agent_pipeline(market_data, portfolio)
            result["agent_result"] = agent_result

            # Phase 3: RL 추론
            rl_prediction = None
            if self.enable_rl and self.trainer:
                rl_prediction = self._get_rl_prediction(
                    market_data, portfolio, agent_result
                )
                result["rl_prediction"] = rl_prediction

            # Phase 4: LLM 분석 (선택적)
            llm_analysis = None
            if self.enable_llm:
                llm_analysis = self._get_llm_analysis(market_data)
                result["llm_analysis"] = llm_analysis

            # Phase 5: 결정 융합
            blended = self.blender.blend(
                agent_result=agent_result.get("decision") if agent_result else None,
                rl_prediction=rl_prediction,
                llm_analysis=llm_analysis,
                portfolio=portfolio,
                market_state=agent_result.get("market_state") if agent_result else None,
            )
            result["blended_decision"] = blended.to_dict()

            logger.info(
                f"융합 결정: {blended.decision} (conf={blended.confidence:.2f}, "
                f"action={blended.action_value:.3f})\n"
                f"  {blended.reason}"
            )

            # Phase 6: 매매 실행
            if blended.decision != "hold":
                trade_result = self._execute_trade(blended)
                result["trade_result"] = trade_result

            # Phase 7: DB 기록 + 알림
            self._save_and_notify(result, blended)

        except Exception as e:
            logger.error(f"매매 사이클 에러: {e}", exc_info=True)
            result["errors"].append(str(e))

        return result

    def _run_script(self, script: str, timeout: int = 30) -> Optional[dict]:
        """기존 Python 스크립트 실행 → JSON 파싱"""
        try:
            proc = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, timeout=timeout,
                cwd=self.project_root,
                **subprocess_kwargs(),
            )
            if proc.returncode == 0:
                return json.loads(proc.stdout)
            logger.error(f"{script} 에러: {proc.stderr[:300]}")
        except Exception as e:
            logger.error(f"{script} 실행 실패: {e}")
        return None

    def _run_agent_pipeline(self, market_data: dict, portfolio: dict) -> Optional[dict]:
        """기존 에이전트 파이프라인 실행

        run_agents.py의 핵심 로직을 인라인으로 호출한다.
        """
        try:
            # ExternalDataAgent import
            sys.path.insert(0, self.project_root)
            from agents.external_data import ExternalDataAgent
            from agents.orchestrator import Orchestrator

            ext_agent = ExternalDataAgent()
            external_data = ext_agent.collect_all(market_data)

            orchestrator = Orchestrator()
            result = orchestrator.run(
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio,
            )

            return result

        except Exception as e:
            logger.error(f"에이전트 파이프라인 에러: {e}", exc_info=True)
            return None

    def _get_rl_prediction(
        self,
        market_data: dict,
        portfolio: dict,
        agent_result: dict = None,
    ) -> Optional[dict]:
        """RL 모델 추론"""
        try:
            # 에이전트 상태 추출
            agent_state = {}
            if agent_result:
                ms = agent_result.get("market_state", {})
                agent_state = {
                    "danger_score": ms.get("danger_score", 30),
                    "opportunity_score": ms.get("opportunity_score", 30),
                    "cascade_risk": agent_result.get("drop_context", {}).get("cascade_risk", 20),
                    "consecutive_losses": ms.get("consecutive_losses", 0),
                }

            # 외부 데이터 기본값 (실시간에서는 agent_result에 포함)
            external_data = {"sources": {}, "external_signal": {"total_score": 0}}

            obs = self.encoder.encode(
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio,
                agent_state=agent_state,
            )

            action, log_prob, value = self.trainer.predict(obs, deterministic=True)

            return {
                "action": action,
                "value": value,
                "log_prob": log_prob,
                "interpretation": self._interpret_action(action),
            }

        except Exception as e:
            logger.error(f"RL 추론 에러: {e}")
            return None

    def _get_llm_analysis(self, market_data: dict) -> Optional[dict]:
        """Gemini LLM 분석 (RAG 파이프라인)"""
        try:
            from rl_hybrid.rag.rag_pipeline import RAGPipeline
            pipeline = RAGPipeline()
            return pipeline.analyze_and_store(
                cycle_id=f"live_{int(time.time())}",
                market_data=market_data,
                external_data={},
            )
        except Exception as e:
            logger.debug(f"LLM 분석 스킵: {e}")
            return None

    # ------------------------------------------------------------------
    # R2 Reconciliation helpers
    # ------------------------------------------------------------------

    def _get_open_orders_locked(self, market: str = "KRW-BTC") -> float:
        """미체결(wait) 주문의 locked BTC 잔량 합산 (거래소 측 가짜 drift 방지).

        bid 주문의 locked KRW는 잔고 측에서 이미 차감되어 있으므로 무시.
        ask(매도) 주문의 locked volume 만 합산하여 보유 BTC에 더한다.
        """
        try:
            import requests as _req
            from urllib.parse import urlencode as _urlencode

            if not os.environ.get("UPBIT_ACCESS_KEY") or not os.environ.get("UPBIT_SECRET_KEY"):
                return 0.0

            qs = _urlencode({"market": market, "state": "wait"})
            headers = _make_auth_header(qs)
            r = _req.get(
                "https://api.upbit.com/v1/orders",
                params={"market": market, "state": "wait"},
                headers=headers,
                timeout=10,
            )
            if not r.ok:
                return 0.0
            locked = sum(
                float(o.get("remaining_volume") or 0)
                for o in r.json()
                if o.get("side") == "ask"
            )
            return locked
        except Exception as e:
            logger.debug(f"open_orders locked 조회 실패: {e}")
            return 0.0

    # Sentinel for DB query errors (distinct from empty snapshot)
    _DB_QUERY_ERROR = object()

    def _get_db_portfolio_snapshot(self):
        """Supabase portfolio_snapshots 에서 최신 스냅샷 반환.

        반환값:
          - dict : 스냅샷 존재
          - None : 스냅샷 없음 (빈 테이블 / 첫 실행)
          - _DB_QUERY_ERROR : DB 연결 에러 / 키 없음 / 예외 → halt 필요
        """
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            return self._DB_QUERY_ERROR
        try:
            import requests as _req
            r = _req.get(
                f"{url}/rest/v1/portfolio_snapshots",
                params={"order": "created_at.desc", "limit": "1"},
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
                timeout=10,
            )
            if r.ok:
                rows = r.json()
                return rows[0] if rows else None
            return self._DB_QUERY_ERROR
        except Exception as e:
            logger.warning(f"DB 스냅샷 조회 에러: {e}")
            return self._DB_QUERY_ERROR

    def _check_portfolio_drift(
        self,
        live_portfolio: dict,
        drift_threshold: float = None,
    ) -> dict:
        """거래소 잔고(live)와 DB 스냅샷을 비교하여 drift 감지.

        - open-orders locked 잔량을 거래소 측에 합산(가짜 drift 방지).
        - fee-net day-1 허용: 임계 미만 drift 는 pass.
        - 자동 write-off/보정 금지 — halt + log 만.
        """
        if drift_threshold is None:
            drift_threshold = float(os.environ.get("R2_DRIFT_THRESHOLD", "0.05"))

        db_snap = self._get_db_portfolio_snapshot()
        if db_snap is self._DB_QUERY_ERROR:
            # DB 조회 에러 → halt + 텔레그램 알림
            self._log_execution({"event": "r2_db_error", "reason": "DB 스냅샷 조회 에러"})
            self._notify_telegram_sync("⚠️ R2 drift 검사 중단: DB 스냅샷 조회 에러 (연결 실패/키 누락)")
            return {"halt": True, "reason": "db_query_error", "skipped": False}
        if db_snap is None:
            # 첫 실행 / 빈 테이블 → 검사 생략
            return {"halt": False, "reason": "no_db_snapshot", "skipped": True}

        # 거래소 BTC 잔고 + locked 합산
        live_btc = 0.0
        for h in live_portfolio.get("holdings", []):
            if h.get("currency") == "BTC":
                live_btc = float(h.get("balance", 0))
                break
        locked_btc = self._get_open_orders_locked("KRW-BTC")
        exchange_btc = live_btc + locked_btc

        db_btc = float(db_snap.get("btc_balance") or db_snap.get("coin_balance") or 0)

        # KRW drift
        live_krw = float(live_portfolio.get("krw_balance", 0))
        db_krw = float(db_snap.get("krw_balance") or 0)

        btc_drift = abs(exchange_btc - db_btc) / max(db_btc, 1e-8) if db_btc else 0.0
        krw_drift = abs(live_krw - db_krw) / max(db_krw, 1) if db_krw else 0.0

        drift_info = {
            "halt": False,
            "exchange_btc": exchange_btc,
            "db_btc": db_btc,
            "btc_drift_pct": round(btc_drift * 100, 4),
            "live_krw": live_krw,
            "db_krw": db_krw,
            "krw_drift_pct": round(krw_drift * 100, 4),
            "locked_btc": locked_btc,
            "threshold_pct": round(drift_threshold * 100, 2),
        }

        if btc_drift > drift_threshold or krw_drift > drift_threshold:
            drift_info["halt"] = True
            drift_info["reason"] = (
                f"BTC drift {drift_info['btc_drift_pct']:.2f}% "
                f"KRW drift {drift_info['krw_drift_pct']:.2f}% "
                f"> threshold {drift_threshold*100:.1f}%"
            )

        return drift_info

    def _clamp_to_balance(self, volume: float, market: str = "KRW-BTC") -> float:
        """실제 보유 잔량을 초과하는 매도 수량을 실잔량으로 클램프.

        미체결 ask locked 를 제외한 가용 잔량 기준.
        """
        try:
            portfolio = self._run_script("scripts/get_portfolio.py")
            if not portfolio:
                return volume
            avail_btc = 0.0
            for h in portfolio.get("holdings", []):
                if h.get("currency") == "BTC":
                    avail_btc = float(h.get("balance", 0))
                    break
            locked = self._get_open_orders_locked(market)
            usable = max(avail_btc - locked, 0.0)
            if volume > usable:
                logger.warning(
                    f"_clamp_to_balance: {volume:.8f} > usable {usable:.8f}, clamp to {usable:.8f}"
                )
                return usable
        except Exception as e:
            logger.debug(f"_clamp_to_balance 실패: {e}")
        return volume

    def _log_execution(self, entry: dict):
        """execution_logs 파일에 이벤트 기록."""
        import json as _json
        from pathlib import Path as _Path
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        log_dir = _Path(self.project_root) / "logs" / "executions"
        log_dir.mkdir(parents=True, exist_ok=True)
        entry.setdefault("timestamp", _dt.now(_tz((_td(hours=9)))).isoformat())
        with (log_dir / "live_trader_events.jsonl").open("a", encoding="utf-8") as f:
            f.write(_json.dumps(entry, ensure_ascii=False) + "\n")

    def _notify_telegram_sync(self, message: str):
        """동기 텔레그램 알림 (subprocess, 에러 무시)."""
        try:
            subprocess.run(
                [sys.executable, "scripts/notify_telegram.py", "--message", message],
                capture_output=True, timeout=10,
                cwd=self.project_root,
                **subprocess_kwargs(),
            )
        except Exception:
            pass

    def _execute_trade(self, blended) -> Optional[dict]:
        """매매 실행"""
        params = blended.trade_params
        side = params.get("side")

        if side == "none" or not side:
            return None

        try:
            cmd = [
                sys.executable, "scripts/execute_trade.py",
                "--side", "buy" if side == "bid" else "sell",
                "--market", params.get("market", "KRW-BTC"),
            ]

            if side == "bid" and params.get("amount"):
                cmd.extend(["--amount", str(params["amount"])])
            elif side == "ask":
                if params.get("volume"):
                    # R2: 실잔량 초과 매도 방지
                    clamped = self._clamp_to_balance(
                        float(params["volume"]),
                        params.get("market", "KRW-BTC"),
                    )
                    cmd.extend(["--volume", str(clamped)])
                elif params.get("sell_ratio"):
                    cmd.extend(["--ratio", str(params["sell_ratio"])])

            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                cwd=self.project_root,
                **subprocess_kwargs(),
            )

            if proc.returncode == 0:
                result = json.loads(proc.stdout)
                logger.info(f"매매 체결: {side} → {result}")
                return result
            else:
                logger.error(f"매매 실행 실패: {proc.stderr[:300]}")
                return {"error": proc.stderr[:300]}

        except Exception as e:
            logger.error(f"매매 실행 에러: {e}")
            return {"error": str(e)}

    def _save_and_notify(self, result: dict, blended):
        """DB 저장 + 텔레그램 알림"""
        try:
            # 텔레그램 알림
            message = (
                f"🤖 *LLM\\-RL 하이브리드 매매*\n\n"
                f"결정: `{blended.decision}` \\(conf={blended.confidence:.2f}\\)\n"
                f"Agent: `{blended.agent_decision}` | "
                f"RL: `{blended.rl_action:.2f}` | "
                f"Action: `{blended.action_value:.3f}`\n"
                f"근거: {self._escape_md(blended.reason[:200])}"
            )

            subprocess.run(
                [sys.executable, "scripts/notify_telegram.py",
                 "--message", message],
                capture_output=True, timeout=10,
                cwd=self.project_root,
                **subprocess_kwargs(),
            )
        except Exception as e:
            logger.debug(f"알림 전송 실패: {e}")

    @staticmethod
    def _interpret_action(action: float) -> str:
        if action > 0.5:
            return "strong_buy"
        elif action > 0.2:
            return "cautious_buy"
        elif action < -0.5:
            return "strong_sell"
        elif action < -0.2:
            return "cautious_sell"
        return "hold"

    @staticmethod
    def _escape_md(text: str) -> str:
        """MarkdownV2 이스케이프"""
        special = r"_*[]()~`>#+-=|{}.!"
        for c in special:
            text = text.replace(c, f"\\{c}")
        return text

    def stop(self):
        """정리"""
        if self.learner:
            self.learner.stop()

    def get_status(self) -> dict:
        """시스템 상태"""
        status = {
            "cycles_completed": self._cycle_count,
            "enable_rl": self.enable_rl,
            "enable_llm": self.enable_llm,
            "dry_run": os.getenv("DRY_RUN", "true"),
        }

        if self.registry:
            current = self.registry.get_current_version()
            status["model_version"] = current["version_id"] if current else None

        if self.learner:
            status["continuous_learning"] = self.learner.get_status()

        if self.trainer:
            status["trainer"] = self.trainer.get_stats()

        return status


# === CLI 실행 ===

def main():
    """CLI에서 단일 사이클 또는 루프 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM-RL 하이브리드 라이브 트레이더")
    parser.add_argument("--loop", action="store_true", help="무한 루프 모드")
    parser.add_argument("--interval", type=int, default=1800, help="루프 간격(초, 기본 30분)")
    parser.add_argument("--no-rl", action="store_true", help="RL 비활성화")
    parser.add_argument("--llm", action="store_true", help="LLM 분석 활성화")
    parser.add_argument("--no-learning", action="store_true", help="지속 학습 비활성화")
    parser.add_argument("--dry-run", action="store_true", help="DRY_RUN 강제 활성화")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    trader = LiveTrader(
        enable_rl=not args.no_rl,
        enable_llm=args.llm,
        enable_continuous_learning=not args.no_learning,
        dry_run=True if args.dry_run else None,
    )

    try:
        if args.loop:
            logger.info(f"루프 모드 시작: interval={args.interval}초")
            while True:
                result = trader.run_cycle()
                decision = result.get("blended_decision", {})
                logger.info(
                    f"사이클 완료: {decision.get('decision', 'N/A')} | "
                    f"다음: {args.interval}초 후"
                )
                time.sleep(args.interval)
        else:
            result = trader.run_cycle()
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    except KeyboardInterrupt:
        logger.info("종료")
    finally:
        trader.stop()


if __name__ == "__main__":
    main()
