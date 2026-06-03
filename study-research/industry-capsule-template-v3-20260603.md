---
tags: [type/capsule-template, domain/inv, scope/equity-industry-dispatch]
date: 2026-06-03
purpose: 산업 subagent 가 채울 summary.yaml 템플릿 v3 — coin 측정 15종(주식 적용 14) + 15축 audit + 6단계 반영. battery(측정방법론 정립 이전 구버전) 대체. study_register/derive_weights/RegimeGlasso 코드 편입 데이터 충실 제공.
supersedes: eq_kr/industries/battery/summary.yaml (coin 측정방법론 정립 이전 = robustness/cross/horizon 필드 부재)
---

# 산업 capsule 템플릿 v3 — 코드 편입 충실 데이터 양식

> **battery 예시 부적합 사유**: battery summary.yaml 은 coin study(측정 15종 정립) **이전**에 작성 → `robustness_checks`(leave-episode/within-period/net-cost/family) · `common_factor_exposure`(cross) · `horizon_verdict`(forward alpha 부재) 필드가 없다. 본 v3 가 그 gap 을 채운 표준 양식.

---

## §0. coin 측정 방법론 15종 주식 산업 "지킬 수 있는지" 검토 + 기준 (사용자 지시)

> coin 측정 방법론 15종(아래 표 1~15)을 주식 산업에 적용 가능한지 항목별 판정 + 데이터 충실 기준. ✅=그대로 / ⚠️=조정(축소 아님) / ❌=주식 부적합. ⚠️=수치·대상만 바꿔 충실 이행, 빼는 건 ❌(intraday) 1개뿐.

| # | coin 축 | 주식 적용 | 데이터 충실 기준 (코드 편입) |
|---|---|:--:|---|
| 1 | Rank-IC (횡단면 Spearman) | ✅ | 월말 산업 universe z-score(지표)→y_20d. `weight_falsification.rank_ic`. IC 분포(mean±SE)+N+t. |
| 2 | Horizon sweep | ✅ | y_5d/20d/60d/1Q. ★forward alpha 부재 falsifier 의무(§horizon_verdict). |
| 3 | Cross-asset | ⚠️ | 코인=ETH/NDX 재현 → 주식=**섹터 간** 재현(타 섹터 부호 일관). 연관성 지표는 학술 리서치 대기. |
| 4 | Regime 4게이트 G1~G4 | ✅ | G1 ex-ante(달력컷 금지) / G2 ★FDR 우선(주식 약신호) / G3 walk-forward(skfolio CPCV) / G4 Newey-West HAC. |
| 5 | leave-episode | ✅ | 최강 기간 제외 후 생존. single-episode artifact 판별. |
| 6 | within-period | ✅ | 동일 regime 내 sub-split(분기) 부호 일관 ≥50%. |
| 7 | partial-corr | ✅ | 공통원인 통제 후 직교(partial-IC>0.5×marginal). `RegimeGlasso` graphical lasso. |
| 8 | placebo | ✅ | 반증조건 사전 명시(e-CUSUM 붕괴). confidence_hook reject_signal. |
| 9 | effective-N tier | ✅ | autocorr 보정 n_eff: ≥100 Validated / 50-100 Tentative / 30-50 Weak / <30 INSUFFICIENT. |
| 10 | net-cost | ⚠️ | 코인 0.30%/side → ★주식 기관 0.03%/side(미)·0.18-0.23% 거래세(한). net Sharpe≥0.5×gross. |
| 11 | e-process | ✅ | e-CUSUM anytime-valid(e-value≥20 retract). `weight_falsification.score_ic_breakdown_eprocess`. ★결선 완료(이번 세션). |
| 12 | block-bootstrap | ✅ | block=60-90d, B=2000, 95% CI 0 포함→비유의. |
| 13 | within-family neutralize | ✅ | FF5 factor 직교(value/momentum/quality/size). raw IC + neutralized IC 병행. |
| 14 | cross-asset family | ⚠️ | 섹터 공유 factor(VIX/dollar/oil/rate) 노출 → L축 1회 계상. cross 조립=통합 단계. |
| 15 | intraday | ❌ | 코인 1-6h microstructure = 주식 부적합(일중 데이터·체결 구조 다름). 제외. |

**검토 결론**: 측정 15종 중 ✅ 11(그대로) / ⚠️ 3(net-cost·cross·family = 주식 파라미터 조정, 축소 아님) / ❌ 1(intraday만 제외 — 코인 1-6h microstructure, 주식 일중 체결구조 다름+일봉만 수신). **주식 적용 = 14종 충실 이행**(+15축 audit A~P 별도 체계). 데이터 충실 기준 = 각 축이 코드 함수(rank_ic / RegimeGlasso / score_ic_breakdown_eprocess / build_indicator_matrix)에 편입될 형식으로 yaml 필드화.

---

## §1. 6단계(S1~S6) ↔ 산출 매핑

| 단계 | 산출 파일 | 코드 편입 |
|---|---|---|
| S1 학술 ground | theory-notes.md | — |
| S2 측정 4게이트 | validation-*.md | `build_indicator_matrix`(PIT panel) → `rank_ic` |
| S3 외부검토 | round-N.md | — |
| S4 재검증(cross/leave-episode/within/partial/placebo/horizon) | validation 보강 | `RegimeGlasso` partial-corr |
| S5 역공격 수렴 | self-audit | — |
| S6 15축 audit(A~P) | 15axis-audit.md | hard-fail B/C/D/I |

---

## §2. summary.yaml 스키마 v3 (전 필드 + 데이터 출처·측정법·충실 기준)

> ★**FHC 어댑트 (2026-06-03 분담 확정)**: 본 summary.yaml = 거시 FHC **core**(btn-Inv 단일 소유, `.coord-fhc-contract-20260603.md` §2)의 **`scope.type=sector` 한 인스턴스**. ⛔ 별 schema 만들지 말 것 — outcome.metric=**cs_rank_IC** / mediator=섹터 펀더멘털(restatement·compute_delay PIT) / e_process=wire_falsification / state 5-state(minted/confirmed/vacated/rejected/revived) 로 어댑트. **산업 subagent 는 측정 필드만 채우면 됨**(FHC wrapper·bonus·lifecycle 집행은 core + supervisor 몫, core 완성 후 결합). confidence_hooks 의 affects_indicator = FHC outcome leg / ★mediator leg(전제 관찰량, 미성립=vacate≠reject)는 core schema 결합 시 보강.

```yaml
industry: <stock.md 구분 단위>   # 미국=eq_us sleeve/Mag7 T0 / 한국=eq_kr 12산업 中 1
asset_scope: [equity.us | equity.kr]
archetype: cyclical|event_driven|spread_driven|asset_stable|compounder  # ★archetype.py 배정 (DEFAULT_SECTOR_ARCHETYPE)
as_of: "YYYY-MM-DD"

# ── 블록1 LENS (정성) ── frame v2 유지
lens:
  pricing_principle: str        # archetype.primary_metric 기반 "무엇 보고 싼가"
  cycle_reading: str            # cycle phase(early/mid/late/down) × 거시 regime
  estimation_note: str          # 현 시점 cycle 위치 (데이터 근거)

# ── 블록2 INDICATORS ── 데이터: build_indicator_matrix PIT panel / 측정: rank_ic
indicators_passed:
  - id: str
    layer: 1|2|3                 # 1=펀더멘털(DART/EDGAR) 2=거시(FRED) 3=산업cycle(리서치)
    family: str                  # factor family (within-family neutralize 대상)
    ic_mean: float               # ★점추정 금지 — 분포로
    ic_ci_95: [float, float]     # 0 비포함 (block-bootstrap)
    n_effective: int             # effective-N tier (autocorr 보정)
    oos_ratio: float             # OOS/IS (skfolio CPCV)
    source_id: str               # validation-*.md cell ID (추적성 hard-fail C)

# ── 블록3 RELATIONSHIPS (partial-corr) ── RegimeGlasso
relationships_passed:
  - {node_a, node_b, lag_months, corr, corr_ci_95, conditioning_set, n, source_id}

# ── 블록4 WEIGHT_RULES ── derive_weights(w∝Ω·IC) 입력
weight_rule_candidates:
  - indicator_id: ref
    base_weight_range: [float, float]   # ★range (점추정 금지)
    modulate_by: [archetype, regime, cycle_phase]
    gate_status: {n, se, power, fdr, oos}  # 5게이트
    source_ids: [str]

# ── 블록5 CONFIDENCE_HOOKS ── ★결선 직결 (affects_indicator 필수!)
confidence_hooks:
  - hypothesis_id: str
    affects_indicator: ref       # ★★필수 — 비우면 결선 dead (이번 세션 발견 B). indicator id 와 매칭
    affects_edge: [ref, ref]
    confirm_signal: str
    reject_signal: str           # e-CUSUM 붕괴 (placebo)
    emit_where: "panel-score-IC 축"   # ★backtest SELL 아님 (발견 A 정정)
    accumulate_in: "weight_falsification.score_ic_breakdown_eprocess"
    feeds_weight: "derive_weights 재적합"

# ── 블록6 COLLECTOR_PLAN ──
collector_plan_industry:
  - {missing, source, priority}

# ── ★신규 A: cross (분석 단위 간 상관) ── ★정의: 산업군 간 / 타자산(금·채권·코인) 간 상관 = coin btc-eth 식. within-industry 아님. 측정 3종.
cross:
  # (a) 동시 상관 + 공통인자 exposure (RegimeGlasso) — 통합 cross 조립 입력
  common_factor_exposure:
    - factor: VIX|dollar|oil|rate|credit
      beta: float
      beta_ci_95: [float, float]
      contemporaneous: true
      source_id: str
  # (b) 방향성 spillover (DY connectedness, Diebold-Yilmaz) — ★신규, RegimeGlasso 사각지대
  directional_spillover:
    - pair: [this_sector, other_unit]   # other = 타 산업군 OR 금/채권/코인
      net_connectedness: float          # generalized VAR FEVD, rolling window
      lead_or_lag: lead|lag
      window_n: int                     # ★rolling n 명시 + 추정오차 CI 의무
      source_id: str
  # (c) 구조 linkage (customer-supplier momentum, Cohen-Frazzini / I-O centrality, Acemoglu) — ★신규
  structural_linkage:
    - supplier_or_customer: str         # I-O 연결 산업
      io_weight: float                  # BEA I-O Leontief / centrality
      lagged_return_signal: float       # 선행 신호 (~88bps/월 prior)
      source_id: str
  # ⛔ sector-rotation business-cycle clock = 학술 myth(Molchanov 2024). 모멘텀 rotation 만 tentative.

# ── ★신규 B: robustness_checks (측정 15종 통과 기록) ──
robustness_checks:
  - indicator_id: ref
    leave_episode: pass|fail         # single-episode 아님
    within_period: pass|fail         # sub-split 부호 일관
    partial_corr_ratio: float        # partial/marginal >0.5
    net_sharpe_ratio: float          # net/gross ≥0.5 (미 0.03%/한 0.18-0.23%+0.3%)
    forward_vs_contemp: str          # 부호 일치 여부
    family_neutralized_ic: float     # FF5 직교 후 잔존 alpha
    eff_n_tier: Validated|Tentative|Weak|INSUFFICIENT

# ── ★신규 C: horizon_verdict (forward alpha 부재 falsifier) ──
horizon_verdict:
  best_horizon: str
  forward_alpha_present: bool        # false → risk-monitor 용도로 격하

# ── Hard-fail 4 (B C D I) self-check ──
hard_fail_self_check:
  B_real_data: {status, note}        # 합성 0, raw .py 재실행
  C_traceability: {status, note}     # yaml↔validation ±5%
  D_pit: {status, note}              # vintage_policy + OOS
  I_survivor_bias: {status, note}    # delisted + PIT universe

verdict_label: CONFIRMED|PARTIAL|TENTATIVE|INSUFFICIENT|REJECTED  # small-n rule
```

---

## §3. 코드 편입 매핑 (yaml 필드 → 함수)

| yaml 필드 | 코드 함수 | 역할 |
|---|---|---|
| indicators_passed | `core/data/weight_panel.build_indicator_matrix` | PIT panel → score 시계열 |
| weight_rule_candidates | `core/assume/weight_card.derive_weights` (w∝Ω·IC + 1/N + cap) | 동적 가중 |
| relationships / partial-corr | `core/structure/conditional_correlation.RegimeGlasso` | 거시국면 조건부 상관 |
| confidence_hooks.affects_indicator | `study_register.wire_falsification` → `weight_falsification.score_ic_breakdown_eprocess` | ★결선(e-CUSUM 청산). **affects_indicator 비면 dead** |
| common_factor_exposure | 통합 단계 `effective_precision` belief-mix | cross 조립 (L축 1회 계상) |
| robustness_checks | validation-*.md raw .py | 측정 15종 게이트 |

★ **사용자 합의 박제** (안 빠지게): 산업 단위 작업 / coin 측정 15종 그대로(주식 적용 14, intraday만 제외 / within=within-period, family=factor-family) / 섹터구분=stock.md(미국 Mag7+macro-sleeve, GICS 11 아님 / 한국 12산업) / 뼈대=archetype.py 5종 척추 / 외부는 우월시만+차용검증 / 결선 완료(panel-score-IC 축) / derive_weights SOTA 충분(보강=1/N baseline ablation) / 산업.py·GitHub 연관성 지표 부재→학술 리서치.

---

## §4. 채움 예시
> ★학술 리서치(연관성 지표) 완료 후 미국 섹터 1개로 common_factor_exposure 포함 완전 예시 작성 예정. 현재는 스키마 + 측정 15종 기준 확정 단계.
