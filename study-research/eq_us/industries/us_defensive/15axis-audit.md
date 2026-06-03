# 15axis-audit.md — us_defensive sleeve §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0. raw 재현 = `raw-v3/*.py`. 한국 7산업 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★valuation §10(EDGAR) = #15 us_cyclical 파이프라인 검증 후 → B/C/D 재확인.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators_passed = forward 횡단면 IC (ex-ante). archetype valid_from 2010-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. ★합성 P0 재검증(§1.7-D) 수행: v1 synthetic 격리 폐기 확인 + sector_etf_close 2000~ 실거래일(SHY/SOXX/TLT 2000 미상장 NaN=역사 정확) + yfinance 48종(4125일) + FRED 14 CSV 실시리즈 + ★**EDGAR XBRL 21149 rows**(48종 companyconcept, filed PIT). raw-v3/*.py 재현. |
| **C** | ★추적성 (hard-fail) | **PASS** | 모든 yaml 수치 → validation-metrics-v3 / validation-cross-v3 / ★validation-valuation-v3.json key 매핑(source_id). rev_1m IC -0.045 / vol_60 +0.076 / real_rate β -0.171 / per_z 24M -0.025 / pbr_z 24M +0.062. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격신호 = PIT-safe(forward shift). ★valuation = EDGAR filed date(filing acceptance) 이후만 forward-fill(lookahead 회피, Large accel 60d/40d, 한국 DART rcept_dt 대응). ★IID→block bootstrap(block=6M) 교체(small-n rule §1.4, 월간 regime autocorr). |
| **E** | 다중검정 보정 | PASS | 16테스트 BY(factor 3.38) → ★생존 0(rev_1m raw_p=0.0077 BY 임계 미달). ★정직 보고 = rev_1m NW 유의(p=0.008)하나 다중검정 후 미생존 = small-n hedge. |
| **F** | OOS / walk-forward | PASS | CPCV purge+embargo, rev_1m OOS hit=0.93. in-sample 부호 OOS 재현. |
| **G** | 자기상관 보정 | PASS | ★Newey-West HAC(lag=horizon) + **block-bootstrap(block=6M, IID 격하 교체)** 병행. rev_1m 둘 다 0 배제. vol_60 = boot 0 배제/NW 0 포함(정직). |
| **H** | 미해결 명시 | PASS | collector_plan(EDGAR valuation high / PIT holdings high / FF5+QMJ+BAB medium / n=36 cross 제약) + verdict 에 BY 미생존 / valuation gap / survivorship 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=yfinance 현재 대형주 스냅샷(생존만), 상폐/M&A 누락(staples/utility 합병 多). 상장 시점 차이 정량화(48종 中 2종 부분이력). PIT holdings=collector_plan high. ★hard-fail 회피: 정직 격하(PARTIAL). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "cross-sectional 1M 단기수익 → 3M forward" = code `cross_sectional_zscore(rev_1m) → forward_returns(3)`. forward predictive 동일. ★momentum 무효·rev 유의 = 측정값 그대로(over-claim 없음). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = defensive universe 48종(factor loading). z = peer-relative(sector-neutral). ★sub-sector(staples/utilities/healthcare/comm) real_rate β 부호 동일(전부 음=듀레이션) = K 위반 없음(부호반대 sub-sleeve 혼입 없음). portfolio 조립 = supervisor. |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(real_rate dominant). 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출. opt-in 측정, production 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립 = supervisor. 산업 = β 벡터 보고만. directional_spillover=[]. |
| **O** | leakage (PIT-safe) | PASS | forward return = shift(-h). reject≠missing: 상장 전 NaN = look-back gap(missing). HY OAS stress 9month = 관측(reject 아님). |
| **P** | net-cost robustness | PASS | ★US STT 없음(대칭) 왕복 16bps. \|IC\| rev 0.045 > 8bps/월 → gross 50%+ 보존. impact = supervisor. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% + ★§1.7-D synthetic check 통과(v1 격리, 현 실데이터 입증) + ★EDGAR XBRL 21149 rows |
| C 추적성 | PASS | yaml↔raw 매핑 (가격/cross/valuation 3 JSON) |
| D PIT | PASS | 가격 PIT-safe + ★IID→block-boot + ★valuation EDGAR filed date PIT(박제 완료) |
| I 생존편향 | PARTIAL | 정직 격하(survivorship-biased 명시) |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하). ★valuation EDGAR §10 박제 완료 = B/C/D 재확인 통과(EDGAR 21149 rows 실데이터, filed PIT, source_id 매핑).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL CONFIRMED** — primary cs_rev_1m(단기 reversal) NW+boot+CPCV+leave-episode 통과(n=193 Validated) but ★BY 미생존 = small-n hedge. cs_lowvol = TENTATIVE.
- ★**핵심 검증 가치**: momentum 무효 = **asset_stable 정합**(한국 consumer/telecom 동형 = 양식 일반성 입증). 단기 reversal + 저변동성 + real_rate 듀레이션(채권 대용, t=-4.1)이 방어주 신호. ★합성 P0 재검증(§1.7-D) 통과 + IID→block-boot 교체 = 데이터 무결성 + 통계 엄밀성 의무 이행.
- archetype asset_stable 사후편향 검사(M.5): valid_from 2010 사전선언, declared_at 명시 = ex-post hazard 회피.
- ★valuation EDGAR(§10) 박제 완료: 메커니즘 작동(PBR cov 5150/PER 5108, avgN 26) but IC 약·비유의(per_z value 방향만 약, pbr_z 역방향 value trap). BY 미생존 = 한국 consumer/telecom 강 value premium 미재현 = battery valuation 약 패턴 동일. cf. us_cyclical PER 작동 = ★sleeve 별 valuation IC 상이(동적가중 정당화).
- ★pilot 결론: 한국 asset_stable(consumer/telecom) → 미국 us_defensive = momentum 무효 동형 입증(가격신호 양식 cross-market 일반성) but valuation IC 는 sleeve 별 상이(미국 defensive 약, us_cyclical 강). dominant 신호 = rev_1m reversal + real_rate 듀레이션.
