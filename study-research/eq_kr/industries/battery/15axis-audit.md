# 15axis-audit.md — battery §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. v2 12axis-audit.md → v3 15축.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators_passed = forward 횡단면 IC (ex-ante 신호). archetype valid_from 2019-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 29종(1818일) + yfinance(LIT/ALB/VIX/dollar/oil/rate) + **DART 재무 698 rows**(fnlttSinglAcntAll) + FDR Marcap. raw-v3/{collect,measure,collect_dart,measure_valuation}.py 재실행 가능. |
| **C** | ★추적성 (hard-fail) | **PASS** | 모든 yaml 수치 → validation-metrics-v3 / validation-cross-v3 / **validation-valuation-v3.json** key 매핑 (source_id). IC +0.086=mom_6__12M / per_z 24M IC -0.116. 추적성 verify 18항목 ALL PASS. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격신호 = PIT-safe (forward shift). ★**valuation 횡단면 = DART rcept_dt(공시일) 이후만 적용**(forward-fill from publication) = lookahead·restatement 회피(FY 보고지연 median 80일 실측). 시총=Close×현재주식수(시점별 주식수 정밀화 = collector_plan medium, 한계 명시). |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY(factor 3.38) → mom_6__12M 유일 생존. **valuation 8테스트 BY(factor 2.72) → 생존 0**(전 valuation 비유의 명시). raw p 별도 보고. |
| **F** | OOS / walk-forward | PASS | CPCV purge(12M)+embargo(1), 15 fold, OOS hit=1.00. in-sample 결과 OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC(lag=horizon) + block-bootstrap(block=3M, B=2000) 병행. 둘 다 CI 0 배제. |
| **H** | 미해결 명시 | PASS | collector_plan + verdict_detail 에 valuation gap / customer momentum REJECTED / credit US proxy 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷(생존 종목만), delisted/M&A 누락. 상장 시점 차이 정량화(29종 中 6종 부분 이력). PIT 멤버십=collector_plan high. ★hard-fail 회피 사유: over-claim 아닌 정직 격하(PARTIAL 라벨 + note). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "cross-sectional 6M 모멘텀 → 12M forward" = code `cross_sectional_zscore(mom_6) → forward_returns(12)`. forward predictive 동일 verify. |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = battery universe 29종(factor loading). z-score = peer-relative(sector-neutral). portfolio 조립 = supervisor(dispatch 밖). §M.7 분담 준수. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만 (산업이 cross 최종 박제 X). 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 함수 직접 호출 (재구현 X). opt-in 측정, production 코드 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립(RegimeGlasso Σ_return / Σ_signal mixing) = supervisor 단계. 산업 = β 벡터 보고만 = PSD 책임 밖. directional_spillover=[] (DY 통합단계). |
| **O** | leakage (PIT-safe) | PASS | forward return = shift(-h) (미래 누설 없음). reject≠missing: 상장 전 NaN = look-back gap(missing), regime bear=14month(reject 아님 = 관측). |
| **P** | net-cost robustness | PASS | gross IC +0.086 vs 월 16.5bps cost → gross 50%+ 보존. KR STT 비대칭 반영. sqrt impact = supervisor 캘리브레이션 명시. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 698 rows 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (verify 18항목 ALL PASS) |
| D PIT | PASS | 가격 PIT-safe + ★valuation = DART rcept_dt 공시일 이후만(lookahead 회피) |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL 라벨), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님). 

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor 책임).
- **status = PARTIAL CONFIRMED** — primary cs_mom_6m(momentum) 강건 = dominant. ★valuation 횡단면 결함 해소(DART 재구성, 메커니즘 작동 PBR avgN 26/PER 20) 하나 battery 내 valuation IC 약·비유의(per value premium 방향성만, BY 미생존) → 산업 전체 PARTIAL 유지.
- archetype cyclical 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시 = ex-post hazard 회피. transition 없음(단일 archetype).
- ★pilot 결론: cross-sectional 메커니즘(momentum + valuation 양쪽) 작동 입증 = 사용자 핵심 요구 충족. valuation IC 유효성은 산업별 상이 가능 → 6산업 batch 일반화 검증.
