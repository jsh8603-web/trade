---
tags: [type/validation, domain/inv, scope/equity-kr, sector/shipbuilding, layer/fundamental]
date: 2026-06-05
---

# validation-fundamental — 조선 valuation + cycle 펀더멘털 IC

> raw 재현: `raw-v3/measure_valuation.py` → validation-valuation-v3.json / `raw-v3/measure_fundamentals_cycle.py` → validation-fundamentals-cycle-v3.json

## valuation 횡단면 (PBR/PER, DART 재구성)
- data: DART fnlttSinglAcntAll 356 rows/16종 + pykrx 가격. PBR 1108 cells / PER 716 cells. PIT rcept_dt.

| 신호 | horizon | IC | t_NW | avgN | BY | 판정 |
|---|---|---|---|---|---|---|
| **per_z** | 24M_value | +0.2041 | 4.47 | 6.9 | 생존 | ★ARTIFACT |
| pbr_z | 24M_value | -0.0447 | -0.39 | 12.4 | X | INSUFFICIENT |
| pbr_z | 3M | +0.0226 | 0.47 | 12.9 | X | 비유의 |

- ★per_z 24M artifact: walk-forward 6M IS-0.132→OOS+0.086 / 12M IS-0.120→OOS+0.140 ★부호반전. avgN 6.9(흑자7종 한정) + 24M overlap eff_N≈2.5 degenerate(frame §M.12) + 적자→흑자 전환 표본 지배. ★BY 생존했으나 tradeable 자격 X.
- 조선 적자/흑자 구조: FY2021 적자7종/FY2022 적자6종 → FY2024 적자0종. = PER cross-sectional 시기별 무효(Damodaran value trap, H3 실증).
- ★PBR cross-sectional OOS 부호반전 = 슈퍼사이클 구간 value 역전. cross-sectional selection 무효. ★PBR 밴드 timing(시계열)은 별개 유효 가능.

## ★cycle 펀더멘털 (capex/재고/R&D, ★이연 금지)
- data: DART dart_extended 371 rows/16종 (inv 92%/ppe 100%/intangible 84%). PIT rcept_dt.

| 신호 | prior | y_20d IC | wc_p | 판정 |
|---|---|---|---|---|
| **capex_ratio** | two-sided(음약+양가능) | +0.0034 | 0.91 | ★INSUFFICIENT (capex 일반화 조선 미적용) |
| ppe_yoy | two-sided | -0.029 | 0.37 | INSUFFICIENT(약한 음=일반론 방향) |
| inv_ratio | two-sided(양가능:재공품) | +0.0142 | 0.67 | INSUFFICIENT(약한 양=재공품 방향) |
| rnd_ratio | 양(친환경선기술) | -0.013 | 0.74 | INSUFFICIENT |

- ★★capex 일반화 결론: capex_ratio ★무신호. 자동차/반도체 음 prior(asset growth anomaly)가 조선엔 약하게도 미발현. ★two-sided 로 one-sided 단정 회피 = 정답. 메커니즘 = 산업 베타 지배(H9).
- FDR family (신규지표 only): m=78, survivors=0.
- 통합 단일 FDR(merge_fdr_family.py): m_total=165(cond 87 + fund 78), survivors=0.
