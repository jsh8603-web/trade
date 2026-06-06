# -*- coding: utf-8 -*-
"""measure_integration.py — cross-industry rotation 통합 (역할 전환: 통합 조율).

★team-lead 역할 전환: 개별 산업 cycle 측정 = 12 analyst 위임. 나(rotation-analyst) = cross-industry 통합.
12 analyst rotation-signals.md (이론→통계 verdict) 취합 → cross-industry 구조:
  (B) residual N_eff: 12산업 strict 패널 ~ 공통인자{d_usdkrw, foreign, semi_ppi} residualize → participation ratio
  (B) sleeve clustering: residual 상관 cross-section 에서 sleeve 묶기 (idiosyncratic-cycle singleton 보존)
  공통 macro 분리: cli_chg/foreign = N_eff≈1 시장 timing vs 산업 고유 rotation 구분

★universe 오염 정정 (refining-analyst 적발): v2 가 디렉토리 전체 prices.parquet 패널 = 부수종목 오염.
  refining = strict2(SK이노/S-Oil)로 교체 (가스 9종 제거, crack 가짜신호 폐기).
  steel/auto/battery/chemical/telecom = strict ≈ v2 (오염 없음 확인) = prices.parquet 유지.

★점추정 박제 금지 — participation ratio + bootstrap CI. residual N_eff = 자문 B 효과 정량.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]
SEMI_PPI_LAG = 1
# ★universe 정정: refining = strict2 (가스 오염 제거)
STRICT_OVERRIDE = {"refining": ["096770", "010950"]}  # SK이노/S-Oil (refining-analyst 적발)


def participation_ratio(corr):
    ev = np.linalg.eigvalsh(corr); ev = ev[ev > 1e-10]
    return float((ev.sum() ** 2) / (ev ** 2).sum())


def pr_bootstrap_ci(R, B=1000, seed=11):
    """participation ratio block-bootstrap CI (점추정 박제 금지)."""
    rng = np.random.default_rng(seed); n = len(R); prs = []
    block = 3
    for _ in range(B):
        nb = int(np.ceil(n / block))
        st = rng.integers(0, n - block + 1, size=nb)
        idx = np.concatenate([np.arange(s, s + block) for s in st])[:n]
        Rb = R.iloc[idx]
        try:
            prs.append(participation_ratio(Rb.corr().values))
        except Exception:
            pass
    return [round(float(np.percentile(prs, 2.5)), 2), round(float(np.percentile(prs, 97.5)), 2)] if prs else [None, None]


def mask_zombies(px, min_obs_ratio=0.5, min_nonzero_ratio=0.3):
    """★좀비 종목 마스킹 (audit minor 1): 상장 짧음(관측 부족) + 장기 무변동(거래정지) 제외.
    bio 코오롱티슈진(47.8%)/aitech 셀바스AI(284일) 류 = forward return 왜곡 차단.
    - 관측 비율 < min_obs_ratio (NaN 多 = 짧은 이력) 제외
    - 일간수익 nonzero 비율 < min_nonzero_ratio (무변동=거래정지/좀비) 제외
    """
    n = len(px)
    keep = []
    dropped = []
    for c in px.columns:
        s = px[c]
        obs_ratio = s.notna().sum() / n
        ret = s.pct_change()
        nonzero_ratio = (ret.abs() > 1e-9).sum() / max(ret.notna().sum(), 1)
        if obs_ratio >= min_obs_ratio and nonzero_ratio >= min_nonzero_ratio:
            keep.append(c)
        else:
            dropped.append((c, round(obs_ratio, 2), round(nonzero_ratio, 2)))
    return px[keep] if keep else px, dropped


def panel_monthly(sector, return_dropped=False):
    d = IND_ROOT / sector / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    if sector in STRICT_OVERRIDE:
        cols = [c for c in STRICT_OVERRIDE[sector] if c in px.columns]
        px = px[cols]
    px, dropped = mask_zombies(px)   # ★좀비 마스킹 (audit minor 1)
    ret = px.resample("ME").last().pct_change().mean(axis=1, skipna=True)
    if return_dropped:
        return ret, dropped
    return ret


def common_factors():
    d = IND_ROOT / "semiconductor" / "raw-v3" / "data"
    rs = pd.read_parquet(d / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    rsm = rs.resample("ME").last()
    F = pd.DataFrame(index=rsm.index)
    F["d_usdkrw"] = rsm["usdkrw"].pct_change()
    F["foreign"] = rsm["foreign_net_kospi"]
    F["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)
    return F


def residualize(y, F):
    common = y.dropna().index.intersection(F.dropna().index)
    if len(common) < 20:
        return y
    X = np.column_stack([np.ones(len(common))] + [F.loc[common, c].values for c in F.columns])
    beta, *_ = np.linalg.lstsq(X, y.loc[common].values, rcond=None)
    return pd.Series(y.loc[common].values - X @ beta, index=common)


def main():
    panels = {}
    zombie_report = {}
    for s in INDUSTRIES:
        ret, dropped = panel_monthly(s, return_dropped=True)
        panels[s] = ret
        if dropped:
            zombie_report[s] = [{"code": c, "obs_ratio": o, "nonzero_ratio": nz} for c, o, nz in dropped]
    P = pd.DataFrame(panels).loc["2019-01-01":]
    F = common_factors()

    out = {"meta": {
        "role": "cross-industry rotation 통합 (역할 전환: 개별 산업=12 analyst, 나=통합 조율)",
        "universe_정정": "refining=strict2(SK이노/S-Oil) 교체 (가스 오염 제거). 나머지=strict≈v2 확인",
        "자문_B": "residual N_eff(공통인자 residualize 후 participation ratio) + sleeve clustering",
        "zombie_masking": "★audit minor 1: 좀비 종목 마스킹(obs_ratio<0.5 OR nonzero_ratio<0.3 제외). bio/aitech 좀비 차단.",
        "zombie_dropped": zombie_report,
    }}

    # ── (B) raw vs residual N_eff ──
    raw_corr = P.corr().values
    Rresid = {s: residualize(P[s], F) for s in INDUSTRIES}
    Rdf = pd.DataFrame(Rresid).dropna()
    resid_corr = Rdf.corr().values
    out["neff"] = {
        "raw_N_eff": round(participation_ratio(raw_corr), 2),
        "raw_N_eff_ci95": pr_bootstrap_ci(P.dropna()),
        "residual_N_eff": round(participation_ratio(resid_corr), 2),
        "residual_N_eff_ci95": pr_bootstrap_ci(Rdf),
        "raw_pc1_var": round(float(np.linalg.eigvalsh(raw_corr).max() / 12), 3),
        "resid_pc1_var": round(float(np.linalg.eigvalsh(resid_corr).max() / 12), 3),
        "mean_pairwise_raw": round(float(raw_corr[np.triu_indices(12, 1)].mean()), 3),
        "mean_pairwise_resid": round(float(resid_corr[np.triu_indices(12, 1)].mean()), 3),
        "verdict": "residual N_eff = 공통인자 제거 후 진짜 독립 차원 (자문 Q-b '~3-4' 검증). 동시 active tilt 수 = floor(N_eff) cap.",
    }

    # ── (B) sleeve clustering (residual 상관 hierarchical) ──
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform
    dist = 1 - resid_corr
    np.fill_diagonal(dist, 0)
    dist = (dist + dist.T) / 2
    Z = linkage(squareform(dist, checks=False), method="average")
    sleeve_map = {}
    for nclust in [3, 4, 5]:
        labels = fcluster(Z, t=nclust, criterion="maxclust")
        groups = {}
        for ind, lab in zip(INDUSTRIES, labels):
            groups.setdefault(int(lab), []).append(ind)
        sleeve_map[f"k={nclust}"] = {f"sleeve_{k}": v for k, v in sorted(groups.items())}
    out["sleeve_clustering"] = {
        "method": "residual 상관 → 1-corr distance → average linkage hierarchical (raw-PCA 아닌 residual, 자문 B)",
        "clusters": sleeve_map,
        "note": "★idiosyncratic-cycle 산업(refining/shipbuilding) = thin sleeve/singleton 보존(대형 cyclical sleeve 희석 시 residual alpha 죽음). flow-beta redundant 묶기.",
    }

    # ── residual 상관 상위 pair (sleeve 묶기 근거) ──
    rc = pd.DataFrame(resid_corr, index=INDUSTRIES, columns=INDUSTRIES)
    pairs = []
    for i in range(12):
        for j in range(i + 1, 12):
            pairs.append((round(float(resid_corr[i, j]), 3), INDUSTRIES[i], INDUSTRIES[j]))
    pairs.sort(reverse=True)
    out["residual_top_pairs"] = [{"corr": c, "a": a, "b": b} for c, a, b in pairs[:8]]
    out["residual_bottom_pairs"] = [{"corr": c, "a": a, "b": b} for c, a, b in pairs[-5:]]

    fp = ROOT / "validation-integration-v1.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")
    print("=== (B) N_eff (raw vs residual, 자문 B 효과) ===")
    for k, v in out["neff"].items():
        print(f"  {k}: {v}")
    print("\n=== (B) sleeve clustering (residual hierarchical) ===")
    for kk, vv in out["sleeve_clustering"]["clusters"].items():
        print(f"  {kk}: {vv}")
    print("\n=== residual 상관 상위 pair (묶기 근거) ===")
    for p in out["residual_top_pairs"]:
        print(f"  {p['a']:13s} ~ {p['b']:13s} = {p['corr']:+.3f}")
    print("=== residual 상관 하위 (격리 근거) ===")
    for p in out["residual_bottom_pairs"]:
        print(f"  {p['a']:13s} ~ {p['b']:13s} = {p['corr']:+.3f}")


if __name__ == "__main__":
    main()
