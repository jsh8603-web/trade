---
tags: [type/plan, study/eq_us_cyclical, phase/post-M3, topic/industry-regime-delta-matrix]
date: 2026-05-30
study_id: eq_us_cyclical
phase: "산업×regime δ_regime/δ_arch 가중 매트릭스"
session: btn-common-task (eq_us_cyclical workspace)
deliver_to: btn-Codlearn (main)
inputs:
  - study-research/eq_us_cyclical/raw/m3-findings.md (epoch × sector driver loading)
  - study-research/eq_us_cyclical/raw/m3-metrics.json
  - study-research/eq_us_cyclical/study_session.yaml v2 (블록3 relationships + 블록4 base_weight)
  - CONSULT-DECISIONS-layering-20260530.md (5 영속 원칙 — Belief-Truth 격리, single-writer, partial pooling, soft gate, consensus)
  - core/assume/judge.py (R15 weight_card composed_weights 구조)
note: |
  main 지시 — "주식 sleeve 산업×regime 동적 평가지표 가중 보정" + "산업별 subagent 분할 + n<30=5게이트 + James-Stein 3-tier".
  ⛔ small-n-statistical-rigor.md SSOT 부재 (find 결과 0건) → 본 plan §3 에서 자체 정의, main 검토 시 SSOT 보정.
---

# Industry × Regime δ Matrix — Master Plan

> R15 weight_card `composed_weights = w_global + δ_regime + δ_arch + δ_inter` 구조에서 주식 sleeve 의 δ_regime / δ_arch 실측 충전. 경기민감 산업 4개 (반도체/소재/산업재/에너지) subagent 분할 → 통합 매트릭스.

## §0. 핵심 불변식 (Belief-Truth 격리, CONSULT-DECISIONS-layering)

| 영속 원칙 | 본 task 적용 |
|---|---|
| **Belief-Truth 격리** | 거시 numeric (Δus10y/r_dxy/r_oil) = 배분레이어 (sleeve 게이트) 전담. 종목레이어 = **펀더멘털만**. δ_regime 은 **regime tag** 만 입력 (numeric 거시 직접 X) → reflexive loop 차단 |
| **single-writer** | δ_regime ← regime tag, δ_arch ← 펀더멘털 (forward EPS / capex / inventory / book-to-bill ...). 두 path 분리 |
| **partial pooling** | n 작은 epoch×산업 cell → James-Stein λ shrinkage 의무 (점추정 박제 금지) |
| **soft gate** | δ 자체는 weight 가산 (clamp 후 floor), hard switch X. judge L1 down-only 유지 |
| **agreement consensus** | 산업 4개 + 4 epoch 의 conditional β 합의도 = confidence. averaging X, discrete + disagreement = regime transition signal |

★ **이중계상 회피** (자문 R2 gemini+claude): 거시 = 배분, 종목 = 펀더멘털. 산업별 δ_regime 도 **regime tag 의 epoch 조건부 weight** 만, 거시 numeric loading 직접 박제 금지.

## §1. Sleeve 분류 — GICS 멤버십 아닌 팩터노출

자문 R2 확정 원칙: sleeve = ETF 라벨 (XLI 등) 아닌 **팩터노출** 정의. ★eq_us_cyclical 안 산업 분할:

| 산업 sub-sleeve | proxy ETF | 팩터노출 정의 | 분리 근거 (M3 실측) |
|---|---|---|---|
| **반도체 (semi)** | SOXX | 글로벌 cycle + dollar high-β + 고듀레이션 (성장기대 sensitive) | β_dxy=−1.62 (최대), epoch swing −50%→+89% (변동성 최대), within-corr 0.56~0.75 |
| **소재 (materials)** | XLB | 산업금속 + 중국 PMI + dollar | β_dxy=−1.18, R²=0.215 (cyclical 두번째 설명력), 산업금속 sub-channel |
| **산업재 (industrials)** | XLI | classic cyclical + CapEx + ISM PMI | β_dxy=−0.81, full-cycle 안정 (epoch swing +30~+44%), XLF/XLB 와 corr 0.84+ (cyclical 공통인자) |
| **에너지 (energy)** | XLE | oil-driven (이중채널 별도) | β_oil=+0.41, rank-IC +0.602, within-corr 0.26~0.51 (outlier), anti-cyclical hedge (E1 +47.9%·E3 +18.0%) |

★ XLY (consumer disc) / XLF (financials) 는 본 task 범위 외 (deferred — main 추후 지시 시 별도). 사용자 명시 4개로 시작.

## §2. δ_regime / δ_arch 정의

### δ_regime (regime tag conditional weight)

```
δ_regime[industry, regime_tag] : weight 가산
  regime_tag ∈ {E1_tightening_shock, E2_transition_rally, E3_rate_re_rise, E4_pivot_cuts}
  ★Belief-Truth 격리: regime_tag 는 macro layer (배분) 가 제공.
                     본 layer 는 tag 수신 → weight 가산 (numeric 거시 직접 X)
  값 = M3 epoch-conditional β 기반 + partial pooling shrinkage 후
```

### δ_arch (architecture-specific fundamental weight)

```
δ_arch[industry, fundamental_metric] : weight 가산
  fundamental_metric ∈ industry-specific 펀더멘털 (forward EPS / capex_to_rev / inventory_days / book-to-bill ...)
  ★거시 driver 절대 포함 안 함 (배분레이어 전담)
  값 = 도메인 리서치 + EDGAR 적재 후 실측 (현 단계 = 후보 식별 + 이론적 정당화)
```

### 산업별 δ_arch 후보 (이론 + 가용 데이터)

| 산업 | δ_arch fundamental 후보 | 실데이터 가용성 |
|---|---|---|
| **반도체** | (a) forward EPS revision breadth (b) book-to-bill (SEMI 협회) (c) inventory days (d) R&D/revenue | (a)/(c)/(d) = EDGAR 적재 후 / (b) = SEMI 월별 무료 |
| **소재** | (a) gross margin trend (b) capex/revenue (c) inventory turnover (d) LME 산업금속 노출도 | (a)~(c) = EDGAR 후 / (d) = 부분 (LME public) |
| **산업재** | (a) ISM PMI 신규주문 (FRED NEWORDER) — **단 거시 차원으로 분류 시 배분레이어 위임** (b) backlog/revenue (c) capex/rev | (b)/(c) = EDGAR 후 / (a) = 경계 분류 필요 (★중요) |
| **에너지** | (a) WTI/Brent 차이 (b) production volume (c) rig count (FRED BKR) — **위 (c) 거시 sub-channel** (d) reserves/production | (a)/(c) = FRED 가용 / (b)/(d) = EDGAR 후 |

★ **경계 분류 의문**: ISM PMI (산업재 δ_arch) vs 거시 (배분레이어)? **rig count** (에너지 δ_arch) vs oil 채널 (배분)?

해결 — **scope 기준**: 거시 = cross-sleeve (전 종목 영향), 산업-specific = single-sleeve (해당 sleeve 만). ISM 은 cross-sleeve (cyclical 전반 영향) → **배분레이어**. book-to-bill 은 반도체-specific → δ_arch. ★ rig count 는 모호 (oil 1차 driver 면 거시, 에너지 sleeve-specific 면 δ_arch) → sub-agent 분석 결과로 결정.

## §3. 5게이트 정의 (small-n statistical rigor) — 자체 정의

★ SSOT 부재 (find 0건). 일반 통계 best practice + Bayesian rigor 기반 자체 정의. **main 검토 시 보정**.

| 게이트 | 기준 | 통과/실패 처리 |
|---|---|---|
| **G1 minimum-n threshold** | per-cell n ≥ 30 (daily). n < 30 시 **명시 분류** + 보정 의무 | 통과: 직접 점추정 / 실패: G2~G3 강제 |
| **G2 Bootstrap CI** | Stationary bootstrap (Politis-Romano 1994, block length √n) 95% CI 동봉. **점추정 단독 보고 금지** | CI 가 0 통과 = 약화 boundary, 비통과 = 신뢰 |
| **G3 partial pooling shrinkage** | James-Stein λ = τ²/(τ²+σ²/n), epoch×산업 cell 단위 shrinkage → δ_global 로 수렴 | λ 명시. n→0 면 λ→0 = pooled mean (graceful degradation) |
| **G4 cross-validation / OOS** | 4 epoch 중 1 epoch leave-one-out, rolling fit, R²_OOS vs R²_IS 보고 | R²_OOS < 0 = 과적합 경고. 차이 > 50% = degrade |
| **G5 domain plausibility** | 통계적 통과 + 도메인 이론 (반도체 cycle / 소재 commodity / 산업재 ISM lead / 에너지 OPEC) 정합 | 정합: 채택 / 불일치: 명시 + δ 약화 |

**E3 (n=85 daily) ≈ ~17 weekly ≈ ~4 monthly** — daily 기준 G1 통과, monthly 기준 G1 실패. **본 task = daily 기준 적용** (M3 와 정합).

## §4. 검증관 3-tier (사용자 명시)

```
Tier 1 (측정): raw β, R², n, p-value, IS R². ★점추정 박제 금지 → 항상 CI 동봉.
Tier 2 (Bayesian shrinkage): James-Stein λ × Tier1 + (1-λ) × δ_global. graceful degradation.
Tier 3 (도메인): 반도체 cycle theory / 소재 commodity rotation / 산업재 ISM lead 12M / 에너지 OPEC discipline 검토.
```

★ Tier 1 통과 + Tier 2 강한 shrinkage (λ < 0.3) + Tier 3 도메인 불일치 = δ 폐기 또는 zero. Tier 1 약 + Tier 2 강 shrinkage + Tier 3 강 정합 = δ 보존 (도메인 prior 우선).

## §5. Workflow 분할 (산업별 subagent)

```
phase('Research') — 4 산업 병렬 fan-out
  ├── semi-research (SOXX 도메인 + book-to-bill + cycle theory)
  ├── materials-research (XLB + LME + 중국 PMI)
  ├── industrials-research (XLI + ISM PMI + CapEx)
  └── energy-research (XLE + WTI + rig count + OPEC)

phase('Verify-3tier') — 산업별 검증관
  ├── verify Tier1 (측정 신뢰도)
  ├── verify Tier2 (James-Stein shrinkage)
  └── verify Tier3 (도메인 plausibility)

phase('Synthesis') — 통합
  └── 4 산업 × 4 epoch δ 매트릭스 + yaml R15 weight_card 보강안
```

각 sub-agent schema 강제 (workflow JSON Schema), 결과 raw/industry-{key}-delta.md 저장.

## §6. 산출 (예상)

- `raw/industry-semi-delta.md` (반도체)
- `raw/industry-materials-delta.md` (소재)
- `raw/industry-industrials-delta.md` (산업재)
- `raw/industry-energy-delta.md` (에너지)
- `raw/industry-delta-synthesis.md` (통합 매트릭스 + yaml R15 보강안)
- `raw/industry-delta-metrics.json` (구조화 매트릭스)

## §7. 한계·미해결 (정직 명시)

1. **EDGAR 펀더멘털 미적재** → δ_arch 본격 실측 deferred (현 단계 = 이론 후보 식별 + M3 거시 driver 재해석 한정)
2. **small-n SSOT 부재** → 본 plan §3 자체 정의 (5게이트). main 검토 시 보정
3. **E3 epoch n=85 daily** = monthly 환산 시 G1 실패. daily 기준만 적용 명시
4. **4 산업 한정** (XLY/XLF 제외) — main 후속 지시 시 확장
5. **검증관 3-tier λ τ² σ² 추정** = 산업별 cell shrinkage 기준 τ² (between) / σ² (within) 추정에 prior 가정 필요 (weakly informative). 결과에 prior 명시

---

## Working Notes

- §1 sleeve 분류 = M3 실측 근거 (within-corr 0.617, XLE outlier 0.26) + 자문 R2 팩터노출 원칙
- §3 5게이트 = SSOT 부재 → 일반 통계 best practice 자체 정의 (main 보정 받음)
- workflow JSON Schema 강제 → sub-agent 일관 출력
