---
tags: [type/summary, domain/inv, asset/bond, asset/cash, phase/study]
date: 2026-05-30
study_id: bond_cash
note: bond_cash 작업방 산출 요약 — 채권/현금 sleeve 평가 lens + 가중룰 + 코드변경계획. study_session.yaml(7블록) 동반.
---

# bond_cash 스터디 요약

**study_id**: `bond_cash` (asset_scope = `[bond, cash]`, 2-sleeve 동시 스터디)
**as_of**: 2026-05-30
**산출**: `study_session.yaml` (블록1~7) + 본 summary + `raw/` 분석 출력

---

## 1) 왜 bond_cash 를 한 방에서 함께 보는가

`core/brain/regime_to_weights.py` L50 `SLEEVES = [..., "bond", "cash", ...]` 에 bond/cash 는 **별도 sleeve** 로 등록되어 있다. 그러나 둘은 자연적 **상보 defensive pair**:

| Regime | bond 등급 | cash 등급 | 해석 |
|--------|----------:|----------:|------|
| Reflation   | **top** (×1.8) | neutral | 명목금리↓+성장↑ → long-duration 우위 |
| Recovery    | down (×0.6)    | down    | 금리정상화 → 채권 매도, 위험자산으로 |
| Overheat    | down (×0.6)    | down    | real rate·breakeven 동반↑ → 듀레이션 페널티 |
| Stagflation | down (×0.6)    | **top** (×1.8) | 인플레↑+성장↓ → 현금이 유일한 방어 |

→ 4국면 중 **Reflation 과 Stagflation 정확히 교차**. bond/cash 를 함께 보지 않으면 *국면 전환점에서 둘 사이 비중 swap* 을 학습할 수 없다. 본 방은 둘을 **묶어 학습**하고 sleeve 가중은 regime 신뢰도(블록5 confirm/reject flag) 로 동적 보정한다.

---

## 2) 일반론 + 리포트 정제 (블록1 lens 핵심)

### 가격결정 방정식
```
ΔP/P ≈ -Duration · Δy + 0.5 · Convexity · (Δy)² + carry(쿠폰)
y = real_rate + breakeven_inflation      ← Fisher 분해
HY price = -D·Δy_tsy - SpreadDuration·Δspread + carry
```

### 종목간 가중을 가르는 *프리미티브 3축*
1. **Duration bucket** (long/mid/short/cash_like) — TLT(D≈17)/IEF(D≈8)/SHY(D≈2)/BIL(D≈0.1)
2. **Credit quality** (Tsy/IG/HY) — 신용 spread duration ≈ duration 으로 1:1 가산
3. **Curve location** (belly/wing) — roll-down carry 와 직결

### 핵심 리포트 관계도 (블록1 report_relations 발췌 — 9 channel)
- **Fed funds → DGS2 → DGS10**: 정책 전달경로. 인상기 = bear flattening = 침체 선행
- **10Y-2Y 역전 → 해소 (steepening)** = Recovery 진입 anchor (12~18M lag)
- **DGS10 = DFII10 + T5YIE**: real rate vs breakeven 분해 — 듀레이션 vs 인플레 axis 분리
- **HY OAS spike ↔ long Tsy rally** (flight-to-quality 카운터-사이클)
- **rate-shock 국면** = 듀레이션 1차 페널티 = 장기 >> 중기 >> 단기 손실
- **curve carry**: 정상커브 → roll-down 추가 수익 / 평탄·역전 → carry 사라짐
- **credit cycle**: 저금리·성장 → spread 압축 / 고금리·둔화 → spread 확대
- **엔캐리 채널**: BOJ vs Fed 금리차 축소 → 일본 자금 미 채권 매도 = bear steepening 외력

---

## 3) 우리 데이터로 번역 (블록2 indicators)

`fred_adapter.py FRED_SERIES` 17 시리즈 중 **6개가 채권/현금 분석에 직접 가용**:

| in_our_system | indicator | family | core | 활용 |
|:---:|---|---|:---:|---|
| ✅ | `yield_10y_2y` (T10Y2Y) | macro_driver | ★ | 커브 본체, 역전·steepening anchor |
| ✅ | `credit_spread_hy_oas` (BAMLH0A0HYM2) | macro_driver | ★ | HY 위험 + cash flight 대용 |
| ✅ | `credit_spread_baa` (BAA10Y) | macro_driver | ★ | IG spread 보완 |
| ✅ | `breakeven_5y` (T5YIE) | macro_driver | ★ | 인플레 기대 → real rate 분해 |
| ✅ | `nfci` | risk | — | HY 와 중복신호(합산 cap) |
| ✅ | `fred_recession_prob` | macro_driver | — | curve↔credit 매개 통제용 |

**부재 6+종** (블록6 collector_plan → main 요청):
- **DGS10/DGS2/DGS3MO/FEDFUNDS** (절대량 본체 — 듀레이션 베타 계산 input)
- **DFII10** (10Y TIPS = real rate 본체. macro 방과 공유)
- **MORTGAGE30US** (long Tsy + credit 잔차)
- **TLT/IEF/SHY/BIL/LQD/HYG/JNK 일별가** (sleeve 본 forward return)
- **ICE BofA US Treasury Index TR** (장기 OOS 백테스트)

→ 부재 자료는 main 요청하되, **있는 6종으로 본 분석은 진행**(§2 ② idle 금지). `raw/correlation_analysis.txt` 에 실 데이터 partial-corr 결과 저장.

---

## 4) ★최종 산출 = 동적 가중 룰 (블록4 요약)

| indicator | base_weight | modulate_by | 핵심 direction | granularity |
|---|---:|---|---|---|
| `duration_bucket_id` | 0.30 | regime, name_specific | Reflation/rate-down → long↑ / Overheat/rate-shock → short↑ + long penalty | ticker |
| `credit_quality_id` | 0.20 | regime | Reflation/Recovery → HY/IG↑ / Stagflation/risk-off → Tsy↑(flight) | ticker |
| `credit_spread_hy_oas` | 0.18 | regime | OAS Z↑ → HY↓ + long Tsy↑(역카운터) | ticker |
| `yield_10y_2y` | 0.15 | regime | Steepening → bond sleeve 회복 + long↑ | sleeve |
| `real_rate_10y` | 0.10 | regime | real rate Z↑ → 듀레이션 페널티 + cash↑ | sleeve |
| `breakeven_5y` | 0.07 | regime | breakeven↑ → TIPS↑ + 명목 long↓ | ticker |

**부록 B hierarchical pooling**: ticker 가중 = `w_global + δ_regime + δ_arch(duration bucket) + ticker shrinkage`. TLT={long:1.0}, IEF={mid:0.7, long:0.3} 같이 **soft membership** 으로 hard sub-sample 회피.

---

## 5) ★flag → 신뢰도 → lens 갱신 루프 (블록5 hooks 6종)

| hypothesis_id | confirm | reject | feeds_weight |
|---|---|---|---|
| `duration_rate_sensitivity` | rate-shock 페널티 OOS 효과↑ | 과조정(false rate-shock) | duration_bucket_id IC 보정 |
| `hy_oas_credit_regime` | HY↓+Tsy↑ 사이징 PnL 방어 | OAS widening false signal | HY 가중 0.18→±0.02 |
| `curve_inversion_recession_lag` | steepening→Recovery 정합 | lag 불안정 → bond 회복 오인 | curve 가중 + estimation_note 갱신 |
| `carry_to_total_return` | carry 정상커브 IC 양 | spread widening 시 carry 무효 | roll_carry_yield 가중 변동 |
| `cash_optionality_value` | shock event CVaR 방어 | 정상기 missed-rally cost | BASE_WEIGHTS[cash] 동적 floor |
| `bond_sleeve_omega_drift` | Ω 구조 안정 | HY-Tsy sign flip 등 drift | re-fit trigger |

→ 모두 `core/assume/weight_falsification.score_ic_breakdown_eprocess` 또는 `omega_drift` 에 매핑. e-process anytime-valid (Ville 부등식, false-kill ≤ alpha=0.05).

---

## 6) 코드 변경 계획 요약 (블록7 — 4단계 × 파일:심볼)

### ① learn
- `core/brain/fred_adapter.py FRED_SERIES`: **DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US 6 추가**
- `core/data/weight_panel.py`: 반사성 게이트 통과 self-test 만 추가
- `core/structure/conditional_correlation.py corr_prior`: 블록3 force-include 4 엣지 주입
- `scripts/train_weights.py train_weight_cards`: **domain=bond_cash 배치 추가** (regime_ids = 4국면 × rate-shock/risk-off flag)

### ② card
- `core/assume/weight_card.py WeightAssumptionCard`:
  - lens 정성필드 추가 (macro 방과 공유)
  - **archetype = duration bucket** (delta_arch_by_type 으로 ETF soft membership)
- `core/assume/registry.py`: 카드 id `weight.bond.{regime}` / `weight.cash.{regime}` / `weight.bond.{credit|transition|carry}` / `weight.cash.optionality`

### ③ inject
- `core/brain/regime_to_weights.py`:
  - `BASE_WEIGHTS bond/cash` 를 **confidence_now 로 동적 보정** (opt-in)
  - `REGIME_DIRECTION` 정적 anchor 유지
  - `_belief_conditional_cov` 에 채권 ETF returns_history 자동 활성
- `core/stock_track.py`: 주식 sleeve 본질이라 **bond_cash 영향 없음**. 단 ETF universe 확장 시 *asset_class router* 분기 (또는 `etf_track` 신설 권장)
- `core/assume/judge.py`: LLM 컨텍스트에 lens 주입 (down-only 보존)

### ④ falsify
- `core/assume/weight_falsification.py`: 블록5 hooks 6종 매핑 (alpha=0.05, tau_fro=0.5)
- `core/assume/update_controller.py`: bond/cash dwell↑ (분기 단위), K-window=2분기, cash floor 즉시 발동 hook 분리

---

## 7) main 통합 시 충돌·공유 포인트

### macro 방과 공유
- **DFII10 (real rate)** = macro 블록2 와 본 방 블록2 양쪽 요청 → main 이 collector_plan 통합 시 **중복 추가 금지**(한 번만)
- **lens 정성필드** (pricing_principle/report_relations/regime_reading) = macro 방이 이미 weight_card.py 에 제안 → 본 방은 그 필드 *공유 사용*
- **belief 동적 공분산** = macro 가 belief b(t) 공급, 본 방은 그 belief 를 *수신* (regime_to_weights `_belief_conditional_cov` 이미 wire)
- **corr_prior force-include** = macro(dxy~real_rate, dxy~gold 등) ⊥ 본 방(fed_funds~yield_2y, duration~yield_10y 등). 직교 → 단일 prior_matrix 에 block-diagonal 결합 가능

### 다른 방과 충돌 없음
- bond/cash sleeve 는 stock_track 미적용 → `eq_us_*`/`eq_kr`/`reit` 방의 `_extract_indicator_z` 변경과 무충돌
- `commodity`/`gold` 방의 sleeve cov 와는 `_belief_conditional_cov` 입력 `returns_history` 컬럼만 공유

### main 액션 요청
1. **FRED 시리즈 6종 추가** (DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US) — macro 방 DFII10 와 통합
2. **채권 ETF universe 적재** (TLT/IEF/SHY/BIL/LQD/HYG/JNK Yahoo 일별가) → VintageStore
3. **`etf_track` 모듈 신설 여부 의사결정** — stock_track 분기 vs 신설 (권장: 신설, 사이징 천장 불변식 공유)
4. **카드 archetype = duration bucket** 합의 — 본 방의 `delta_arch_by_type` 활용

---

## 8) 막힌 점·진행 불가 영역

없음. 가용 6종 데이터로 본 yaml 완성. 실 데이터 partial-corr 분석은 `raw/correlation_analysis.txt` 에 저장(별첨). 부재 자료는 collector_plan 으로 명시 요청하고 분석은 진행했음(§0 idle 금지 준수).
