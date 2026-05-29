#!/usr/bin/env python3
"""
Python 기반 에이전트 모드 파이프라인 (Cross-platform 지원)
기존 run_agents.sh를 대체하며, Windows/Linux 어디서든 안전하게 동작합니다.

사용법:
  python scripts/run_agents.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 부모 디렉토리 sys.path 추가 및 상대 임포트 준비
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
import requests

from agents.external_data import ExternalDataAgent
from agents.orchestrator import Orchestrator

KST = timezone(timedelta(hours=9))


def _get_active_agent() -> str:
    """agent_state.json에서 현재 활성 에이전트 이름을 읽는다."""
    try:
        state_path = PROJECT_DIR / "data" / "agent_state.json"
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            return state.get("active_agent", "conservative")
    except Exception:
        pass
    return "conservative"


def _action_to_direction(action: float) -> str:
    """연속 행동값 [-1, 1]을 방향 문자열로 변환."""
    if action > 0.3:
        return "buy"
    elif action < -0.3:
        return "sell"
    return "hold"


def _normalize_portfolio_btc(portfolio: dict) -> dict:
    """get_portfolio.py의 holdings list 형식을 agents/orchestrator가 기대하는 dict로 정규화.

    매도 평가가 운영에서 0건이던 근본 원인 — 데이터 구조 미스매치 해결.

    get_portfolio 출력: holdings: [{"currency": "BTC", "balance": ..., "eval_amount": ..., "profit_loss_pct": ...}]
    agents 기대:       portfolio["btc"]: {"balance": ..., "eval_amount": ..., "profit_pct": ...}

    profit_pct/evaluation은 agents/orchestrator가 사용하는 별칭 키.
    """
    btc: dict = {}
    # 1순위: holdings list에서 BTC 추출
    for h in portfolio.get("holdings", []) or []:
        if isinstance(h, dict) and h.get("currency") == "BTC":
            btc = dict(h)
            break
    # 2순위: 기존 coins.BTC / btc 키 (백테스트/테스트 호환)
    if not btc:
        btc = portfolio.get("coins", {}).get("BTC") or portfolio.get("btc") or {}
        if isinstance(btc, dict):
            btc = dict(btc)
        else:
            btc = {}

    # 별칭 키 채우기 (agents 코드 호환)
    if "profit_pct" not in btc and "profit_loss_pct" in btc:
        btc["profit_pct"] = btc["profit_loss_pct"]
    if "evaluation" not in btc and "eval_amount" in btc:
        btc["evaluation"] = btc["eval_amount"]

    return btc


def get_rl_advisory(market_data: dict, external_data: dict,
                    portfolio: dict, agent_state: dict,
                    regime_weights: dict | None = None,
                    disabled_models: list | None = None,
                    current_regime: str | None = None) -> dict | None:
    """Phase 2.5: RL 모델 어드바이저리 시그널 (다중 모델 앙상블).

    사용 가능한 모든 RL 모델의 시그널을 수집하고, 가중 평균 앙상블로
    최종 어드바이저리를 생성한다. 개별 모델은 모두 선택적(try/except).

    지원 모델:
      1. SB3 (PPO/SAC/TD3) -- data/rl_models/best/best_model.zip
      2. Decision Transformer -- data/rl_models/transformer/dt_model.pt
      3. Multi-Agent Consensus -- data/rl_models/multi_agent/
      4. Offline RL (CQL/BCQ) -- data/rl_models/offline/
      5. Historical Regime Expert -- data/rl_models/historical/regime_{regime}_{algo}.zip
    """
    advisories = {}

    # 공통 StateEncoder (한 번만 초기화)
    encoder = None
    obs = None
    try:
        from rl_hybrid.rl.state_encoder import StateEncoder
        encoder = StateEncoder()
        obs = encoder.encode(market_data, external_data, portfolio, agent_state)
    except Exception as e:
        log(f"RL StateEncoder 초기화 실패: {e}")

    # ── 1. 기존 SB3 모델 (PPO/SAC/TD3) ──
    try:
        # SB3 존재 여부를 가볍게 확인 (policy.py import 시 SB3 전체 로딩 방지)
        import importlib.util
        _sb3_available = importlib.util.find_spec("stable_baselines3") is not None
        if _sb3_available and obs is not None:
            model_path = str(PROJECT_DIR / "data" / "rl_models" / "best" / "best_model")
            if (PROJECT_DIR / "data" / "rl_models" / "best" / "best_model.zip").exists():
                # 알고리즘 감지: model_info.json이 있으면 해당 알고리즘 사용
                algo = "ppo"  # 기본값 (폴백)
                info_path = PROJECT_DIR / "data" / "rl_models" / "best" / "model_info.json"
                if info_path.exists():
                    try:
                        with open(info_path, encoding="utf-8") as f:
                            model_info = json.load(f)
                        algo = model_info.get("algorithm", "ppo")
                    except (json.JSONDecodeError, KeyError):
                        pass

                from rl_hybrid.rl.train import get_trader_class
                TraderClass = get_trader_class(algo)
                trader = TraderClass(env=None, model_path=model_path)
                sb3_action = trader.predict(obs)
                advisories["sb3"] = {
                    "action": round(float(sb3_action), 4),
                    "source": f"sb3_{algo}",
                }
                log(f"  SB3({algo}): action={sb3_action:.4f}")
    except Exception as e:
        log(f"  SB3 advisory 실패: {e}")

    # ── 2. Decision Transformer ──
    try:
        dt_model_path = PROJECT_DIR / "data" / "rl_models" / "transformer" / "dt_model.pt"
        if dt_model_path.exists() and obs is not None:
            from rl_hybrid.rl.decision_transformer import DTPredictor
            predictor = DTPredictor(model_path=str(dt_model_path))
            # 활성 에이전트에 맞게 리스크 프로파일 설정
            active_agent = agent_state.get("active_agent", _get_active_agent())
            predictor.set_risk_profile(active_agent)
            # 시장 상황으로 RTG 동적 조정
            danger = agent_state.get("danger_score", 50)
            opportunity = agent_state.get("opportunity_score", 50)
            predictor.adjust_rtg_for_market(danger, opportunity)
            dt_action = predictor.predict(obs)
            advisories["dt"] = {
                "action": round(float(dt_action), 4),
                "source": "decision_transformer",
            }
            log(f"  DT: action={dt_action:.4f} (agent={active_agent})")
    except Exception as e:
        log(f"  Decision Transformer advisory 실패: {e}")

    # ── 3. Multi-Agent Consensus ──
    try:
        from rl_hybrid.config import SystemConfig
        cfg = SystemConfig()
        if cfg.multi_agent.enabled:
            from rl_hybrid.rl.multi_agent_consensus import MultiAgentPredictor
            ma_predictor = MultiAgentPredictor()
            ma_result = ma_predictor.predict(
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio,
                agent_state=agent_state,
            )
            if ma_result and ma_result.get("action", 0) != 0:
                advisories["multi_agent"] = {
                    "action": round(float(ma_result["action"]), 4),
                    "source": "multi_agent_consensus",
                    "consensus": ma_result.get("consensus"),
                }
                log(f"  Multi-Agent: action={ma_result['action']:.4f}")
    except Exception as e:
        log(f"  Multi-Agent Consensus advisory 실패: {e}")

    # ── 4. Offline RL (CQL/BCQ) ──
    try:
        offline_dir = PROJECT_DIR / "data" / "rl_models" / "offline"
        if offline_dir.exists() and obs is not None:
            # 최신 모델 파일 찾기 (cql_*.pt 또는 bcq_*.pt)
            import glob
            offline_models = sorted(
                glob.glob(str(offline_dir / "*.pt")),
                key=os.path.getmtime,
                reverse=True,
            )
            if offline_models:
                best_offline = offline_models[0]
                offline_algo = "cql" if "cql" in os.path.basename(best_offline).lower() else "bcq"
                if offline_algo == "cql":
                    from rl_hybrid.rl.offline_rl import CQLTrainer
                    trainer = CQLTrainer()
                    trainer.load(best_offline)
                    offline_action = trainer.predict(obs)
                else:
                    from rl_hybrid.rl.offline_rl import BCQTrainer
                    trainer = BCQTrainer()
                    trainer.load(best_offline)
                    offline_action = trainer.predict(obs)
                advisories["offline"] = {
                    "action": round(float(offline_action), 4),
                    "source": f"offline_{offline_algo}",
                }
                log(f"  Offline RL({offline_algo}): action={offline_action:.4f}")
    except Exception as e:
        log(f"  Offline RL advisory 실패: {e}")

    # ── 5. Historical Regime Expert (7년 역사 데이터 전문 모델) ──
    # 레짐별 최적 알고리즘: bull→SAC, bear→PPO, sideways→TD3, volatile→PPO
    REGIME_BEST_ALGO = {
        "bull_strong": "sac",
        "bull_weak": "sac",
        "bear_strong": "ppo",
        "bear_weak": "ppo",
        "sideways": "td3",
        "volatile": "ppo",
    }
    try:
        regime = current_regime or "sideways"
        best_algo = REGIME_BEST_ALGO.get(regime, "ppo")
        hist_model_path = str(PROJECT_DIR / "data" / "rl_models" / "historical" / f"regime_{regime}_{best_algo}")
        hist_zip = PROJECT_DIR / "data" / "rl_models" / "historical" / f"regime_{regime}_{best_algo}.zip"

        if hist_zip.exists() and obs is not None:
            from rl_hybrid.rl.train import get_trader_class as _get_tc
            HistTrader = _get_tc(best_algo)
            hist_trader = HistTrader(env=None, model_path=hist_model_path)
            hist_action = hist_trader.predict(obs)
            advisories["historical"] = {
                "action": round(float(hist_action), 4),
                "source": f"historical_{regime}_{best_algo}",
            }
            log(f"  Historical({regime}/{best_algo}): action={hist_action:.4f}")
        else:
            # 레짐 모델 없으면 crisis 모델 시도
            crisis_path = str(PROJECT_DIR / "data" / "rl_models" / "historical" / "crisis_sac")
            crisis_zip = PROJECT_DIR / "data" / "rl_models" / "historical" / "crisis_sac.zip"
            if crisis_zip.exists() and obs is not None:
                from rl_hybrid.rl.train import get_trader_class as _get_tc2
                CrisisTrader = _get_tc2("sac")
                crisis_trader = CrisisTrader(env=None, model_path=crisis_path)
                crisis_action = crisis_trader.predict(obs)
                advisories["historical"] = {
                    "action": round(float(crisis_action), 4),
                    "source": "historical_crisis_sac",
                }
                log(f"  Historical(crisis/sac fallback): action={crisis_action:.4f}")
    except Exception as e:
        log(f"  Historical Regime Expert 실패: {e}")

    # ── 5.5. Feedback Hub 비활성 모델 제거 ──
    if disabled_models:
        for dm in disabled_models:
            if dm in advisories:
                log(f"  Feedback Hub: {dm} 모델 비활성 → 앙상블에서 제외")
                del advisories[dm]

    # ── 5. 앙상블: 레짐 가중 평균 (또는 균등 평균) ──
    if not advisories:
        return None

    if regime_weights:
        # 레짐별 가중치 적용
        weighted_sum = 0.0
        weight_total = 0.0
        for model_key, info in advisories.items():
            w = regime_weights.get(model_key, 0.25)
            weighted_sum += info["action"] * w
            weight_total += w
        ensemble_action = weighted_sum / weight_total if weight_total > 0 else 0.0
        log(f"  앙상블: 레짐 가중 평균 (weights={regime_weights})")
    else:
        actions = [v["action"] for v in advisories.values() if "action" in v]
        ensemble_action = sum(actions) / len(actions) if actions else 0.0
    ensemble_direction = _action_to_direction(ensemble_action)

    # ── 6. DB 기록: 앙상블 추론 결과 ──
    try:
        from rl_hybrid.rl.rl_db_logger import log_prediction as _log_pred

        # 개별 모델 액션/버전 추출
        sb3_info = advisories.get("sb3", {})
        dt_info = advisories.get("dt", {})
        ma_info = advisories.get("multi_agent", {})
        offline_info = advisories.get("offline", {})

        # SB3 버전: model_info.json에서 읽기
        sb3_ver = None
        try:
            _info_path = PROJECT_DIR / "data" / "rl_models" / "best" / "model_info.json"
            if _info_path.exists():
                with open(_info_path) as _f:
                    sb3_ver = json.load(_f).get("version_id")
        except Exception:
            pass

        # Multi-Agent 세부 액션 추출
        ma_consensus = ma_info.get("consensus", {}) if ma_info else {}
        ma_scalp = ma_consensus.get("scalp_action") if isinstance(ma_consensus, dict) else None
        ma_swing = ma_consensus.get("swing_action") if isinstance(ma_consensus, dict) else None

        # 시장 컨텍스트
        ticker = market_data.get("ticker", {})
        indicators = market_data.get("indicators", {})
        fgi_data = market_data.get("fear_greed", {})

        _log_pred(
            cycle_id=_CYCLE_ID,
            ensemble_action=round(ensemble_action, 4),
            ensemble_direction=ensemble_direction,
            num_models=len(advisories),
            sb3_action=sb3_info.get("action"),
            sb3_version=sb3_ver,
            dt_action=dt_info.get("action"),
            dt_version=None,
            multi_agent_action=ma_info.get("action"),
            multi_agent_direction=_action_to_direction(ma_info["action"]) if ma_info.get("action") is not None else None,
            multi_agent_scalp_action=ma_scalp,
            multi_agent_swing_action=ma_swing,
            offline_action=offline_info.get("action"),
            offline_version=None,
            btc_price=market_data.get("current_price") or ticker.get("trade_price"),
            rsi_14=indicators.get("rsi_14"),
            fgi=fgi_data.get("value"),
            danger_score=agent_state.get("danger_score"),
            opportunity_score=agent_state.get("opportunity_score"),
        )
    except Exception as _db_err:
        log(f"RL 추론 DB 기록 실패 (비치명적): {_db_err}")

    return {
        "action": round(ensemble_action, 4),
        "abs_action": round(abs(ensemble_action), 4),
        "direction": ensemble_direction,
        "models": advisories,
        "sources": list(advisories.keys()),
        "num_models": len(advisories),
    }


# cycle_id: 이 파이프라인 실행의 모든 DB 기록을 연결하는 키
try:
    from scripts.cycle_id import make_cycle_id, set_cycle_id
    _CYCLE_ID = make_cycle_id("agent")
    set_cycle_id(_CYCLE_ID)
except Exception:
    _CYCLE_ID = datetime.now(KST).strftime("%Y%m%d-%H%M") + "-agent"


def log(msg: str):
    print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] {msg}", file=sys.stderr)


def notify_error(msg: str, detail: str):
    log(f"ERROR: {msg}")
    try:
        import subprocess
        from scripts.hide_console import subprocess_kwargs
        from utils.machine import get_machine_name
        tagged_msg = f"{msg} [{get_machine_name()}]"
        subprocess.run(
            [sys.executable, "scripts/notify_telegram.py", "error", tagged_msg, detail],
            cwd=str(PROJECT_DIR),
            check=False,
            capture_output=True,
            **subprocess_kwargs(),
        )
    except Exception as e:
        log(f"텔레그램 전송 실패: {e}")


async def run_script(script_name: str) -> dict:
    """별도 프로세스로 스크립트를 실행하여 JSON 결과 반환"""
    from scripts.hide_console import subprocess_kwargs
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, f"scripts/{script_name}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_DIR),
            **subprocess_kwargs(),
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            log(f"스크립트 {script_name} 실패: {stderr.decode('utf-8', errors='ignore')}")
            return {"error": f"{script_name} 실패: {proc.returncode}"}
        
        return json.loads(stdout.decode('utf-8', errors='replace'))
    except Exception as e:
        log(f"스크립트 {script_name} 실행 중 예외: {e}")
        return {"error": str(e)}


async def collect_internal_data() -> tuple[dict, dict, dict]:
    """Phase 1: 마켓, 포트폴리오, AI 시그널 동시 수집"""
    log("Phase 1: 내부 데이터 수집...")
    results = await asyncio.gather(
        run_script("collect_market_data.py"),
        run_script("get_portfolio.py"),
        run_script("collect_ai_signal.py"),
        return_exceptions=True
    )
    
    market_data = results[0] if not isinstance(results[0], Exception) else {"error": "market_data 수집 실패"}
    portfolio = results[1] if not isinstance(results[1], Exception) else {"error": "portfolio 수집 실패"}
    ai_signal = results[2] if not isinstance(results[2], Exception) else {"error": "ai_signal 수집 실패"}
    
    log("Phase 1 완료.")
    return market_data, portfolio, ai_signal


def supabase_headers() -> dict:
    """Supabase REST API 공통 헤더"""
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def save_execution_log(
    execution_mode: str,
    duration_ms: int,
    data_sources: dict | None = None,
    errors: dict | None = None,
    raw_output: str | None = None,
    decision_id: str | None = None,
    phases_completed: list | None = None,
) -> bool:
    """execution_logs 테이블에 파이프라인 실행 기록을 저장한다."""
    from utils.machine import skip_trade_db
    if skip_trade_db("execution_logs"):
        return False
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        log("execution_logs 저장 스킵: Supabase 미설정")
        return False

    has_errors = bool(errors and errors.get("pipeline_errors"))
    from utils.machine import get_machine_name
    row = {
        "execution_mode": execution_mode,
        "duration_ms": duration_ms,
        "data_sources": json.dumps(data_sources or {}, ensure_ascii=False),
        "errors": json.dumps(errors or {}, ensure_ascii=False),
        "cycle_id": _CYCLE_ID,
        "success": not has_errors,
        "execution_started_at": datetime.now(KST).isoformat(),
        "execution_completed_at": datetime.now(KST).isoformat(),
        "machine_name": get_machine_name(),
    }
    if phases_completed:
        row["phases_completed"] = json.dumps(phases_completed, ensure_ascii=False)
    if raw_output:
        row["raw_output"] = raw_output[:10000]  # 10KB 제한
    if decision_id:
        row["decision_id"] = decision_id

    try:
        resp = requests.post(
            f"{supabase_url}/rest/v1/execution_logs",
            json=row,
            headers=supabase_headers(),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            log("execution_logs 기록 완료")
            return True
        else:
            log(f"execution_logs 기록 실패 (HTTP {resp.status_code}): {resp.text[:300]}")
            return False
    except Exception as e:
        log(f"execution_logs 기록 예외: {e}")
        return False


def save_market_data_record(market_data: dict, external_data: dict) -> bool:
    """market_data 테이블에 시장 데이터 스냅샷을 저장한다."""
    from utils.machine import skip_trade_db
    if skip_trade_db("market_data"):
        return False
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        log("market_data 저장 스킵: Supabase 미설정")
        return False

    ticker = market_data.get("ticker", {})
    indicators = market_data.get("indicators", {})
    fgi = market_data.get("fear_greed", {})
    news = market_data.get("news", {})

    price = market_data.get("current_price") or ticker.get("trade_price", 0)
    volume_24h = market_data.get("volume_24h") or ticker.get("acc_trade_volume_24h")
    change_rate = market_data.get("change_rate_24h") or ticker.get("signed_change_rate")

    from utils.machine import get_machine_name
    row = {
        "market": "KRW-BTC",
        "price": int(price) if price else 0,
        "volume_24h": float(volume_24h) if volume_24h else None,
        "change_rate_24h": float(change_rate) if change_rate else None,
        "fear_greed_value": fgi.get("value"),
        "fear_greed_class": fgi.get("value_classification"),
        "rsi_14": indicators.get("rsi_14"),
        "sma_20": int(indicators.get("sma_20")) if indicators.get("sma_20") else None,
        "news_sentiment": news.get("overall_sentiment", "neutral"),
        "cycle_id": _CYCLE_ID,
        "machine_name": get_machine_name(),
    }

    try:
        resp = requests.post(
            f"{supabase_url}/rest/v1/market_data",
            json=row,
            headers=supabase_headers(),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            log("market_data 기록 완료")
            return True
        else:
            log(f"market_data 기록 실패 (HTTP {resp.status_code}): {resp.text[:300]}")
            return False
    except Exception as e:
        log(f"market_data 기록 예외: {e}")
        return False


def main():
    load_dotenv(PROJECT_DIR / ".env")

    # 파이프라인 시작 시간 기록
    pipeline_start = time.time()
    pipeline_errors = []
    data_sources_used = []

    # 1. 수동 긴급 정지 확인
    if os.environ.get("EMERGENCY_STOP", "false").lower() == "true":
        log("[STOP] 사용자 EMERGENCY_STOP 활성화됨. 실행 중단.")
        notify_error("EMERGENCY_STOP", "사용자 긴급 정지 활성화로 에이전트 실행 중단")
        sys.exit(1)
        
    # 2. 감독 자동 긴급 정지 확인
    auto_emergency_file = PROJECT_DIR / "data" / "auto_emergency.json"
    if auto_emergency_file.exists():
        try:
            with open(auto_emergency_file, "r", encoding="utf-8") as f:
                auto_em = json.load(f)
            if auto_em.get("active"):
                reason = auto_em.get("reason", "알 수 없음")
                log(f"[STOP] 감독 자동 긴급정지 활성 중: {reason}")
                log("[STOP] Orchestrator가 해제 조건을 평가합니다...")
        except Exception:
            pass
            
    timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = PROJECT_DIR / "data" / "snapshots" / timestamp
    log_dir = PROJECT_DIR / "logs" / "executions"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log("═══ Python 에이전트 모드 시작 ═══")

    # Phase 1
    market_data, portfolio, ai_signal = asyncio.run(collect_internal_data())

    # 데이터 소스 추적
    if "error" not in market_data:
        data_sources_used.append("market_data")
    else:
        pipeline_errors.append({"phase": "phase1", "source": "market_data", "error": market_data.get("error")})
    if "error" not in portfolio:
        data_sources_used.append("portfolio")
    else:
        pipeline_errors.append({"phase": "phase1", "source": "portfolio", "error": portfolio.get("error")})
    if "error" not in ai_signal:
        data_sources_used.append("ai_signal")
    else:
        pipeline_errors.append({"phase": "phase1", "source": "ai_signal", "error": ai_signal.get("error")})
    
    with open(snapshot_dir / "market_data.json", "w", encoding="utf-8") as f:
        json.dump(market_data, f, ensure_ascii=False)
    with open(snapshot_dir / "portfolio.json", "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False)
    with open(snapshot_dir / "ai_signal.json", "w", encoding="utf-8") as f:
        json.dump(ai_signal, f, ensure_ascii=False)
        
    # Phase 2: 파이프라인 실행
    log("Phase 2: 에이전트 파이프라인 실행...")
    
    try:
        ext_agent = ExternalDataAgent(snapshot_dir=snapshot_dir)
        external_data = ext_agent.collect_all()
        # NVT Signal을 최상위에 배치 (StateEncoder 호환)
        nvt_data = external_data.get("sources", {}).get("nvt", {})
        external_data["nvt_signal"] = nvt_data.get("nvt_signal", 100.0)
        log(f"외부 데이터 수집 완료 ({external_data.get('collection_time_sec', 0)}초)")
        data_sources_used.append("external_data")
        ext_errors = external_data.get("errors", [])
        if ext_errors:
            pipeline_errors.append({"phase": "phase2", "source": "external_data", "errors": ext_errors})
        
        # 데이터 병합
        market_data["ai_composite_signal"] = ai_signal.get("ai_composite_signal", ai_signal.get("composite_signal", {}))
        
        fgi_data = external_data.get("sources", {}).get("fear_greed", {})
        market_data["fear_greed"] = fgi_data.get("current", {})
        
        news_data = external_data.get("sources", {}).get("news", {})
        if not isinstance(news_data, dict):
            news_data = {}
        market_data["news"] = news_data
        news_sentiment = external_data.get("sources", {}).get("news_sentiment", {})
        market_data["news"]["overall_sentiment"] = news_sentiment.get("overall_sentiment", "neutral")
        market_data["news"]["sentiment_score"] = news_sentiment.get("sentiment_score", 0)
        
        # RAG: 현재 시장과 유사한 과거 경험 조회 (LIMIT 10 → 벡터 유사도 Top 3)
        past_decisions = []
        try:
            import subprocess as _sp
            from scripts.hide_console import subprocess_kwargs
            rag_result = _sp.run(
                [sys.executable, "scripts/recall_rag.py", "--json", "--top", "3"],
                cwd=str(PROJECT_DIR),
                capture_output=True, text=True, timeout=30,
                **subprocess_kwargs(),
            )
            if rag_result.returncode == 0 and rag_result.stdout.strip():
                rag_data = json.loads(rag_result.stdout)
                if isinstance(rag_data, dict) and rag_data.get("results"):
                    past_decisions = rag_data["results"]
                    log(f"RAG: 유사 과거 경험 {len(past_decisions)}건 조회")
                elif isinstance(rag_data, list) and rag_data:
                    past_decisions = rag_data
                    log(f"RAG: 유사 과거 경험 {len(rag_data)}건 조회")
        except Exception as e:
            log(f"RAG 조회 실패 (fallback): {e}")

        # RAG 실패 시 기존 방식 fallback (최근 5건만)
        if not past_decisions:
            supabase_url = os.environ.get("SUPABASE_URL", "")
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            if supabase_url and supabase_key:
                try:
                    resp = requests.get(
                        f"{supabase_url}/rest/v1/decisions",
                        params={"select": "id,decision,reason,confidence,current_price,profit_loss,created_at", "order": "created_at.desc", "limit": "5"},
                        headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        past_decisions = resp.json()
                        log(f"RAG fallback: 최근 {len(past_decisions)}건 조회")
                except Exception as e:
                    log(f"Supabase 조회 실패: {e}")
                
        # 포트폴리오 메타 데이터 주입 — holdings list를 정규화해 portfolio["btc"]로 노출
        btc_info = _normalize_portfolio_btc(portfolio)
        total_eval = portfolio.get("total_eval", 0)
        btc_eval = btc_info.get("eval_amount", 0)
        portfolio["btc_ratio"] = btc_eval / total_eval if total_eval > 0 else 0
        portfolio["btc"] = btc_info
        
        # 오케스트레이터 실행
        orchestrator = Orchestrator()
        result = orchestrator.run(
            market_data=market_data,
            external_data=external_data,
            portfolio=portfolio,
            past_decisions=past_decisions,
        )
        log(f"결정: {result.get('decision', {}).get('decision', '?')} by {result['active_agent']}")
        
        output = {
            "timestamp": external_data.get("timestamp", datetime.now(KST).isoformat()),
            "active_agent": result["active_agent"],
            "switch": result.get("switch"),
            "decision": result["decision"],
            "external_data_summary": {
                "collection_time_sec": external_data.get("collection_time_sec"),
                "errors": external_data.get("errors"),
                "signal": external_data.get("external_signal", {}),
            },
            "snapshot_dir": str(snapshot_dir),
            # DB 연결용 ID
            "external_signal_id": ext_agent.saved_signal_id,
            "buy_score_id": result.get("buy_score_id"),
        }
        
    except Exception as e:
        log(f"Phase 2 실패: {e}")
        import traceback
        traceback.print_exc()
        pipeline_errors.append({"phase": "phase2", "source": "orchestrator", "error": str(e)})
        # 실패해도 execution_logs는 기록
        duration_ms = int((time.time() - pipeline_start) * 1000)
        save_execution_log(
            execution_mode="dry_run" if os.environ.get("DRY_RUN", "true").lower() == "true" else "execute",
            duration_ms=duration_ms,
            data_sources={"sources": data_sources_used},
            errors={"pipeline_errors": pipeline_errors, "fatal": str(e)},
            phases_completed=["phase1"],
        )
        notify_error("Agent Pipeline", f"에이전트 파이프라인 실패: {e}")
        sys.exit(1)
        
    log("Phase 2 완료.")

    # Phase 2.4: 시장 레짐 감지 + Feedback Hub confidence 보정
    regime_info = None
    try:
        from scripts.regime_detector import detect_regime
        regime_info = detect_regime(
            rsi=market_data.get("indicators", {}).get("rsi_14"),
            fgi=market_data.get("fear_greed", {}).get("value"),
            change_rate_24h=market_data.get("change_rate_24h") or market_data.get("ticker", {}).get("signed_change_rate"),
            atr_pct=None,  # bollinger proxy는 detect_regime_from_market_data에서 계산
        )
        log(f"레짐 감지: {regime_info['regime']} ({regime_info['description']}, conf={regime_info['confidence']:.0%})")
        output["regime"] = regime_info
    except Exception as e:
        log(f"Phase 2.4 레짐 감지 예외: {e}")

    # Feedback Hub: confidence 자동 보정 + 비활성 RL 모델 체크
    confidence_adj = 0.0
    disabled_rl_models = []
    try:
        from scripts.feedback_hub import get_confidence_adjustment, get_disabled_rl_models
        confidence_adj = get_confidence_adjustment()
        disabled_rl_models = get_disabled_rl_models()
        if confidence_adj != 0:
            orig = output["decision"].get("confidence", 0.5)
            adjusted = max(0.0, min(1.0, orig + confidence_adj))
            output["decision"]["confidence"] = adjusted
            log(f"Feedback Hub confidence 보정: {orig:.2f} → {adjusted:.2f} (adj={confidence_adj:+.3f})")
        if disabled_rl_models:
            log(f"Feedback Hub 비활성 RL 모델: {disabled_rl_models}")
    except Exception as e:
        log(f"Feedback Hub 보정 예외: {e}")

    # Phase 2.5: RL 모델 어드바이저리
    rl_advisory = None
    agent_state_for_rl = {}
    try:
        market_state = result.get("market_state", {})
        agent_state_for_rl = {
            "active_agent": output.get("active_agent", "conservative"),
            "danger_score": market_state.get("danger_score", 50),
            "opportunity_score": market_state.get("opportunity_score", 50),
            "consecutive_losses": market_state.get("consecutive_losses", 0),
        }
        _regime_weights = regime_info.get("weights") if regime_info else None
        _current_regime = regime_info.get("regime") if regime_info else None
        rl_advisory = get_rl_advisory(
            market_data, external_data, portfolio, agent_state_for_rl,
            regime_weights=_regime_weights,
            disabled_models=disabled_rl_models,
            current_regime=_current_regime,
        )
        if rl_advisory:
            sources = ", ".join(rl_advisory.get("sources", []))
            log(f"RL advisory: {rl_advisory['direction']} (action={rl_advisory['action']:.4f}, models=[{sources}])")
            output["rl_advisory"] = rl_advisory

            # 에이전트 결정과 RL 방향 비교하여 confidence 조정
            agent_decision = output["decision"]["decision"]
            rl_dir = rl_advisory["direction"]
            rl_strength = rl_advisory["abs_action"]
            orig_conf = output["decision"].get("confidence", 0.5)

            if agent_decision == rl_dir:
                # 일치: confidence 부스트 (최대 +10%)
                boost = min(0.10, rl_strength * 0.15)
                output["decision"]["confidence"] = min(1.0, orig_conf + boost)
                log(f"RL 일치 → confidence {orig_conf:.2f} → {output['decision']['confidence']:.2f}")
            elif rl_dir == "hold":
                pass  # RL이 hold이면 간섭 안 함
            elif agent_decision == "hold" and rl_strength > 0.5:
                # 에이전트 관망인데 RL이 강한 시그널 → advisory 메모만
                output["decision"]["rl_override_hint"] = rl_dir
                log(f"RL 강한 시그널({rl_dir}, {rl_strength:.2f}) -- advisory 메모 추가")
            else:
                # 불일치: confidence 감소 (최대 -20%)
                dampen = min(0.20, rl_strength * 0.25)
                output["decision"]["confidence"] = max(0.0, orig_conf - dampen)
                log(f"RL 불일치({rl_dir}) → confidence {orig_conf:.2f} → {output['decision']['confidence']:.2f}")
        else:
            log("RL advisory: 모델 없음 또는 비활성")
    except Exception as e:
        log(f"Phase 2.5 RL advisory 예외: {e}")

    # Phase 2.6: Kelly Criterion 포지션 사이징
    try:
        agent_decision_type = output["decision"]["decision"]
        if agent_decision_type in ("buy", "sell") and output["decision"].get("trade_params"):
            from agents.base_agent import kelly_position_size

            final_conf = output["decision"].get("confidence", 0.5)

            # 승률 조회 (에이전트별)
            win_rate = 0.5
            try:
                from agents.base_agent import BaseStrategyAgent
                # orchestrator에서 활성 에이전트 가져오기
                active = output.get("active_agent", "conservative")
                agent_map = {
                    "conservative": "agents.conservative",
                    "moderate": "agents.moderate",
                    "aggressive": "agents.aggressive",
                }
                if active in agent_map:
                    mod = __import__(agent_map[active], fromlist=["*"])
                    agent_cls = [c for c in dir(mod) if not c.startswith("_")]
                    for name in agent_cls:
                        obj = getattr(mod, name, None)
                        if isinstance(obj, type) and issubclass(obj, BaseStrategyAgent) and obj is not BaseStrategyAgent:
                            win_rate = obj()._get_historical_win_rate(30)
                            break
            except Exception:
                pass

            tp = output["decision"]["trade_params"]
            if agent_decision_type == "buy" and tp.get("amount"):
                base_amount = int(tp["amount"])
                kelly_amount, kelly_frac = kelly_position_size(final_conf, base_amount, win_rate)
                log(f"Kelly 사이징: {base_amount:,} → {kelly_amount:,}원 (conf={final_conf:.2f}, wr={win_rate:.2f}, frac={kelly_frac})")
                tp["amount"] = kelly_amount
                output["decision"]["kelly_applied"] = True
                output["decision"]["kelly_fraction"] = kelly_frac
                output["decision"]["kelly_base_amount"] = base_amount
    except Exception as e:
        log(f"Phase 2.6 Kelly 사이징 예외: {e}")

    agent_result_path = snapshot_dir / "agent_result.json"
    with open(agent_result_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Phase 3: 매매 실행
    decision = output["decision"]["decision"]
    reason = output["decision"]["reason"]
    agent_name = output["active_agent"]
    switch_sw = output.get("switch")
    switch_info = f"전략 전환: {switch_sw['from']} → {switch_sw['to']} ({switch_sw['reason']})" if switch_sw else "전환 없음"
    
    log(f"Phase 3: 매매 실행 -- {decision} ({agent_name})")
    
    trade_params = output["decision"].get("trade_params", {})
    market = trade_params.get("market", "KRW-BTC")

    # ── Phase I core/ 게이트 wiring (WP1/WP2/WP3) ──────────────────────────────
    # INV_CORE_GATE 옵트인(기본 off=레거시 byte-identical 보존=SACRED·무회귀).
    # on: 신규 core/ 안전 백스톱(RiskGate)+학습 로깅(MemoryLayer)을 라이브 경로에 연결.
    # try/except 로 라이브 절대 미크래시(예외=레거시 경로 유지). DRY_RUN/execute_trade 미변경.
    if os.environ.get("INV_CORE_GATE", "false").lower() == "true" and decision in ("buy", "sell"):
        try:
            from core.risk_gate import RiskGate, VerdictType
            from core.brain.memory_layer import MemoryLayer

            _btc = portfolio.get("btc", {}) if isinstance(portfolio, dict) else {}
            _pnl = float(_btc.get("profit_rate", 0.0) or 0.0) / 100.0
            _proposed = float(
                (trade_params.get("amount", 0) if decision == "buy"
                 else trade_params.get("volume", 0)) or 0
            )
            _verdict = RiskGate().check(
                cycle_id=str(timestamp),
                action=decision,
                proposed_size=_proposed,
                position_pnl_pct=_pnl,
            )
            try:  # WP3: 결정 로깅(S9) — 학습 메모리
                MemoryLayer().store_decision(
                    decision=decision,
                    reason=str(reason),
                    confidence=float(output["decision"].get("confidence", 0.0) or 0.0),
                    asset=market,
                )
            except Exception as _me:
                log(f"[core-gate] memory 로깅 예외(무시): {_me}")
            try:  # WP4: 거시 레짐 분류 chain — FRED_API_KEY 있으면 실데이터, 없으면 NullFredAdapter stub
                from core.brain.regime_classifier import RegimeClassifier
                _fred_key = os.environ.get("FRED_API_KEY", "")
                if _fred_key:
                    from core.brain.fred_adapter import RealFredAdapter
                    _clf = RegimeClassifier(usd_adapter=RealFredAdapter(api_key=_fred_key))
                else:
                    _clf = RegimeClassifier()
                _mv = _clf.classify()
                _st = getattr(_mv, "status", None)
                log(f"[core-gate] 거시 레짐 chain 가동: status={getattr(_st, 'value', _st)} "
                    f"fred={'real' if _fred_key else 'stub'} regimes={getattr(_mv, 'regimes', {})}")
            except Exception as _re:
                log(f"[core-gate] 레짐 분류 예외(무시): {_re}")
            if _verdict.verdict == VerdictType.REJECTED:  # WP2: 우회불가 백스톱
                log(f"[core-gate] RiskGate 거부 → 주문 차단(hold): {_verdict.reason}")
                decision = "hold"
            elif _verdict.verdict == VerdictType.REDUCED and _verdict.adjusted_size:
                log(f"[core-gate] RiskGate 사이즈 축소 권고: {_verdict.adjusted_size} ({_verdict.reason})")
        except Exception as _ge:
            log(f"[core-gate] 예외 → 레거시 경로 유지: {_ge}")
    # ──────────────────────────────────────────────────────────────────────────

    import subprocess
    from scripts.hide_console import subprocess_kwargs
    trade_log = str(log_dir / f"trade_{timestamp}.log")

    if decision == "buy":
        amount = trade_params.get("amount", 0)
        is_dca = trade_params.get("is_dca", False)
        if float(amount or 0) > 0:
            dca_tag = " [DCA]" if is_dca else ""
            log(f"매수 실행: {market} {amount} KRW{dca_tag}")
            with open(trade_log, "w", encoding="utf-8") as tf:
                subprocess.run([sys.executable, "scripts/execute_trade.py", "bid", market, str(amount)], cwd=str(PROJECT_DIR), stdout=tf, stderr=subprocess.STDOUT, **subprocess_kwargs())
    elif decision == "sell":
        volume = trade_params.get("volume", 0)
        sell_all = trade_params.get("sell_all", False)
        if sell_all:
            # sell_all 플래그: 포트폴리오에서 BTC 잔고를 조회하여 전량 매도
            btc_bal = float(portfolio.get("btc", {}).get("balance", 0))
            if btc_bal > 0:
                volume = btc_bal
        if float(volume or 0) > 0:
            log(f"매도 실행: {market} {volume} BTC")
            with open(trade_log, "w", encoding="utf-8") as tf:
                subprocess.run([sys.executable, "scripts/execute_trade.py", "ask", market, str(volume)], cwd=str(PROJECT_DIR), stdout=tf, stderr=subprocess.STDOUT, **subprocess_kwargs())
    else:
        log("관망 결정. 매매 없음.")
        
    # Phase 4: 텔레그램 알림 (풍부한 정보 전달 피드백 루프 포함)
    log("Phase 4: 텔레그램 알림...")
    buy_score = output["decision"].get("buy_score", {}).get("total", "N/A")
    confidence = round(output["decision"].get("confidence", 0) * 100)
    current_price = market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price", 0)
    fgi = market_data.get("fear_greed", {}).get("value", "N/A")
    krw_bal = float(portfolio.get("krw_balance", 0))
    # portfolio["btc"]는 _normalize_portfolio_btc로 holdings에서 정규화된 상태
    btc_bal = float(portfolio.get("btc", {}).get("balance", 0))
    btc_ratio = round(portfolio.get("btc_ratio", 0) * 100, 1)

    # 피드백 상태 조회
    state_file = PROJECT_DIR / "data" / "orchestrator_state.json"
    user_bias = 0.0
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                user_bias = state.get("feedback_bias", 0.0)
        except Exception:
            pass

    from utils.machine import get_machine_name
    machine_tag = get_machine_name()
    summary_msg = f"[{agent_name}] {decision.upper()} 결정 ({confidence}%) [{machine_tag}]"
    if rl_advisory:
        rl_parts = [f"- RL 앙상블: {rl_advisory['direction']}({rl_advisory['action']:+.4f}) [{rl_advisory.get('num_models', 1)}모델]"]
        for src, info in rl_advisory.get("models", {}).items():
            rl_parts.append(f"  · {src}: {info['action']:+.4f}")
        rl_line = "\n".join(rl_parts) + "\n"
    else:
        rl_line = ""
    detail_msg = (
        f"💡 근거: {reason}\n\n"
        f"📊 시장 현황:\n"
        f"- 현재가: {int(current_price):,}원\n"
        f"- 매수점수: {buy_score}/100\n"
        f"- 탐욕지수(FGI): {fgi}\n\n"
        f"💼 포트폴리오:\n"
        f"- 자산 비율: BTC {btc_ratio}% / KRW {100-btc_ratio:.1f}%\n"
        f"- KRW 잔고: {int(krw_bal):,}원\n"
        f"- BTC 잔고: {btc_bal:.6f} BTC\n\n"
        f"🤖 감독 상태:\n"
        f"- 사용자 피드백 Bias: {user_bias:+.2f} (음수:보수적, 양수:공격적)\n"
        f"- {switch_info}\n"
        f"{rl_line}\n"
        f"ℹ️ 피드백을 주시려면 'python scripts/feedback.py +0.5' 를 실행하세요."
    )
    
    try:
        subprocess.run([sys.executable, "scripts/notify_telegram.py", "trade", summary_msg, detail_msg], cwd=str(PROJECT_DIR), check=False, **subprocess_kwargs())
    except Exception:
        pass
        
    # Phase 5: Supabase 기록 (decisions + market_data + execution_logs)
    from utils.machine import skip_trade_db
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if supabase_url and supabase_key and not skip_trade_db("decisions"):
        log("Phase 5: Supabase 기록...")

        # 5a. decisions 테이블
        resp = None
        emb_decision_id = None  # resp.json()을 한 번만 파싱하여 추출, 5a-2에서 재사용
        try:
            DECISION_MAP = {"buy": "매수", "sell": "매도", "hold": "관망"}
            dec = output["decision"]
            buy_score_dict = dec.get("buy_score", {})
            ext_summary = dec.get("external_signal_summary", {})

            reason_parts = [dec.get("reason", "")]
            if agent_name:
                reason_parts.append(f"에이전트: {agent_name}")
            if buy_score_dict:
                reason_parts.append(f"매수점수: {buy_score_dict.get('total', '?')}/{buy_score_dict.get('threshold', '?')}")
            if ext_summary:
                reason_parts.append(f"외부시그널: {ext_summary.get('fusion_signal', '?')}({ext_summary.get('total_score', '?')})")

            raw_conf = float(dec.get("confidence") or 0)
            confidence_val = max(0.0, min(1.0, raw_conf))

            _cp_raw = market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price")
            _current_price = int(_cp_raw) if _cp_raw else None
            if _current_price is None:
                log(f"[경고] current_price 누락 — market_data keys={list(market_data.keys())[:10]}")

            decision_row = {
                "market": "KRW-BTC",
                "decision": DECISION_MAP.get(decision, decision),
                "confidence": round(confidence_val, 2),
                "reason": " | ".join(reason_parts),
                "current_price": _current_price,
                "rsi_value": market_data.get("indicators", {}).get("rsi_14"),
                "fear_greed_value": market_data.get("fear_greed", {}).get("value"),
                "sma20_price": int(market_data.get("indicators", {}).get("sma_20")) if market_data.get("indicators", {}).get("sma_20") else None,
                "market_data_snapshot": json.dumps({
                    "buy_score": buy_score_dict,
                    "external": ext_summary,
                    "rl_advisory": rl_advisory,
                    "regime": regime_info.get("regime") if regime_info else None,
                    "regime_confidence": regime_info.get("confidence") if regime_info else None,
                    "kelly_fraction": dec.get("kelly_fraction"),
                    "confidence_adj": confidence_adj,
                    "snapshot_dir": str(snapshot_dir),
                }, ensure_ascii=False),
                "cycle_id": _CYCLE_ID,
                "source": "agent",
                "machine_name": __import__("utils.machine", fromlist=["get_machine_name"]).get_machine_name(),
            }
            # 외부 정보 및 매수 점수와 직접 연결 (FK)
            if output.get("external_signal_id"):
                decision_row["external_signal_id"] = output["external_signal_id"]
            if output.get("buy_score_id"):
                decision_row["buy_score_id"] = output["buy_score_id"]
            decision_headers = supabase_headers()
            decision_headers["Prefer"] = "return=representation"
            resp = requests.post(
                f"{supabase_url}/rest/v1/decisions",
                json=decision_row,
                headers=decision_headers,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                log("decisions 기록 완료")
                # 임베딩 생성 (RAG 벡터검색용)
                try:
                    resp_data_for_emb = resp.json()
                    emb_decision_id = None
                    if isinstance(resp_data_for_emb, list) and resp_data_for_emb:
                        emb_decision_id = resp_data_for_emb[0].get("id")
                    elif isinstance(resp_data_for_emb, dict):
                        emb_decision_id = resp_data_for_emb.get("id")

                    if emb_decision_id:
                        from scripts.save_decision import generate_state_embedding, _update_embedding_via_sql
                        emb_data = {
                            "current_price": market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price"),
                            "change_rate_24h": market_data.get("change_rate_24h") or market_data.get("ticker", {}).get("signed_change_rate"),
                            "rsi_14": market_data.get("indicators", {}).get("rsi_14"),
                            "sma_20": market_data.get("indicators", {}).get("sma_20"),
                            "fear_greed_value": market_data.get("fear_greed", {}).get("value"),
                            "volume_24h": market_data.get("volume_24h") or market_data.get("ticker", {}).get("acc_trade_volume_24h"),
                            "news_sentiment": market_data.get("news", {}).get("overall_sentiment"),
                        }
                        emb_text, emb_vector = generate_state_embedding(emb_data)
                        if emb_vector:
                            _update_embedding_via_sql(emb_decision_id, emb_vector, emb_text)
                            log("임베딩 생성 완료 (RAG)")
                except Exception as emb_e:
                    log(f"임베딩 생성 실패 (비치명적): {emb_e}")

                # RL prediction에 decision_id 연결
                if emb_decision_id and rl_advisory:
                    try:
                        from rl_hybrid.rl.rl_db_logger import log_prediction as _log_pred_final
                        _log_pred_final(
                            decision_id=emb_decision_id,
                            cycle_id=_CYCLE_ID,
                            ensemble_action=round(rl_advisory.get("action", 0), 4),
                            ensemble_direction=rl_advisory.get("direction"),
                            num_models=rl_advisory.get("num_models", 0),
                            btc_price=market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price"),
                            rsi_14=market_data.get("indicators", {}).get("rsi_14"),
                            fgi=market_data.get("fear_greed", {}).get("value"),
                            danger_score=result.get("market_state", {}).get("danger_score"),
                            opportunity_score=result.get("market_state", {}).get("opportunity_score"),
                        )
                        log("RL prediction DB 기록 (decision_id 연결)")
                    except Exception as _rl_db_err:
                        log(f"RL prediction DB 기록 실패 (비치명적): {_rl_db_err}")
            else:
                log(f"decisions 기록 실패 (HTTP {resp.status_code}): {resp.text[:300]}")
                pipeline_errors.append({"phase": "phase5", "source": "decisions", "error": resp.text[:300]})
        except Exception as e:
            log(f"decisions 기록 예외: {e}")
            pipeline_errors.append({"phase": "phase5", "source": "decisions", "error": str(e)})

        # 5a-2. market_context_log 테이블 (결정 시점 전체 시장 스냅샷)
        try:
            # emb_decision_id는 위 5a에서 이미 resp.json() 파싱하여 추출됨 — 재파싱 불필요
            decision_id = emb_decision_id

            from scripts.save_decision import save_market_context
            market_state = result.get("market_state", {})
            save_market_context(
                decision_id=decision_id,
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio,
                agent_state={
                    "active_agent": agent_name,
                    "danger_score": market_state.get("danger_score"),
                    "opportunity_score": market_state.get("opportunity_score"),
                },
            )
            log("market_context_log 기록 완료")
        except Exception as e:
            log(f"market_context_log 기록 예외: {e}")
            pipeline_errors.append({"phase": "phase5", "source": "market_context_log", "error": str(e)})

        # 5b. market_data 테이블
        try:
            save_market_data_record(market_data, external_data)
        except Exception as e:
            log(f"market_data 기록 예외: {e}")
            pipeline_errors.append({"phase": "phase5", "source": "market_data", "error": str(e)})

        # 5c. execution_logs 테이블
        try:
            duration_ms = int((time.time() - pipeline_start) * 1000)
            dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
            if decision in ("buy", "sell") and not dry_run:
                exec_mode = "execute"
            elif decision in ("buy", "sell") and dry_run:
                exec_mode = "dry_run"
            else:
                exec_mode = "analyze"

            save_execution_log(
                execution_mode=exec_mode,
                duration_ms=duration_ms,
                data_sources={
                    "sources": data_sources_used,
                    "agent": agent_name,
                    "decision": decision,
                    "snapshot_dir": str(snapshot_dir),
                },
                errors={"pipeline_errors": pipeline_errors} if pipeline_errors else None,
                raw_output=json.dumps(output, ensure_ascii=False)[:10000],
                decision_id=decision_id,
                phases_completed=["phase1", "phase2", "phase2.5", "phase3", "phase4", "phase5"],
            )
        except Exception as e:
            log(f"execution_logs 기록 예외: {e}")

    # Phase 5.5: DRY_RUN/워커 임베딩 생성 (DB 미저장이어도 RAG 학습용 임베딩 생성)
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
    try:
        from utils.machine import skip_trade_db as _skip_trade_db_55
        _is_worker = _skip_trade_db_55("decisions")
    except Exception:
        _is_worker = False
    if dry_run or _is_worker:
        try:
            from scripts.save_decision import generate_state_embedding
            emb_data = {
                "current_price": market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price"),
                "change_rate_24h": market_data.get("change_rate_24h") or market_data.get("ticker", {}).get("signed_change_rate"),
                "rsi_14": market_data.get("indicators", {}).get("rsi_14"),
                "sma_20": market_data.get("indicators", {}).get("sma_20"),
                "fear_greed_value": market_data.get("fear_greed", {}).get("value"),
                "volume_24h": market_data.get("volume_24h") or market_data.get("ticker", {}).get("acc_trade_volume_24h"),
                "news_sentiment": market_data.get("news", {}).get("overall_sentiment"),
            }
            emb_text, emb_vector = generate_state_embedding(emb_data)
            if emb_vector:
                # 로컬 캐시에 저장 (나중에 primary 머신에서 DB에 업로드)
                emb_cache_dir = PROJECT_DIR / "data" / "embedding_cache"
                emb_cache_dir.mkdir(parents=True, exist_ok=True)
                emb_cache_file = emb_cache_dir / f"emb_{timestamp}.json"
                with open(emb_cache_file, "w", encoding="utf-8") as ef:
                    json.dump({
                        "text": emb_text,
                        "vector_dim": len(emb_vector),
                        "decision": decision,
                        "confidence": output["decision"].get("confidence"),
                        "timestamp": timestamp,
                        "dry_run": dry_run,
                    }, ef, ensure_ascii=False)
                log(f"DRY_RUN 임베딩 생성 → 캐시 저장 ({len(emb_vector)}d)")

                # 캐시 정리 (최근 100개만 유지)
                cached = sorted(emb_cache_dir.glob("emb_*.json"), key=lambda p: p.stat().st_mtime)
                if len(cached) > 100:
                    for old_f in cached[:-100]:
                        old_f.unlink(missing_ok=True)
        except Exception as e:
            log(f"Phase 5.5 DRY_RUN 임베딩 예외: {e}")

    # Phase 5c: portfolio_snapshots 기록
    try:
        from utils.machine import skip_trade_db, get_machine_name
        if not skip_trade_db("portfolio_snapshots") and supabase_url and supabase_key:
            if "error" not in portfolio:
                log("Phase 5c: portfolio_snapshots 기록...")
                krw_balance = int(portfolio.get("krw_balance", 0))
                holdings = portfolio.get("holdings", [])
                crypto_value = int(sum(h.get("eval_amount", 0) for h in holdings))
                total_value = int(portfolio.get("total_eval", 0))

                snap_row = {
                    "total_krw": krw_balance,
                    "total_crypto_value": crypto_value,
                    "total_value": total_value,
                    "holdings": json.dumps(holdings, ensure_ascii=False),
                    "cycle_id": _CYCLE_ID,
                    "machine_name": get_machine_name(),
                }
                snap_resp = requests.post(
                    f"{supabase_url}/rest/v1/portfolio_snapshots",
                    json=snap_row,
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    timeout=10,
                )
                if snap_resp.status_code in (200, 201):
                    log("[Agent] portfolio_snapshots 기록 완료")
                else:
                    log(f"[Agent] portfolio_snapshots 실패: HTTP {snap_resp.status_code}: {snap_resp.text[:200]}")
            else:
                log("[Agent] portfolio_snapshots 스킵: 포트폴리오 수집 실패")
    except Exception as e:
        log(f"Phase 5c portfolio_snapshots 예외: {e}")

    # Phase 5d: 피드백 applied 처리
    try:
        if supabase_url and supabase_key:
            from utils.machine import skip_trade_db as _skip_fb
            if not _skip_fb("feedback"):
                _fb_headers = {
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                }
                _fb_r = requests.get(
                    f"{supabase_url}/rest/v1/feedback?applied=eq.false&select=id",
                    headers=_fb_headers, timeout=10,
                )
                _fb_data = _fb_r.json() if _fb_r.ok else []
                if _fb_data:
                    _fb_ids = ",".join(str(f['id']) for f in _fb_data if f.get('id'))
                    requests.patch(
                        f"{supabase_url}/rest/v1/feedback?id=in.({_fb_ids})",
                        headers=_fb_headers, timeout=10,
                        json={"applied": True, "applied_at": datetime.now(KST).isoformat()},
                    )
                    log(f"[Agent] {len(_fb_data)}건 피드백 applied 처리")
    except Exception as e:
        log(f"Phase 5d 피드백 applied 예외: {e}")

    # Phase 6: 전환 성과 평가
    log("Phase 6: 전환 성과 평가...")
    subprocess.run([sys.executable, "scripts/evaluate_switches.py"], cwd=str(PROJECT_DIR), check=False, **subprocess_kwargs())
    
    # Phase 6.3: 사후 추적 + 온라인 버퍼 outcome 백필
    try:
        from scripts.retrospective import update_decisions
        log("Phase 6.3: 사후 추적 (retrospective)...")
        retro_result = update_decisions()
        if retro_result:
            log(f"사후 추적: {retro_result.get('updated', 0)}건 업데이트")

            # 온라인 버퍼에 outcome 백필
            if retro_result.get("outcomes"):
                try:
                    from rl_hybrid.rl.online_buffer import OnlineExperienceBuffer
                    buf_backfill = OnlineExperienceBuffer()
                    buf_backfill.update_outcomes(retro_result["outcomes"])
                    log(f"온라인 버퍼 outcome 백필: {len(retro_result['outcomes'])}건")
                except Exception as be:
                    log(f"온라인 버퍼 백필 예외: {be}")
    except Exception as e:
        log(f"Phase 6.3 사후 추적 예외: {e}")

    # Phase 6.5: RL 온라인 학습 버퍼
    if rl_advisory:
        try:
            from rl_hybrid.rl.online_buffer import OnlineExperienceBuffer
            log("Phase 6.5: RL 온라인 학습 버퍼...")
            buf = OnlineExperienceBuffer()
            buf.add_experience(
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio,
                agent_state=agent_state_for_rl,
                rl_action=rl_advisory["action"],
                agent_decision=decision,
            )
            stats = buf.get_stats()
            log(f"온라인 버퍼: {stats['total']}/{stats['trigger_size']}건 (outcome: {stats['outcome_filled']}건)")
            if buf.should_train():
                log("Phase 6.5: RL 미세 학습 시작...")
                train_result = buf.micro_train()
                log(f"RL 미세 학습: {train_result.get('message', 'N/A')}")
        except Exception as e:
            log(f"Phase 6.5 온라인 학습 예외: {e}")

    # Phase 6.7: Parameter Self-Tuning
    try:
        from rl_hybrid.config import SystemConfig as _STConfig
        if _STConfig().self_tuning.enabled:
            log("Phase 6.7: 파라미터 자동 튜닝...")
            from rl_hybrid.rl.self_tuning_rl import run_parameter_tuning
            # 현재 에이전트 파라미터 및 시장 레짐 수집
            _market_state = result.get("market_state") or {}
            _perf_metrics = {
                "recent_decision": decision,
                "danger_score": _market_state.get("danger_score", 50),
                "opportunity_score": _market_state.get("opportunity_score", 50),
            }
            _market_regime = {
                "fgi": market_data.get("fear_greed", {}).get("value"),
                "rsi": market_data.get("indicators", {}).get("rsi_14"),
                "change_rate_24h": market_data.get("change_rate_24h") or market_data.get("ticker", {}).get("signed_change_rate"),
            }
            tuning_result = run_parameter_tuning(
                performance_metrics=_perf_metrics,
                market_regime=_market_regime,
            )
            if tuning_result:
                log(f"Phase 6.7: {tuning_result.get('status', '?')} -- {tuning_result.get('message', 'N/A')}")
    except Exception as e:
        log(f"Phase 6.7 Self-tuning 스킵: {e}")

    # Phase 7-12: 공유 캐시로 Supabase 조회 최적화 (4~5회 → 1회)
    _cached_7d = None   # 7일 buy/sell 결정
    _cached_14d = None  # 14일 전체 결정
    _cached_30d = None  # 30일 전체 결정
    try:
        from scripts.phase_cache import prefetch_decisions, get_cached_decisions, invalidate as _invalidate_cache
        log("Phase 7-12 캐시: Supabase decisions 프리로드...")
        if prefetch_decisions(max_days=30):
            _cached_7d = get_cached_decisions(days=7, buy_sell_only=True)
            _cached_14d = get_cached_decisions(days=14, buy_sell_only=False)
            _cached_30d = get_cached_decisions(days=30, buy_sell_only=False)
            log(f"  캐시 로드: 7d={len(_cached_7d or [])}건, 14d={len(_cached_14d or [])}건, 30d={len(_cached_30d or [])}건")
        else:
            log("  캐시 프리로드 실패 — 각 Phase에서 개별 조회")
    except Exception as e:
        log(f"  캐시 프리로드 예외: {e}")

    # Phase 7: Feedback Hub 전체 분석 (비동기 — 다음 사이클에 반영)
    try:
        from scripts.feedback_hub import run_full_analysis
        log("Phase 7: Feedback Hub 분석...")
        fb_result = run_full_analysis(cached_decisions=_cached_14d)
        if fb_result:
            cal = fb_result.get("calibration", {})
            rl_scores = fb_result.get("rl_model_scores", {})
            log(f"Feedback Hub: confidence 보정={cal.get('adjustment', 0):+.3f}, "
                f"RL 모델 {len(rl_scores)}개 평가, "
                f"비활성={fb_result.get('disabled_models', [])}")
    except Exception as e:
        log(f"Phase 7 Feedback Hub 예외: {e}")

    # Phase 8: 동적 리스크 조절
    try:
        from scripts.dynamic_risk import update_risk
        log("Phase 8: 동적 리스크 조절...")
        risk = update_risk(cached_decisions=_cached_7d)
        if risk:
            _sharpe = risk.get('sharpe_7d')
            _sharpe_str = f"{_sharpe:.2f}" if _sharpe is not None else "N/A"
            _adj_amt = risk.get('adjusted_amount', 0) or 0
            log(f"  리스크: {risk.get('risk_level')} (Sharpe={_sharpe_str}, 조정액={_adj_amt:,}원)")
    except Exception as e:
        log(f"Phase 8 동적 리스크 예외: {e}")

    # Phase 9: 전략 건강검진
    try:
        from scripts.strategy_health import check_health
        log("Phase 9: 전략 건강검진...")
        health = check_health(cached_decisions=_cached_7d)
        if health:
            status = health.get("status", "UNKNOWN")
            wr = health.get("win_rate_7d", 0)
            log(f"  건강: {status} (승률 {wr:.0%}, 연패 {health.get('consecutive_losses', 0)}회)")
    except Exception as e:
        log(f"Phase 9 전략 건강검진 예외: {e}")

    # Phase 10: 알림 집계
    try:
        from scripts.alert_aggregator import aggregate_and_send
        log("Phase 10: 알림 집계...")
        alert_result = aggregate_and_send()
        if alert_result:
            sent = alert_result.get("sent_count", 0)
            suppressed = alert_result.get("suppressed_count", 0)
            log(f"  알림: {sent}건 전송, {suppressed}건 억제")
    except Exception as e:
        log(f"Phase 10 알림 집계 예외: {e}")

    # Phase 11: RL 모델 자동 재훈련
    try:
        from scripts.model_retrainer import check_and_queue, process_queue
        log("Phase 11: RL 모델 재훈련 큐...")
        queue_result = check_and_queue()
        if queue_result and queue_result.get("queued", 0) > 0:
            log(f"  재훈련 큐: {queue_result['queued']}개 모델 추가")
            proc_result = process_queue()
            if proc_result:
                log(f"  처리: {proc_result.get('processed', 0)}개 완료, {proc_result.get('failed', 0)}개 실패")
    except Exception as e:
        log(f"Phase 11 RL 재훈련 예외: {e}")

    # Phase 12: 레짐 가중치 학습
    try:
        from scripts.regime_learner import learn_weights
        log("Phase 12: 레짐 가중치 학습...")
        learn_result = learn_weights(cached_decisions=_cached_30d)
        if learn_result:
            updated = sum(1 for v in learn_result.get("sample_counts", {}).values() if v >= 5)
            total = len(learn_result.get("sample_counts", {}))
            log(f"  학습: {updated}/{total} 레짐 가중치 업데이트 (충분한 데이터)")
    except Exception as e:
        log(f"Phase 12 레짐 학습 예외: {e}")

    # Phase 13: API 건강 점검 (Predictive Throttler)
    try:
        from scripts.api_throttler import get_api_health, get_throttle_stats
        log("Phase 13: API 건강 점검...")
        api_health = get_api_health()
        overall = api_health.get("overall", "unknown")
        degraded_apis = [
            name for name, info in api_health.items()
            if name != "overall" and isinstance(info, dict) and info.get("status") != "healthy"
        ]
        if degraded_apis:
            log(f"  API 건강: {overall} — 주의: {', '.join(degraded_apis)}")
            pipeline_errors.append({
                "phase": "phase13",
                "source": "api_health",
                "error": f"degraded APIs: {degraded_apis}",
            })
        else:
            log(f"  API 건강: {overall}")

        # 통계 요약 로그
        stats = get_throttle_stats()
        for api_name, s in stats.items():
            if s.get("calls_last_5min", 0) > 0:
                log(f"  {api_name}: {s['calls_last_5min']}calls/5m, "
                    f"429={s['rate_429_5min']:.1%}, lat={s['avg_latency_ms']:.0f}ms")
    except Exception as e:
        log(f"Phase 13 API 건강 점검 예외: {e}")

    # Phase 14: RL 모델 다양성 검증
    try:
        from scripts.model_diversity import check_diversity, get_diversity_summary
        log("Phase 14: RL 모델 다양성 검증...")
        diversity = check_diversity(cached_decisions=_cached_7d)
        if diversity:
            d_score = diversity.get("diversity_score", 0)
            d_samples = diversity.get("sample_count", 0)
            d_summary = get_diversity_summary(diversity)
            log(f"  다양성: {d_score}/100 [{d_summary['status']}] ({d_samples}건)")
            output["diversity_score"] = d_score
            for detail in d_summary.get("details", []):
                log(f"    {detail}")
            if d_score < 40:
                log("  [!] 다양성 위험 — 모델 중복/편향 심각")
        else:
            log("  RL 어드바이저리 데이터 없음 — 스킵")
    except Exception as e:
        log(f"Phase 14 모델 다양성 예외: {e}")

    # Phase 캐시 해제
    try:
        _invalidate_cache()
    except Exception:
        pass

    log("═══ 에이전트 모드 완료 ═══")
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # Windows cp949 인코딩 문제 방지
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    import argparse as _ap
    _parser = _ap.ArgumentParser()
    _parser.add_argument("--dry-run", action="store_true", help="DRY_RUN=true 강제 (포어그라운드 테스트용)")
    _args = _parser.parse_args()
    if _args.dry_run:
        os.environ["DRY_RUN"] = "true"
    main()
