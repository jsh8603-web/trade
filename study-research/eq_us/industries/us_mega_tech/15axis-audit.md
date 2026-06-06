<!-- author: us_mega_tech rework teammate (Opus 1m, §2 자가 audit 초안, 2026-06-03) -->
<!-- ★G-C 독립 audit (별도 세션, author != auditor) = 하단 비워둠 (supervisor 가 독립 teammate dispatch) -->

# 15axis-audit.md — us_mega_tech sleeve §M v3 (★재작업, A~P 15축 3컬럼)

> ★재작업 audit: yaml↔raw 재현·hard-fail 0 자가 점검. raw 재현 = `raw-v3/{collect,measure}.py` + validation-metrics-v3.json.
> Hard-fail 코어: **B(실데이터)·C(추적성)·D(PIT)·I(생존편향)** + 조건부 J/K/L/M/N/O. ★§M.12 + 자문 R2 수정4(basket화) 반영.
> ★G-A 3컬럼 = ① 적용했나 ② 어떻게 측정(코드·수치 경로) ③ 결과·판정. ★G-A.5 = sector-neutral 비적용 사유 명시.

## G-A. 축별 3컬럼 (15축 A~P)

| 축 | ① 적용 | ② 측정 방법 (코드·수치 경로) | ③ 결과·판정 |
|---|---|---|---|
| **A** 이론 실재 | ✅ | theory-notes.md S1: Gormsen-Lazarus(2023) JF 78(3) duration / BAB Frazzini-Pedersen(2014) / Cooper-Gulen-Schill(2008) / Daniel-Moskowitz(2016). archetype valid_from 2015 사전선언. | PASS — basket-level real_rate(duration) 학술 ground 강. citation 환각검증 통과. |
| **B★** 실데이터 | ✅ | 합성 0%. yfinance 11종(2867일) + EDGAR XBRL 6630 rows(filed PIT) + FRED CSV(DFII10/VIXCLS/DTWEXBGS/DGS10, us_defensive 재사용). `measure.py` 재현. | **PASS** — 합성 0%, 실 데이터. np.random=block-boot seed 42만. |
| **C★** 추적성 | ✅ | yaml 수치 → validation-metrics-v3.json key 매핑(source_id). real_rate β −0.2096=family_1b._multivariate.real_rate / vol_60 +0.241=family_1_cross_sectional.vol_60__12M / per_z ≈0 / capex post-AI −0.404. | **PASS** — 1:1 매핑. M_eff=19.0 raw 일치. |
| **D★** PIT-safe | ✅ | 가격=forward shift(-h). valuation=EDGAR filed date 이후만(lookahead 회피). real_rate Δ=동시 β(미래 누설 X). 거시=FRED. block-boot block=horizon. | **PASS** — filed PIT + forward shift + 동시 β. |
| **E** 자문 환각 | ✅ | S1 citation 환각검증(Gormsen-Lazarus vol/page/year 일치, Daniel-Moskowitz 122/221-247 일치, Cooper-Gulen-Schill 일치). 자문 R2 수정4 = basket화 코드 반영(복붙 아님). | PASS — citation cross-verify 통과. |
| **F** 반증+기각 | ✅ | falsifier: real_rate β 부호반전(reject) / per_z 무신호=expected null(기각 아닌 확인) / capex 양방향(post-AI 음). ★G-A.5 capex IC~VIX interaction = ★B″ STEP 2 fixed-b 재검정: 전체 n=125 SURVIVE(t 2.43>CV 2.19, p_wild 0.044) but ★post-AI n=29(신호 구간) ★DIE(t 1.94<CV 2.86, p_wild 0.234 = payout 동일 size-invalid artifact) → timing 신호 자격 미달(diagnostic 정정). | PASS — falsifier + ★fixed-b size-valid 재검정(capex regime interaction post-AI 사망 정직 정정). |
| **G** 검정력·tier | ✅ | ★eff_N 이중보정: ρ̄=0.429 → cross_eff_n 11→2.08(급감) + ts_eff_n=T/h. tier=Validated(real_rate n=136) / cs_lowvol Validated(cross_eff_n 2.08 small-basket). | PASS — eff_N 이중보정 + tier 라벨. |
| **H** 미해결 명시 | ✅ | collector_plan(fwd EPS/ERB high=IBES 유료 gap / gross_prof medium / FF5+QMJ+BAB medium) + research-log 미해결 5 + candidate-ledger 이연. | PASS — gap 명시(compounder primary fwd EPS 미측정 박제). |
| **I★** 생존편향 | ✅ | basket=현 Mag7 스냅샷. mega-tech 생존편향 약(상폐 거의 없음) but PIT 멤버십(NVDA pre/post-AI, TSLA 2020 편입)=look-back. | **PARTIAL** — 정직 격하(hard-fail 회피). collector_plan medium. |
| **J** 측정 axis 일치 | ✅ | spec↔code: "basket real_rate Δ β"=`basket_factor_beta` HAC / "cross-sec 저변동→12M forward"=`cs_z(vol_60)→fwd12`. ★real_rate level vs Δ 명시(Δ가 신호). | PASS — spec/code 1:1. level-vs-Δ 구분 명시. |
| **K** 분석 unit↔portfolio | ✅ | 분석 unit=basket-level(real_rate/vix β) + cross-sec(11종 factor loading). portfolio label=mega_tech sleeve. sub-basket(mag7/ai_semi) real_rate β 둘 다 음(부호 일관, cancel 없음). | PASS — unit 분리 + sub-basket 부호 일관. |
| **L** 공통인자 1회 계상 | ✅ | common_factor_exposure = real_rate/vix/rate/dollar β 보고만. ★VIX β = risk overlay·L축(supervisor 1회 계상). reflexivity=DY 채널(L축 아님). | PASS — β 보고만, supervisor L축. |
| **M★** wire 충실 | ✅ | measure.py = 독립 측정 스크립트(production 미변경). opt-in. core/assume 직접 호출 없음(이전 rank_ic import 제거 = basket-level 자체 구현). | PASS — production 미변경, opt-in 측정. |
| **N★** cross PSD | ✅(후보 보고) | ★G-A.3 + ★B″ STEP 5(⑨): directional_spillover = ★Cohen-Frazzini lagged firm-pair 재측정(기존 k=0 +0.69=오용 동조). CF 정합(고객 hyper_t→공급사 semi_{t+1}) lead 1-3m 비유의(−0.07~−0.09) + ★achieved power/MDE 동반(power 0.13, MDE\|ρ\|=0.238=underpowered). 조립/PSD=supervisor. | PASS(후보 보고) — CF lagged null+MDE(증거부재≠부재증거). semi↔hyperscaler 한정. |
| **O★** leakage | ✅ | forward return=shift(-h). real_rate Δ=동시(미래 누설 X). reflexivity 60d rolling=과거 window. reject≠missing(panel NaN tri-state). | PASS — forward shift + 동시 β + 과거 window. |
| **P** net-cost | ✅ | US mega-cap 최저(STT 없음, 왕복 14bps). basket-level timing=turnover 낮음. cs_lowvol \|IC\| 0.241 >> 7bps/월. | PASS — net-cost robust. |

### ★G-A.4 sub-sector 부호 일관성 (★basket 단일 archetype = N/A, 사유 명시)
- ★us_mega_tech = 단일 archetype(compounder) basket = sub-sector 부호 점검 **N/A**(us_cyclical 5 sector 부호 cancel 점검과 다름).
- ★단 sub-basket(mag7 vs ai_semi) real_rate β = 둘 다 음(mag7 −0.148 / ai_semi −0.175) = ★부호 일관(cancel 없음). cs_lowvol 도 양 일관.
- = K축 위반 없음(부호 반대 sub-sleeve eq-weight cancel 없음).

### ★G-A.5 sector-neutral z 비적용 사유 (★dispatch 명시 의무)
- ★us_mega_tech ⛔ sector-neutral z 비적용 = **단일 archetype(compounder) basket**, 11종 모두 mega-tech 그룹 = sub-sector demean 할 **peer 구조 없음**.
- ★us_cyclical = multi-sector(SOXX/XLB/XLI/XLE/XLF 5 sector) → sector-neutral z 로 sector-level value trap 제거 = BY 0→8 회복 필수였음.
- ★us_mega_tech = universe-demean = sector-neutral **동치**(별 sector factor 없음 = demean 모집단이 곧 전체 basket). `measure.py` cs_z = universe-demean 유지.
- = us_cyclical pilot 의 sector-neutral 발견은 mega_tech 에 **비적용**(이론적으로 무의미), 대신 자문 R2 수정4 basket화로 대응.

### ★G-A.6 basket-level 측정 명시 (★자문 R2 수정4 = N=11 small-basket)
- ★측정 단위 = **basket-level time-series factor exposure** (family_1b) **우선** + cross-sectional (family_1) small-basket hedge. 근거 = Grinold IR=IC√breadth → N=11 cross-sec breadth 협소(ρ̄=0.429 보정 cross_eff_n=2.08) = 통계력 약.
- **basket-level (family_1b)**: `basket_factor_beta`(basket EW 월수익 ~ real_rate/vix/dollar/rate Δ, HAC multivariate+단독) + `basket_factor_timing`(factor→forward 시계열 IC) + `basket_beta_robustness`(sub-basket/leave-year/level-vs-Δ). → real_rate 노출 −0.21 t−5.14.
- **cross-sectional (family_1)**: `cs_z`(universe-demean) → `cs_ic` rank-IC + ★small-basket hedge(`eff_n_double` ρ̄ 보정 + `breadth_ir` cross_eff_n 사용 = 과대 방지 + magnitude 50~70% haircut). 단독 verdict 금지.
- ★**노출 ≠ alpha 구분**(team-lead 가이드1): contemporaneous β(노출 강) vs forward timing(예측 약 ts_IC −0.191). duration timing = supervisor macro overlay 몫.
- = G-A.6 = basket-level 측정이 실제 코드(measure.py family_1b)로 이행됨 입증(인지≠이행 게이트 충족).

## G-A. 6단계 (S1~S6) 산출물 경로 + 결과

- **S1** 학술 ground: theory-notes.md + candidate-ledger.md (WebSearch 7주제, Gemini 429 폴백, citation 환각검증). → real_rate(duration) primary 발굴.
- **S2** 실측 4게이트: G1 ex-ante(NDX/VIX regime) / G2 BY-FDR+M_eff(19.0, survivors nondegenerate=[]) / G3 CPCV(vol_60 OOS 1.00) / G4 NW-HAC(real_rate t−5.14). `measure.py` → validation-metrics-v3.json.
- **S3** 외부검토: round-N.md (S3 자문 skip 사유 박제 = §M.12 사전준수 + compounder 특이점). ★재작업도 G-B 미발동(real_rate 강).
- **S4** 재검증: real_rate robustness(sub-basket/leave-year/level-vs-Δ) + capex AI-regime split + cs_lowvol leave-episode.
- **S5** 역공격: ★real_rate 기존 −0.030 비유의 반증 → multivariate −0.210 회복(측정 부족 입증). cs_lowvol BY 미생존 정직 격하(over-claim 회피).
- **S6** ★15축 독립 audit (별도 세션 = G-C 하단, supervisor dispatch).

## G-A. cross 3종 (★G-A.3 = sleeve 후보 보고 의무, [] 금지)

- **동시** RegimeGlasso → Σ_return = supervisor (sleeve=공통인자 β 보고: real_rate −0.21/vix −0.0073/rate +0.11/dollar 비유의).
- **방향성** Diebold-Yilmaz = ★sleeve **선행신호 후보 보고**(G-A.3): hyperscaler(MSFT/AMZN/GOOGL/META)→semi(NVDA/AVGO/AMD/ASML) lead-lag corr_0m +0.69 동시 강 / lead 1-3m 비유의 = ★동시 동조만 선행 없음. DY 후보 박제(directional_spillover). 조립=supervisor.
- **구조** supply-chain = ★AI capex→Mag7(mega_tech 핵심 영역, skip 아님): capex post-AI IC −0.404 over-investment + ★capex IC~VIX interaction β +0.0083 t+2.34(family_2b G-A.5). structural_linkage 박제.

## Hard-fail 코어 종합

| hard-fail 축 | 판정 | 비고 |
|---|---|---|
| B 실데이터 | PASS | 합성 0% + EDGAR 6630 + FRED 실데이터 |
| C 추적성 | PASS | yaml↔raw 매핑(real_rate −0.2096 / vol_60 +0.241 / per_z ≈0 / capex −0.404) |
| D PIT | PASS | EDGAR filed + forward shift + 동시 β + block=horizon |
| I 생존편향 | PARTIAL | 정직 격하(mega-tech 생존편향 약, PIT 멤버십 명시) |

★**hard-fail 0** (B/C/D PASS, I PARTIAL = 정직 격하).

## verdict (자가 audit 초안)

- 코어 4축 위반 0. 조건부 J/K/L/M/O/P PASS, N=PASS(후보 보고).
- **★B″ 3R STEP 0(⑧) 재분류: sleeve_type = exposure_timing_overlay (★verdict 생성 폐기)** — us_mega_tech = cross-sectional factor ranking sleeve 아님 = ★verdict 없는 macro exposure/timing overlay. 유효 cross-section n≈8 = factor 추정 통계적 void(강제 시 spurious factor) → cross-sectional family_1(vol_60/per/capex) = ★DIAGNOSTIC ONLY(참고 지표, PASS/FAIL/verdict 없음).
- ★보고 3종(verdict 아님): (1) factor exposure 한계기여 = basket-level real_rate β −0.21 t−5.14(duration EXPOSURE, ★노출≠alpha = supervisor macro overlay 입력) + VIX β 고베타 risk-on (2) concentration/crowding = reflexivity(현 정점 아님) (3) regime-conditional beta 안정성 = capex×VIX interaction = ★B″ fixed-b 재검정 결과 ★MIXED(전체 n=125 SURVIVE but post-AI n=29 신호 구간 ★DIE = size-valid 미입증 → diagnostic, timing 신호 자격 미달).
- ★핵심 = (1) ★STEP 0 재분류(cross-sectional verdict 폐기 = ③ PASS-search 압력 제거) (2) ★STEP 5 spillover CF lagged 재측정(기존 +0.69 동조 오용 → CF 정합 lead 1-3m underpowered null + MDE) (3) F-score/net-issuance 측정 폐기(설계 mismatch).
- ★sector-neutral 비적용(G-A.5) + basket-level 측정(G-A.6) + reflexivity risk overlay(G-A.4 sub-basket 부호 일관) 명시.
- ★G-B 미발동(real_rate 노출 강 유의). ★sleeve 본질 = exposure overlay(supervisor RegimeGlasso/macro 입력) = cross-sectional alpha sleeve 아님.

---

## ★G-C 독립 audit (별도 세션, author ≠ auditor) — 비워둠

> ★dispatch §3 G-C = 만든 사람 ≠ 감사자. supervisor 가 독립 teammate dispatch 하여 본 섹션 작성.
> 검증 대상(★B″ STEP 0/5 반영): (1) ★sleeve_type=exposure_timing_overlay 재분류 타당성(cross-sectional family_1 diagnostic-only = 유효 n≈8 void 정합) (2) basket-level real_rate robustness 재현(노출≠alpha) (3) ★spillover CF lagged 재측정 정합(기존 +0.69 동조 오용→lead underpowered null+MDE) (4) M_eff/eff_N raw 대조 (5) hard-fail B/C/D/I 독립 재독 (6) sector-neutral 비적용 사유 + F-score/net-issuance 측정 폐기 타당성.

(독립 audit 세션이 여기 작성)
