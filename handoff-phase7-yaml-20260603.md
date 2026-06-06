---
tags: [type/handoff, domain/inv, scope/equity-phase7, session/btn-Codlearn]
date: 2026-06-03
next-action: "study_session.yaml 7블록 작성 — eq_kr(7산업) + eq_us(3 sleeve)"
---

# Handoff — Phase 7 supervisor 통합 yaml (2026-06-03)

## 1. 현재 상태 + 첫 행동

10개 summary.yaml 전부 읽기 완료 (btn-button 2877ea0 반영). 다음 세션은 바로 yaml 작성 착수.

**첫 행동**: `study-research/eq_kr/study_session.yaml` + `study-research/eq_us/study_session.yaml` 7블록 작성.

## 2. 10개 산업 요약 (primary indicator + key cross β)

### eq_kr (한국 7산업)

| industry | archetype | primary_indicator | ic_mean | verdict | key_cross_β |
|---|---|---|---|---|---|
| kr_battery | cyclical | cs_mom_6m | +0.086 | PARTIAL | credit -0.164*, oil +0.248* |
| kr_semiconductor | cyclical | cs_pbr_z_24m | -0.114 | PARTIAL | credit -0.190* |
| kr_auto | cyclical | cs_pbr_z_24m | -0.463 (haircut→-0.12~-0.20) | PARTIAL | all β 비유의 |
| kr_financial | spread_driven | cs_mom_6m_rate_up | +0.102 (rate_up only) | TENTATIVE | rate β n/s (level vs regime 분리) |
| kr_consumer | asset_stable | cs_per_z_24m / cs_per_z_3m | -0.141 / -0.077 | TENTATIVE | dollar -1.19* |
| kr_bio | event_driven | cs_lowvol | -0.078 | PARTIAL | VIX +0.011*** |
| kr_telecom | asset_stable | cs_pbr_z_24m | -0.542 (haircut→-0.14~-0.22) | PARTIAL | all β 비유의 (n=13 협소) |

### eq_us (미국 3 sleeve)

| industry | archetype | primary_indicator | ic_mean | verdict | key_cross_β |
|---|---|---|---|---|---|
| us_cyclical | cyclical | cs_per_z_24m | -0.119 | TENTATIVE | hy_oas -0.093***, rate -0.039*, vix -0.003* |
| us_defensive | asset_stable | cs_rev_1m + cs_lowvol | -0.045 / +0.076 | PARTIAL | real_rate -0.171*** |
| us_mega_tech | compounder | cs_lowvol | +0.241 (breadth-IR 2.56) | PARTIAL | VIX -0.008** |

## 3. L축 직교화 분석 (common factor 중복 목록)

Phase 7 supervisor yaml에서 다음 공통 인자를 1회만 계상해야 함:

### eq_kr L축
- **credit (US HY OAS proxy)**: battery(-0.164) + semi(-0.190) = 유의 중복. supervisor 공통인자로 1회.
- **dollar (DTWEXBGS)**: consumer(-1.19 유의). battery/semi 비유의 → consumer 단독.
- **VIX**: bio(+0.011***) 단독. battery/semi 비유의.
- **rate (금리 level)**: financial regime-conditional. level β는 전 산업 비유의 → regime-conditional 채널이 primary.
- → **eq_kr L축 = {credit, dollar, VIX, rate_regime}** (4인자)

### eq_us L축
- **real_rate (DFII10)**: defensive(-0.171***) 강. mega_tech 약(-0.030 비유의).
- **hy_oas**: cyclical(-0.093***). defensive(비유의).
- **VIX**: mega_tech(-0.008**). cyclical(-0.003*). defensive(비유의).
- **dollar**: 전부 비유의.
- → **eq_us L축 = {real_rate, hy_oas, vix}** (3인자)

## 4. Phase 7 yaml 7블록 구조 (작성 가이드)

### study_session.yaml 구조
```yaml
# ── 블록1 LENS: 자산군 단위 정성 (eq_kr / eq_us) ──
lens:
  scope: "eq_kr 7산업 supervisor 통합"
  L_axis: [credit, dollar, vix, rate_regime]  # eq_kr 공통인자
  derive_weights_note: "w∝Θ_signal·IC, regime/archetype-conditional. Σ_signal ≠ Σ_return."
  cross_routing: "RegimeGlasso→Σ_return / DY throttle / customer→alpha"

# ── 블록2 INDICATORS: 10개 산업 primary indicator 집약 ──
indicators:
  - {industry: kr_battery,      id: cs_mom_6m,          family: momentum, horizon: 12M_mom, ic_mean: 0.086, verdict: PARTIAL}
  - {industry: kr_semiconductor, id: cs_pbr_z_24m,       family: value,    horizon: 24M_value, ic_mean: -0.114, verdict: PARTIAL}
  # ...

# ── 블록3 RELATIONSHIPS: L축 공통인자 + regime 경로 ──
relationships:
  L_axis_credit:  {node_a: credit, affects: [kr_battery, kr_semiconductor], mechanism: risk-off 공통노출}
  L_axis_dollar:  {node_a: dollar, affects: [kr_consumer], mechanism: 수입원가/내수}
  # ...

# ── 블록4 WEIGHT_RULES: derive_weights 입력 ──
weight_rules:
  - industry: kr_battery
    base_weight_range: [0.06, 0.13]
    regime_modulate: true
    archetype: cyclical

# ── 블록5 CONFIDENCE_HOOKS: FHC e-process 연결 ──
confidence_hooks:
  - industry: kr_battery
    hook_id: battery_cs_momentum_persistence
    affects_indicator: cs_mom_6m
    # (summary.yaml 의 confidence_hooks 직접 참조)

# ── 블록6 COLLECTOR_PLAN: 공통 우선순위 ──
collector_plan:
  - gap: "HY OAS 장기 시계열(BAMLH0A0HYM2 2023~만 → BBB-AAA spread proxy 대안)"
    priority: high
  - gap: "PIT universe 멤버십 (전 산업 공통)"
    priority: high

# ── 블록7 CODE_CHANGE_PLAN: 배선 TODO ──
code_change_plan:
  - "study_register.wire_falsification() → 산업별 FHC confidence_hook 연결"
  - "derive_weights 에 archetype·regime conditional IC 적용"
  - "RegimeGlasso common_factor_exposure β 입력 (산업별 cross β 통합)"
```

## 5. PSD 게이트 (10×10 공분산)

```
eq_kr (7×7): [battery, semi, auto, financial, consumer, bio, telecom]
eq_us (3×3): [cyclical, defensive, mega_tech]
합산 (10×10): 블록 대각 + off-diagonal RegimeGlasso Ω 추정
```
PSD 확인: `np.linalg.eigvalsh(Σ_signal)` → 최소 고유값 ≥ 0.

## 6. 파일 경로

- 입력: `study-research/eq_kr/industries/*/summary.yaml` (7개)
- 입력: `study-research/eq_us/industries/*/summary.yaml` (3개)
- 산출: `study-research/eq_kr/study_session.yaml`
- 산출: `study-research/eq_us/study_session.yaml`
- 참조: `study-research/frame-v3-draft-industry-dispatch-20260603.md` (§M 전체)
- 참조: `core/structure/archetype.py` (5종 archetype 정의)
- 참조: `study-research/_wire/indicator-ledger.md`

## 7. 제약

- ⛔ push 금지
- ⛔ go-live = 사람 게이트
- 승인게이트: Phase 7 완성 후 사용자 보고 → 검토 → 승인
