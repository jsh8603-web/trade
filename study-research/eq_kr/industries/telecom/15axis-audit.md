<!-- author: equity study subagent (1단계 산출, 2026-06-04) -->
<!-- auditor: harness2 Worker (§M.12 반영 audit + S6 추적성, author != auditor, 2026-06-04) -->
<!-- audit_date: 2026-06-04 -->

# 15axis-audit.md — telecom(통신) §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery/consumer 미러.
> ★universe 협소(14종) = magnitude 과대 = small-n 핵심 점검.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators = forward 횡단면 IC. regime = ex-ante 금리. archetype valid_from 2019 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 14종 + yfinance(^TNX/factors) + DART 357 rows(2019~) + FDR. raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-metrics-v3 / valuation-v3 / cross-v3.json key 매핑. pbr 24M IC -0.542. LOO raw 재현. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 forward-shift safe. valuation = DART rcept_dt 공시일 이후만. regime = ex-ante 금리 Δ. |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY 0. valuation 8테스트 BY → 6 생존. ★단 n=13 협소로 magnitude 과대 명시(생존=방향, 크기 hedge). |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo. valuation OOS hit 0.80-1.00. value 방향 OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC + block-bootstrap. pbr 12M block-boot CI 0배제. ★+LOO 종목 robustness(14종 제외 전부 음). |
| **H** | 미해결 명시 | PASS | collector_plan: ★universe 확장(협소 high) + 배당수익률 + PIT 멤버십. magnitude 과대 hedge 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe = FDR 현재 스냅샷. 통신 = 합병 잦음(LG텔레콤/데이콤 통합). 14종 中 1종 부분 이력. ★universe 협소 자체가 더 큰 제약. PIT 멤버십=collector_plan. 정직 격하. |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "저PBR cross-sectional → 24M forward value" = code `cross_sectional_zscore(pbr) → fwd_24M`. 부호=value(음) verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | ★분석 unit = telecom 14종(service 3 + equipment 11). ★archetype 혼재(service asset_stable / equipment cyclical) = §1.6 부호 cancel 주의 명시. service sub n=3 = INSUFFICIENT 별도 격하. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(전부 비유의). 통합 supervisor L축. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = weight_falsification 직접 호출. opt-in, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward = shift(-h). valuation rcept_dt 이후. regime ex-ante. reject≠missing 구분. |
| **P** | net-cost robustness | PASS | 왕복 33bps. ★valuation 저회전 net 유리 but n=13 분산 제한 = concentration cap 주의 명시. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 357 rows) |
| C 추적성 | PASS | yaml↔raw 매핑 (LOO 포함) |
| D PIT | PASS | 가격/valuation/regime PIT-safe |
| I 생존편향 | PARTIAL | 합병 잦음 + universe 협소, 정직 격하 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하 → hard-fail 아님). ★단 universe 협소(14종) = magnitude 과대평가 명시 = over-claim 회피의 핵심(IC -0.54 를 CONFIRMED 박제 안 함 → PARTIAL + 방향/magnitude 분리).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — ★value premium 방향 강(BY 6 생존, LOO robust 14종, within 100%) but magnitude(-0.54 t=-12) = n=13 협소 과대평가(small-universe artifact). 방향 신뢰/magnitude small-n hedge. service sub(3종)=INSUFFICIENT.
- archetype asset_stable(서비스) + cyclical(장비) 혼재. valuation value 정합 = consumer 재현.
- ★**universe 협소 = 양식 경계 케이스 입증**: cross-sectional 최소 종목 수 ~13 = magnitude 신뢰 하한. n<5종 = INSUFFICIENT(service sub) / ~13종 = 방향만 신뢰. = 6산업 batch 시 협소 산업 magnitude hedge 의무 + over-claim 회피.
- ★**5산업 분기 (kr-battery 담당)**: battery momentum / financial regime-conditional / consumer valuation / bio event_driven(변동성) / telecom asset_stable valuation(consumer 재현, universe 협소) = 동적가중 정당화 + 양식 경계 케이스(데이터 부재 financial / universe 협소 telecom / 멀티플 부적합 bio) 다각 입증.
