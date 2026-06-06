# -*- coding: utf-8 -*-
"""build_rotation_signal_panel.py — WIRE5 Phase 1: 11산업 rotation primary 신호 통합 패널 동결.

★목적 = fork OOS 실측(_sleeve_rotation_kr.py)의 입력. yaml §3 12산업 primary 신호(ship=monitor 제외)를
각 측정 source(_rotation/data/cycle_*.parquet + 각 raw-v3/data)에서 추출 → **OW 방향 부호 정렬**(높을수록
비중확대) → 월말 통합 패널 parquet 동결.

★spec-exact 반영 (rotation-study_session.yaml §1/§3):
- §3 primary 신호 + 사전확약 부호 1:1 (아래 SIGNALS dict 주석 = yaml 행).
- §1 제외: 외국인flow(L축 1회계상) / cli_chg(1층 시장timing) = 패널 미포함(애초 primary 아님, 명시).
- shipbuilding = monitor_only(weight 0) = 신호 미투입(정직 박제).
- 부호 정렬: 모든 컬럼 = "OW 방향"(값↑ = 비중확대 권고) = fork tilt 부호 일관.

★재현성: _rotation/data/cycle_*.parquet = yfinance proxy frozen(cycle_collect_meta.json). 1회 fetch 동결.
  consumer cosmetics = prices.parquet(frozen) sub eq-weight. fetch 신호 없음(전부 parquet 동결).

⛔ production(core/stock) 무접촉. 산출 = _rotation/data/rotation_signals_panel.parquet.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
IND = ROOT.parent                      # industries/
ROT_DATA = ROOT / "data"               # _rotation/data (cycle_*.parquet frozen proxy)
OUT = ROT_DATA / "rotation_signals_panel.parquet"
START, END = "2019-01-01", "2026-05-31"
SEMI_PPI_LAG = 1


def _me(s: pd.Series) -> pd.Series:
    """일별/월별 → 월말 last."""
    s = s.copy(); s.index = pd.to_datetime(s.index)
    return s.resample("ME").last()


def _z(s: pd.Series) -> pd.Series:
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 1e-12 else s * 0.0


def _pq(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path); df.index = pd.to_datetime(df.index)
    return df


# ── 산업별 primary 신호 빌더 (각 = yaml §3 행, OW 방향 부호 정렬 반환) ──

def sig_steel():
    # §3 steel STRONG iron_ore_d3 (양: 철광석 3M=중국 수요 cycle). cycle_steel=TIO=F frozen.
    c = _pq(ROT_DATA / "cycle_steel.parquet")
    return _me(c["iron_ore"]).pct_change(3)            # 양 → 그대로

def sig_auto():
    # §3 auto STRONG global_auto_d3 (양: 글로벌 신차). cycle_auto=CARZ frozen.
    c = _pq(ROT_DATA / "cycle_auto.parquet")
    return _me(c["global_auto"]).pct_change(3)         # 양

def sig_battery():
    # §3 battery STRONG lithium_yoy (양: EV 수요). cycle_battery=LIT frozen.
    c = _pq(ROT_DATA / "cycle_battery.parquet")
    return _me(c["lithium"]).pct_change(12)            # 양

def sig_semiconductor():
    # §3 semi tradeable soxx_d3 (양: SOXX 선행). cycle_semiconductor=SOXX frozen. (rotation 보조, 종목선택 primary)
    c = _pq(ROT_DATA / "cycle_semiconductor.parquet")
    return _me(c["soxx"]).pct_change(3)                # 양

def sig_chemical():
    # §3 chemical STRONG spread_china_naphtha (양: 중국 demand−원가 margin). chem_rotation_cycle frozen.
    #   measure_chem_rotation_v2:85 = z(yoy(china_fxi)) − z(yoy(wti_naphtha)). mom_3 보조는 G-C 재audit 폐기(미투입).
    c = _pq(IND / "chemical" / "raw-v3" / "rotation" / "data" / "chem_rotation_cycle.parquet")
    cm = c.resample("ME").last()
    naph = cm["wti_naphtha"] / cm["wti_naphtha"].shift(12) - 1
    fxi = cm["china_fxi"] / cm["china_fxi"].shift(12) - 1
    return _z(fxi) - _z(naph)                          # 양

def sig_telecom():
    # §3 telecom tradeable semi_ppi_yoy (음: 반도체 cycle 약→통신 방어 OW). regime_series frozen.
    #   L축 외국인flow = 1회계상 제외(telecom 고유=semi_ppi 한정). 부호 음 → OW 방향 위해 ×(-1).
    r = _pq(IND / "semiconductor" / "raw-v3" / "data" / "regime_series.parquet")
    semi = _me(r["semi_ppi"].shift(SEMI_PPI_LAG))
    return -1.0 * (semi / semi.shift(12) - 1)          # 음 → ×(-1) = OW 방향

def sig_financial():
    # §3 financial tradeable_weak credit_spread_d6 (음: 신용위험 확대→금융 상대 UW). regime_labels frozen.
    #   term_spread NIM=시장timing 채택불가 / credit_spread 대손=금융 고유(비대칭). 부호 음 → ×(-1).
    r = _pq(IND / "financial" / "raw-v3" / "data" / "regime_labels.parquet")
    return -1.0 * _me(r["credit_spread"]).diff(6)      # 음 → ×(-1)

def sig_aitech():
    # §3 aitech tradeable signals=[game_espo, rate_10y, global_sw, cloud] (IT 성장+금리 duration).
    #   yaml primary 단일 미지정(복수) → 4신호 OW정렬 z 동일가중 합성(대표). cycle_aitech_ext frozen.
    #   transform(measure_rotation_ext:54): rate_10y=diff3(음), 나머지=pct3(양).
    c = _pq(IND / "aitech" / "raw-v3" / "data" / "cycle_aitech_ext.parquet").resample("ME").last()
    parts = []
    parts.append(_z(c["game_espo"].pct_change(3)))               # 양
    parts.append(_z(-1.0 * c["rate_10y"].diff(3)))               # 음 → ×(-1)=OW (금리↑→IT UW)
    parts.append(_z(c["global_sw_igv"].pct_change(3)))           # 양
    parts.append(_z(c["cloud_skyy"].pct_change(3)))              # 양
    return pd.concat(parts, axis=1).mean(axis=1)                 # 합성 = OW 방향

def sig_bio():
    # §3 bio tradeable signals=[rate_overlay, bio_global] (US금리 duration + 글로벌바이오 상대).
    #   measure_rotation_composite full_overlay = mean(z(-us_10y_d3), z(xbi_rel3), z(ibb_rel3)). frozen.
    cf = _pq(IND / "bio" / "raw-v3" / "data" / "common_factors.parquet").resample("ME").last()
    gb = _pq(IND / "bio" / "raw-v3" / "data" / "global_bio_etfs.parquet").resample("ME").last()
    rate = _z(-1.0 * cf["rate10y"].diff(3))                      # 금리↓=bio OW → ×(-1)
    xbi_rel = _z((gb["XBI"] / gb["SPY"]).pct_change(3))          # 양
    ibb_rel = _z((gb["IBB"] / gb["^NDX"]).pct_change(3))         # 양
    return pd.concat([rate, xbi_rel, ibb_rel], axis=1).mean(axis=1)  # full_overlay 합성

def sig_consumer():
    # §3 consumer tradeable primary=mom_6_reversal_cosmetics (음: 화장품 변동성 평균회귀).
    #   G-C 재audit: 외부시장 resid 후 -0.425 강화=genuine(primary). prices.parquet(frozen) cosmetics sub eq-weight.
    #   CSI는 tentative(미투입, theory-family 한정 BY). 부호 음(reversal) → ×(-1)=OW.
    u = _pq(IND / "consumer" / "raw-v3" / "data" / "universe.parquet")
    cos = u[(u["subcl"] == "cosmetics") & (u.get("pass_floor", True) == True)]["Code"].astype(str).tolist()
    px = _pq(IND / "consumer" / "raw-v3" / "data" / "prices.parquet")
    px.columns = [str(c) for c in px.columns]
    cols = [c for c in cos if c in px.columns]
    if not cols:
        raise ValueError(f"consumer cosmetics 종목 매칭 0 (universe {len(cos)})")
    ret = px[cols].resample("ME").last().pct_change().mean(axis=1, skipna=True)
    cum = (1 + ret.fillna(0)).cumprod()
    return -1.0 * cum.pct_change(6)                              # 음(reversal) → ×(-1)

def sig_refining():
    # §3 refining tradeable_weak [유가_mean_rev, 배당_income_trap] (음: 고유가 peak-out UW).
    #   crack=가스9종 오염 폐기(strict2 무신호). 유가 mean-rev = brent yoy 음(고유가→forward 음). refining_cycle frozen.
    #   배당 income-trap = DART 배당 미수집(collector_plan) → 본 패널은 유가 mean-rev primary 단일(배당 caveat).
    c = _pq(IND / "refining" / "raw-v3" / "data" / "refining_cycle.parquet")
    return -1.0 * (_me(c["brent"]).pct_change(12))               # 음 → ×(-1)


SIGNALS = {
    "steel": (sig_steel, "STRONG", "iron_ore_d3"),
    "auto": (sig_auto, "STRONG", "global_auto_d3"),
    "battery": (sig_battery, "STRONG", "lithium_yoy"),
    "chemical": (sig_chemical, "STRONG", "spread_china_naphtha"),
    "semiconductor": (sig_semiconductor, "tradeable", "soxx_d3"),
    "telecom": (sig_telecom, "tradeable", "semi_ppi_yoy(음)"),
    "bio": (sig_bio, "tradeable", "rate+bio_global_overlay"),
    "aitech": (sig_aitech, "tradeable", "game/rate/sw/cloud 합성"),
    "consumer": (sig_consumer, "tradeable", "mom_6_reversal_cosmetics(음)"),
    "financial": (sig_financial, "tradeable_weak", "credit_spread_d6(음)"),
    "refining": (sig_refining, "tradeable_weak", "유가_mean_rev(음)"),
    # shipbuilding = monitor_only(weight 0) = 신호 미투입(정직 박제, 자문 3R 복합 verdict)
}
EXCLUDED = {"외국인flow": "L축 1회계상(전산업 공통, 2층 1회 계산)", "cli_chg": "1층 시장timing(N_eff≈1)"}


def main():
    cols, ok, fail = {}, [], {}
    for ind, (fn, tier, name) in SIGNALS.items():
        try:
            s = fn().loc[START:END]
            s = s.replace([np.inf, -np.inf], np.nan)
            cols[ind] = s
            ok.append((ind, tier, name, int(s.notna().sum())))
        except Exception as e:
            fail[ind] = repr(e)[:120]
    panel = pd.DataFrame(cols)
    panel = panel.loc[START:END]
    panel.to_parquet(OUT)

    report = {
        "meta": {
            "purpose": "WIRE5 Phase1 — 11산업 rotation primary 신호 통합 패널(OW 방향 부호 정렬)",
            "spec": "rotation-study_session.yaml §3 primary 1:1 + §1 제외(외국인flow/cli_chg) + ship monitor 미투입",
            "sign_convention": "전 컬럼 OW 방향(값↑=비중확대 권고). 부호 음 신호(telecom/financial/consumer/refining/bio금리)는 ×(-1) 정렬",
            "frozen": "_rotation/data/cycle_*.parquet(yfinance proxy) + raw-v3 frozen parquet. fetch 신호 0(재현성).",
            "excluded": EXCLUDED,
            "window": [START, END],
        },
        "shape": list(panel.shape),
        "signals_ok": [{"industry": i, "tier": t, "signal": n, "n_obs": c} for i, t, n, c in ok],
        "signals_fail": fail,
        "monitor_only": {"shipbuilding": "weight 0 = 신호 미투입(자문 3R 복합 verdict: trailing REJECTED/overall INSUFFICIENT/contrarian LIVE_UNPROVEN)"},
    }
    rp = ROOT / "validation-rotation-signal-panel-v1.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"Saved panel: {OUT}  shape={panel.shape}")
    print(f"Saved report: {rp}\n")
    print(f"=== G1 게이트 점검 ===")
    print(f"G1-a 신호 추출: 성공 {len(ok)}/11 산업" + (f" / ★실패 {list(fail)}" if fail else " (누락 0)"))
    print(f"G1-b 제외(§1): {list(EXCLUDED)} = 패널 미포함 ✓")
    print(f"G1-c 재현성: fetch 신호 0 (전부 frozen parquet) ✓")
    print(f"G1-d shape: {panel.shape} (기대 ≈11 col × 88~89 mo)")
    print(f"G1-e 월수익: measure_integration.panel_monthly() 재사용(fork에서)\n")
    print(panel.tail(6).round(3).to_string())
    if fail:
        print(f"\n★실패 산업:")
        for k, v in fail.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
