<!-- author: equity study subagent (1단계 산출, 2026-06-04) -->
<!-- auditor: harness2 Worker (§M.12 반영 audit + S6 추적성, author != auditor, 2026-06-04) -->
<!-- audit_date: 2026-06-04 -->

# 15axis-audit.md — auto(자동차) §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery/반도체 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators_passed = forward 횡단면 IC (ex-ante 신호). archetype valid_from 2019-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 17종(1818일) + yfinance(CARZ/SLX/VIX/dollar/oil/rate) + DART 재무 + FDR Marcap. raw-v3/*.py 재실행 가능. |
| **C** | ★추적성 (hard-fail) | **PASS** | 모든 yaml 수치 → validation-metrics-v3 / validation-cross-v3 / validation-valuation-v3.json key 매핑 (source_id). ★pbr_z 24M IC -0.463 / per_z 무신호 ≈0 / mom_6__3M -0.064 / credit β -0.072. yaml 파싱 + 추적성 verify PASS. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격신호 = PIT-safe (forward shift). ★valuation 횡단면 = DART rcept_dt(공시일) 이후만 적용 = lookahead·restatement 회피(FY 보고지연 median 108-120일 실측). 시총=Close×현재주식수(시점별 주식수 정밀화 = collector_plan high, 한계 명시). |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY → **생존 0**(raw_p_min=0.0958). ★valuation 8테스트 BY(factor 2.72) → **pbr 4개 생존(24M/12M/6M/3M), per 전부 미생존(peak-EPS 무신호)**. ★단 pbr magnitude = n=14 협소 과대 = 방향 생존 신뢰/크기 hedge. raw p 보고. |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo, mom_6__3M OOS hit=0.87(부호 약 일관). 게이트 통과하나 신호 자체 약. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC(lag=horizon) + block-bootstrap(block=3M, B=2000) 병행. ★둘 다 CI 0 포함 = 비유의(정직). |
| **H** | 미해결 명시 | PASS | collector_plan(EV-EBITDA high / PIT 멤버십 high / 화이트리스트 영속화) + verdict 에 가격신호 무효 / customer momentum REJECTED / valuation gap 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷(생존 종목만), ★자동차 구조조정 多(쌍용차→KG모빌리티 법정관리 등) delisted/M&A 누락. 상장 시점 차이 정량화(17종 中 3종 부분이력). ★화이트리스트 = 현재 스냅샷 큐레이션(PIT 멤버십 아님). PIT=collector_plan high. ★hard-fail 회피: over-claim 아닌 정직 격하(PARTIAL). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "cross-sectional 6M 모멘텀 → 3M forward" = code `cross_sectional_zscore(mom_6) → forward_returns(3)`. forward predictive 동일. ★IC 약·비유의 = 측정값 그대로 보고(over-claim 없음, 신호 무효 정직). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = auto universe 17종(factor loading). z-score = peer-relative(sector-neutral). ★화이트리스트(완성차/부품/타이어)로 부호 반대 sub-sleeve(보험·2차전지) 혼입 배제 = K 위반 회피(battery K 우려 직접 대응). portfolio 조립 = supervisor. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만. 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출. opt-in 측정, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor 단계. 산업 = β 벡터 보고만. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward return = shift(-h). reject≠missing: 상장 전 NaN = look-back gap(missing). |
| **P** | net-cost robustness | PASS | ★가격신호 비유의라 net Sharpe 무의미(정직). KR STT 비대칭 모델 반영. valuation 확정 후 재평가 명시. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% |
| C 추적성 | PASS | yaml↔raw 매핑 |
| D PIT | PASS | 가격 PIT-safe + valuation DART rcept_dt |
| I 생존편향 | PARTIAL | 정직 격하(자동차 구조조정 多 생존편향 우려 명시) |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — ★**valuation(PBR) = 자동차 진짜 신호**: PBR value premium 방향 강(BY 4 생존, LOO robust 17종, within 100%@24M, block-boot 0배제) = 가격 momentum 무효 대체(예고 적중). ★단 magnitude(-0.46 t=-17.6) = n=14 협소 과대 = small-n hedge(CONFIRMED 박제 안 함). ★PER = peak-EPS trap 무신호 = archetype.py cyclical 정의 데이터 입증.
- 가격 momentum/reversal = 전 16 신호 비유의(BY 0). customer momentum REJECTED. common factor 비유의.
- ★**핵심 검증 가치**: cyclical 3산업(battery 양 momentum CONFIRMED / 반도체 음 reversal PARTIAL / 자동차 가격 무효+PBR value) = **같은 cyclical 도 유효 신호·metric 상이**. ★archetype별 valuation metric 차등 입증(cyclical=PBR○ PER✗ / asset_stable=PER value / event_driven=멀티플 부적합) = 동적가중 + metric 적합도 데이터 입증.
- archetype cyclical 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시. PBR value + peak-EPS trap = cyclical 정합.
- ★universe 화이트리스트(완성차/부품/타이어 17종, 오염 18종 블랙리스트 배제) = K축 부호반대 sub-sleeve 혼입 회피. ★universe 협소(17종) = PBR magnitude 과대 = over-claim 회피(방향/magnitude 분리).
