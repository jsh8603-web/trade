<!-- author: equity study subagent (1단계 산출, 2026-06-04) -->
<!-- auditor: harness2 Worker (§M.12 반영 audit + S6 추적성, author != auditor, 2026-06-04) -->
<!-- audit_date: 2026-06-04 -->

# 15axis-audit.md — semiconductor §M v3 (frame v3 §E, A~P 15축)

> 독립 감사: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. battery 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 가설 사전선언 | PASS | indicators_passed = forward 횡단면 IC (ex-ante 신호). archetype valid_from 2019-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 85종(1818일) + yfinance(SOXX/NVDA/VIX/dollar/oil/rate) + **DART 재무**(fnlttSinglAcntAll) + FDR Marcap. raw-v3/{collect,measure,collect_dart,measure_valuation}.py 재실행 가능. |
| **C** | ★추적성 (hard-fail) | **PASS** | 모든 yaml 수치 → validation-metrics-v3 / validation-cross-v3 / validation-valuation-v3.json key 매핑 (source_id). IC -0.065=mom_6__12M / credit β -0.190=cross. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격신호 = PIT-safe (forward shift). ★valuation 횡단면 = DART rcept_dt(공시일) 이후만 적용(forward-fill from publication) = lookahead·restatement 회피(FY 보고지연 median 108-120일 실측). 시총=Close×현재주식수(시점별 주식수 정밀화 = collector_plan high, 한계 명시). |
| **E** | 다중검정 보정 | PASS | momentum 16테스트 BY(factor 3.38, rank1 thresh 0.00185) → ★**생존 0**(raw_p_min=0.00498 > thresh). Bonferroni α/16=0.00313 도 미생존. ★정직 보고 = 방향 robust but 보정 후 비유의(battery 와 차이 = battery 생존 vs semi 미생존). |
| **F** | OOS / walk-forward | PASS | CPCV purge(12M)+embargo(1), 15 fold, primary OOS hit=1.00. in-sample 결과 OOS 재현. |
| **G** | 자기상관 보정 | PASS | Newey-West HAC(lag=horizon) + block-bootstrap(block=3M, B=2000) 병행. 둘 다 CI 0 배제. |
| **H** | 미해결 명시 | PASS | collector_plan(EV-EBITDA high / PIT 멤버십 high) + verdict_detail 에 valuation gap / customer momentum REJECTED / credit US proxy / BY 미생존 명시. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷(생존 종목만), delisted/M&A 누락. 상장 시점 차이 정량화(85종 中 21종 부분 이력 = 신규상장). PIT 멤버십=collector_plan high. ★hard-fail 회피 사유: over-claim 아닌 정직 격하(PARTIAL 라벨 + note). |
| **J** | 측정 axis 일치 (spec↔code) | PASS | spec "cross-sectional 6M 모멘텀 → 12M forward" = code `cross_sectional_zscore(mom_6) → forward_returns(12)`. forward predictive 동일 verify. ★부호 음(reversal) = 측정값 그대로 보고(over-claim 없음). |
| **K** | 분석 unit ↔ portfolio label 분리 | PASS | 분석 unit = semi universe 85종(factor loading). z-score = peer-relative(sector-neutral). portfolio 조립 = supervisor(dispatch 밖). §M.7 분담 준수. ⚠️ sub-cluster(메모리/파운드리/소부장) 부호 동일(전 신호 음) = K 위반 없음(battery K 의 부호반대 sub-sleeve 우려 미발생). |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만 (산업이 cross 최종 박제 X). 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 함수 직접 호출 (재구현 X). opt-in 측정, production 코드 미변경. |
| **N** | cross 관계 PSD | N/A | cross 조립(RegimeGlasso Σ_return / Σ_signal mixing) = supervisor 단계. 산업 = β 벡터 보고만 = PSD 책임 밖. directional_spillover=[] (DY 통합단계). |
| **O** | leakage (PIT-safe) | PASS | forward return = shift(-h) (미래 누설 없음). reject≠missing: 상장 전 NaN = look-back gap(missing), regime bear=6month(reject 아님 = 관측). |
| **P** | net-cost robustness | PASS | gross \|IC\| 0.065 vs 월 16.5bps cost → gross 50%+ 보존(marginal, reversal turnover caveat 명시). KR STT 비대칭 반영. sqrt impact = supervisor 캘리브레이션. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 재무 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | PASS | 가격 PIT-safe + ★valuation = DART rcept_dt 공시일 이후만(lookahead 회피) |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL 라벨), over-claim 회피 |

★**hard-fail 0** (B/C/D PASS, I 는 PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor 책임).
- **status = PARTIAL CONFIRMED** — primary cs_mom_6m_reversal(momentum→reversal) 방향 robust(CI 0배제+CPCV 1.00+within 100%+cap-weighted 강) but ★BY/Bonferroni 미생존 = battery momentum(CONFIRMED) 보다 한 단계 낮음.
- ★**핵심 검증 가치**: momentum forward IC 부호 = **음(reversal)** = battery(양)와 반대 = **cyclical archetype 지지**(peak 되돌림). 부호 검증이 산업별 archetype 판별에 결정적.
- archetype cyclical 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시 = ex-post hazard 회피. transition 없음(단일 archetype).
- ★pilot 결론(미러): cross-sectional 메커니즘 작동 입증 + 부호가 산업 특성(cyclical vs growth) 반영 = 7산업 batch 일반화의 핵심 증거. ★valuation 횡단면 측정 완료(§10): PBR value premium 작동(pbr_z 24M IC -0.114, BY 유일 생존, CPCV 1.00, within 100%) + PER 무효(peak-EPS trap, 전 horizon 비유의) = archetype.py cyclical(PBR○ PER✗) 실데이터 입증, auto 동형.

---

# ★S2 conditional IC surface self-audit 보강 (2026-06-05, dispatch 원의도 본체)

> 위 audit = unconditional 측정(2026-06-04). 본 섹션 = S2 신규 conditional IC(measure_conditional.py) + G-F 7항 + family_2 의 15축 self-check. raw = validation-conditional-v3.json + regime_*.parquet.

| 축 | conditional 측정 판정 | 근거 |
|---|---|---|
| **A** 이론실재 | PASS | theory-notes §1 부호 사전확약(M1~M4) = Daniel-Moskowitz 2016/Asness QMJ/Choe-Kho-Stulz 2005/MS Memory Tracker. round-1(측정前) HARKing 방지. |
| **B** ★실데이터 | **PASS** | regime = FRED CLI/DEXKOUS + ECOS 외국인순매수 일별 실데이터. 합성지문 PASS(USDKRW 2022-10 1440.5/CLI 2020 99.13/외국인 대량매도 episode). collect_regime.py 재현. |
| **C** ★추적성 | **PASS** | summary.yaml conditional_ic_surface 수치 = validation-conditional-v3.json key 매핑. family_2(measure_interaction_terms 정식함수) + critique_validation(Fama-MacBeth) 재현가능. |
| **D** ★PIT | **PASS** | ★OECD CLI 발표지연(~1-2M) → CLI_PUB_LAG=2 적용(Macro regime PIT-safe). KRW(DEXKOUS)/flow(ECOS) 일별 실시간. forward=shift(+h). lag 보강 후 핵심발견 유지. |
| **E** 다중검정 | PASS | ★G-F §3 family 측정前 사전고정(6신호×3h×regime cell 단일 BY-FDR). m=105 BY survivors=[]. M_eff_signal=3.0(Li-Ji) 박제. ★over-claim 정정: naive m 과대 = M_eff 통합 supervisor 단계. |
| **F** OOS/walk-forward | **PASS** | ★walk-forward IS(2019-22)/OOS(2023-26) split: KRW_weak conditional 3신호(mom_6 -0.060→-0.155 / rev_1m -0.117→-0.064 / pbr_z -0.051→-0.050) 전부 OOS 부호+magnitude 유지. family_2 mom_6 IS t=-2.09→OOS t=-2.69 유의. = in-sample artifact 아님. (진짜 holdout 2026+ = flip-register pristine OOS 별개 미래 보너스.) |
| **G** 자기상관 | PASS | ★small-block size-invalid(Kiefer-Vogelsang) → wild-cluster bootstrap(Rademacher B=2000) per-cell p + n_eff(autocorr) + block-boot CI. asymptotic NW-HAC t = 참고만. |
| **A-5** ★regime interaction | **PASS** | ★family_2 의무 충족(rejected 박제 前). mom_6/rev_1m interaction t=-2.95/-2.33 유의(main 비유의) = "국면 따라 부호 갈림" 입증. mom_12_1/vol_60 비유의(정직). regime별 block-boot CI(wild-cluster). |
| **I** ★생존편향 | PARTIAL | universe = FDR 현재 스냅샷(생존종목). delisted/M&A 누락 = PIT 멤버십 collector_plan high(unconditional audit 동일). |
| **K** 다중검정/over-claim | PASS | ★비판검토 = 데이터 직접 검정(team-lead). Q6 PBR size위장 기각(Fama-MacBeth PBR|Size t=-2.47) + Q10 episode종속 기각(sub-period 부호일관). 무비판 채택 0. |

## S2 conditional verdict

- ★hard-fail 코어 (B/C/D) PASS, I PARTIAL(정직 격하). conditional 측정 = hard-fail 0.
- **핵심 = conditional IC surface 작동**(dispatch 원의도): KRW_weak regime서 value/reversal 증폭(family_2 t=-2.95) / flow_strong_buy서 momentum 소멸 / pbr 전horizon robust. = "어느 국면에 어느 지표" 답.
- ★G-B = "약함" 아님(family_2 살아있음 = conditional 본질, supervisor skip 판정). BY naive 미생존은 M_eff 미통합 + small-n.
- ★**verdict 확정 (walk-forward OOS)**: mom_6/pbr_z KRW_weak = CONFIRMED(tentative, n<30) / rev_1m KRW_weak = PARTIAL. = in-sample artifact 아님(OOS 부호+magnitude 유지).
- ★정직 단서: (a) OOS n=13 small-n → magnitude tentative(부호·방향만) (b) M_eff 통합 supervisor 단계 (c) magnitude hedge(PBR 24M overlap inflation) (d) 종목레벨 외국인flow = DATA-GATE(KRX 차단, deferral 아님).

## S2 신규 cycle 지표 측정완료 (★이연 금지 이행, 2026-06-05)

- ★사용자 박제 "이연 금지" 이행: 재고/CAPEX/R&D = DART 분기 재구성으로 **측정완료**(measure_fundamentals_cycle.py → validation-fundamentals-cycle-v3.json). 불확실해도 verdict 박제.
- **측정결과 (정직, over-claim 0)**: ppe_yoy(CAPEX asset growth) = TENTATIVE(y_60d IC -0.034 wc_p=0.0155, OOS -0.028 부호유지, prior 음 정합, BY 미생존) / inv_ratio = ★prior 반증(y_60d +0.045 일관 양, 재고순환 가설 반대) / 나머지(inv_yoy/capex_ratio/rnd_ratio) 비유의.
- **★통합 단일 FDR family**(merge_fdr_family.py): m_total=183(conditional 105 + fundamentals 78) survivors=0 = garden-of-forking-paths 차단(신규 추가시 더 엄격). raw_p_min 0.0005(pbr_z KRW_weak + ppe_yoy 동률).
- B/C/D PASS(DART 실재 + rcept_dt PIT + json 추적). 신규지표 hard-fail 0. = 약신호지만 정직 측정·박제.
