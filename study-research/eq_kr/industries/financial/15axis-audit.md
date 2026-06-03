<!-- author: equity study subagent (1단계 산출, 2026-06-04) -->
<!-- auditor: harness2 Worker (§M.12 반영 audit + S6 추적성, author != auditor, 2026-06-04) -->
<!-- audit_date: 2026-06-04 -->

# 15axis-audit.md — financial(금융) §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery 15axis 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators = forward 횡단면 IC. regime = ex-ante 금리 Δ. archetype valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 34종 + yfinance(^TNX/VIX/dollar/oil/rate) + DART 312 rows + FDR. raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-metrics-v3 / valuation-v3 / cross-v3.json key 매핑. regime rate_up +0.102 = regime_g1.regime_conditional_ic.rate_up. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 forward-shift safe. valuation = DART rcept_dt 공시일 이후만. regime = ex-ante 금리 3M Δ(진입시점 관측). |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY(factor 3.38) → 생존 0. valuation 8테스트 BY → per_z n=7 형식상 생존하나 INSUFFICIENT 격하 → 실질 0. raw p 보고. |
| **F** | OOS / walk-forward | PASS(조건부) | CPCV purge+embargo. ★단 unconditional 신호 무유의 + valuation n 부족(24M CPCV=nan) → OOS 판정 = regime-conditional 한정 의미. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC + block-bootstrap 병행. unconditional CI 전부 0 포함(비유의 정직). |
| **H** | 미해결 명시 | PASS | collector_plan: DART 금융재무 2023~ high / valuation value 분기 consumer 이관 / regime small-n / KR 금리 proxy 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷. ★금융 = 합병 잦음(외환은행 등 delisted 누락) → 생존편향 잔존. 34종 中 3종 부분 이력. PIT 멤버십=collector_plan high. 정직 격하(PARTIAL). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "regime-conditional 6M 모멘텀 → 12M forward" = code `regime[rate_up] 필터 → cross_sectional_zscore(mom_6) → fwd_12M`. forward predictive verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = financial 34종(은행/증권/보험 sub-cluster). z = peer-relative. portfolio 조립 = supervisor. ★sub-cluster 부호 cancel 주의(은행 NIM+ vs 증권 시황) = §1.6 — regime-conditional 이 부분 분리. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(전부 비유의). 통합 supervisor L축. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = weight_falsification 직접 호출. opt-in 측정, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward = shift(-h). regime = ex-ante. reject≠missing: 상장 전 NaN=missing / rate regime = 관측. |
| **P** | net-cost robustness | PASS(조건부) | 왕복 33bps. ★unconditional 유효신호 부재 → net IC = regime-conditional 한정. gross 보존 논의 = regime 조건부. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 312 rows) |
| C 추적성 | PASS | yaml↔raw 매핑 |
| D PIT | PASS | 가격/valuation/regime 모두 PIT-safe |
| I 생존편향 | PARTIAL | 금융 합병 잦음, 정직 격하 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O PASS, F/P 조건부(regime-conditional 한정), N=N/A.
- **status = TENTATIVE** — ★핵심 = regime-conditional 모멘텀(rate_up +0.102, NIM, n=21 small). unconditional 비유의(battery 대조). valuation 데이터 제약(DART 2023~).
- archetype spread_driven 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시. regime-conditional 금리 의존이 spread_driven 정합 입증(tentative).
- ★pilot 분기 학습 박제: 산업별 (a) 유효 신호 상이(battery momentum / financial regime-conditional) (b) 데이터 양식 상이(제조 fnlttSinglAcntAll 충분 / 금융 2023~) (c) universe 키워드 부정확 → 산업별 측정·화이트리스트·데이터양식 검증 필수.
