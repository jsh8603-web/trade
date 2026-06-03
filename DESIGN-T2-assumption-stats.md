---
tags: [type/design, domain/inv, phase/II, track/T2, topic/assumption-lifecycle]
date: 2026-05-29
session: btn-button
research: ./RESEARCH-T2-assumption-stats-20260529.md
task: ./TASK-T2-assumption-research-20260529.md
---

# DESIGN-T2 — 가정 검증·변경 통계 + regime-conditional (코드레벨)

> T2 도메인 = 검증통계·regime·구조모델. T3(btn-Codlearn) = AssumptionCard/Registry/Validator/UpdateController orchestration + derivation seam + orphaned position 안전.
> 본 설계는 T2 가 **구현 완료**한 통계 엔진(file:function 명시)과 T3 가 호출할 **계약**을 고정한다.

## 0. 레이어 아키텍처 (claude D — 엄격 하향 의존, 단일 seam)

```
L_assume   AssumptionCard / Registry / Validator / Ledger / UpdateController / DAG   [T3 owns]
   │ (단 하나의 seam: 버전드 derivation fn + provenance ref — 위로 부르는 호출 금지)
   ▼
L_derive   순수함수 f:{assumption_refs}→DerivedParameterSet{value, band, provenance[]}  [T3 seam, T2 band 산출]
   ▼
L_signal   seed / signal / rule (기구현, 그대로)                                          [기존]
   ▼
L1/L2/L3 · ledger · kill_switch (불변)
```
- validator 는 ledger 를 **구독**(rule/seed 내부 안 읽음, 결과만). 가정레이어가 기존 analysis-ledger 를 evidence source 로 구독 → rule 코드에 새 훅 0 (claude D-3).
- T2 의 통계 엔진은 **관측·산출만**(결정 X) — rule_observer 의 "관측≠제어" 원칙 동형.

## 1. AssumptionCard 스키마 (검증 관련 필드 — T2 규정분, 전체 Card 는 T3)
discriminated union 후보(archetype.py 패턴 재사용). T2 가 검증에 필요로 하는 필드:
```
AssumptionCard(
  id: str, version: str,
  kind: Literal["structural","parametric"],          # ★ validator dispatch 키 (claude A-0)
  scope: Literal["global","sector","asset","macro"],  # 충돌해소 우선순위 (asset>sector>global=floor)
  domain: Literal["macro","equity","commodity"],      # 3 도메인 (TASK §2-B 5)
  statement: str, rationale: str,
  falsification_metric: str,                          # ★ kill condition 의무 (gemini C-1) — 반증불가 = 진입금지
  depends_on: list[str],                              # DAG (T3, 무효화 전파)
  is_base_layer: bool = False,                        # ★ regime 모델 등 = 자동변경 금지 (claude C-meta)
  half_life: Optional[float] = None,                  # decay/반사성 (claude C-반사성)
  posterior_confidence: float, band_halfwidth: float, # 신뢰도→사이징 (claude C / gemini C-2)
  valid_from: date, regime_model_version: str,        # 시변 + regime 정의 버전 (재현성)
)
```
- ★ **AssumptionCard ≠ IndustryCharCard** (claude D-★): 후자=반증불가 정성맥락→L2 soft 전용·threshold 도출 금지. 전자=반증가능 정량→threshold 도출→L1 floor. 한 카드가 둘일 수 없음.

## 2. kind dispatch validator [구현 완료 — `core/structure/assumption_stats.py`]
- `validate_parametric(assumption_id, assumed_value, realized, regime_ids, current_regime, sd=None, psi_threshold=0.25) -> RegimeConditionalReport`
  - 모수가정("정상 멀티플=[12,18]", "임계값=θ") → 추정 안정성. 레짐별 `Cusum`(평균이동) + `psi`(분포이동) + Cohen's d.
- `validate_structural(assumption_id, predictions, outcomes, regime_ids, current_regime) -> RegimeConditionalReport`
  - 구조가정("PER 은 공정주기를 탄다") → 메커니즘 작동성. 레짐별 `prequential_loss` kink + `Bocpd` run-length 붕괴. **멀티플 수준 설명력**(estimand 분리, forward return 아님).
- T3 Validator 는 `card.kind` 로 둘 중 하나에 dispatch (archetype dispatch 동형).

## 3. regime-conditional ValidationReport [구현 완료]
- `RegimeConditionalReport.by_regime: dict[regime_id, RegimeHolds]` — ★ **pooled 금지**(claude A-1 핵심 누락). 레짐 A 참·B 거짓 조건부 가정 오판 방지.
- `.holds_now` = **현재 regime 의 holds 만** 거래 판정에 사용. `.confidence_now` = 현재 regime 신뢰도.
- `RegimeHolds(regime_id, holds, n_obs, confidence, evidence)` — evidence = detector 출력(감사용).
- regime 입력 = `core/regime/pit_regime.py` (regime_model_version 태깅) 또는 `core/brain/regime_classifier.py`(JumpModel) adapt.
- **생존편향**: 검증 패널은 panel_schema 의 delist_flag 포함 모집단 그대로 신뢰(필터 안 함). as-of 당시 살아있던 전체(상폐 포함, 양 자문).

## 4. change-point 통합 — 공유 detectors [구현 완료 — `core/structure/detectors.py`]
- `psi`, `near_zero_mass`, `PageHinkley` = `rule_observer` 에서 **re-export**(SSOT 1곳, claude D-6 중복제거). 양쪽 import, 대상만 다름(가정 예측량 vs rule divergence).
- 추가: `Cusum`(±k_sigma/h_sigma), `Sprt`(H0/H1 LLR), `Bocpd`(run-length MAP 붕괴 = 실신호), `prequential_loss`(비율 2배+outcome분산 floor kink).
- ⚠️ CUSUM k=0.5σ 노이즈 발화 = **AND-gate 필요성 근거**(단독 detector 신뢰 금지).

## 5. hysteresis AND-gate [구현 완료]
- `hysteresis_and_gate(fdr_significant, effect_size, effect_threshold=0.5, dwell_ok, k_window_persist, k_window_required=2, same_regime, is_base_layer=False) -> AndGateResult`
- 승격 = **5조건 AND**: online-FDR 유의 ∧ 효과 material(Cohen's d>0.5) ∧ dwell-time ∧ K-윈도우 지속 ∧ 동일 regime.
- `is_base_layer=True` → **항상 차단**(사람 비준, C-meta). `AndGateResult.conditions` = 각 조건 pass/fail = 감사가능 **변경 사유서**.
- **online-FDR** = `online_fdr.LordPlusPlus` (T3 UpdateController 가 가정별 스트림 보유, p-value→reject 산출해 `fdr_significant` 주입). 부활은 `AlphaInvesting` wealth 고갈로 차단.
- consensus.py 재사용: `ProposerChallengerArbiter`/`cap_change`/`detect_change_trigger`(regime-aware) 를 **객체타입 파라미터화**(fork 금지). 가정 변경 caps 더 빡세게(dwell↑, FDR 엄격).

## 6. base-layer regime 가정 (claude C-meta)
- regime 모델 = `is_base_layer=True` AssumptionCard. 모든 조건부 가정의 토대 → 자동변경 금지·사람 소유·더 보수적.
- regime_model_version 변경 = cheapness_z σ 재현성 직결(`structure_model` regime별 σ) → 반드시 사람 비준 + 의존 가정 전체 재검증 epoch.

## 7. 신뢰도 → band → 사이징 [구현 완료]
- `confidence_to_band(point, confidence, base_halfwidth) -> (lo,hi)` — 신뢰도 낮을수록 넓은 band.
- `band_to_size_multiplier(band_halfwidth, ref_halfwidth, abstain_ratio=3.0) -> float` — 넓으면 작은 포지션, 너무 넓으면 abstain(0).
- `assumption_confidence(n_obs, effect_size) -> 0..1` (gemini C-2). cheapness_z band 상속 = `structure_model` 의 σ_resid·regime σ 를 band 로 전파 → L1/Portfolio Optimizer 사이징 페널티.

## 8. 3 도메인 확장 (TASK §2-B 5)
- **equity**: 반도체 PER 착시(cyclical, structure_model T2-7 GO 입증) / 화학·철강(cyclical) / 바이오(event_driven). 기구현 archetype 재사용.
- **commodity**: spread_driven(롤수익률·캐리) / 계절성(난방유·곡물) / 재고기반 — **신규 archetype/검증 경로**. archetype.py 에 `commodity_carry`/`seasonal` 추가 + parametric 가정(캐리 정상범위)·structural 가정(계절 패턴 작동).
- **macro**: 레짐 정의·전이 = base-layer 가정. regime_classifier + pit_regime.

## 9. 의존 전파 (ATMS 무효화, claude A-3) [T3 도메인, T2 계약]
- A 변경 → B 값 재계산 X, B validation **stale 마킹** → B validator 를 **데이터에 대해** 재실행(fixed point=데이터, 대수루프 차단).
- epoch topological single-pass: 무효화 위상순 1회, 재검증이 또 ChangeRequest 낳으면 다음 epoch 큐. graph-level rate-limit 초과 = 사람 에스컬레이션(레짐붕괴 신호, kill_switch 철학).
- T2 계약: validator 는 stateless 재검증 함수 — T3 가 stale 마킹 후 데이터 주입해 호출하면 동일 결과(idempotent).

## 10. 산출 파일 (T2 구현 완료)
- `core/structure/detectors.py` (CUSUM/SPRT/BOCPD/prequential + PSI/PH re-export)
- `core/structure/online_fdr.py` (LORD++/alpha-investing)
- `core/structure/assumption_stats.py` (kind dispatch + regime-conditional + AND-gate + band)
- `tests/structure/test_assumption_stats.py` (12 tests, 전체 25/25 PASS)

## 11. T3 가 wire 할 계약 (분담 경계)
1. AssumptionCard/Registry/Validator: `card.kind` → `validate_parametric`/`validate_structural` dispatch.
2. UpdateController: 가정별 `LordPlusPlus` 스트림 보유 → p-value 산출 → `hysteresis_and_gate(fdr_significant=...)`.
3. orphaned position: AssumptionInvalidated 시 depends_on 역추적 → open position review/managed-exit (emergency_stop 연결).
4. derivation seam: DerivedParameterSet 에 `assumption_stats.confidence_to_band` 결과 band 전파.
5. data contract 게이트(GE/Soda) = validator 앞단(측정 incident 분리).
