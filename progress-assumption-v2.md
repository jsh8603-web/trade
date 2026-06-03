---
tags: [type/progress, domain/inv, phase/II, track/T3, topic/assumption-lifecycle-v2]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-assumption-v2-axes.md
autopilot: OFF
note: 가정 라이프사이클 v2 진행 + ★누락방지 GATE. 직전 실패 = FINDINGS 후 분할했으나 부분구현. 이번엔 요청→구현 추적 + 완료 GATE 로 부분구현 차단.
---

# progress — 가정 라이프사이클 v2 (★누락방지 GATE 박제)

> ⛔ 루트 `progress.md` = btn-Inv 소유, 건드리지 말 것. 본 파일 = 가정 v2 SSOT.
> 인계: [handoff-assumption-v2-20260529.md](./handoff-assumption-v2-20260529.md) — in-flight 상태 + 재개 다음행동(claude-web R1 미실행→여기부터). 재개 시 첫 Read.
> ⛔ **직전 실패 원인** = FINDINGS 작성 후 3분할 했으나 **부분만 구현, 사용자 요청 누락**. → 본 progress 의 GATE 통과 전 "완료" 마킹 금지.

## ★ 절대 불변 (사용자 확정 Q1~Q4, 2026-05-29)
- **Q1** 모의 API 연결됨 → 학습루프 + **실거래까지** (shadow→live 사람게이트).
- **Q2** 거시·주식·상품 **3 도메인 동순위**.
- **Q3** 거시 = 지표 의미변화 학습(decoupling 6 case 승격) **AND** open-ended regime 발견(bnpy), 둘 다.
- **Q4** 판정 고도화 전부 — **L1 결정론 + L2 Qwen + L3 BGE + DCF@agent**.
- **통합 method** = 거시 `indicator_event_correlation` decoupling-case 패턴이 **template**, 주식/상품 동형 복제 (지표만 다름). plan §3.5.

## ★ 참고 문서 (각 세션 착수 전 필독 — SSOT 그라운딩)
| 문서 | 용도 |
|---|---|
| `plan-assumption-v2-axes.md` | 마스터: 6축·최소기준·통합 method·세션 분배 |
| `macro.md` / `quant.md` | 거시·주식/상품 도메인 상세 (이미 코드 대부분 반영, 참고) |
| `FINDINGS-phase2-sector-rule-framework.md` | 8R 자문 종합, 7축, 리소스맵(bnpy/Damodaran/French) |
| `core/brain/indicator_event_correlation.py` + `MACRO_CORRELATION_BACKGROUND.md` | ★거시 method reference 구현 (6 decoupling case) |
| `handoff-T3-assumption-integration-20260529.md` | S14~S20 설계 (T1·T2 계약) |
| `.consult-R1-{claude,gemini}.txt` | belief revision 자문 (ATMS+SR11-7+online FDR) |
| `.audit-assumption-requests.txt` / `.audit-macro-prompts.txt` | 사용자 프롬프트 원본 (준거) |

## ★★ 요청 → 구현 추적 매트릭스 (누락방지 GATE)
> 각 행 = 사용자 명시 요청. `[x]` = **실구현 + self-test 통과 확인** 후에만. 설계만/부분구현 = `[ ]` 유지. 담당 세션이 GATE 충족 증거 보고해야 마킹.

| # | 사용자 요청 (출처) | 담당 | 구현 위치 | 완료 GATE (이거 통과해야 [x]) | 상태 |
|---|---|---|---|---|---|
| R1 | D1 open-ended 신규 regime 발견 (FINDINGS §1, prompt#8) | button | `core/regime/regime_discovery.py` | bnpy/BOCPD novelty → 후보 regime 발행 + 사람비준 gate self-test | [ ] |
| R2 | 거시 지표 의미변화 학습 (6 decoupling case → 버전드 가정) | button | `core/assume/` + indicator_event_correlation 연결 | 6 case 가 AssumptionCard 化 + ingest/recall **live 연결** + self-test | [ ] |
| R3 | D3 valuation 기간/산업 적응 (주식) | codlearn | `core/assume/` + cheapness_z/archetype | 산업×기간 가정 카드 → 판정 주입 closed-loop self-test | [~] spine✅(derivation scope계층 sector×period×regime + closed-loop equity PASS), 실 cheapness_z/archetype dispatch=Phase II |
| R4 | 상품 기준 (carry/계절성/COT/재고/iNAV) — 전무 | button+inv | `core/structure/archetype`(commodity) + data | commodity archetype + 검증경로 + 데이터 self-test | [ ] |
| R5 | 학습루프: 결정 log→학습→가정 수정 (거시+가치 **둘 다**) | inv+codlearn | ledger 구독 + `core/assume/validator` | 결정→outcome→가정 holds 재측정 closed-loop (3 도메인) | [x] test_closed_loop_end_to_end[macro/equity/commodity] PASS (8/8) |
| R6 | 판정: L1+L2 Qwen+L3 BGE 싼지/비싼지 | codlearn | `core/assume/judge.py` | L1 floor + L2 Qwen hook + L3 BGE hook 결합 self-test | [x] judge.py self-test 8/8 (L2/L3 monotone-down + fail=manifest) |
| R7 | valuation 가치평가(DCF) = agent 결정 bottom (prompt#5) | codlearn | `stock/valuation.py` wire to agent decision | 퀀트후보 → DCF confirm → 결정 경로 self-test | [x] judge.py L1∥DCF disjunctive veto self-test (DCF_VETO_GAP) |
| R8 | D4 Book 실데이터 연동 + to_context 소비 | inv+codlearn | `core/book/d4_book.py` | 실데이터 populate + LLM to_context 소비처 wire | [ ] |
| R9 | seed=상수, 메인 seed 박기 + consensus 조정 | codlearn | seed_builder + consensus + `core/assume/update_controller` | seed→consensus 변경 AND-gate self-test | [~] AND-gate spine✅(update_controller hysteresis_and_gate self-test), seed_builder/consensus 실배선=후속 |
| R10 | 변경 시 기존 학습데이터 versioned 처리 (PIT) | codlearn | ledger version_basis + bitemporal | rule_version 박제 + 과거 재현 self-test | [x] derivation PIT replay frozen + registry.get_version + closed-loop PIT 재현 PASS |
| R11 | data_contract/lineage/online_fdr 영속 (T1 미구현) | inv | `core/data/{data_contract,lineage,online_fdr}.py` | Pandera gate + lineage jsonl + alpha_wealth 영속 self-test | [ ] |
| R12 | 실거래까지 (모의 API→live, 사람게이트) | inv | 모의 API outcome 수집 + shadow→live gate | 모의계정 outcome 수집 + live 진입 사람게이트 | [ ] |
| R13 | orphaned position + decay/half-life (실거래 안전) | codlearn | `core/assume/` S19 + Card half_life | 가정 기각→의존 포지션 managed-exit + decay self-test | [x] orphan_guard.py 4/4 (hard/soft·netting·token-bucket·half_life decay) + closed-loop retract→exit PASS |
| R14 | 다산업/다기간 학습 수용 충분성 | codlearn | SeedRegistry + assumption_store | 다산업×다기간 카드 append + 무한확장 self-test | [x] registry append-only(무한) + derivation scope계층(sector×period×regime) + 3도메인 closed-loop PASS |
| R15 | ★관계있는 지표 함께 학습(조건부 상관) → 평가기준 안 지표 비중(계수)을 거시 국면·산업 사이클/특성 조건부로 조절 (사용자 2026-05-29 명시 2회 강조 — "학습의 기본") | codlearn+button+inv | `core/assume/weight_card.py`(신규) + `core/structure/conditional_correlation.py`(신규) + structure_model 교호항·regime_to_weights·indicator_event_correlation adapter | 조건부 상관(regime-conditional glasso) 학습 → regime×archetype 비중 카드 → **L1 결정론 합성 S_L1=clamp_floor(Σ w·z) 주입**(LLM·agent는 down-only) → 결정 → 학습으로 비중 재조절 closed-loop self-test (거시 AND 주식) | [ ] ✅설계확정(자문3R saturation, **[CONSULT-DECISIONS-weight-20260529.md](./CONSULT-DECISIONS-weight-20260529.md)**) → 구현 대기 |

> ⛔ **15 행** 전부 `[x]` 아니면 = **요청 누락 상태**. 통합 완료 선언 금지.
> ⛔ **R15 = 사용자가 직접 "명시적으로 지시했는데" 라고 2회 지적한 누락 축** — 현 구현(정적 Investment Clock 표 regime_to_weights·정적 attenuation·additive regime 더미)은 "학습 기반 조건부 비중 조절"이 아님. 이 행 미충족 시 메타레이어 핵심 미달. 자문/구현/통합 전 단계에서 이 행을 최우선 추적.

## 6축 × 3도메인 GATE (각 셀 v1 wired = 최소기준, plan §2)
| 축 | 거시 | 주식 | 상품 |
|---|---|---|---|
| A 학습 | [x] | [x] | [x] |
| B 기준화 | [x] | [x] | [x] |
| C 주입 | [x] | [x] | [x] |
| D 검증 | [x] | [x] | [x] |
| E 변경 | [x] | [x] | [x] |
| F 거버넌스 | [x] | [x] | [x] |

> 18 셀 = 부분구현 차단 grid. 셀 = 해당 도메인이 그 축에서 v1 동작 + self-test.
> ✅ **2026-05-29 충족 (btn-Codlearn)**: `tests/assume/test_closed_loop_3domain.py` 가 macro/equity/commodity 각각 6축 spine 전부 통과 — A(validator.validate regime-conditional)·B(registry 버전드 카드+derivation)·C(derivation→결정)·D(ValidationVerdict holds/fdr)·E(update_controller transition/retract)·F(dag grace/lazy gridlock-free + orphan_guard token-bucket + base human_review). 8/8 PASS + 회귀 0(structure+assume 47/47). **최소기준=v1 spine wired** 충족. ★학습 depth(open-ended regime 발견·수치 S' 계산·실 cheapness_z archetype)=Phase II 별 세션. live circuit breaker=btn-Inv(보고 완료).

## ★★ 세션별 "지켜야 할 평가 축" (btn-Codlearn 정의 = 바인딩 게이트)
> 사용자 위임 "지켜져야하는 평가 축을 너가 각 과제별로 만들라". 아래 = 각 세션이 **반드시 충족**할 통과 기준. design·method 는 자문으로 발전하되 이 축은 고정. 자문으로 누락 축 발견 시 btn-Codlearn 에 추가 제안.

### btn-Inv (학습 데이터 기반 + 실거래 안전)
- **IA-1** [축A·F] 모든 결정이 trigger 가정 id+version 과 PIT-safe log + 실현 outcome join (3도메인, 결과라벨 100%, 역추적 가능).
- **IA-2** [축D] data_contract 게이트가 validator 앞단 — 측정깨짐(계약위반=incident) ≠ 가정틀림 분리.
- **IA-3** [축F] 임의 as_of 결정의 입력 가정 체인 재현(lineage replay_provenance) + online_fdr alpha-wealth 영속.
- **IA-4** [상품] 상품 무료 데이터소스 확보 + panel commodity 컬럼 + 생존편향(소멸선물/청산ETF) 포함.
- **IA-5** [축F·Q1] 모의계정 API outcome 수집 동작 + shadow→live 사람게이트 데이터 경로.

### btn-button (거시 학습 + 검증·판정 통계)
- **BB-1** [축B] 거시 6 decoupling case 가 falsification_metric 있는 **버전드 AssumptionCard** + 신규 case 추가 가능.
- **BB-2** [축A] indicator_event_correlation ingest_correction/recall_similar **live 루프 연결**(현재 dead) — 실시간 판정 vs 사후정답 학습.
- **BB-3** [축A·Q3] open-ended regime 발견(bnpy/BOCPD)→후보 신규 regime 발행 + **사람비준 gate**(발견자동·승격사람).
- **BB-4** [축D] regime-conditional holds 측정 + online-FDR 다중검정(가정별 alpha-wealth).
- **BB-5** [상품] commodity archetype(carry/seasonal/inventory) + 검증 통계 경로.

### btn-Codlearn (오케스트레이션 + 판정 + 통합)
- **CL-1** [축B] `core/assume/` Card/Registry/Validator/UpdateController 오케스트레이션 (3도메인 공통, AssumptionCardLike 충족).
- **CL-2** [축C·Q4] 가정→derivation→판정(L1 floor + L2 Qwen + L3 BGE + DCF@agent) + 신뢰도→band→사이징.
- **CL-3** [축E] AND-gate + base-layer 사람비준 + ATMS 의존전파 + orphaned position + decay/half-life.
- **CL-4** [통합 GATE] closed-loop(결정→학습→검증→변경→재주입) 가 **거시 AND 주식 AND 상품** 전부 통과.
- **CL-5** [주식/상품] cheapness_z/archetype + commodity 기준이 기간/산업별 적응 (통합 method §3.5 동형).

## 단계 (Phase)
- [x] **P0 설계+분배** — 감사(요청 14개 식별) + 코드맵 + 6축·최소기준 정의 + 통합 method(거시 template) + 3세션 분배. (plan-assumption-v2-axes.md)
- [~] **P1 세션별 자문+보완** — 각 세션 자기 주제 ≤5R 자문(gemini+claude 병렬) + 소유 셀 보완 + self-test. 산출 `DESIGN-{sess}-v2.md` + `.consult-{sess}-Rn.txt`. btn-Codlearn 보고.
  > **P1 현황 (2026-05-29, btn-Codlearn 집계)**:
  > - **btn-Codlearn(나)**: 설계 `DESIGN-codlearn-v2.md` 완료(CL-1~5 code-level). **자문 R1 ✅수렴**(gemini R1 + claude R1 Opus4.8, raw=`.consult-codlearn-R1.txt`) — topology 수렴 + claude 안전정정 7건 전부 반영(adopt/retract gate 분리·per-domain alpha-wealth·L2/L3 monotone-down·base shadow/canary·orphan token-bucket+netting·★first break=reflexivity(gridlock 아님)·PIT replay SHA+fixture). plan §2.2 갱신. **`core/assume/judge.py` ✅구현완료**(CL-2, self-test **7/7** PASS — L2/L3 monotone-down 불변식 포함, L1=sizing∥DCF=kill 비결합, fail-open). 잔여 core/assume(registry/validator/update_controller/derivation/dag/orphan_guard) = 확정설계로 card_contract(btn-button) 랜딩 후 착수.
  > - **btn-button(T2)**: ✅**자문 5R saturation 완료**(gemini saturation 선언, `CONSULT-DECISIONS-button-v2-20260529.md` + `DESIGN-button-v2.md §10`). BB-1~5 확정. **V0~V6 빌드 진입**(Walking Skeleton: event ledger 배선+dummy TDD 먼저→통계 플러그인→최소 backtest). 완료시 재보고. 핵심결정 = closed-loop substrate = **bitemporal append-only event ledger(11 event, state=reduce, FDR_DECISION decision_time-immutable)**. instrument 우선=crypto+sector-ETF+commodity.
  > - **btn-Inv(T1)**: 데이터/PIT R2 자문 진행(.consult-inv-R2 발사 확인). v2 설계 산출 대기. ⚠️**event ledger schema 3자 합의 메시지 전송**(btn-button 11-event 계약 정렬, 본체=btn-Inv IA-1, 회신 대기).
  > - **★교차세션 조율 3건**(btn-button R5 §6, btn-Codlearn 주관): (1) event ledger schema 3자 합의(btn-Inv 본체·btn-button read-only·나 lifecycle emit, 메시지 전송완료·회신대기) (2) cross-asset cascade=내 ATMS 의존전파로 해소(DESIGN §10.2 반영완료) (3) revision-drift monitor=closed-loop reflexivity 방어 편입(DESIGN §10.3). 상세 = `DESIGN-codlearn-v2.md` §10.
  > - **계약 의존**(내 구현 선행조건): card_contract.py·validation_engine·HumanApprovalGate·correction_loop(btn-button V0~V6) + event ledger 본체·data_contract/lineage/online_fdr 영속·모의API outcome·crypto on-chain(btn-Inv). 상세 = `DESIGN-codlearn-v2.md` §9.
  > ⚠️ **구분 (사용자 2026-05-29 명시)**:
  > - **§2 6축(A~F) = btn-Codlearn 이 정의한 "지켜져야하는 평가 축" = 바인딩 게이트** (사용자 위임 "평가 축은 너가 만들라"). 각 세션 **반드시 충족**. 자문으로 누락 축 발견 시 btn-Codlearn 에 추가 제안 가능(축 집합 확장 OK, 정의된 축은 必충족).
  > - **반면 design 내용·통합 method·셀 구현 = 예시 출발점(고정 아님)** → 각 세션 자문(≤5R)으로 **발전**: 축×3도메인(거시/주식/상품) 완성도 평가, 부족분 위주 보완, 직접 리서치 허용.
- [x] **P2 통합** (btn-Codlearn) — 3 세션 산출물 통합 + `core/assume/` 오케스트레이션 + 계약 정합. ✅ core/assume 7모듈(registry/validator/judge/dag/update_controller/derivation/orphan_guard) 구현·self-test 전 PASS. btn-button engine(R4/R5 보강 완료) wrap + btn-Inv substrate(event_ledger·data_contract·lineage PIT) 계약 양방향 확인 락. 회귀 0(structure+assume 47/47).
- [x] **P3 ★closed-loop GATE (부분구현 차단)** — 결정→log→학습→검증→변경→재주입 end-to-end 가 **거시 AND 주식 AND 상품** 전부 통과. ✅ `tests/assume/test_closed_loop_3domain.py` 8/8 PASS(3도메인 6스텝 + PIT replay + gridlock-free + reflexivity 3종). 18 셀 [x]. ⚠️ **14 요청행 중 codlearn spine 행(R5/R6/R7/R10/R13/R14) [x], R3/R9 [~](깊은적응=Phase II)**. button(R1/R2/R4)·inv(R8/R11/R12) 행은 담당세션 보고분 — 별도 검증 필요(통합 완료 선언 전 14행 전수 확인).
- [ ] **P4 실거래 wiring** — 모의 API outcome 수집 → shadow 검증 → live 사람게이트. Q1 충족.

## Working Notes
> 인계: [handoff-study-system-20260530.md](./handoff-study-system-20260530.md)
> [ckpt-202605300500-O:btn-Codlearn] **★통합 골격 G1 + 수집기 2종 완료. 사용자 A(골격 선구축) 진행 중.**
> - **마지막 결정**: (1) 통합 골격 **G1** `core/study/study_loader.py`(+__init__) — study_session.yaml 7블록
>   로드·정규화(전방호환)·검증(통일 하드룰 코어셋6/force-include≤4/partial-corr conditioning/vintage
>   point_in_time/4단계 커버/ticker→pooling 경고/coin 예외), errors=거부·warnings=허용, self-test 6/6 PASS.
>   (2) 수집기: FX `core/data/macro_market.py`(self-test7/7) + French·ETF `stock/data/french_factors.py`·
>   `us_etf.py`(11/11) + HY OAS(fred_adapter BAMLH0A0HYM2), 전부 무회귀. KRX(a5bafda9) 진행중.
>   (3) STUDY-KIT 완성(§0 행동규칙+§3 7블록+§4 4단계 코드위치+§6 하드룰+§7-1 자산군별 소스+부록A/B).
> - **다음 의도**: G2 panel_manifest(build_indicator_matrix manifest wrap) / G3 lens 주입(weight_card+judge) /
>   G4 flag 경로(confidence_hooks→weight_falsification) / G5 선결2건(cross-sleeve cov factor-implied + regime
>   obs floor). KRX 수집기 수령 확인. 사용자 psmux 10세션 생성 시 STUDY-KIT+study_id 전달.
> - **동기화 필요**: long-mode ON(cap500k). ④ belief Σ_eff + 골격 + 수집기 전부 커밋 미지시 stage. 자문
>   동시 9세션 경합 미검증(3세션까지 OK) → KIT 에 직접 리서치(WebSearch/WebFetch) 폴백 허용 명시.

> [ckpt-202605300400-N:btn-Codlearn] **★종목 스터디 시스템 설계 확정 — 자문 3R saturation + plan/KIT 작성. psmux 세션 사용자 생성 대기.**
> - **마지막 결정**: 사용자 새 요청(자산군별 깊은 스터디 → 종목별 평가지표 가중치 동적 변경 규칙 산출, 4단계 구현). gemini+claude **3R saturation**: 아키텍처=조건부 cglasso(asset_core|macro ~ N(B·macro, Ω_asset⁻¹), Block Matrix 기각[N≈45 과적합], 거시 driver 2-4개만 named 채널), 그룹=study 10 / panel template 4(equity[us/kr/intl/reit]/commodity/gold/bond) / sleeve 8(기존7+intl, REIT=equity sub-panel 승격조건부), prior=EBIC+EB shrink+force-include≤4(full adaptive 보류), 주식 통일 하드룰 코어셋, partial-corr 하드룰. 사용자 정정 수용: 스터디 재료=일반론+리포트(렌즈) × 우리 시스템 자료(없으면 수집기 선구축), 최종산출=종목별 가중치 동적변경. 렌즈 LLM 주입+확신/거부 flag 신뢰도 누적=기존 가정 라이프사이클(judge 카드주입+DUAL falsification)과 일치.
> - **다음 의도**: (1) **무료 수집기 선구축**(main 우선): WICS 업종·외국인순매수(pykrx)·HY OAS(FRED BAMLH0A0HYM2)·Ken French 팩터·US ETF holdings·DXY/USDKRW(FxStore PIT). 기존 VintageProvider/FundamentalsProvider 인터페이스, off graceful, self-test. (2) 시스템 선결 2건(cross-sleeve 공분산 출처 / regime obs floor). (3) 사용자가 psmux 10세션 생성(계획대로) → 각자 STUDY-KIT.md 읽고 6블록 채움 → main 통합→3R 자문→코드구현.
> - **동기화 필요**: 산출물 = **plan-study-system.md**(세션10 목록+phase) + **STUDY-KIT.md**(통일 산출계약 6블록+코드 4단계 위치+자료 현황+자문결론, 각 방 자기완결 지시서). 자문 raw=.gemini-web-last.md/.claude-web-basic-last.md(grouping R1~R3). long-mode ON(cap500k). 스폰방식=teammate(harness2)→**psmux 직접**(사용자 결정, 개별 자문 도구 풀사용 위해). ④ 코드(regime_to_weights belief Σ_eff+연율화) 커밋 미지시 stage 보류.

> [ckpt-202605300230-M:btn-Codlearn] **★④ 자산 배분 belief 동적 공분산 완료 (선결과제 종결) — 종목 스터디 시스템 착수.**
> - **마지막 결정**: ④ 선결과제 4-step 완료(opt-in INV_R15_WEIGHTS off 기본 byte-identical, R15 stock track 과 동일 패턴 fork):
>   (a) `core/brain/regime_history.py::build_sleeve_regime_ids`(슬리브 returns_history.index→classify(as_of) PIT→regime int id substrate, regime_history 재사용).
>   (b) `core/brain/regime_to_weights.py`: 시그니처 `belief`/`sleeve_regime_ids` 추가 → `_belief_conditional_cov`(RegimeGlasso.fit(슬리브수익률,ids)→effective_precision(models,belief_by_id)→Σ_eff) → `_bl_returns_path(cov_override=)` 로 BL 공분산 주입(method=bl_returns 강제, caution=belief_conditional_cov). substrate 부족/실패=Ledoit-Wolf graceful. **★연율화 fix**: `_periods_per_year`(index 간격 추정)로 Σ·π 연율화 — btn-button(T2) 진단 일치(주간 π≪연율 rf 0.02→max_sharpe infeasible→fallback→belief cov 효과 소실)를 cov 연율화로 해소(opt-in bl_returns 한정, 기본 weight_tilt 무영향).
>   (c) `core/portfolio_orchestrator.py::allocate`: belief 를 regime_to_weights **호출 전** 산출→전달(현 호출후 기록만=끊김→재배치), `sleeve_regime_ids` 인자 추가.
> - **검증**: `tests/test_sleeve_belief_cov.py` 7/7 PASS(helper 결정론 동적성·BL 주입·연율화 end-to-end belief→배분변화·substrate없음 graceful·빌더·orchestrator opt-in on/off). **회귀 0** — 동일 `-k` 조합 stash 유무 FAIL 집합 동일(3개 전부 pre-existing: TestPhase12RegimeLearner 2=테스트간 상태오염 flaky / cooldown 1=날짜의존). regime_history self-test PASS, import OK. ⛔커밋 사용자 미지시=보류(코드 stage 상태).
> - **다음 의도(사용자 새 요청)**: **종목 스터디 시스템** — (1) 자산을 스터디 단위로 그룹 분할 + 학습 계획을 main 이 자문(gemini+claude 3R) 거쳐 확정 → 대화 보고 → 사용자가 그룹별 psmux 세션 오픈. 자문 입력 3축: ①자산 구분(거시/국가지수ETF 대형·소형/비미한=지수ETF/미한=산업별묶음/리츠/기타, 레버리지제외·인버스x1포함) ②학습방법(거시 예=macro.md 기반 일반론+투자리포트 지표 의미·관계도, 통화량↔미일채권↔금리) ③코드적용 개략(현재 학습 파이프라인 구현 정리 동반). 깃허브 리소스 subagent 탐색 선행. main=통합 책임(주식 지표 통일 하드룰 등). 개별 세션엔 "학습→규칙화→주입→해제(약화신호)" 개념도 + 현 코드 위치 안내. study raw+요약 1폴더 집결. (d) README 미결정 동반.
> - **동기화 필요**: long-mode ON(cap500k). SACRED(DRY_RUN/execute_trade 미변경, opt-in off). self-check OBSERVE(promo-log): FRED 환경제약↔불가 혼동=E94 변종 + 본 세션 회귀판정 정정(격리실행 vs 동일명령 비교 = 후자만 유효) 기록 대상.

> [ckpt-202605300120-G:btn-Codlearn] **★R15 가중학습 자문 3R saturation + 워커 분담 전달 + 압축 진입.**
> - **마지막 결정**: R15(지표 조건부 상관 학습→평가기준 비중 국면·산업 조건부 조절) = 사용자 명시 누락축. 자문 3R(gemini+claude) **saturation 확정**. 확정설계 = [CONSULT-DECISIONS-weight-20260529.md](./CONSULT-DECISIONS-weight-20260529.md). 핵심: regime-conditional Graphical Lasso(sparse Ω)+nonparanormal+EB shrink(λfloor) → w∝Ω·IC+1/N+cap → **L1 결정론 합성 S_L1=clamp_floor(Σ w_i(regime)·z_i)** 주입(L2/L3/agent=down-only ∏, 천장 S_out≤S_L1) → WeightCard(registry 서브타입, DUAL falsification) → regime soft-belief b(t) cov-space mix(Σ_eff between-dispersion) frozen 박제. ★judge L1∥DCF 병렬가법 → **DCF도 down-only 재캐스팅** 필요. OSS 백본=skfolio/skggm(mlfinlab 금지). accepted residual=regime schema 불확실성(scope밖 문서화). 별도: subagent 4축 검토=core/assume spine 7모듈+closed-loop GATE는 self-test PASS이나 **production wiring 0**(오케스트레이터/outcome join/event_sink/judge주입/derive↔dag/decay↔사이징 미배선, 테스트 안에서만 닫힘).
> - **다음 의도(압축 후 내 분담)**: (1) ★judge DCF down-only 재캐스팅 (2) `core/assume/weight_card.py` WeightAssumptionCard + derivation w∝Ω·IC+1/N+cap 확장 + L1 합성 주입 + DUAL falsification(validator/update_controller 재사용) + soft archetype membership + b(t) frozen 적용 (3) 배선 gap 메우기(run_cycle 오케스트레이터·outcome→Evidence join·registry event_sink 어댑터·judge production 호출·derive(dag=)·decay→judge). btn-button/btn-Inv 산출물 도착 후 통합.
> - **동기화 필요**: 워커 분담 전달 완료 — btn-button(core/structure conditional_correlation: glasso+nonparanormal+EB+cov-space belief-mix+calibration+IC검정력) / btn-Inv(core/data: PIT패널+WeightCard영속 이중시간축+purged CV split+과거포지션배제+cold-start OOD). 두 세션 **이전작업 커밋 진행중** → 내 git 커밋 보류(충돌회피), 커밋정리 후 배선 재검증. long-mode ON(cap500k). 14행 매트릭스 R15 추가(15행).

> [ckpt-202605302000-L:btn-Codlearn] **★R15 production ①②③ 완료(주식 판정 지표가중 전 경로) + brain 문서. ④=다음 세션 선결 과제.**
> - **마지막 결정**: R15 production 배선 — ① regime_history.py(11dd4a4) ② scripts/train_weights.py(84532bb 배치학습→registry 영속) ③ stock_track._resolve_weight_card/_apply_r15_sizing(a21bfd7 registry 조회→주식 sizing). **학습→영속→조회→판정 전 경로 완성**, self-test 전부 PASS 무회귀. FRED key .env 7종 확인(내 "substrate 부재"=오판, 샌드박스 504 검증제약). brain 문서 ARCHITECTURE-brain.md(797d9fd). README.md=레거시 코인봇 v1.29(519줄) 미결정.
> - **다음 세션 선결 과제(④ 자산 배분 belief 동적 공분산 — 사용자 "4번 선결" 지시)**:
>   (a) `core/brain/` 슬리브 regime 히스토리 — returns_history(슬리브 수익률 시계열) + classify(as_of) → 슬리브용 regime_id_series(regime_history.py 재사용 or 슬리브판).
>   (b) `core/brain/regime_to_weights.py` 시그니처에 `belief=None` 추가 → `_weight_tilt_path`(L153) 의 `conf=_aggregate_confidence`(L175)를 belief 집중도(1-normalized_entropy)로 보정 OR 슬리브 effective_precision(RegimeGlasso(슬리브수익률,ids), belief).Omega_eff 를 `_bl_returns_path`(L193) cov_matrix 로 주입(자문 §1.10 BL view=학습Σ̂). off graceful(belief None=기존).
>   (c) `core/portfolio_orchestrator.py allocate`(L146) 가 belief 를 regime_to_weights **호출 전** 산출→전달(현 L181 r15_belief 는 호출 후 기록만=끊김 → 호출 전 산출로 재배치). INV_R15_WEIGHTS opt-in, off 무회귀.
>   (d) README.md 교체 결정: 1=Inv 통합본(코인봇→README-coin-legacy.md 백업 후 ARCHITECTURE-brain+TODO 구조) / 2=현상유지 / 3=상단 prepend. ⛔ 레거시 덮어쓰기 사용자 확인 필수.
> - **동기화 필요**: long-mode ON(cap500k). SACRED(DRY_RUN/execute_trade 미변경, opt-in off). 커밋체인 87655fe→9d70a84→817791d→5ce9d59→72b632c→11dd4a4→84532bb→a21bfd7→797d9fd. self-check 미기록(promo-log OBSERVE: FRED 환경제약↔불가 혼동=E94 변종, 다음 세션 기록).

> [ckpt-202605301800-K:btn-Codlearn] **★R15 production 배선 진행 — FRED key 확인(내 substrate 오판 정정) + regime 히스토리 substrate 빌더 ① 완료.**
> - **마지막 결정**: 사용자 "production 준비 안된거 다 수정 + FRED 왜 안되냐". **FRED 정정**: `.env` 7종 전부 SET 확인(FRED_API_KEY len=32·DART 40·ECOS 20·KIS APPKEY 36/SECRET 180/ACCOUNT 11/HTS_ID 7). 내가 "substrate 부재"라 한 건 **오판** — 샌드박스 외부망 504(검증제약)를 production 불가로 혼동(E94 변종). production(사용자 PC, key 보유)=FRED 작동. RealFredAdapter.get_series(as_of) vintage✓ + classify(as_of) 과거호출✓ → substrate 확보 가능. **production ① 완료**: `core/brain/regime_history.py`(커밋 11dd4a4) build_regime_history(classify(as_of) PIT 반복→시점별 regime)+regime_id_series(→RegimeGlasso int ids)+valid_mask, self-test 4/4, FRED 504→None degrade.
> - **다음 의도(production ②③④, fresh ctx 즉시 착수)**: ② **weight_cycle 라이브 오케스트레이션** — `scripts/run_agents.py` core-gate INV_R15_WEIGHTS on 시: weight_panel.build_indicator_matrix(FRED/KIS series, as_of)→IndicatorPanel → regime_history.build_regime_history(RegimeClassifier(RealFredAdapter), panel_dates)→regime_id_series → GlassoWeightLearner.fit(panel.matrix, ids) → build_weight_card(belief=belief_from_macro_view(_mv)) → registry.register. (substrate 다 확보됨, FRED key 있음). ③ **stock_track registry 조회** — `core/stock_track.py`에 `_resolve_weight_card(registry, sector, regime_id)`: _weight_card_override 없으면 registry.get(f"weight.equity.{regime}") 조회 → generate_candidate 가 그 카드로 _apply_r15_sizing. ④ **배분 동적 cov** — `core/brain/regime_to_weights.py` 시그니처에 belief=None 추가 → _weight_tilt_path 가 effective_precision(regime_history glasso, belief).Omega_eff 로 _sleeve_vol Ω 보정 대체. portfolio_orchestrator.allocate 가 belief 인자 전달(현 r15_belief 기록만→실사용). 전부 off 기본 opt-in, SACRED(DRY_RUN/execute_trade 미변경).
> - **동기화 필요**: long-mode ON(cap500k). FRED production 작동(샌드박스만 504). 커밋체인 87655fe→9d70a84→817791d→5ce9d59→72b632c→11dd4a4. self-check: FRED 환경제약↔불가 혼동=E94 변종, promo-log OBSERVE 대상(compact 후).

> [ckpt-202605301600-J:btn-Codlearn] **★주식 트랙 판정에 R15 지표 동적가중 연결 — 핵심 끊김 해소(사용자 정정 반영).**
> - **마지막 결정**: 사용자 정정 "stock 판정에 지표별 가중 넣는 게 핵심인데 belief만 연결하고 일단락=회피". 전수 재판정(2-subagent): R15 가중이 계산만 되고 평가 미반영(끊김) 확정 — 주식 평가가 valuation_gap 단일지표만, judge(weight_card) production 호출 0. **해소**: `core/stock_track.py generate_candidate`에 `_apply_r15_sizing` 추가 — buy 결정에 다중지표 합성 S_L1=clamp_floor(Σ wᵢ·zᵢ) 반영(EV/EBITDA·book_to_bill·inventory 거시국면·archetype 조건부 가중). 자문 §1.4: R15=L1 결정론(pre-agent)/value_trigger=down-only attenuator, final=l1_size·a 천장 불변식, deadzone→abstain. weight_card/indicator_z/regime_pi override 주입(미주입=무회귀). `_extract_indicator_z`(state features→series 순서). 커밋 72b632c, tests/test_stock_r15_weight.py 6/6, pytest 28 passed(stock R15+assume) 0회귀.
> - **다음 의도**: 잔여 끊김(전수 판정 결과) — (1) 배분 r15_belief = regime히스토리 substrate(실 FRED vintage) 게이트(portfolio_orchestrator). (2) 코인 = RSI 패러다임이라 지표가중 부적합, belief→사이징 조절만 적합(coin_track_macro:62). (3) weight_cycle 라이브 호출 = substrate 게이트. weight_card 학습공급 = registry 학습카드(substrate 후)/prior 주입. 라이브 stock entrypoint(run_agents=coin 전용) 활성화=go-live. + README brain 섹션 작성(사용자 요구, core/assume·judge·R15·belief 어댑터 핵심코드 성격+이유 주석).
> - **동기화 필요**: ⛔SACRED(DRY_RUN/execute_trade 미변경, override 미주입=무회귀). long-mode ON(cap500k). 커밋 체인: 87655fe(카드/judge/falsification)·9d70a84(통합GATE)·817791d(오케스트레이터)·5ce9d59(belief어댑터/라이브게이트)·72b632c(주식 R15 연결).

> [ckpt-202605301400-I:btn-Codlearn] **★R15 라이브 결정경로 배선 — belief 공급 production 연결(INV_R15_WEIGHTS opt-in, off 기본).**
> - **마지막 결정**: 사용자 "라이브 배선까지 진행 우선" 지시. 라이브가 R15 belief 모듈을 실제 호출하도록 연결(connectivity '호출자 0' 갭 해소). 커밋 5ce9d59, pytest 61 passed 0회귀:
>   · `core/brain/regime_belief_adapter.py`(신규, 6/6): MacroView(거시상황 regime_now+confidence_now)→belief b(t) 분포. soft-spread(confidence 高=집중/低=평탄→de-risk), floor, unavailable→uniform, belief_vector 순서박제, TemperatureCalibrator graceful.
>   · `core/portfolio_orchestrator.py` allocate: INV_R15_WEIGHTS opt-in — belief 산출→result["r15_belief"] 기록+caution. **off 기본 byte-identical 무회귀**.
>   · `scripts/run_agents.py` INV_CORE_GATE: WP-R15 belief 공급(WP4 _mv 활용), try/except graceful.
> - **다음 의도(go-live/별도세션 게이트, 이 환경 불가 사유 명시)**: (a) **동적 조건부 공분산 overlay** = 시점별 regime 히스토리 substrate(실 FRED vintage) 필요 — 샌드박스 504로 실작동 검증 불가 → go-live 데이터 게이트. (b) **judge(weight_card) stock 주입** = stock 트랙이 자체 판정체계(value_trigger/HeavyAgent, core.assume.judge 미사용) + stock 라이브 루프 부재(run_agents=coin 전용) → stock entrypoint 활성화 + 판정체계 통합(별도세션 '판단레이어' 분담)이 선결. (c) README brain 섹션 작성(사용자 요구).
> - **동기화 필요**: ⛔SACRED 보존(DRY_RUN/execute_trade 미변경, off 기본). 라이브 배선 = belief 공급 production 연결까지(실 동적 결정변경은 substrate/stock활성 게이트). long-mode ON(cap500k).

> [ckpt-202605301200-H:btn-Codlearn] **★R15 가중학습 통합 완료 — 조건부상관→동적비중→L1주입(pre-agent)→DUAL falsification, 미배선 4 seam 해소.**
> - **마지막 결정**: 사용자 2회 명시 누락축(R15) 구현·통합 완료. 내 분담 5모듈 self-test 12/12 + pytest 61 passed 0회귀:
>   · `core/assume/weight_card.py`(8/8): WeightAssumptionCard(registry 서브타입) + derive_weights(w∝Ω·IC Grinold + 1/N + **capped-simplex projection**) + synthesize_l1(clamp_floor deadzone, 학습분리 primitive) + soft archetype membership(π) + hierarchical partial pooling + **b(t) frozen 박제** + 천장 불변식.
>   · `core/assume/judge.py`(11/11): R15 opt-in L1 합성 경로 `S_L1=clamp_floor(Σ w·z)`(단일 cheapness_z 대체) + 천장 불변식 assert. ★**DCF 는 이미 down-only veto**(가법 아님) 확인 — 자문 §1.4 "DCF 재캐스팅 필수" 권고는 plan 서술 기준, 실코드는 이미 충족(advisory 구조claim 코드read 검증). 미제공 시 무회귀.
>   · `core/assume/weight_falsification.py`(7/7): DUAL — PRIMARY(score OOS Rank-IC **e_cusum 단측붕괴**=kill, mixture 양측이 IC개선도 kill·overflow 하던 버그 해소) + SECONDARY(ΔΩ·logdet drift=re-fit). ValidationVerdict 패키징→update_controller 재사용.
>   · `tests/assume/test_weight_closed_loop.py`(10/10): 3세션 모듈 통합 — ★`test_weights_shift_by_regime_belief`(같은 IC라도 거시상황 belief 다르면 비중 동적변화=사용자 핵심) + 4단계 1회전 3도메인 동형 + kill/re-fit/frozen/calibration.
>   · `core/assume/weight_cycle.py`(6/6): **production 오케스트레이터** — GlassoWeightLearner(WeightLearner Protocol 구현체=누락글루) + build_weight_card + inject_l1 + route_lifecycle(★SECONDARY→derive_weights 재적합→transition, PRIMARY→RETIRE) + run_weight_cycle(4단계 1회전, offline/replay).
> - **3-subagent connectivity 검증(2026-05-30)**: 만장일치 — R15 알고리즘 4단계 완비+동적성 실증, "거시상황(regime)→belief→비중" 사슬 완비(**누락 아님**), lifecycle(기준화/검증/해제) production-grade 닫힘. 지적된 **미배선 4 seam(패널→glasso·S_L1→IC join·SECONDARY→re-fit·오케스트레이터)을 weight_cycle.py 로 해소**. 커밋 87655fe/9d70a84/817791d.
> - **다음 의도**: ⛔**라이브 결정루프(run_agents/stock_track) 실주입 = go-live 경계(N-INT, 자율 범위 밖)**. 잔여(go-live 시): (a) judge(weight_card=) 라이브 caller (b) regime_classifier confidence→TemperatureCalibrator→belief 공급 배선 (c) 정적 Investment Clock 표(regime_to_weights)→동적 비중 경로 병합/교체. Phase II 학습 depth(open-ended regime 발견·수치 S' 계산)=별 세션.
> - **동기화 필요**: btn-button R15 T2(7543463: RegimeGlasso/effective_precision→Ω_eff/TemperatureCalibrator→belief/ic_power_gate 계약)·btn-Inv weight_panel(PIT+반사성 게이트) 수신·정합 wire·양세션 회신 완료. long-mode ON(cap500k) 압축시 원복.

> [ckpt-202605300010-F:btn-Codlearn] **★core/assume spine 완성 + closed-loop GATE 통과 (P2·P3 ✅).**
> - **마지막 결정**: core/assume 7모듈 전부 구현·self-test PASS — registry(6/6)·validator(6/6 elond기본+축A영속+incident skip)·judge(8/8)·dag(6/6 hard/soft·grace/lazy·churn escalate·base cutover)·update_controller(6/6 ★retract 판별 e_value→effect/hard_falsifier 교정: 엔진 e_value 가 p-floor서 saturate라 판별력 0 이던 결함 probe로 발견·수정)·derivation(5/5 순수·PIT frozen·scope계층)·orphan_guard(4/4 netting·token-bucket·decay). **closed-loop GATE** `tests/assume/test_closed_loop_3domain.py` 8/8 — 3도메인 6스텝 + PIT replay + gridlock-free + reflexivity 3종(frozen control book·off-policy log·per-domain 격리). 회귀 0(structure+assume 47/47). e-allocation property=btn-button test_eprocess_backbone_properties.py 가 이미 커버(중복 회피). btn-button engine·btn-Inv substrate 계약 양방향 락.
> - **다음 의도**: (a) **14행 전수 확인** — button(R1/R2/R4)·inv(R8/R11/R12) 담당행 실제 self-test 증거 수집 후 통합 완료 선언 (현재 codlearn spine 행만 검증). (b) Phase II(학습 depth — open-ended regime 발견·수치 S' 계산·실 cheapness_z archetype dispatch)=별 세션. (c) P4 실거래 wiring=Q1 모의API outcome→shadow→live 사람게이트.
> - **동기화 필요**: btn-button "R4/R5 robustness v2 완료"(e-value backbone·graph e-allocation·spec sentinel·decay·V&V) + btn-Inv "데이터·PIT·안전 v2 16모듈 0 FAIL" 수신·계약 확인 완료. core/assume 는 둘 다 위에 얹힘(engine wrap + substrate duck-type). long-mode ON(cap500k) — 압축시 원복.

> [ckpt-202605292330-E:btn-Codlearn] **core/assume 구현 착수 — card_contract 랜딩(차단해제), registry.py ✅완료(self-test 6/6).**
> (1) 마지막 결정: 워커 산출 전부 랜딩 확인(btn-button: card_contract·assumption_validation_engine·hierarchical_fdr·regime_discovery·correction_loop·macro_assumption_card·commodity / btn-Inv: event_ledger·data_contract·lineage·instrument_source·universe_membership·identity·calendar·fx). card_contract.AssumptionCardLike(Protocol)+BaseAssumptionFields(frozen)+assert_falsifiable = 내 설계 가정과 정확 일치. **`core/assume/registry.py` 구현완료**: AssumptionRegistry(register/transition/retire/get(PIT as_of)/get_version(replay)/active/dependents(ATMS 역색인) + lifecycle event_sink[btn-Inv event_ledger 배선점]). self-test 6/6 PASS(PIT 버전전환 S→S'·retire PIT·반증불가게이트·중복거부·lifecycle emit). judge.py 는 기구현(self-test 8/8, fail-safe).
> (2) 다음 의도(구현 순서): ① `validator.py` = assumption_validation_engine.AssumptionValidationEngine.validate wrap + ★per-domain alpha-wealth 격리(card.domain 키) + data_contract incident skip + RulePerformance 영속(축A). ② `update_controller.py` = ★adopt/retract 비대칭 gate(retract=hard-falsifier disjunctive fast / adopt=hysteresis_and_gate conjunctive slow) + base-layer→HumanApprovalGate(regime_discovery) + transition→dag.invalidate. ③ `derivation.py` = 가정→{value,band,provenance} 순수함수 + event_ledger state projection(3 timestamp tt/dt/vt) + PIT replay(get_version+frozen-fixture L2/L3). ④ `dag.py` = cross-asset edge(거시→하위) + grace/lazy + hard/soft mode + BaseLayerCutover(shadow/canary) + hierarchical FDR gate(parent macro). ⑤ `orphan_guard.py` = token-bucket+도메인 netting + decay/half-life. ⑥ ★e-allocation(graph-structured online e-process) + property test(btn-Inv 가 내 영역으로 지정). ⑦ closed-loop GATE(3도메인 + sequestered control stream + adversarial PIT replay).
> (3) 동기화 필요: btn-Inv ledger reducer = reorder-invariant + dt/vt-cut watermark 조상 e-state read 계약 보장(replay 순서불변), e-증분 ℓ_t=(dt,vt) 키 → as-of 누적=dt≤cut 곱. btn-Inv P3 closed-loop 6/6 PASS·P4 진행. btn-button v2 완료. 설계 SSOT = DESIGN-codlearn-v2.md §1~11 + CONSULT-DECISIONS-whole-20260529.md(5R). raw=.consult-whole-R{1..5}-prompt.txt.
> (4) ★validator.py wiring 확정(grep 확인): btn-button 이 R4/R5 보강을 engine 에 **이미 구현** — `core/structure/assumption_validation_engine.py`: `AssumptionValidationEngine(alpha_by_domain, use_eprocess=True, power_floor=0.5, cascade=HierarchicalFDRCascade, fdr_backbone='lord'|'elond')`. stream key=`(domain, assumption_id)`(자산클래스 격리 완료), `_eprocess`(EProcessSpender, per-domain decay via DOMAIN_ESTIMATION_POLICY), `_elond`(ELOND e값 online FDR), HierarchicalFDRCascade(부모게이트). `validate(card, *, regime_ids, current_regime, realized=None, predictions=None, ...) -> ValidationVerdict(assumption_id, domain, kind, holds_now, confidence_now, p_value, alpha_t, fdr_significant, ...)`. → **내 validator.py = 얇은 wrap**: (a) engine.validate dispatch (b) data_contract incident → validate skip(측정깨짐≠가정틀림) (c) RulePerformance.log(축A 영속, ledger.py: log(rule_version, regime_id, sector, regime_model_version, ic, n)) (d) fdr_backbone='elond' 기본 권장(임의의존 robust). 다음 턴 validator.py 부터 plug-and-play.

> [ckpt-202605292xxx-D:btn-Codlearn] **전체구조 5R 자문 ✅practical saturation — 워커 둘 다 빌드 대량완료, 통합 임박.**
> (1) 마지막 결정: 사용자 "안나올때까지 돌려봐" → gemini+claude 병렬 **5R 완주**(R1 결함→R2 횡단면해소→R3 시간축 식별→R4 시간축[e-process/graph e-allocation]→R5 프레임밖[내생성·null·meta·decay]). **R5 양모델 practical saturation 선언**(잔여=V&V 코드정합 property test·인프라 DR=모델 밖 엔지니어링, 정지규칙=ROI 기반). 전문=`CONSULT-DECISIONS-whole-20260529.md`. judge.py fail 방향 역전(안전버그)→manifest fail-safe 재정정(self-test 8/8). 핵심 신규: e-process backbone(임의의존 robust)·graph-structured online e-allocation(2D 다중성)·spec sentinel(wrong-H0)·shadow→live e-gated ramp(fill 내생성)·sequester(Thresholdout/DP+forward-time).
> (2) 다음 의도: 워커 보강 전달완료(btn-button=e-process backbone/spec sentinel/decay detector, btn-Inv=ramp 프로토콜/V&V property test). **워커 산출 통합 착수** — btn-button v2 빌드완료(BB-1~5+V7), btn-Inv ledger 본체 빌드완료(12-event+3ts+CQRS 반영)+crypto closed-loop 진입. card_contract 랜딩 확인 후 내 core/assume(registry/validator/update_controller/derivation/dag/orphan) 구현.
> (3) 동기화 필요: dumb circuit breaker·V&V property test 소유 경계 조율. closed-loop GATE 에 sequestered control stream+online e-process+adversarial PIT replay 편입. raw=.consult-whole-R{1..5}-prompt.txt + .gemini-web-last.md/.claude-web-basic-last.md.

> [ckpt-202605292xxx-B:btn-Codlearn] **압축복귀 후 — 내 슬라이스 설계 완료, 자문 보류, 워커 랜딩 대기.**
> (1) 마지막 결정: 압축 직후 long-mode ON 으로 spurious critical 해제(재압축 회피). 내 CL 슬라이스 설계 `DESIGN-codlearn-v2.md` 완료 — 전 wire 표면 실재 시그니처 확정(L1 `l1_verdict`·DCF `value_stock.valuation_gap`·cheapness_z regime-σ·L3 `RagPitPipeline.query_similar(as_of)`·ledger frozen/counterfactual·as_of resolver=내SSOT·card_contract=btn-button). judge 경계 = gemini R1(L1 veto floor / L2·L3 confirm-on-pass / DCF dual-gate 병렬 / grace+lazy cascade방어) 채택. claude-web R1 프롬프트 작성완료(`.consult-codlearn-R1-prompt.txt`).
> (2) 다음 의도: ⚠️사용자 지시 — 자문 발사 보류(채널 타세션 점유), 다른 작업 진행. 코드는 card_contract(btn-button) 랜딩 후 착수, judge.py 만 선구현 가능(card_contract-무관). 워커 보고 도착 시 통합.
> (3) 동기화 필요: 자문채널 비면 claude-web R1 발사→≤5R 수렴→DESIGN §3·§4 확정. btn-Inv v2 진행 확인. card_contract/validation_engine 랜딩 = 내 core/assume 구현 트리거.

> [ckpt-202605292xxx:btn-Codlearn] **가정 라이프사이클 v2 — 설계+분배 완료, 분배 직전.**
> (1) 마지막 결정: 사용자 재작업 사유 = 직전 FINDINGS 후 부분구현 누락. 본 progress 에 요청14→구현 추적 GATE + 6축×3도메인 18셀 GATE 박음. 통합 method 확정 = 거시 `indicator_event_correlation` 6 decoupling case 패턴이 template, 주식(공정전환기 PER)·상품(공급과잉 COT) 동형. 거시모듈 실재하나 live 미연결+정적. 6축 = A학습 B기준화 C주입 D검증 E변경 F거버넌스. 코드맵: 주식~70%(엔진+shadow), 거시~40%(고정-K, decoupling 정적), 상품~5%(전무), core/assume=0%. Q1실거래 Q2동순위 Q3둘다 Q4판정전부.
> (2) 다음 의도: 3 세션 분배 dispatch (psmux-send.sh) — btn-Inv(데이터·lineage·실거래 R11/R12·상품데이터), btn-button(거시 R1/R2·D1 bnpy·상품검증 R4), btn-Codlearn(core/assume 오케스트레이션·판정 R6/R7·통합). 각 ≤5R 자문+보완→보고. 최종통합=나.
> (3) 동기화 필요: btn-button cwd=D:\projects\button → 먼저 cd /d D:\projects\Inv. 자문 raw=.consult-{sess}-Rn.txt. 통합 method=plan §3.5. dispatch 메시지에 plan+progress+이 GATE 포인터 동봉.
