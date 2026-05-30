"""H5 halving phase — standalone IC 금지, H1 (MVRV) 의 phase 별 conditioning 만.

방법:
- phase 별 MVRV->fwd_30d Rank-IC 안정성
- N=4 검정력 0 명시 (G축 tier 강등 라벨)
- across-phase 비교 = power 0 -> 보고만, 판정 X
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from scipy import stats
from lib_common import (
    load_coinmetrics, load_btc_klines, rank_ic, effective_n, halving_phase, HALVING_DATES
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h5-halving.md"

def main():
    klines = load_btc_klines()
    try:
        cm = load_coinmetrics()
    except FileNotFoundError:
        cm = pd.DataFrame()

    lines = []
    def w(s=""): lines.append(s)

    w("# H5 Halving phase regime — 실데이터 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w(f"★N=4 사실상 검정 불가 명시 (PlanB S2F OOS 붕괴 교보재). standalone IC 산출 금지.")
    w(f"본 검증 = phase 별 conditioning 변수로서 H1 (MVRV) IC 안정성 확인만.")
    w()
    w("## 0. Halving events 가용 범위")
    for h in HALVING_DATES:
        w(f"- {h.date()}")
    w()

    # ===== 1. phase 분류 + 분포 =====
    klines["phase"] = klines["date"].apply(halving_phase)
    klines["log_ret_30d_fwd"] = np.log(klines["close"].shift(-30) / klines["close"])
    w("## 1. Phase 별 N (klines 일수)")
    n_by_phase = klines.groupby("phase").size().sort_index()
    w("```")
    w(n_by_phase.to_string())
    w("```")
    w()

    # ===== 2. Phase 별 BTC log_ret_30d_fwd 단순 평균 (★across-phase 비교 X) =====
    w("## 2. Phase 별 BTC fwd_30d 분포 (★across-phase 통계검정 X — N=4 power 0)")
    w("```")
    summary = klines.groupby("phase")["log_ret_30d_fwd"].describe().round(4)
    w(summary.to_string())
    w("```")
    w()
    w("- ★구조적 prior (저신뢰) 라벨: 4 사이클 데이터로 phase 효과 통계 검정 X")
    w("- post_6_18m / post_18_24m 단순 평균이 양 / 음 부호인지만 보고")
    w()

    # ===== 3. Phase 별 H1 (MVRV) 매핑 conditional IC =====
    if not cm.empty:
        df = cm.merge(klines[["date", "phase", "log_ret_30d_fwd"]], on="date", how="inner")
        df["mvrv"] = df["CapMVRVCur"]
        w("## 3. Phase 별 MVRV -> fwd_30d Rank-IC (conditioning 안정성)")
        for ph in sorted(df["phase"].unique()):
            sub = df[(df["phase"] == ph) & df["mvrv"].notna() & df["log_ret_30d_fwd"].notna()]
            if len(sub) < 30:
                w(f"- {ph}: n={len(sub)} (N<30 small-N 미달, IC 보류)")
                continue
            rho, n = rank_ic(sub["mvrv"], sub["log_ret_30d_fwd"])
            eff = effective_n(sub["mvrv"].values)
            w(f"- {ph}: Rank-IC = {rho:+.4f}, raw N={n}, effective N={eff:.1f}")
        w()
        w("- ★해석: phase 별 IC 부호 일관성 = MVRV 가 phase 전반에 걸쳐 안정한 mean-revert 신호 / "
          "부호 반전 / 절대값 차이 = phase modulator 필요 신호")
    else:
        w("## 3. CoinMetrics MVRV 미수집 -> phase 별 MVRV IC 보류")
    w()

    # ===== 4. Phase 별 effective N gate 통과 여부 (G축 tier) =====
    w("## 4. Effective N gate (G축 tier)")
    if not cm.empty:
        for ph in sorted(df["phase"].unique()):
            sub = df[(df["phase"] == ph) & df["mvrv"].notna()]
            if len(sub) < 10:
                continue
            eff = effective_n(sub["mvrv"].values)
            tier = "validated alpha 후보" if eff >= 100 else ("partial (structural prior)" if eff >= 24 else "small-N 차단")
            w(f"- {ph}: N raw={len(sub)}, effective={eff:.1f} -> tier: {tier}")
    w()

    w("## 5. 결론")
    w("- ★H5 standalone IC 산출 = 수행 안 함 (사용자 명시 N=4 power 0)")
    w("- phase 는 regime label only (belief b(t) regime 입력)")
    w("- conditioning 효과만 H1 (MVRV) 의 phase 별 IC 로 간접 평가")
    w("- prior_strength = 0.1 (channel 최하, direction.md D1 합의)")
    w()
    w("## 6. 미해결 의문")
    w("- 각 halving 이 다른 macro epoch 와 confound (2012 태동 / 2016 ICO / 2020 COVID / 2024 ETF)")
    w("- phase modulator 가 진짜 supply 효과인지 epoch artifact 인지 식별 불가")
    w("- 채굴자 매도 압력 (hashrate / miner outflow) 연속 보조 지표 추가 권고 (별도 collector 필요)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] H5 -> {OUT}")


if __name__ == "__main__":
    main()
