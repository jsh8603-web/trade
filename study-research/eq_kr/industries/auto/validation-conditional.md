---
tags: [type/validation, domain/equity, sector/auto, scope/equity-kr, stage/conditional-ic]
date: 2026-06-05
purpose: S2 conditional IC surface 실측 상세. raw = validation-conditional/fundamentals-cycle/critique/attack/merged-fdr-v3.json.
---

# auto(자동차) S2 conditional IC surface 실측

## 측정 설계 (G-F 7항)

- 측정 = IC(지표, regime, horizon). 지표 = 가격(mom_6/mom_12_1/rev_1m/vol_60) + valuation(pbr_z/per_z) + DART cycle(capex_ratio/inv_ratio/ppe_yoy/inv_yoy/rnd_ratio).
- regime = Macro 4(CLI amplitude-adj level×6M momentum) × KRW 3(USDKRW yoy ±5%) × flow 3(ECOS 외국인순매수 28d z ±1). 36셀 full N>=24=0 → 단일축.
- horizon = y_5d/y_20d/y_60d 일간 forward. anchor = 월말 cross-sectional z-score.
- per-cell p = wild-cluster bootstrap(Rademacher B=2000, small-block size-invalid 회피). n_eff = autocorr 보정. block-boot CI.
- 단일 FDR family 측정前 고정. walk-forward OOS = IS 2019-22 / OOS 2023-26.

## 1. 가격신호 (unconditional 비유의 + conditional OOS flip)

| 신호 | uncond IC(y_20d) | wc_p | best conditional | walk-forward OOS | verdict |
|---|---|---|---|---|---|
| mom_6 | -0.028 | 0.417 | KRW_weak -0.003 | KRW_weak IS-0.098→OOS+0.150 FLIP | REJECTED(OOS) |
| mom_12_1 | -0.008 | 0.805 | KRW_weak interaction t=2.18(양) | uncond IS-0.082→OOS+0.061 FLIP | REJECTED(OOS) |
| rev_1m | +0.020 | 0.579 | — | KRW_weak IS-0.121→OOS+0.197 극단FLIP | REJECTED(OOS) |
| vol_60 | +0.005 | 0.895 | KRW_weak interaction t=2.75(양) | KRW_weak IS+0.051→OOS+0.281(magnitude 폭증) | TENTATIVE(불안정) |

★결론: 가격신호 unconditional 전부 비유의. family_2 interaction(mom_12_1/vol_60 KRW_weak) 유의하나 부호 양(momentum continuation, 반도체 reversal 음 증폭과 반대) + 해당 cell OOS flip = in-sample artifact. weight ~0.

## 2. valuation (PBR robust / PER peak-EPS trap)

| 신호 | uncond IC | best cell(wc_p) | walk-forward OOS | size-orth(Fama-MacBeth) | verdict |
|---|---|---|---|---|---|
| pbr_z (y_60d) | -0.108 | Slowdown -0.184(wc_p 0.0005) | uncond IS-0.108→OOS-0.117 ✅ | pbr t=-2.67 / size t=-0.38 | PARTIAL CONFIRMED(OOS robust) |
| per_z (y_20d) | -0.0001 | — | — | — | INSUFFICIENT(peak-EPS trap, IC≈0) |

## 3. ★신규 DART cycle 지표 (capex_ratio = 자동차 진짜 신호)

| 신호 | prior | uncond IC(y_60d) | wc_p | walk-forward OOS | FDR 생존 | verdict |
|---|---|---|---|---|---|---|
| ★capex_ratio | 음 | -0.103 | 0.0015 | IS-0.044→OOS-0.172 ✅강화 | ✅(통합 m=168) | PARTIAL CONFIRMED(OOS robust) |
| inv_ratio | 음 | -0.051 | 0.156 | y_20d ✅ / y_60d FLIP | ✗ | TENTATIVE |
| ppe_yoy | 음 | -0.017 | 0.607 | FLIP | ✗ | INSUFFICIENT |
| inv_yoy | 음 | +0.036 | 0.278 | (prior 반대) | ✗ | INSUFFICIENT |
| rnd_ratio | 양 | -0.028 | 0.485 | FLIP | ✗ | INSUFFICIENT |

★capex|Size(Fama-MacBeth y_60d): capex t=-3.78 / size t=-2.23(공존) → multivariate(pbr+capex+size) capex t=-3.38 독립 유지.

## 4. 통합 단일 FDR family (garden-of-forking-paths 차단)

- merge_fdr_family.py: cond 90 + fund 78 = ★m_total=168, BY survivors=**5**.
- survivors: pbr_z y_60d(uncond + Slowdown) 2 + capex_ratio 3(Recovery×2 + KRW_neutral). raw_p_min=0.0005.
- ★반도체(survivors=0)와 결정적 차이 = 자동차 valuation+asset growth 가 보정 후에도 생존.

## 5. S5 역공격 (validation-attack-v3.json)

- A1 size-bucket capex IC: 대형 -0.168 / 소형 -0.118 (양쪽 음 = size 위장 아님).
- A2 sub-period: pbr(pre -0.105/post -0.117) + capex(pre -0.044/post -0.172) 부호 일관(episode 종속 아님, capex 2023+ 강화 명시).
- A3 LOO: 현대/기아 각 제외 pbr·capex 부호 robust(ex둘다 pbr -0.106/capex -0.083).

## 6. 정직 단서

- ★universe 17종 협소 = magnitude 과대(small-universe inflation). 모든 점추정 = 방향+breadth-adj 권역만.
- ★OOS 검증 완주(IS/OOS split). 진짜 holdout(2026+) = flip-register 보너스.
- ★capex size 공존 = 정직 명시(독립이나 size effect 존재).
- ★small-N hedge: TENTATIVE/PARTIAL 라벨, CONFIRMED 강 금지.
