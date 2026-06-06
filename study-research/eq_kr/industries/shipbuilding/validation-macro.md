---
tags: [type/validation, domain/inv, scope/equity-kr, sector/shipbuilding, layer/macro]
date: 2026-06-05
---

# validation-macro — 조선 거시 regime + 공통인자 β

> raw 재현: `raw-v3/collect_regime.py`(regime) + `raw-v3/measure_cross.py`(공통인자 β)

## regime (Macro 4 × KRW 3 × flow 3)
- Macro = FRED KORLOLITOAASTSAM(CLI amplitude-adj 4국면). KRW = DEXKOUS yoy ±5%. flow = ECOS 802Y001/0030000 외국인순매수 28d z ±1.
- ★36셀 full N≥24 = 0개(최대 N=18) → 단일축 측정 + 2축 merge(통합단계).
- regime conditional IC = vol_60 Reflation -0.155 / flow_neutral -0.088 증폭 (validation-conditional 참조).

## 공통인자 β (contemporaneous, HAC, n=35)
| factor | β | t | CI95 | 판정 |
|---|---|---|---|---|
| **VIX** | -0.0145 | -2.00 | [-0.029, -0.0003] | ★유의(고베타, H7 입증) |
| dollar | -1.332 | -1.10 | [-3.71, 1.05] | 약 음(수출주 환율 가설 약, H1) |
| oil | +0.131 | +0.68 | [-0.24, 0.51] | 비유의(약 양=해양플랜트 방향) |
| rate | +0.014 | +0.25 | — | 비유의 |
| credit | -0.021 | -0.33 | — | 비유의(US HY proxy n=35) |

- ★VIX 고베타 = 조선 risk-off 시 약세(H7 입증). 유일한 유의 공통인자.
- ★H1 수출주 환율(원화약세→outperform): dollar β 약 음(t=-1.10 비유의) = 가설 약/비유의.

## verdict
조선 거시 민감도 = VIX 고베타(유의)만. 나머지 비유의. cross-sectional regime conditional = vol_60 증폭만 약하게.
