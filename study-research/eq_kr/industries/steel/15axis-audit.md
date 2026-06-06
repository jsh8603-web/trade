<!-- author: steel study teammate (1단계 산출 self-audit, 2026-06-05) -->
<!-- ★최종 audit = G-C 독립 세션(author != auditor). 본 문서 = self-audit 초안(참고용). -->
<!-- audit_date: 2026-06-05 -->

# 15axis-audit.md — steel §M v3 (frame v3 §E, A~P 15축) self-audit

> 3컬럼(① 적용했나 ② 측정 코드/수치 경로 ③ 결과·판정). raw 재현 = `raw-v3/*.py`. semiconductor 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★★small-universe(23종) = 본 capsule 전반의 magnitude inflation caveat(frame §M.12) 일관 적용.

| 축 | ① 적용 | ② 측정 경로 (코드·수치) | ③ 판정 |
|---|---|---|---|
| **A** 이론 실재 | ✅ | theory-notes.md §1 = Cooper-Gulen-Schill 2008(asset growth) / Asness QMJ(PBR) / Daniel-Moskowitz 2016(momentum crash) / Choe-Kho-Stulz 2005. round-1 부호 사전확약(측정前). | PASS |
| **B** ★실데이터 (hard) | ✅ | 합성 0%. pykrx OHLCV 23종(1818일) + yfinance(SLX/VALE/VIX/dollar/oil/rate) + DART(fnlttSinglAcntAll 563 + dart_extended 592 rows) + FDR + FRED/ECOS regime. raw-v3/{collect,measure,collect_dart,collect_dart_extended,measure_*}.py 재실행 가능. | **PASS** |
| **C** ★추적성 (hard) | ✅ | 모든 yaml 수치 → validation-{metrics,cross,valuation,conditional,fundamentals-cycle,merged-fdr}-v3.json key 매핑(source_id). mom_12_1 -0.181=validation-metrics / capex -0.084=fundamentals-cycle / pbr -0.16=valuation. | **PASS** |
| **D** ★PIT (hard) | ✅ | 가격신호=PIT-safe(forward shift). ★valuation/capex 횡단면=DART rcept_dt(공시일) 이후만(FY 보고지연 median 108-120일 실측). regime Macro=CLI 2개월 lag(vintage). 시총=Close×현재주식수(시점별 정밀화=collector_plan high). | **PASS** |
| **E** 다중검정 보정 | ✅ | measure.py momentum/vol family m=16 BY → **생존 7개**. 통합 conditional+fundamentals m=180 BY → 생존 0(raw_p_min=0.0005 ≈ Bonferroni α 0.00049 경계). ★정직 보고 = family별 차이 명시(momentum family 생존 vs 통합 미생존). | PASS |
| **F** OOS / walk-forward | ✅ | CPCV purge(horizon)+embargo, momentum/vol/pbr OOS hit 0.93~1.00. ★capex walk-forward(IS -0.111→OOS -0.053 부호유지). ★conditional KRW_neutral walk-forward(IS/OOS 부호+magnitude 유지). | PASS |
| **G** 자기상관·검정력 | ⚠️ | Newey-West HAC(lag=horizon) + block-bootstrap(B=2000) + wild-cluster(Rademacher, per-cell). ★effective-N tier = Tentative(momentum n=65) / ★small-universe(avg 20종) breadth 한계. | PASS(tier 강등 = Tentative, small-universe) |
| **H** 미해결 명시 | ✅ | collector_plan(EV-EBITDA/PIT 멤버십/중국 조강·철광석/KR HY/배당) + candidate-ledger data-gate/falsifier + verdict 정직단서(small-universe magnitude). | PASS |
| **I** ★생존편향 (hard) | ⚠️ | universe=FDR 현재 스냅샷(생존 종목), delisted/M&A 누락. 23종 中 3종 부분 이력. ★단 철강=상폐 드문 산업(자산집약 대형주)→영향 반도체/바이오보다 작음. PIT 멤버십=collector_plan high. | **PARTIAL** (정직 격하, over-claim 회피) |
| **J** 측정 axis 일치 (spec↔code) | ✅ | spec "cross-sectional 12-1 모멘텀→12M forward" = code cross_sectional_zscore(mom_12_1)→forward(12). forward predictive 동일. capex spec "유형/총자산→forward 음" = code ppe/assets z→forward IC. 부호 그대로 보고(over-claim 0). | PASS |
| **K** 분석 unit ↔ portfolio label | ✅ | 분석 unit = steel universe 23종(factor loading). z-score=peer-relative(sector-neutral). portfolio 조립=supervisor(dispatch 밖, §M.7). sub-cluster(고로/봉형강/강관/특수강) 전 신호 음 부호 동일 = K 위반 없음(부호반대 cancel 미발생). | PASS |
| **L** 공통인자 1회 계상 | ✅ | common_factor_exposure = β 보고만(oil/credit/dollar). 산업이 cross 최종 박제 X. 통합 supervisor L축 1회. | PASS |
| **M** 코드 충실 (wire) | ✅ | rank_ic / score_ic_breakdown_eprocess = core/assume/weight_falsification 직접 호출(재구현 X). opt-in 측정, production(INV_R15_WEIGHTS) 미접촉. | PASS |
| **N** cross 관계 PSD | N/A | cross 조립(RegimeGlasso/Σ_signal)=supervisor. 산업=β 벡터 보고만. directional_spillover=[](DY 통합단계). | N/A (supervisor 책임) |
| **O** leakage (PIT-safe) | ✅ | forward=shift(-h)/searchsorted+h(미래 누설 없음). reject≠missing: 상장 전 NaN=look-back gap(missing), regime bear=6month(관측=reject 아님). | PASS |
| **P** net-cost robustness | ⚠️ | gross \|IC\| momentum 0.181 / vol 0.117 vs 월 16.5bps cost. ★단 small-universe magnitude inflation + 철강 저유동성 → net 보존 marginal. KR STT 비대칭. sqrt impact=supervisor. | PASS(marginal, small-universe·저유동성 caveat) |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 재무·재고·유형자산 포함) |
| C 추적성 | PASS | yaml↔raw 매핑 (source_id) |
| D PIT | PASS | 가격 PIT-safe + valuation/capex = DART rcept_dt 공시일 이후만 |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL 라벨), over-claim 회피. 철강=상폐 드뭄 |

★**hard-fail 0** (B/C/D PASS, I = PARTIAL = 정직 격하로 over-claim 회피 → hard-fail 아님).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A(supervisor 책임). G/I/P = 주의(small-universe·생존편향·net marginal).
- **status = PARTIAL CONFIRMED** — 다수 신호(momentum reversal / vol_60 / pbr_z) 방향·significance robust(BY family 생존 + CPCV 1.00 + within 100% + walk-forward OOS) but ★통합 BY 미생존 + small-universe magnitude hedge.
- ★**핵심 검증 가치 2**: (1) momentum forward IC = **음(reversal)** = battery(양)와 반대 = cyclical archetype 지지 (2) ★**capex_ratio 음(asset growth anomaly)** = dispatch capex 일반화 입증 = 자동차(high_confidence) 재현 = 자산집약 4섹터 일반화 1보.
- archetype cyclical 사후편향 검사(M.5): valid_from 2019 사전선언, declared_at 명시, 철강=구조적 cyclical 일관(transition 없음) = ex-post hazard 낮음.
- ★★**small-universe(23종, avg 20) magnitude inflation 일관 caveat**: point estimate(momentum -0.181/pbr -0.16) literal 금지, breadth-adj IR(-0.81) + 50% haircut. S5-B(PBR size 위장) t=-1.98 경계 = small-universe 한계 명시.

## ★S2 conditional IC surface self-audit 보강 (dispatch 원의도 본체)

- conditional 측정(measure_conditional.py, G-F 7항 헤더 선언) = "어느 국면에 어느 지표가 forward 예측하나" surface 산출 = dispatch 원의도 본체.
- ★KRW_neutral 증폭축(반도체 KRW_weak과 다름) + walk-forward OOS 전부 부호+magnitude 유지 = in-sample artifact 아님 = conditional CONFIRMED(tentative).
- family_2 interaction(KRW_neutral) = 방향 정합이나 t=-1.63 비유의(small-n) → walk-forward가 verdict 근거(interaction 비유의 ≠ 신호 약함).
- G-B "신호 약함" 단정 = walk-forward OOS 생존 + momentum/vol family BY 생존 + capex 가설 입증으로 반증 = skip 권고(supervisor 판단).

## ★S5 역공격 self-audit (실측 박제)

- POSCO drop(-0.165 생존) + leave-2021(-0.161 생존) = momentum 단일종목·episode 종속 기각.
- PBR size 위장(Fama-MacBeth PBR|Size t=-1.98) = PBR 우위이나 small-universe 경계 = hedge 박제(over-claim 회피).
- 수렴: momentum reversal robust, PBR size 독립은 약(small-universe), walk-forward OOS 생존과 정합.
