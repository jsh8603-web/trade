# -*- coding: utf-8 -*-
"""measure_oos_event.py — financial walk-forward OOS verdict + 밸류업 event study (S2 보강).

★team-lead 지시: walk-forward OOS (IS2019-22/OOS2023-26 split) — in-sample만으론 tentative.
★이연 금지: 밸류업 event study (2024-02-26 / 2024-05-02) 지금 측정. CAAR(저PBR 금융주 vs 고PBR).

측정:
  1. walk-forward OOS: 핵심 발견(bank pbr_z value / bank mom_12_1 momentum / sub-sector PBR cancel)을
     IS(2019-2022) / OOS(2023-2026) split → 부호+magnitude 유지 여부 = in-sample artifact 판별.
  2. 밸류업 event study: 2024-02-26(1차) / 2024-05-02(2차) event window CAAR.
     저PBR 금융주(이벤트 직전 PBR 하위 33%) vs 고PBR(상위 33%) Market Model abnormal return.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def csz(panel):
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def build_signals(px, fin, uni):
    pxm = px.resample("ME").last()
    sigs = {
        "mom_6": csz(pxm / pxm.shift(6) - 1),
        "mom_12_1": csz(pxm.shift(1) / pxm.shift(12) - 1),
        "rev_1m": csz(pxm / pxm.shift(1) - 1),
    }
    # pbr_z (PIT)
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and lp.iloc[-1] > 0:
                shares[code] = mc / lp.iloc[-1]
    fin = fin.copy(); fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    pbr_panel = {}
    for code in px.columns:
        if code not in shares:
            continue
        cf = fin[fin["code"] == code].sort_values("rcept_dt")
        if len(cf) == 0:
            continue
        sh = shares[code]; pbr_s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            avail = cf[cf["rcept_dt"] <= dt]
            if len(avail) == 0 or pd.isna(pxm.loc[dt, code]):
                continue
            eq = avail["equity"].iloc[-1]; mktcap = pxm.loc[dt, code] * sh
            if eq and eq > 0:
                pbr_s[dt] = mktcap / eq
        pbr_panel[code] = pbr_s
    sigs["pbr_z"] = csz(pd.DataFrame(pbr_panel))
    return sigs


def forward_daily(px, anchor, h):
    out = {}
    for dt in anchor:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        p0 = min(pos, len(px.index) - 1); p1 = p0 + h
        if p1 >= len(px.index):
            continue
        out[dt] = px.iloc[p1] / px.iloc[p0] - 1
    return pd.DataFrame(out).T


def ic_split(sig, fwd, codes, months):
    ics = {}
    for dt in sig.index.intersection(fwd.index):
        if months is not None and dt not in months:
            continue
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index).intersection(codes)
        if len(c) < 6:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics[dt] = rho
    return pd.Series(ics).sort_index()


def walk_forward_oos(px, fin, uni):
    """핵심 발견 IS(2019-2022)/OOS(2023-2026) split. 부호+magnitude 유지 = artifact 아님."""
    code_map = uni["subcl"].to_dict()
    sigs = build_signals(px, fin, uni)
    anchor = sigs["mom_6"].dropna(how="all").index
    bank = [c for c, s in code_map.items() if s == "bank"]
    secur = [c for c, s in code_map.items() if s == "securities"]
    rate_pos = [c for c, s in code_map.items() if s in ("bank", "insurance", "other_fin", "credit")]

    out = {}
    IS = pd.date_range("2019-01-01", "2022-12-31", freq="ME")
    OOS = pd.date_range("2023-01-01", "2026-12-31", freq="ME")
    # 핵심 발견 5종
    cases = [
        ("bank_pbr_z_y60d", "pbr_z", bank, 60),
        ("bank_mom12_1_y60d", "mom_12_1", bank, 60),
        ("bank_rev1m_y5d", "rev_1m", bank, 5),
        ("secur_pbr_z_y60d", "pbr_z", secur, 60),   # ★증권 = 반대부호 (cancel 검정)
        ("ratePOS_rev1m_y20d", "rev_1m", rate_pos, 20),
    ]
    for name, sname, codes, h in cases:
        fwd = forward_daily(px, anchor, h)
        ic_is = ic_split(sigs[sname], fwd, codes, set(IS))
        ic_oos = ic_split(sigs[sname], fwd, codes, set(OOS))
        is_m = float(ic_is.mean()) if len(ic_is) else None
        oos_m = float(ic_oos.mean()) if len(ic_oos) else None
        sign_hold = (is_m is not None and oos_m is not None and np.sign(is_m) == np.sign(oos_m))
        out[name] = {
            "signal": sname, "horizon_d": h, "n_codes": len(codes),
            "IS_ic": round(is_m, 4) if is_m is not None else None, "IS_n": len(ic_is),
            "OOS_ic": round(oos_m, 4) if oos_m is not None else None, "OOS_n": len(ic_oos),
            "sign_hold": bool(sign_hold),
            "verdict": ("OOS 부호유지" if sign_hold else "OOS 부호반전/약화"),
        }
    return out


def value_up_event_study(px, fin, uni):
    """밸류업 event study. 2024-02-26(1차) / 2024-05-02(2차).
    저PBR 금융주(직전 PBR 하위33%) vs 고PBR(상위33%) Market Model CAAR.
    Market Model: R_i = α + β·R_mkt (estimation [-120,-11]). R_mkt = universe eq-weight 일별 평균."""
    code_map = uni["subcl"].to_dict()
    fin = fin.copy(); fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and lp.iloc[-1] > 0:
                shares[code] = mc / lp.iloc[-1]
    ret_d = px.pct_change()
    mkt = ret_d.mean(axis=1)  # universe eq-weight 일별 (금융 섹터 시장)

    events = {"valueup_1st_20240226": pd.Timestamp("2024-02-26"),
              "valueup_2nd_20240502": pd.Timestamp("2024-05-02")}
    out = {}
    for ename, edate in events.items():
        # 이벤트 직전 PBR (공시일 이후 최신, edate 1개월 전 기준)
        ref = edate - pd.Timedelta(days=30)
        pbr_at = {}
        for code in px.columns:
            if code not in shares:
                continue
            cf = fin[(fin["code"] == code) & (fin["rcept_dt"] <= ref)].sort_values("rcept_dt")
            if len(cf) == 0:
                continue
            eq = cf["equity"].iloc[-1]
            ppos = px.index.searchsorted(ref)
            if ppos >= len(px.index) or eq <= 0:
                continue
            price = px[code].iloc[min(ppos, len(px.index) - 1)]
            if pd.notna(price):
                pbr_at[code] = price * shares[code] / eq
        if len(pbr_at) < 9:
            out[ename] = {"status": "INSUFFICIENT pbr coverage", "n": len(pbr_at)}
            continue
        pbr_s = pd.Series(pbr_at).sort_values()
        n3 = max(3, len(pbr_s) // 3)
        low_pbr = pbr_s.index[:n3].tolist()    # 저PBR (value)
        high_pbr = pbr_s.index[-n3:].tolist()  # 고PBR

        epos = px.index.searchsorted(edate)
        def caar(codes, w):
            est_lo, est_hi = epos - 120, epos - 11
            ev_lo, ev_hi = epos + w[0], epos + w[1]
            if est_lo < 0 or ev_hi >= len(px.index):
                return None
            ar_sum = []
            for code in codes:
                r = ret_d[code]
                rest = r.iloc[est_lo:est_hi]; mest = mkt.iloc[est_lo:est_hi]
                valid = rest.notna() & mest.notna()
                if valid.sum() < 60:
                    continue
                beta, alpha = np.polyfit(mest[valid], rest[valid], 1)
                rev = r.iloc[ev_lo:ev_hi + 1]; mev = mkt.iloc[ev_lo:ev_hi + 1]
                ar = (rev - (alpha + beta * mev)).dropna()
                ar_sum.append(ar.sum())
            if not ar_sum:
                return None
            return float(np.mean(ar_sum)), len(ar_sum), float(np.std(ar_sum, ddof=1) / np.sqrt(len(ar_sum)) if len(ar_sum) > 1 else np.nan)

        res = {"event_date": str(edate.date()), "n_low_pbr": len(low_pbr), "n_high_pbr": len(high_pbr)}
        for wname, w in [("short_-5_+5", (-5, 5)), ("mid_+1_+60", (1, 60))]:
            lc = caar(low_pbr, w); hc = caar(high_pbr, w)
            res[wname] = {
                "low_pbr_caar": round(lc[0], 4) if lc else None,
                "low_pbr_se": round(lc[2], 4) if lc and not np.isnan(lc[2]) else None,
                "high_pbr_caar": round(hc[0], 4) if hc else None,
                "spread_low_minus_high": round(lc[0] - hc[0], 4) if (lc and hc) else None,
            }
        out[ename] = res
    return out


def main():
    px, lab, fin, uni = load()
    print("=== walk-forward OOS (IS2019-22 / OOS2023-26) ===")
    oos = walk_forward_oos(px, fin, uni)
    for k, v in oos.items():
        print(f"  {k}: IS={v['IS_ic']}(n{v['IS_n']}) OOS={v['OOS_ic']}(n{v['OOS_n']}) {v['verdict']}")

    print("\n=== 밸류업 event study (CAAR 저PBR vs 고PBR) ===")
    ev = value_up_event_study(px, fin, uni)
    for ename, r in ev.items():
        if r.get("status"):
            print(f"  {ename}: {r['status']}")
            continue
        print(f"  {ename} ({r['event_date']}, 저PBR {r['n_low_pbr']}종 vs 고PBR {r['n_high_pbr']}종):")
        for w in ["short_-5_+5", "mid_+1_+60"]:
            d = r[w]
            print(f"    {w}: 저PBR CAAR={d['low_pbr_caar']} (se={d.get('low_pbr_se')}) / 고PBR={d['high_pbr_caar']} / spread(저-고)={d['spread_low_minus_high']}")

    out = {"walk_forward_oos": oos, "value_up_event_study": ev}
    (ROOT / "validation-oos-event-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nSaved validation-oos-event-v3.json")


if __name__ == "__main__":
    main()
