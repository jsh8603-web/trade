---
tags: [type/progress, domain/inv, phase/II, track/T2, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-button
task: ./TASK-T2-assumption-research-20260529.md
research: ./RESEARCH-T2-assumption-stats-20260529.md
design: ./DESIGN-T2-assumption-stats.md
owner: button (T2) — 검증통계·regime / T3(btn-Codlearn) — orchestration·안전
---

# progress-T2 — 가정 라이프사이클 검증·변경 통계 (구현 계획)

> 3 산출물: [RESEARCH](./RESEARCH-T2-assumption-stats-20260529.md) + [DESIGN](./DESIGN-T2-assumption-stats.md) + 본 구현계획.
> ⚠️ 사용자 불만 회피: 스텁 X — prior art 실조사 + 설계 + **동작·테스트 완료 통계엔진**.

## A. 완료 (T2 검증통계 엔진 — 25/25 PASS)
- [x] **A1 공유 detectors** `core/structure/detectors.py`: CUSUM·SPRT·BOCPD(run-length 붕괴)·prequential + rule_observer PSI/PageHinkley re-export(중복제거). self-test PASS.
- [x] **A2 online FDR** `core/structure/online_fdr.py`: LORD++ (FDR 제어) + AlphaInvesting (부활 남용 wealth 차단). self-test: null 500→0, 강신호 20→20, 부활 50→0.
- [x] **A3 검증통계 엔진** `core/structure/assumption_stats.py`: kind dispatch(parametric/structural) + **regime-conditional ValidationReport**(pooled 금지) + **hysteresis AND-gate**(5조건, base-layer 차단) + 신뢰도→band→사이징.
- [x] **A4 테스트** `tests/structure/test_assumption_stats.py` 12 + 기존 13 = **25/25 PASS**.
- [x] **A5 리서치·설계 문서** 2건.

## B. 잔여 — T2 (검증통계·regime 도메인)
- [ ] **B1 commodity archetype 신규** `core/structure/archetype.py`: `commodity_carry`(롤수익률·캐리 spread_driven) + `seasonal`(난방유·곡물) discriminated union 추가 + config yaml. parametric 가정(캐리 정상범위)·structural 가정(계절 패턴 작동) 검증 경로. `model: opus` (설계판단).
- [ ] **B2 cheapness_z band 상속**: `structure_model` 의 σ_resid·regime σ → `confidence_to_band` 로 band 전파하는 어댑터 함수(`structure_model.cheapness_band(firm,sector,date,as_of) -> (z, lo, hi)`). `model: sonnet`.
- [ ] **B3 falsifiability 검증 헬퍼**: AssumptionCard.falsification_metric 을 detector 로 컴파일(예: "Inv-to-Ship 3분기 밴드 이탈" → Cusum/prequential 파라미터). `model: sonnet`.
- [ ] **B4 ★ T2-7 실데이터 재검증 연계**: T1 반도체 패널 도착 시 (a) `validate_semiconductor.run_validation(panel=실패널)` STOP gate 재확정 + (b) 같은 패널로 가정 검증(structure_model 잔차 = 구조가정 예측, regime-conditional). 두 게이트 동일 패널 공유. `model: opus`.

## C. 잔여 — T3 (btn-Codlearn, orchestration·안전) — 계약만 T2 제공
- [ ] C1 AssumptionCard/Registry/Validator: `card.kind` → T2 `validate_*` dispatch.
- [ ] C2 UpdateController: 가정별 `LordPlusPlus` 스트림 → `hysteresis_and_gate(fdr_significant=...)`. consensus.py 객체타입 파라미터화(fork 금지, caps 빡세게).
- [ ] C3 ★ orphaned position 안전: AssumptionInvalidated → depends_on 역추적 → review/managed-exit + emergency_stop. (실거래 안전 공백, claude TOP-2)
- [ ] C4 DAG 무효화 전파(ATMS): epoch topological single-pass + nogood + graph rate-limit→사람.
- [ ] C5 derivation seam: DerivedParameterSet band 전파 + data contract(GE/Soda) validator 앞단.
- [ ] C6 base-layer regime 가정 등록: regime_model 을 `is_base_layer=True` Card 로 + regime_model_version 변경 시 의존 전체 재검증 epoch.

## D. 진입 순서 (의존)
1. T2 B1(commodity) + B2(band) — 독립, 병렬 가능.
2. T3 C1·C2 wire (T2 A3 엔진 호출) — A 완료라 즉시 가능.
3. T3 C3(orphaned) — 실거래 안전, C2 후.
4. B4(실데이터 재검증) — **T1 패널 도착 의존** (현 합성 fixture 로 회로 검증 완료, 실확정 대기).

## E. T2-7 STOP gate 연계 (명시)
- 현 상태: 합성 fixture GO(잔차 PR-AUC 0.854 vs raw 0.513). 가정 레이어의 "구조가정 검증"은 이 잔차 예측력을 prequential 로 재채점 = 같은 전제 공유.
- T1 실패널 도착 = **단일 트리거**로 (a) cheapness_z STOP gate 재확정 (b) 구조가정 regime-conditional 검증 동시 수행. 안 갈리면 T3 전제 + 가정 레이어 동반 재검토 → btn-Codlearn 즉시 통지.

## v2 BB 빌드 (자문 5R saturation 후 — 2026-05-29)
> SSOT 설계 = `DESIGN-button-v2.md` §10.1~10.7. 자문 raw = `.consult-button-R{1..5}.txt`. R5 권고 = Walking Skeleton 먼저(인프라 배선 증명 → 통계 플러그인). 각 step self-test 필수(스텁 금지).

- [x] **V0 Walking Skeleton** `core/assume/card_contract.py` — AssumptionCardLike protocol + BaseAssumptionFields(frozen)+assert_falsifiable. ledger 본체 persistence=btn-Inv(IA-1), 여기선 계약. self-test PASS.
- [x] **V1 BB-1** `core/brain/macro_assumption_card.py` — 6+1 AnomalyCase → 버전드 MacroAssumptionCard + anomaly↔card 어댑터 + add_candidate_card. self-test PASS.
- [x] **V2 BB-2** `core/brain/correction_loop.py` — JM divergence harvest → ingest_correction(live) + recall PIT mask + attach_to_classifier. self-test PASS.
- [x] **V3 BB-4** `core/structure/assumption_validation_engine.py` — card.kind dispatch → holds_now + 가정별 LORD++ FDR(자산클래스 격리) + falsification compile + 부활차단. self-test PASS.
- [x] **V4 BB-3** `core/regime/regime_discovery.py` — BOCPD timing + Hotelling/χ² novelty + online-FDR wrap + HumanApprovalGate(승격=사람) + bnpy seam. self-test PASS.
- [x] **V5 BB-5** `core/structure/archetype.py` 확장(commodity 3+crypto 3, ARCHETYPE_NAMES 11종+DEFAULT_SECTOR_ARCHETYPE) + `config/archetypes/*.yaml` 6종 + `core/structure/commodity_assumptions.py`(carry slope/flip·seasonal F·variance-ratio·threshold·oversupply·MVRV·netflow stub + 카드발행). self-test PASS.
- [x] **V7 BB-3/BB-4 보강** (btn-Codlearn 전체구조 3R 확정) `core/structure/hierarchical_fdr.py` 신규 + 엔진/discovery 배선 — ①cascade(BB 독립substrate+de-risking bypass) ②e-process anytime-valid(FDR∧) ③falsification POWER 게이트 ④per-domain 추정 다형성(DOMAIN_ESTIMATION_POLICY) ⑤sequestered stream+정지 합성 FP rate. self-test PASS.
- [x] **V6 통합 검증** 전 11 모듈 self-test PASS + 기존 25 structure regression PASS(`tests/structure/`) + DESIGN/progress 최종화 + btn-Codlearn 보고.

### 계약/조율 (btn-Codlearn·btn-Inv 보고)
- ledger(R3~R5 #1 레버리지) = btn-Inv IA-1 도메인. BB-4 는 read-only 소비. 계약 = event schema 11종 + (assumption_id,version) join + FDR decision_time 불변.
- cross-asset cascade(R5 맹점1) + revision-drift(R5 맹점2) = T3 ATMS/거시 base-layer 조율 항목.

## Working Notes
> [ckpt-202605291453:btn-button] **R15 가중학습(조건부상관→비중) T2 통계 본체 완료 — btn-Codlearn 분담(§1.1/1.2/1.6/calibration/1.8) 구현.** 외부 의견 3R(gemini+claude 병렬, 세부구현만·확정설계 고정) R2 saturation 후 착수. **신규 파일**: `core/structure/conditional_correlation.py`(nonparanormal_transform rank-Gaussianize + fit_glasso_ebic EBIC grid + eb_shrink λ_floor + RegimeGlasso hard-per-regime + effective_precision cov-space belief-mix 1회역행렬 + TemperatureCalibrator frozen+hash + ic_power_gate MDE/effective_n_ar1/block_bootstrap_se, 8/8 self-test PASS). **수정**: `structure_model.py`(§1.10 use_interaction driver×regime 교호항 + ridge_alpha OLS fit_regularized, 기본 off=무회귀, 11→26 cols 검증) + `assumption_stats.py`(hysteresis_and_gate falsifiable 조건 추가 + ic_power_gate re-export, 기본 True=무회귀). **외부 의견 3R 수렴(.consult-r15-impl-R{1,2} + gemini/claude-R{1,2})**: Q1=EBIC grid(소표본 CV fold 부족 회피, γ=0.5 geomspace 결정론, LW fallback) / Q2=temperature(isotonic은 OOS label 대량+부호반전시만, temperature가 belief 궤적 연속→between-dispersion feature 정합) / Q3=소스 EB λ_floor margin(별도 per-regime floor 중복 배제, cond≤p/λ_floor)+싱크 대칭화+Cholesky fail-loud(정상 dead code)+de-risk feature는 between_term 직접(fix 상류)+scaled loading은 fallback 전용. **검증 수치**: nonparanormal 첨도 15.6→-0.46 / glasso edges 2 / EB λ n10=0.50·n200=0.05 / regime 조건부상관 회복(r0[0,1]=0.37·r1[2,3]=0.40) / belief-mix dispersion uniform 6.08≫one-hot 0.24(transition de-risk) / temperature T=2.47 ECE 0.239→0.006 / IC power short falsifiable=F·long=T / 결정론 replay Ω_eff·T·pin 동일. **전체**: 14 모듈 self-test PASS + tests/structure/ 39 passed(회귀 0). **계약 표면(T3 소비)**: export RegimeGlasso·effective_precision(→Ω_eff for w∝Ω·IC)·TemperatureCalibrator(→belief b(t))·ic_power_gate(→falsifiable for DUAL falsification)·nonparanormal_transform·eb_shrink. btn-Inv 분담=데이터 패널 PIT 공급(as_of vintage). btn-Codlearn 분담=WeightAssumptionCard·w∝Ω·IC·L1 주입·judge down-only. **다음**: btn-Codlearn psmux 회신(완료+계약 표면). long-mode ON(cap500k).

> [ckpt-202605300030:btn-button] **R4/R5 robustness 업그레이드(e-value backbone) 완료 — btn-Codlearn 전체구조 자문 R4/R5 saturation 반영.** 전 12 모듈 self-test PASS + tests/structure/ 39 passed(기존 25 + 신규 property 14, 회귀 0). **신규 파일**: `core/structure/eprocess_backbone.py`(MixtureSPRTEProcess Robbins 폐형 test martingale + ELOND e값 online FDR + GraphEAllocation DAG e-wealth + SpecSentinel PIT/exchangeability + ReverseEProcess + e_cusum + classify_decay_vs_regime) + `tests/structure/test_eprocess_backbone_properties.py`(14 property: replay reorder-invariance·Ville false-alarm≤2α·e-LOND AR(1) robust·graph 안전축). **수정**: `assumption_validation_engine.py`(fdr_backbone='lord'|'elond' 옵션 + verdict fdr_backbone/elond_significant 필드, 기본 lord=하위호환). **R4/R5 5종**: (R4) e-process backbone 마이그레이션[최우선, 자기상관에서 p값 LORD++ 독립가정 취약→e값 임의의존 robust] + graph-structured e-allocation / (R5) spec sentinel 층(wrong-H0 방어→abstain) + decay-vs-regime(reverse e-process+E-CUSUM) + V&V property test(R5 유일 material 잔여). **검증 수치**: e-process H0 false-alarm 7/400≤2α / replay 정역순 E 동일(1e-9) / e-LOND AR(1) 자기상관 발견 폭주 X / spec sentinel 균일=ok·치우침=abstain / reverse e-process 단조감소 decay 점화. **계약 표면(T3)**: export MixtureSPRTEProcess·ELOND·GraphEAllocation·SpecSentinel·ReverseEProcess·e_cusum·classify_decay_vs_regime + engine fdr_backbone 옵션(하위호환). 상세=DESIGN-button-v2.md §12. **practical saturation(R5)**: 추가 자문 ROI 음→엔지니어링·운영 이행. 잔여=graph×online joint 이론 보수·fill 내생성(btn-Inv ramp)·meta-reflexivity(hash-commit)·인프라 DR(모델밖). **다음**: btn-Codlearn psmux 회신(완료+계약 표면). long-mode ON(cap500k).
>
> [ckpt-202605292355:btn-button] **V5(BB-5) + V7(BB-3/BB-4 보강) + V6 통합 전부 완료 — T2 v2 종결.** 전 11 모듈 self-test PASS + 기존 25 structure regression PASS(회귀 0). **신규/수정 파일**: `config/archetypes/{commodity_carry,seasonal,inventory,monetary_store,network_utility,speculative_flow}.yaml`(6) + `core/structure/archetype.py`(DEFAULT_SECTOR_ARCHETYPE commodity/crypto 8섹터 추가 + __main__ 11종 round-trip) + `core/structure/commodity_assumptions.py`(신규: carry_forward_slope/seasonal_f_test/variance_ratio Lo-MacKinlay/threshold_regression Hansen/oversupply_decoupling/mvrv_mean_revert/netflow_guard stub + build_commodity_cards/build_crypto_cards) + `core/structure/hierarchical_fdr.py`(신규: pvalue_to_evalue VS calibrator + EProcessSpender anytime-valid + falsification_power/protectable + HierarchicalFDRCascade BB+de-risking bypass) + `core/structure/assumption_validation_engine.py`(DOMAIN_ESTIMATION_POLICY + validate 에 ②e-process AND-gate·③power 게이트·①cascade parent_id/action 배선 + 신규 verdict 필드 eprocess_significant/power/protectable/cascade_reason) + `core/regime/regime_discovery.py`(SequesteredVerdict + sequestered_confirm + false_positive_rate + HumanApprovalGate require_sequestered). **검증 수치**: power 게이트 n=8→power0.345→protectable=False→fdr무효 / cascade 부모미통과→new_entry locked·de_risking bypass / 비독립 substrate→부모 통과불가 / e-process 200 null-스트림 1/α 돌파 7(≤α·200) / sequestered 신규 confirmed(max_e 5e5)·기존 미confirmed / 정지 합성 FP rate 0.000(≤0.10). **계약 표면 변화(T3 소비)**: ValidationVerdict 4 신규 필드(하위호환, 기본값 보존), engine.validate 2 신규 kwarg(parent_id/action, 기본 new_entry), HierarchicalFDRCascade·EProcessSpender·falsification_protectable 신규 export. **scipy 1.17.1 사용**(F/norm; 부재 graceful fallback). py=/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe, 콘솔 utf-8=PYTHONIOENCODING. **다음**: btn-Codlearn psmux 보고(완료+계약 표면). R4 후보(online FDR/optional-stopping 단독 자문)는 사용자 결정 — 미해결로 둠.
>
> [ckpt-202605292050:btn-button] **v2 빌드 V0~V4 완료(card_contract+BB-1/2/3/4, 전부 self-test PASS), V5(BB-5)부터 재개.** BB-3=`core/regime/regime_discovery.py`(OnlineRegimeDiscovery: BOCPD+Hotelling/χ² novelty+LORD++ wrap, HumanApprovalGate approve=사람→k3→k4 bump, bnpy seam) 추가 완료. **V5 BB-5 진행중(부분)**: `core/structure/archetype.py` 에 6 카드(CommodityCarryCard/SeasonalCard/InventoryCard + MonetaryStoreCard/NetworkUtilityCard/SpeculativeFlowCard) + ArchetypeCard Union + ARCHETYPE_NAMES(11종) + _CARD_CLASSES **추가 완료**. ⚠️ **남은 BB-5 (이거 안 하면 archetype.py `__main__` config 테스트 FAIL)**: (a) DEFAULT_SECTOR_ARCHETYPE 에 commodity/crypto 섹터 매핑 추가 (b) `config/archetypes/` 에 commodity_carry.yaml/seasonal.yaml/inventory.yaml/monetary_store.yaml/network_utility.yaml/speculative_flow.yaml 6종 생성(기존 yaml 5종 포맷 참고: archetype/primary_metric/companion_signals/value_trap_guards/cheapness_sign/percentile_overfit_risk) (c) archetype.py `__main__` 에 6 신규 round-trip assert 추가 (d) `core/structure/commodity_assumptions.py` 신규(carry convenience-yield rolling-z + carry→fwd-return slope prequential / seasonal 월dummy F-test+STL strength / inventory variance-ratio Lo-MacKinlay+threshold-reg Hansen / crypto MVRV regime-median mean-revert + netflow guard=비활성 stub) + self-test. 그 다음 **V6**=전 self-test(card_contract/macro_assumption_card/correction_loop/assumption_validation_engine/regime_discovery/archetype/commodity_assumptions)+기존 25 regression(assumption_stats/detectors/online_fdr)+DESIGN/progress 최종화+btn-Codlearn 재보고.
>
> **★ V7 BB-3/BB-4 보강 (btn-Codlearn 전체구조 3R 자문 확정 2026-05-29, 정독필수=`CONSULT-DECISIONS-whole-20260529.md` §btn-button)**: (1) **BB-4 cascade=hierarchical FDR**(Benjamini-Bogomolov: 거시 regime 전이=부모가설, ★독립 substrate 엄격통과해야 자식 3도메인 family 예산 해금, post-selection 차단) + bypass(de-risking 보호액션만 per-stream 우회, 신규진입 부모게이트 우회 금지). (2) **BB-4 online multiplicity**: LORD++ 위 **e-process alpha-spending schedule**(optional-stopping robust) — hierarchical 은 batch라 시간차원 post-selection 재유입 차단. (3) **BB-1/BB-4 falsification POWER 게이트**: 형식존재+통계power 하한. power=0(crypto post-ETF 1회성·baseline부재)→진입통과+보호 0. (4) **BB-2/BB-4 decoupling 추정 per-domain 다형성**(update주기·decay, crypto tick vs macro 분기). (5) **BB-3 거짓 regime 방어**: optimizer 미접촉 **sequestered stream** + anytime-valid(e-process) 사전 threshold + **정지regime 합성데이터 주입→FP rate 정량화**(stationary 에서 regime '발견'=실거래 발견 의심). 적용 순서: BB-5 마저완료 → BB-3 (5) → BB-4 (1)(2) → falsification power (3) → V6. 인계: [handoff-assumption-v2-button-20260529.md](./handoff-assumption-v2-button-20260529.md)
> (1) 완료(전부 self-test PASS): `core/assume/card_contract.py`(공유 계약 AssumptionCardLike+BaseAssumptionFields+assert_falsifiable) / BB-1 `core/brain/macro_assumption_card.py`(6+1 카드 승격, FALSIFICATION_BY_CASE, anomaly↔card 어댑터, add_candidate_card) / BB-2 `core/brain/correction_loop.py`(LiveCorrelationLoop, JM divergence harvest→ingest_correction, recall PIT, attach_to_classifier) / BB-4 `core/structure/assumption_validation_engine.py`(kind dispatch→holds_now + 자산클래스 격리 LORD++ FDR + 부활차단 + compile_falsification). btn-Codlearn 이 core/assume/ 병렬(judge.py 존재) — card_contract.py 만 내 소유 합의.
> (2) 다음 의도: V4 BB-3 `core/regime/regime_discovery.py` (BOCPD timing 1-D + Hotelling T²/χ² novelty full-다변량 + 후보발행 online-FDR wrap + dwell·time-separation + HumanApprovalGate 승격=사람 + bnpy seam graceful). → V5 BB-5 `core/structure/archetype.py` commodity 3(carry/seasonal/inventory)+crypto 3(monetary_store/network_utility/speculative_flow) + `config/archetypes/*.yaml` + `core/structure/commodity_assumptions.py`. → V6 전 self-test + 기존 25 regression + btn-Codlearn 재보고.
> (3) 동기화: ledger 본체=btn-Inv IA-1(BB-4는 주입식). SSOT 설계=DESIGN-button-v2.md §10. 자문=.consult-button-R1~5.txt. 결정요약=CONSULT-DECISIONS-button-v2-20260529.md(Codlearn 전달완료). calibration: LORD++ α crypto0.10/macro0.05, BOCPD λ1/60·1/48, Hotelling F=(n-p)/(p(n-1))·T²~F(p,n-p) n≥3p, χ² 99th/95th, DM lag h-1. py=/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe.

- ckpt 2026-05-29 (btn-button): 두 자문(claude 핵심+gemini) 정독 → 3산출물. 검증통계 엔진 구현·테스트 완료(스텁 아님). 분담 경계 준수(T2=통계, T3=orchestration).
- ckpt 2026-05-29 v2 (btn-button): 자문 5R saturation(DESIGN-button-v2.md §10). 사용자 "착수" → V0~V6 빌드 진입. 스코프 = 매크로 코어 + commodity + crypto(권장 B1).
