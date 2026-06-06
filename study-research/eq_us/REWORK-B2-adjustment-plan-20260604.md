---
tags: [type/adjustment-plan, domain/equity-us, phase/rework-b2]
date: 2026-06-04
purpose: 미국 3 sleeve 재작업 — 현 measure.py 코드 → 대안 B″ 조정안(코드 레벨, 함수:라인 지목). 자문 3R(.consult-us-rework-3R-results.md) 확정 설계의 구현 매핑. ★실행순서 = ⑧즉시 → ④·②⑤·⑥게이트 → ⑦·⑨·①나중.
source: .consult-us-rework-3R-results.md (R1 발산→R2 수렴→R3 2게이트, 2채널 Gemini+Claude)
verify: subagent reflection-verify (조정안 ↔ 3R 자문 전수 매핑) — §검증 결과 참조
---

# 미국 3 sleeve 재작업 B″ 조정안 (현 코드 → 조정)

> ★자문 9수정 번호 = 3R 결과 R1 Claude 9점. 실행순서 = Claude R2 lock(⑧ 무비용→④·②⑤·⑥ lock-blocking 게이트→⑦·⑨·① breadth/codify).
> 각 항목 = **현 구현(함수:라인) → B″ 조정(구체) → 효과**. E95 5단 준수.

---

## STEP 0 — ⑧ mega_tech 재분류 (무비용 reframe, 즉시)

**Design intent**: mega_tech sleeve = compounder basket(N=11). cross-sectional factor ranking이 본질이 아니라 macro exposure/timing이 본질.
**현 구현**: `us_mega_tech/raw-v3/measure.py` — family_1(cross-sectional N=11 rank-IC, line 13: vol_60/mom/per_z/pbr_z/capex_z) + family_1b(basket exposure, line 14) + family_2b interaction(line 396) + spillover(line ~418). summary.yaml verdict=PARTIAL_CONFIRMED.
**B″ 조정**:
- (a) family_1 cross-sectional → **diagnostic only, verdict 생성 폐기**. 유효 cross-section n≈7 = factor 추정 통계적 void(강제 시 spurious factor 제조). vol_60 small-basket hedge 등은 "참고 지표"로만, PASS/FAIL 라벨 제거.
- (b) sleeve verdict 재구성 = **verdict 없는 exposure/timing overlay**: (1) factor exposure 한계기여(real_rate basket β−0.210 t−5.14 = duration EXPOSURE, alpha 아님) (2) concentration/crowding 지표 (3) regime-conditional beta 안정성(family_2b capex×VIX 유지하되 "timing overlay" 라벨).
- (c) F-score/net-issuance 강제 측정 **폐기**(F-score=high-BM 부실주 설계 mismatch / net-issuance=n=11 동질 buyback dispersion 고갈).
**코드 변경**: measure.py main() family_1 결과 dict에 `"role":"diagnostic_no_verdict"` 태그 + summary.yaml `verdict:` → `sleeve_type: exposure_timing_overlay` (PASS/FAIL 필드 제거). cross-sectional factor add 없음.
**효과**: PASS-search 압력 제거 → ③(mega_tech만 interaction 받아 capex×VIX t+2.34 상대 inflate) **자동 해소**. ROI 무한대(계산 아닌 scope 결정).

---

## STEP 1 — ④ payout duration-orthogonalize → credit (lock-blocking, defensive 최고 stakes)

**Design intent**: defensive payout이 regime-conditional alpha인지 검증. 단 real_rate gate가 이미 식별된 duration beta면 재포장(spurious).
**현 구현**: `us_defensive/raw-v3/measure.py:341` `regime_conditional(signals, fwd, macro, top_q=0.6)` = baa_aaa **quintile split**(상위 40% high-spread vs low). payout = line 481 `payout_z=cs_z(payout_yield)`, family_2 reg_signals(line 536)에 포함. → split만 → summary rejected_provisional. **interaction term·orthogonalize 없음** = frame line 323 위반.
**B″ 조정 (신규 `payout_interaction()` 함수)**:
1. **직교화 선결**: payout-premium return Rₚ를 duration/term-premium beta에 residualize. α_payout,t = R_payout,t − β_duration·ΔReal_rate_t (FWL). ★직교화 **order/basis 명시**(R3 runner-up): duration 먼저 → 잔차에 credit 적층.
2. **conditioning = 직교 real_rate 성분만**(split 아닌 continuous interaction): 잔차 α를 ΔReal_rate(직교분)에 interaction. mega_tech `regime_interaction()`(measure.py:396 IC_t~regime_chg_t HAC) 구조 이식하되 **regime_chg=ΔReal_rate continuous**(VIX quintile 아님).
3. **credit-spread regime 적층**: 직교 후 baa_aaa 조건 추가.
4. **λ = PIT expanding-window Ridge 동결**(⑥): 2022+ 포함 full-panel CV 금지. λ는 평가구간 진입 전 expanding-window로 확정. λ 점추정 금지 → λ-민감도 hedge 보고 — ★λ ∈ {0.1·λ*, λ*, 10·λ*} 3점 격자에서 잔차 α 부호·유의 안정성 hedge table 의무(검증 보완 2).
5. **effective-n = regime block 수**(한자릿수), NW-HAC lag=regime persistence(현 `nw_se` maxlags=3 → block persistence로 교체).
6. **verdict 어휘**: "조건부 PASS(잠정), OOS 게이트 미충족 시 자동 강등"(armed-pending, kill-switch trigger 명시). ⛔ confirmed/회생확실 금지.
**효과**: real_rate duration beta 재포장 차단 → payout-specific alpha만 인정. 검증 = 직교 후 잔차 α의 OOS(e-process) 통과 여부. 직교 전 유의 → 직교 후 소멸이면 duration-in-disguise 판정(spurious).

---

## STEP 2 — ②+⑤+⑦(per-test calibration) 추론 교정 (lock-blocking, 전 verdict 신뢰 근간)

**Design intent**: 모든 sleeve의 t-stat/IC 신뢰성 = per-test p-value validity + FDR family budget.
**현 구현**: `nw_se(ic, lags)`(각 measure.py ~205) + `benjamini_yekutieli`(~286, q=0.10, M_eff override). family_1/2/3 별 m. payout interaction = 신규라 family 미배정.
**B″ 조정**:
- **② 단일 FDR family**: payout main+interaction+add(idio-vol/residual-mom)를 **하나의 alpha budget** 공유(별개 family 금지=garden-of-forking-paths). interaction은 payout-family 안 alpha-spending. e-process/LORD++ ledger 권장.
- **⑤ effective-n NW-HAC**: regime small-n 검정 t = 명목 obs(185) 아닌 block 수 기준. autocorr-deflated effective-n 명시 — ★산식 `n_eff = n / (1 + 2·Σ_k ρ_k)`(Newey-West variance inflation factor 기반), `nw_se` 모듈에 `n_eff` 반환 추가(검증 보완 1).
- **⑦(R3 Claude) per-test null calibration**: ★effective-n=block 한자릿수 + NW-HAC = **size-invalid**(Kiefer-Vogelsang fixed-b). in-sample per-test calibration을 **fixed-b critical value OR wild-cluster bootstrap**(또는 OOS와 통일=e-value)로 사전등록. `nw_se` asymptotic t → small-block regime 검정엔 fixed-b CV 적용. frame contract (3)/(4)에 "per-test null calibration basis" 명시.
**효과**: per-test p miscalibrated 차단 → FDR alpha-budget이 유효 단위로 denominate → defensive "조건부 PASS"·cyclical TENTATIVE 게이트가 무효 단위 붕괴 방지(거버넌스 키스톤).

---

## STEP 3 — ⑥ Ridge λ PIT 동결 (lock-blocking, OOS 게이트 유효성 선결)

**Design intent**: defensive verdict이 "OOS-gated"인데 λ가 full-sample tuning이면 OOS가 진짜 OOS 아님.
**현 구현**: 현 코드 Ridge 미사용(payout interaction 신규). 
**B″ 조정**: STEP 1-4와 동일 = payout_interaction()의 Ridge λ를 expanding-window PIT로 동결. normalization 창·regime threshold·factor lag도 동일 OOS 전 동결.
**효과**: OOS 게이트가 의미를 가짐(저비용·고stakes). λ 사후조정=모든 in-sample verdict 재계산 강제.

---

## STEP 4 — ⑦ cyclical factor breadth (나중, 게이트 통과 후)

**Design intent**: cyclical = peak-EPS trap. value(PBR/EV-EBITDA) confirmed 위 price-based 보강.
**현 구현**: `us_cyclical/raw-v3/measure.py` — pbr/ev_ebitda CONFIRMED, per_z TENTATIVE(peak flag), family_2 `regime_conditional`(line 350) **계산하나 summary 사장**. residual-mom 없음. regime_interaction 없음.
**B″ 조정**:
- (a) 첫 add = **residual-mom(12-1, sector·beta orthogonalized)** — price-based, PIT-free, "가격 먼저" 원칙 정합. ⛔ SUE 첫-add 아님(peak EPS→high SUE→직후 mean-revert=peak 오염 뒷문). 신규 `residual_momentum()`: 12-1 month return을 sector + market beta에 회귀 → 잔차.
- (b) **PER 재계산**: normalized EPS(full-cycle 또는 trailing 7yr 평균 EPS, 정규화 창 PIT ex-ante 동결)일 때만 composite 진입. 동결 못하면 normalization=researcher-DoF → TENTATIVE 유지·composite 제외(폐기 아님).
- (c) **SUE = 동일 FDR family 별도 candidate**(우선순위 아님): EDGAR 분기 EPS SRW(seasonal random walk, Foster-Olsen-Shevlin 1984 본류, IBES 아님). ★event anchor = **8-K Item 2.02 furnish date**(10-Q filing date 아님). peak-cycle interaction control 부착. cyclical은 시장이 계절 swing 선반영→false surprise→efficacy 하향 hedge.
- (d) **family_2 surface**: regime_conditional 결과를 summary에 표출 + mega_tech `regime_interaction()` 이식(부호 갈리는 family_1 신호에).
**효과**: 오염 추론(게이트 미통과) 위에 factor 쌓기 방지 위해 STEP 1~3 후 진입. residual-mom = incremental(PBR/EV-EBITDA workhorse).

---

## STEP 5 — ⑨ cross 축 (나중)

**Design intent**: sleeve = cross 선행신호 후보 측정+보고. supervisor = cross-sleeve matrix 배분.
**현 구현**: cyclical/defensive directional_spillover=빈 [](frame line 85 위반). mega_tech `supply_chain_lead_lag`(measure.py:418) = hyperscaler→semi corr+0.69 **contemporaneous**.
**B″ 조정**:
- (a) 모든 sleeve null = **null + achieved power/MDE 동반**(n=11~12 null=power 실패일 수, "우리 power로 |corr|>X만 검출 가능"). power<th = underpowered 라벨(=measured-null로 cross 의무 충족, 단 evidence-of-absence 오인 차단).
- (b) mega_tech spillover **재측정**: ★보고된 +0.69 contemporaneous=같은 risk cluster=오용(Cohen-Frazzini=고객 return_t→공급사 return_t+1 lagged firm-pair). → **lagged firm-pair**(10-K segment 매출집중도 EDGAR 추출, SFAS 131 주요고객) + MDE 동반. NVDA/AVGO→MSFT/GOOGL/AMZN/META capex 체인=생존 pocket 후보(post-pub decay 감안).
- (c) cyclical/defensive null = 정상(customer-supplier는 테크/반도체만 강) — measured-null+MDE로 명문화. ★cross 측정은 **semi↔hyperscaler 체인 한정**, 그 외 sleeve는 구조적 measured-null(테크/반도체 외 customer-supplier 약함)으로 cross 의무 충족 경계 명문화(검증 보완 3).
**효과**: absence-of-evidence를 evidence-of-absence로 오인 방지. CF frame error 교정.

---

## STEP 6 — ① frame contract 코드화 (나중, 재발방지 산출물)

**Design intent**: supervisor가 정의 대조 없이 verdict 승인한 근본 원인 = frame-contract 부재(명세실패). 선언적 contract를 sleeve별 동일 인스턴스화 + conformance check.
**현 구현**: `study-research/_dispatch-gates.md` G-A~G-E + A-3/A-5/A-6 추가됨(부분). frame contract 7항 미코드화.
**B″ 조정 — frame contract 7항(측정 前 선언 의무, sleeve 공통)**:
1. **regime 선언규칙**: regime 변수·개수·effective-n(obs 아닌 block 수)·HAC lag=persistence 사전 기재. 미기재=regime 검정 실행 불가.
2. **interaction/split 사전확약 + 직교화**: conditioning=interaction(pooled, power↑) vs split(clean, n-costly) 결과 보기 전 동결, 사후 전환 금지. interaction은 main effect 기지 beta에 직교화. ★직교화 **order/basis 명시**(R3 runner-up).
3. **단일 FDR family**: sleeve별 family 정의, main+interaction+add가 하나의 alpha budget(e-process ledger). "공짜" interaction 검정 없음.
4. **null + MDE/power 사전등록**: 모든 주장에 null·effective-n에서 MDE·power 명시. power<th=underpowered=PASS 아님.
5. **PIT 동결 + 비대칭 search 금지**: λ·normalization창·regime threshold·factor lag OOS 전 expanding-window 동결. 가설 방향 사전선언.
6. ★**Turnover/T-cost 제약**(R3 Gemini): Max Turnover 상한 또는 Net-Alpha 기반 MDE — residual-mom+regime 동적가중+직교화=고회전 → Gross→Net alpha 침식(Spurious Strategy) 차단. (현 `long_only_net` cost=(0.0005+0.0003)*2 존재 → frame contract로 승격·명문화.)
7. ★**per-test null calibration basis**(R3 Claude): fixed-b CV / wild-cluster bootstrap / e-value 통일 사전등록 — in-sample HAC small-block size validity.
**B″ 조정 코드**: `_dispatch-gates.md`에 G-F(frame contract 7항) 추가 + 각 sleeve measure.py 헤더에 contract 선언 블록.
**효과**: rubber-stamping 증상의 본질 fix(명세 강제). conformance check로 sleeve 이질 방법론 방지.

---

## STEP 7 — ★factor×factor interaction (사용자 발견, 원 3R 누락 차원, 2026-06-04)

**Design intent**: 단일 factor(capex/asset_growth 단독)는 경제적으로 불완전. 진짜 신호는 **지표간 조건부**(q-factor investment×profitability, investment×value, value×quality).
**현 구현**: B″는 단일 factor + factor×**macro regime**(capex×VIX 등, 다 fixed-b 사망) + 직교화만. ★factor×factor(지표 pair) interaction **누락**.
**B″ 조정 (pre-specified 경제 pair만 = forking-paths 방지)**:
- **cyclical**: ① asset_growth × valuation(investment×value, empire building) ② asset_growth × profitability(★q-factor Hou-Xue-Zhang 핵심, 고투자+저수익=최악) ③ valuation × profitability(value×quality, value trap 회피) ④ per × asset_growth. ★특히 asset_growth(직전 REJECTED)가 profitability 조건부 회생하는지.
- **defensive**: ① net_issuance × valuation(buyback-aversion이 비쌀 때 강한가=net_issuance PARTIAL 메커니즘 검증) ② ep_yield × quality(anti-value가 저품질서 심한가=value trap).
- **mega_tech**: ❌ 불가(n≈8~11 cross-sectional interaction = 단일보다 더 void).
- **방법**: 각 factor 독립 z-score 후 곱(다중공선성), continuous, ★단일 FDR family 추가(M_eff 재계산), fixed-b CV + wild-cluster size-valid 필수, small-n hedge(sub-sector 12 = interaction 자유도 더 부족). pre-specified만, 사후 추가 ⛔.
**효과**: "capex 단독 무의미" 해소. 조건부 신호 발굴(예: 고투자가 저수익서만 penalty). 단 small-n + interaction = size-validity 더 엄격(payout/capex 교훈 = 대부분 fixed-b 사망 가능, 정직 박제).

## 실행 순서 요약 (의존성)

| 순서 | STEP | 자문수정 | 성격 | 의존 |
|---|---|---|---|---|
| 0 | STEP 0 | ⑧ | 무비용 reframe | 없음(즉시) |
| 1 | STEP 1 | ④ | lock-blocking 게이트 | STEP 3(λ) 동반 |
| 2 | STEP 2 | ②⑤⑦(calib) | lock-blocking 게이트 | 전 sleeve 적용 |
| 3 | STEP 3 | ⑥ | lock-blocking 게이트 | STEP 1 내장 |
| 4 | STEP 4 | ⑦(breadth) | breadth(나중) | STEP 1~3 통과 후 |
| 5 | STEP 5 | ⑨ | cross(나중) | 독립 |
| 6 | STEP 6 | ① | 재발방지 산출 | 전체 흡수 |

★게이트(1~3) 통과 전 breadth(4) 진입 금지 = 오염 추론 위 factor 적층 ROI 음수.

## 재작업 후 G-C 재audit
- cyclical/defensive measure.py 조정 후 → G-C 독립 audit 재스폰(author≠auditor). mega_tech = STEP 0 reframe 후 G-C audit(미스폰분 포함).
- verdict 변동 예상: defensive payout Rejected→조건부 PASS(잠정 OOS-gated) / cyclical family_2 surface+PER normalized / mega_tech verdict 없는 exposure overlay.

## §검증 결과 (subagent reflection-verify, 2026-06-04)
- **자문 항목 32개 → 조정안 매핑 32개 (반영 R=29 / 부분 P=3 / 누락 K=0 / skip S=0). 불일치 0건.**
- **역방향 기각 5종 전부 차단 PASS**: (a) SUE 첫-add 아님(residual-mom 첫-add, SUE=FDR family 별도 candidate) (b) mega_tech cross-sectional factor 강제 폐기(exposure overlay only) (c) F-score/net-issuance 강제 측정 폐기 (d) payout "회생확실/confirmed" 어휘 차단(조건부 PASS 잠정) (e) regime split만 처리 교정(interaction term+orthogonalize).
- **정량 anchor 6종 1:1 일치**: 8-K Item 2.02 furnish date / CF lagged firm-pair(+0.69 contemporaneous 오용) / effective-n=block수 / λ=expanding-window PIT / per-test calibration=fixed-b·wild-cluster·e-value / real_rate β−0.210 t−5.14·capex×VIX t+2.34.
- **실행순서 일치**: ⑧즉시→④·②⑤⑦·⑥ lock-blocking 게이트→⑦·⑨·① 나중 = R2 Claude lock spec 정합("게이트 전 breadth=ROI 음수" 명문화).
- **부분반영 3건 보완 완료**(verdict 불변, 산식·양식 디테일): (1) effective-n 산식 `n_eff=n/(1+2Σρ_k)` 명시 → STEP 2 (2) λ 3점 격자 hedge table → STEP 1-4 (3) cross semi↔hyperscaler 한정 명문화 → STEP 5(c). 모두 박제 반영.
- 결론: 조정안 = 3R 자문 raw와 전수 정합, lock 가능.
