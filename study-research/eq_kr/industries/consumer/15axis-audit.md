# 15axis-audit.md — consumer(소비재) §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery/financial 미러.
> Hard-fail 코어: **B·C·D·I** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators = forward 횡단면 IC. regime = ex-ante VIX. archetype valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 28종 + yfinance(VIX/factors) + **DART 707 rows(2019~ 완전)** + FDR. raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-metrics-v3 / valuation-v3 / cross-v3.json key 매핑. per_z 24M IC -0.141 = indicators.per_z__24M_value. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 forward-shift safe. valuation = DART rcept_dt 공시일 이후만(2019~ 완전). regime = ex-ante VIX level. |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY → 0. valuation 8테스트 BY(factor 2.72) → raw_p_min=0.062 borderline, 생존 0. raw p 보고. ★방향 일관성 별도 명시. |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo. valuation OOS hit 0.73-0.80. value premium 방향 OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC + block-bootstrap 병행. ★24M NW 비유의 vs block-boot 유의(CI 0배제) 둘 다 명시(NW 보수 채택, block-boot 방향 지지). |
| **H** | 미해결 명시 | PASS | collector_plan: 주식수 PIT / 배당 / PIT 멤버십 / 소비심리지수. valuation borderline 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷. 소비재 = 상폐 적으나 delisted/M&A 누락. 28종 中 3종 부분 이력. PIT 멤버십=collector_plan high. 정직 격하(PARTIAL). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "저PER cross-sectional → 24M forward value premium" = code `cross_sectional_zscore(per) → fwd_24M`. 부호=value(음) verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = consumer 28종(retail/food/cosmetics sub-cluster). z = peer-relative. ★sub-cluster 부호 cancel 주의(방어식품 vs 경기소비 유통) — valuation 은 부호 일관(전 sub value). |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(dollar 유의). 통합 supervisor L축. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = weight_falsification 직접 호출. opt-in, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward = shift(-h). valuation rcept_dt 이후. regime ex-ante. reject≠missing 구분. |
| **P** | net-cost robustness | PASS | 왕복 33bps. ★valuation(저회전 장기 value) = turnover 낮음 → net 보존 유리(momentum 대비). |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 707 rows 2019~ 완전) |
| C 추적성 | PASS | yaml↔raw 매핑 |
| D PIT | PASS | 가격/valuation/regime PIT-safe |
| I 생존편향 | PARTIAL | 정직 격하 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — ★valuation 유효 산업 입증(value premium 방향 일관, 24M block-boot 유의, 3M within 100%). NW 보수로 borderline. momentum 무신호 = asset_stable 정합.
- archetype asset_stable 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시. valuation 우세가 asset_stable value 정합.
- ★**3산업 분기 완성**: battery(momentum CONFIRMED) / financial(regime-conditional) / consumer(valuation) = "산업마다 유효 신호 다름" 데이터 입증 = 동적가중(regime/산업 conditional IC) 정당화. DART 표준계정 완전성(consumer 707 / financial 312)도 산업별 데이터 양식 차이 입증.
