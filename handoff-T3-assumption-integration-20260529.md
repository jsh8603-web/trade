---
tags: [type/handoff, domain/inv, phase/II, track/T3, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-phase2-T3.md
progress: ./progress-phase2-T3.md
consult: [.consult-R1-claude.txt, .consult-R1-gemini.txt]
inputs: [handoff-T1-assumption-20260529.md, DESIGN-T1-assumption-data.md, DESIGN-T2-assumption-stats.md]
note: 가정(Assumption) 라이프사이클 T3 통합 인계. T1·T2 완료, T3 통합 미착수. 다음 세션 동등 재개용.
---

# 핸드오프 — 가정(Assumption) 라이프사이클 T3 통합

## 0. 현황 한 줄
사용자가 한참 논의했으나 findings·자문·코드에 통째 빠진 축 = **가정 라이프사이클**(산업/자산별 가정 표 → 데이터로 주기 검증 → seed 기준 도출 → 틀리면 변경[잦으면 X, 누적데이터 근거] → 변경 시 의존 가정 재평가). scope = **거시/주식/상품(ETF·원자재) 3 도메인 전부**. 기존 rule/signal 레이어(S0~S13) **위에** 얹는 상류 레이어.
- T1(btn-Inv) ✅ 완료 (데이터·PIT) / T2(btn-button) ✅ 완료 (검증·변경통계) / **T3(나) = 통합 미착수**.
- ⚠️ 사용자 불만 "코드 일부만 만들고 끝 금지" → T1·T2 둘 다 prior art 실조사+설계+동작테스트 충족 확인.

## 1. T1 산출물 ✅ (데이터·PIT)
파일: `RESEARCH-T1-assumption-data-20260529.md` · `DESIGN-T1-assumption-data.md` · `handoff-T1-assumption-20260529.md`
- prior art 실조사: **Pandera(MIT) 채택**(data_contract 게이트 본체) / GE·Deequ·Marquez 기각 / **OpenLineage 스펙만 차용**(서버없이 jsonl) / **onlineFDR Python 포트 부재 → 논문 직접구현** / 통합 OSS 부재 확정.
- 설계: `core/data/data_contract.py`(Pandera, pit_query **앞단** 게이트 — 계약위반=측정 incident, 가정검증과 분리) + 3도메인 검증패널(**생존편향=상폐종목·만기소멸 선물·청산 ETF 포함**) + `core/data/lineage.py`(OpenLineage jsonl, derived_from provenance) + `core/data/online_fdr.py` 상태영속(LORD++/SAFFRON alpha-wealth) + **knowable_from 합성규칙**(도출물 ≥ max(입력 knowable_from)+계산지연, lookahead 차단).
- ★ **T1↔T3 계약**: T3 가 `assumption_store.is_active(id, ver, as_of) -> bool` 제공해야 함 (referential PIT 검사용 — 활성 seed의 derived_from 이 그 as_of 활성 가정 가리키는지).
- 신규 의존: **Pandera 1개만**.
- ⚠️ 미해결: **상품(commodity) 무료 데이터소스 = 미조사** (N-T1-COMMODITY-SRC, 확신<80%). Gemini Phase2 또는 자문 1회 추가 권장.

## 2. T2 산출물 ✅ (검증·변경통계)
파일: `RESEARCH-T2-assumption-stats-20260529.md` · `DESIGN-T2-assumption-stats.md` · 코드 `core/structure/{detectors,online_fdr,assumption_stats}.py` (**self-test 25/25 PASS, 스텁 아님**).
- 설계: 검증 3층(조기경보 CUSUM/SPRT + 지속 prequential + 누적 posterior) / **구조 vs 모수 dispatch**(structural=메커니즘=regime detection, parametric=모수=change-point) / **regime-conditional**(pooled 금지) / online FDR(LORD++/SAFFRON, batch BH와 분리) / 변경 hysteresis **AND-gate**(online-FDR ∧ 효과크기 ∧ dwell-time ∧ K-윈도우 ∧ regime).
- ★ **T2↔T3 계약** (T3 가 호출):
  ```python
  validate_assumption(card, evidence, cfg=StatsConfig())
      -> ValidationReport(holds, holds_prob, alarm, slope, n_obs, regime_id, detail)
  should_change_assumption(card, history, cfg)   # history = ValidationReport 누적 list
      -> ChangeDecision(should_change, reasons[], blocked_by[])
  confidence_to_band(holds_prob, base_value, cfg) -> (lo, hi)   # 신뢰도→사이징
  ```
  - **AssumptionCardLike Protocol** (T3 의 AssumptionCard 가 충족해야): `.assumption_id .kind .scope .regime_id .params`
  - enums: `AssumptionKind`, `AssumptionDomain`. validator: `StructuralValidator`/`ParametricValidator`/`_RegimeConditionalValidator`.
  - detectors: CUSUM/SPRT/BOCPD-lite/prequential + rule_observer PSI/PageHinkley re-export(공유 추출 완료).

## 3. ★ T3 구현 (미착수 — 7요소, S14~S20)
다음 세션 진입점. 전부 `model: opus`(설계 판단 포함). self-test fixture 통과 후 [x].
- **S14** `core/assume/assumption.py` — `AssumptionCard`(frozen pydantic, **AssumptionCardLike 충족**: assumption_id/kind/scope/regime_id/params + 추가: condition/value/confidence_band/rationale/source/**falsification_metric**(gemini 의무: kill_condition 없으면 진입금지)/status(active/under_review/rejected/dormant)/effective_from/knowable_from/**depends_on[]**/**half_life**(decay)).
- **S15** `core/assume/assumption_store.py` — bitemporal_store.py **라이브러리 재사용**(별도 스트림). publish/invalidate/rollback/as_of_query + ★**is_active(id,ver,as_of)->bool**(T1 계약) + online_fdr alpha_wealth 영속 연결.
- **S16** `core/assume/validator.py` — T2 `validate_assumption` wrap, regime-conditional, **T1 data_contract 게이트를 validator 앞단**에(계약위반=측정 incident → 검증 skip). 누적 ValidationLedger.
- **S17** `core/assume/update_controller.py` — T2 `should_change_assumption`(AND-gate) + **consensus 재사용**(object type 파라미터화, fork 금지, caps 더 빡세게) + **의존전파**(무효화[재계산 X]+epoch topological single-pass+**DAG 비순환 write-time 강제**+ATMS nogood 충돌) + graph rate-limit(depth/fan-out 초과 → 사람 에스컬레이션).
- **S18** derivation seam — `core/assume/derivation.py`: `f({assumption_refs}) -> DerivedParameterSet{value, confidence_band, provenance[{assumption_id,version,derivation_fn_version}]}`(**다대다=bipartite**). `seed_builder.Signal` 에 **optional `derived_from`** 추가(없으면 기존과 100% 동일 = additive). knowable_from 합성(T1 규칙).
- **S19** orphaned position 정책 — 가정 기각 → 의존 open position **review/managed-exit 플래그**(조용히 보유 금지, emergency_stop 연결). 불변식① rule_version 고정은 유지하되 thesis 증발 포지션 표시. **실거래 안전요건**.
- **S20** `config/assumptions/{macro,equity,commodity}.yaml` — 3도메인 가정 표(거시 레짐-지표, 주식 섹터 valuation 상수·반도체 PER 착시, 상품 spread/계절성/재고) + 통합 self-test(가정→검증→변경→derivation→seed 닫힌 루프).
- d4_book IndustryCharCard(서사, 반증불가→L2 soft) vs AssumptionCard(정량, 반증가능→L1 floor) **분리 유지**. 서사가 정량화되면 학습 축 통해 AssumptionCard 로 승격.

## 4. 자문 핵심 (원문 `.consult-R1-{claude,gemini}.txt` — 다음 세션 정독)
- 4축 = "거버넌스 하의 belief revision" = ATMS(de Kleer 1987) + SR 11-7(champion-challenger) + online FDR.
- TOP3: (1)online FDR (2)orphaned position 정책 (3)regime 모델을 base-layer 가정 승격(자동변경 금지·사람소유 = 발산 막는 고정점).
- 빠진 축: 측정깨짐vs가정틀림 분리(T1 data_contract 완료) / 신뢰도→사이징(T2 confidence_to_band 완료) / 가정 decay(half_life=S14) / nogood 충돌(S17).
- ⚠️ regime 모델 base-layer 승격은 T2 미수렴 경계(regime_id 순환, plan §6)와 연결 — 통합 시 흡수.

## 5. 기존 T3 잔여 (가정 레이어와 별개, 먼저/나중 무관)
- **INT**: as_of wire(`core/data/pit_query.py:set_as_of_resolver` ← `core/pit/as_of.py:resolve_as_of`) + kill_switch→execute_trade + RuleProvider shadow + run_agents.py:873 INV_CORE_GATE. ⚠️StockTrack 미가동=shadow까지.
- **VERIFY**: 전 모듈 `PYTHONIOENCODING=utf-8 PY -m core.X` 일괄.
- **REVIEW**: opus 1M subagent 축별 (`handoff-T3-impl-20260529.md` §2 rubric R-A~R-G+R-SEED). ★ 이제 R-SEED 에 **가정 레이어(S14~S20) 완전성**도 평가축 추가.

## 6. 환경·재개
- python: `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (pandas/numpy/statsmodels/pydantic OK). **Pandera 신규 설치 필요**(T1 의존).
- psmux: `PSMUX_BIN=/c/Users/jsh86/AppData/Local/Microsoft/WinGet/Packages/marlocarlo.psmux_Microsoft.Winget.Source_8wekyb3d8bbwe/psmux.exe`. 세션 = btn-Inv(T1)/btn-button(T2)/btn-Codlearn(나).
- 재개 순서: 이 핸드오프 → DESIGN-T1·DESIGN-T2 정독 → S14 부터 구현(또는 INT/VERIFY 먼저). plan §7·progress S14~ 는 다음 세션이 이 핸드오프 기반 반영.
- runner.js 수정됨(claude.ai/code networkidle→domcontentloaded, claude-web-code 자문 재가동 가능).
