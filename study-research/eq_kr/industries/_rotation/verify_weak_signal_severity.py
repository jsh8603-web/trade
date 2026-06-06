# -*- coding: utf-8 -*-
"""verify_weak_signal_severity.py — 자문 신규지적 실제 심각도 검증 (시뮬, production 무접촉).

자문(gemini+claude 1R) 신규 지적 중 within 데이터로 즉시 검증 가능한 3건:
- (c) battery: inv_ratio(+0.112 TENTATIVE) vs cs_mom_6m(+0.075 primary) → ρ 변화
- (e) EB 부호보존|IC| DL "약신호 대평균 끌어 부풀림" → 3방식 ρ 비교 + 등급 뒤집힘
- (d) grade cut(高/中/低) vs 연속수축 → ρ 분포 경계 밀집

입력 = validation-within-residual-v2.json (capsule IC + N_eff PR 실측, 재측정 X).
산출 = verify-weak-signal-severity.json. ⛔ within v2 무수정(읽기만).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "validation-within-residual-v2.json"
T_MONTHS = 88


def rho(mag_pp, n_eff, n0, ic0, gate):
    breadth = n_eff / (n_eff + n0)
    signal = abs(mag_pp) / (abs(mag_pp) + ic0)
    return round(breadth * signal * gate, 3)


def grade(r):
    return "高" if r >= 0.45 else "中" if r >= 0.25 else "低"


def gate_of(r):
    cav = r["caveat"]
    if r["by"]:
        return 1.0
    if any(k in cav for k in ["LIMITED", "conditional", "marginal", "단일", "불가"]):
        return 0.5
    return 0.8


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    per = d["per_industry"]
    n0 = d["meta"]["n0"]; ic0 = d["meta"]["ic0"]

    valid = {k: v for k, v in per.items() if v["ic"] is not None}
    ic_bar = float(np.mean([abs(v["ic"]) for v in valid.values()]))

    rows = {}
    for ind, v in valid.items():
        ic = v["ic"]; ne = v["n_eff"]; n = v["n_codes"]; g = gate_of(v)
        w_eb = ne / (ne + n0)
        a_ic = abs(ic)
        # ① 현행: 부호보존 |IC| 대평균 끌림 (within v2)
        mag1 = w_eb * a_ic + (1 - w_eb) * ic_bar
        # ② zero-mean: |IC| 를 0 향해 수축 (자문 권고)
        mag2 = w_eb * a_ic
        # ③ noise-floor 보정: time-avg IC SE ≈ (1/sqrt(n-1))/sqrt(T), E|noise|≈sqrt(2/π)*SE
        floor = np.sqrt(2 / np.pi) * (1.0 / np.sqrt(max(n - 1, 1))) / np.sqrt(T_MONTHS)
        a_corr = max(0.0, a_ic - floor)
        mag3 = w_eb * a_corr  # noise-floor 차감 후 zero-mean 수축
        rows[ind] = {
            "ic": ic, "n_eff": ne, "n_codes": n, "gate": g, "w_eb": round(w_eb, 3),
            "noise_floor": round(floor, 4),
            "rho_①현행": rho(mag1, ne, n0, ic0, g), "등급_①": grade(rho(mag1, ne, n0, ic0, g)),
            "rho_②zeromean": rho(mag2, ne, n0, ic0, g), "등급_②": grade(rho(mag2, ne, n0, ic0, g)),
            "rho_③noisefloor": rho(mag3, ne, n0, ic0, g), "등급_③": grade(rho(mag3, ne, n0, ic0, g)),
            "mag_①": round(mag1, 4), "mag_②": round(mag2, 4),
            "부풀림_①대②": round(mag1 - mag2, 4),
        }

    # (c) battery: inv_ratio(0.112) → cs_mom_6m(0.075 primary) 재계산 (① 현행 방식 기준)
    bat = valid["battery"]
    ne_b = bat["n_eff"]; w_eb_b = ne_b / (ne_b + n0); g_b = gate_of(bat)
    bat_primary_ic = 0.075
    # ic_bar 재계산 (battery 값 교체 시)
    icv2 = [abs(v["ic"]) for k, v in valid.items() if k != "battery"] + [bat_primary_ic]
    ic_bar2 = float(np.mean(icv2))
    mag_bat_primary = w_eb_b * bat_primary_ic + (1 - w_eb_b) * ic_bar2
    rho_bat_primary = rho(mag_bat_primary, ne_b, n0, ic0, g_b)

    out = {
        "meta": {"purpose": "자문 신규지적 (c)(e)(d) 실제 심각도 검증", "ic_bar(대평균|IC|)": round(ic_bar, 4),
                 "n0": n0, "ic0": ic0, "T_months": T_MONTHS},
        "e_EB_3방식": rows,
        "c_battery_primary교체": {
            "현행_inv_ratio_0.112_ρ": bat["rho_i"] if "rho_i" in bat else None,
            "primary_cs_mom_6m_0.075_ρ_①": rho_bat_primary,
            "등급변화": f"{grade(rho_bat_primary)} (현행 低 0.214)",
            "note": "primary 교체 시 ρ 하락폭 = TENTATIVE 채택의 등급 인플레 크기",
        },
    }
    # 뒤집힘 카운트
    flip12 = [k for k, r in rows.items() if r["등급_①"] != r["등급_②"]]
    flip13 = [k for k, r in rows.items() if r["등급_①"] != r["등급_③"]]
    out["meta"]["등급뒤집힘_①대②"] = flip12
    out["meta"]["등급뒤집힘_①대③"] = flip13

    (ROOT / "verify-weak-signal-severity.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    import sys; sys.stdout.reconfigure(encoding="utf-8")
    print(f"대평균 |IC| = {ic_bar:.4f}  (약신호가 이 값으로 끌려가면 부풀림)\n")
    print("=== (e) EB 3방식 ρ 비교 (약신호 부풀림 검증) ===")
    print(f"{'업종':14s} {'IC':>7s} {'Neff':>5s} {'①현행':>6s}{'등급':>4s} {'②zero':>6s}{'등급':>4s} {'③nflr':>6s}{'등급':>4s} {'부풀림①-②':>9s}")
    for ind in sorted(rows, key=lambda x: -rows[x]["rho_①현행"]):
        r = rows[ind]
        print(f"{ind:14s} {r['ic']:+.3f} {r['n_eff']:5.1f} {r['rho_①현행']:6.3f}{r['등급_①']:>4s} {r['rho_②zeromean']:6.3f}{r['등급_②']:>4s} {r['rho_③noisefloor']:6.3f}{r['등급_③']:>4s} {r['부풀림_①대②']:+9.4f}")
    print(f"\n  ★등급 뒤집힘 ①현행→②zeromean: {flip12 or '없음'}")
    print(f"  ★등급 뒤집힘 ①현행→③noisefloor: {flip13 or '없음'}")
    print(f"\n=== (c) battery primary 교체 ===")
    print(f"  inv_ratio(0.112 TENTATIVE) ρ=0.214(低) → cs_mom_6m(0.075 primary) ρ={rho_bat_primary}({grade(rho_bat_primary)})")
    print(f"\n=== (d) ρ 분포 (grade cut 경계 0.25中/0.45高 밀집) ===")
    rs = sorted([r["rho_①현행"] for r in rows.values()], reverse=True)
    print(f"  ρ(현행) 정렬: {rs}")
    print(f"  中컷 0.25 근처(±0.05): {[r for r in rs if abs(r-0.25)<=0.05]}")


if __name__ == "__main__":
    main()
