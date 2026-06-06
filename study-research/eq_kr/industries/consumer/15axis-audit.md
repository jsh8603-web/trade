<!-- author: consumer equity study teammate (semi-analyst, opus 1m, 2026-06-05) -->
<!-- self-audit 초안 (S2 conditional IC + A-4 sub-sector + G-G v2 통합). 최종 G-C 독립 audit = 별 세션(author != auditor) -->
<!-- 구버전(2026-06-04 unconditional only) 대체. audit_date: 2026-06-05 -->

# 15axis-audit.md — consumer(소비재) §M v3 (frame v3 §E, A~P 15축)

> self-audit: yaml↔raw 재현·hard-fail 0 확인. raw 재현 = `raw-v3/*.py`. 반도체 15axis-audit.md 미러.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O.
> ★독립 G-C audit(별 세션)이 본 self-audit 을 신뢰하지 않고 raw 재계산으로 독립 판정.

## A~P 15축 (unconditional + S2 conditional 통합)

| 축 | 항목 | 판정 | 근거 |
|---|---|---|---|
| **A** | 이론 실재·가설 사전선언 | PASS | theory-notes §1(Goldberg-Hellerstein cost pass-through / Adler-Dumas FX exposure / Lehmann reversal / Fama-French value) + §6 부호 one-sided 사전확약(측정前 동결). archetype valid_from 2019-01 사전선언. |
| **B** | ★실데이터 (hard-fail) | **PASS** | 합성 0%. pykrx OHLCV 28종(1818일) + DART 707 rows(2019~2026-03) + FRED CLI/DEXKOUS + ECOS 외국인 + yfinance(VIX/dollar/oil/rate). 합성지문 PASS(USDKRW 2022-10 1440대/CLI 발표지연/외국인 대량매도 episode 실재). raw-v3/{collect,collect_dart,collect_regime,measure_conditional,measure_cross}.py 재실행 가능. |
| **C** | ★추적성 (hard-fail) | **PASS** | yaml 수치 → validation-conditional-v3 / validation-cross-v3 / validation-valuation-v3.json key 매핑. 화장품 per_z -0.258=subsector_sign_check.per_z.cosmetics / dollar β -1.19=cross.dollar / rev_1m KRW_weak -0.082=conditional_ic_surface. |
| **D** | ★PIT (hard-fail) | **PASS** | 가격 = forward shift(-h) PIT-safe. valuation = DART rcept_dt(공시일) 이후만(`avail = cf[rcept_dt<=dt]`) = lookahead/restatement 회피. regime = CLI_PUB_LAG=2(OECD vintage) + KRW/flow 일별 실시간. forward=shift(-h). |
| **E** | 다중검정 보정 | PASS | 단일 FDR family m=105 BY survivors=0. raw_p_min=0.0005(vol_60 y_60d Slowdown). ★정직 = BY 미생존 보고(battery 생존 대조). M_eff_signal 통합 supervisor 단계. |
| **F** | OOS / walk-forward | PASS | walk_forward_oos IS2019-22/OOS2023-26: rev_1m KRW_weak 부호유지(✓ IS-0.099→OOS-0.054) / mom_6 KRW_weak(✓) / cosmetics per_z 5d·20d 부호유지(✓) but 60d FLIP / 대부분 uncond FLIP = in-sample artifact 경계 정직 보고. |
| **G** | 자기상관·검정력 tier | PASS | Newey-West HAC(lag=horizon) + wild-cluster bootstrap(Rademacher B=2000) + block-boot CI + n_eff(autocorr). ★G-G v2 t_obs_eff = IC·√n_eff/σ ⋚ 2.802: well-powered cell **5개**(★audit 정정, "0" 오류) = vol_60 KRW_neutral(-3.46)/per_z Slowdown(+3.40)/vol_60 Recovery(-3.24)/rev_1m Slowdown(+2.89)/pbr_z flow_neutral(-2.89) 모두 wc_p<0.01 but 105 multiplicity 단일 BY 못넘음. = "전부 underpowered" 아니라 "multiplicity 보정 후 미생존". |
| **H** | 미해결 명시 | PASS | candidate-ledger 🔬 falsifier(화장품 small-n / rev_1m wc_p borderline / dollar contemporaneous) + collector_plan(주식수 PIT / 中소비 regime / size-orthogonal). research-log 미해결 5항. |
| **I** | ★생존편향 (hard-fail) | **PARTIAL** | universe=FDR 현재 스냅샷(생존종목). delisted/M&A 누락(소비재=상폐 적으나 잔존). 28종 中 일부 신규상장. PIT 멤버십=collector_plan high. ★hard-fail 회피 = over-claim 아닌 정직 격하(PARTIAL 라벨). |
| **J** | 측정 axis 일치 (spec↔code) + 경제성 | PASS | spec "저PER 화장품 cross-sectional → forward" = code `csz(per) → forward_returns`. forward predictive 동일. 부호 음(value) = 측정값 그대로(over-claim 0). net-cost: gross\|IC\| 화장품 0.258 vs KR STT sell 0.20% = small-n turnover caveat(통합 sqrt impact). |
| **K** | ★분석 unit ↔ portfolio label 분리 + A-4 | **PASS (★핵심)** | ★A-4 sub-sector 부호 cancel **검출+분리 트리거 발동**: 화장품(cyclical value 작동) vs 음식료(defensive 무신호) 부호 정반대 = sub-cluster eq-weight 시 factor β cancel. ★financial XLF cancel 교훈 실증 = K 위반 회피(분리 트리거 보고). z-score=peer-relative. portfolio 조립=supervisor(분담 준수). |
| **L** | 공통인자 1회 계상 | PASS | common_factor_exposure = β 보고만(dollar/credit/oil/rate/VIX). 산업이 cross 최종 박제 X. 통합 supervisor L축 1회 계상. |
| **M** | 코드 충실 (wire) | PASS | rank_ic / wild_cluster_p / n_eff = 자체 측정 함수(core 함수 미변경). opt-in 측정, production(INV_R15_WEIGHTS) 미접촉. |
| **N** | cross 관계 PSD | N/A | cross 조립(RegimeGlasso Σ_return / Σ_signal) = supervisor 단계. 산업=β 벡터 보고. directional_spillover=[](DY 통합단계, customer momentum=소비재 upstream 다양 skip). |
| **O** | leakage (PIT-safe) | PASS | forward=shift(-h) 미래 누설 0. reject≠missing: 상장 전 NaN=missing / regime cell 부재=관측. KRX flow=DATA-GATE(차단=관측불가 ≠ reject). |
| **P** | net-cost robustness | PASS | 화장품 per_z gross\|IC\|0.258 vs 월 cost ~16.5bps → gross 보존(small-n turnover caveat). KR STT 비대칭. sqrt impact=supervisor 캘리브레이션. |

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% (DART 707 + FRED/ECOS 실재) |
| C 추적성 | PASS | yaml↔raw json 매핑 (source_id) |
| D PIT | PASS | 가격 forward-shift + valuation rcept_dt + CLI_PUB_LAG |
| I 생존편향 | PARTIAL | 정직 격하(PARTIAL), over-claim 회피 = hard-fail 아님 |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하). N=N/A(supervisor 책임).

## verdict

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=N/A.
- **status = PARTIAL** — tradeable 후보:
  1. ★**화장품 per_z value premium** = TENTATIVE DIRECTIONAL (IC-0.258 wc_p0.047 t_obs-2.19, 5d/20d OOS 부호유지) but
     ★leave-episode 비유의(single-episode 의존) + n_codes=4 + within 음비율71% = **방향 약 prior, magnitude haircut**.
  2. ★**rev_1m × KRW_weak** = TENTATIVE conditional (IC-0.082 wc_p0.0625, family_2 t=-2.36 유의, OOS 부호유지). 원화약세 단기 reversal 증폭.
  3. **dollar β=-1.19(t=-2.57)** = risk-monitor (contemporaneous, alpha 아닌 de-risk 신호).
- ★**핵심 검증 가치 = A-4 sub-sector 부호 CANCEL 실증**: 화장품(中cyclical, value 작동) vs 음식료(defensive, 무신호)
  부호 정반대 = "같은 소비재 라벨이나 driver 이질" 데이터 입증 = **sub-sleeve 분리 트리거**(financial XLF cancel 교훈 동형).
  momentum 무신호 = asset_stable 정합(battery growth momentum 대조).
- **G-G v2 (tradeable 충분성)**: eligibility 후보 2(화장품 per_z / rev_1m KRW_weak, OOS 부호유지) but conviction 약
  (★well-powered 5개 존재하나 105 multiplicity 단일 BY 미생존 + 화장품 leave-episode 비유의) → **PASS-conditional**
  (conservative cap + monitor + 보강권고: 화장품 universe 확장). M_eff 통합단계서 multiplicity 재평가 시 5개 재검토 여지.
- archetype asset_stable 사후편향 검사: valid_from 2019 사전선언, transition 없음. ★단 화장품 cyclical secondary 발견 =
  asset_stable 단일 라벨의 sub-sector 이질 = secondary(cyclical) prob 상향 데이터(soft).

## ★G-C 독립 audit 으로 넘길 핵심 검증 포인트 (auditor 재계산 대상)

1. 화장품 per_z IC-0.258 = n_codes=4 small-n artifact 인가, genuine value premium 인가? (leave-episode 비유의 = single-episode 의존 정당성)
2. A-4 cancel 검출 = 분류노이즈(코웨이/큐렉소 오분류) 산물 아닌가? (화장품 4사 순수 = 영향 없음 검증)
3. FDR BY 생존 0 = "신호 약" 인가, 36셀 multiplicity artifact 인가? (G-G v2 t_obs<2.802 underpowered = MDE 해석)
4. rev_1m KRW_weak family_2 t=-2.36 = regime episode<3 overfit 인가? (OOS 부호유지로 방어 가능한가)
