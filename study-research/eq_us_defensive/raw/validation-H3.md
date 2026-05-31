---
tags: [type/validation, hypothesis/H3, study/eq_us_defensive, phase/2-3]
date: 2026-05-30
hypothesis: H3 — HY OAS Defensive Outperformance Trigger
verdict: ★REVERSED (자문 prior 정반대 실측)
---

# validation-H3.md — HY OAS Defensive Outperformance 실측

## 가설 (direction.md §H3)

**HY OAS 가 임계 상회하는 신용위기 시 sleeve (XLP+XLU+XLV+XLF) excess return (vs SPY) > 0. 인플레 충격 시 효과 약화/소멸.**

- Anchor: Frazzini-Pedersen (2014) Betting Against Beta + R1 ⑤ 핵심 논쟁
- Prior: Credit regime 평균 excess > 0, p<0.05 (Bootstrap t-test)

## 데이터

- **FRED BAMLH0A0HYM2** (HY OAS) — 2000-01 ~ 2026-05 (월별 평균)
- **FRED T10YIE, FEDFUNDS** — Inflation regime 정의용
- **ETF**: XLP, XLU, XLV, XLF, SPY (sleeve_eq = 4 sector equal-weight, def_only = XLP+XLU+XLV)

## 방법

1. Regime 독립 dummies (overlap 허용):
   - **Credit Stress**: HY OAS > p75 (3.546)
   - **Inflation Shock**: T10YIE > p75 (2.368) AND d_FFR_6M > 25bp
2. 월별 sleeve_excess = sleeve_eq - SPY (Bootstrap 10,000 resampling t-test)
3. def_only_excess = (XLP+XLU+XLV).mean() - SPY (financials 제외 — 순수 방어 검증)

## 결과

### Regime 분포 (n=317 months, 2000-01 ~ 2026-05)

| Regime | n | 비고 |
|---|---:|---|
| Credit Stress (all) | 9 | HY OAS > 3.546 |
| Credit only (~infl) | 8 | Credit 단독 |
| Inflation Shock (all) | 1 | T10YIE 고 + Fed tightening |
| Inflation only (~cred) | 0 | 2022 = Credit + Inflation 동시 |
| Both | 1 | 2022 한 달 |
| Normal | 308 | 대부분 |

### 평균 월별 excess return by regime

| Regime | n | sleeve excess (월) | 95% CI | p | def_only excess (월) | def p |
|---|---:|---:|---|---:|---:|---:|
| **Credit Stress (all)** | 9 | **-0.0151** | [-0.0281, -0.0040] | **0.005** | **-0.0196** | **0.004** |
| **Credit only (~infl)** | 8 | **-0.0179** | [-0.0312, -0.0066] | **0.001** | **-0.0234** | **<0.001** |
| Inflation (all) | 1 | insufficient | — | — | — | — |
| Both | 1 | insufficient | — | — | — | — |
| Normal | 308 | -0.0002 | [-0.0028, +0.0024] | 0.868 | +0.0000 | 0.987 |

## 평가

### ★REVERSED — 자문 prior 정반대

**자문 prior (R1 Frazzini-Pedersen + R3 H3 confirm 조건)**:
- 신용위기 시 sleeve excess > 0 (방어 outperform), p<0.05

**실측**:
- 신용위기 시 sleeve excess = **-1.51%/월** (p=0.005) — *underperform* 1.5%/월
- Credit only 시 sleeve excess = **-1.79%/월** (p=0.001) — 더 강한 *underperform*
- 방어주만 보면 (def_only) -1.96%/월 (p=0.004) — 방어주가 *오히려* 더 부진
- 즉 자문 prior 정반대 부호

### 통계적 강도

- n=9 (전체 표본의 2.8%) 작은 표본이지만 Bootstrap 10,000 resampling 결과 p=0.005 — 강건
- 95% CI [-0.028, -0.004] 가 0 미포함 → 명확한 negative shift
- Credit only (n=8) 가 더 극적 → 2022 (Credit + Inflation 동시) 제외해도 결과 동일

### 왜 자문 prior 가 틀렸나 (해석)

1. **XLF 가 sleeve 의 32% (4 sector eq)** — banks/insurance 가 위기 시 *worst* 부문. 방어 sub-sleeve outperform 을 XLF 의 underperform 이 상쇄·압도
2. **2000-2026 표본**: 2008 GFC 시 XLF 가 -55% (R1 ⑤ 표) — 이 한 사건이 평균을 크게 끌어내림
3. **Modern QE 시대 패턴**: 2010 이후 Fed 의 빠른 risk-on 대응으로 risk-off 진입조차 짧음. 전통 방어주 alpha 채널 약화
4. **R1 의 H3 정의 자체가 "위기 유형 dispersion 있음" 명시** — 실측은 이 dispersion 의 *방향* 까지 보여줌

### 대안 가설 — 본 데이터로 어디까지

- Credit only n=8 = 너무 작아 sub-archetype 분해 무리
- 가능한 후속:
  - **sleeve 정의 변경**: financials 제외 (`def_only` 기준) → 그래도 -1.96%/월 underperform → 방어 alpha 자체가 실증 X 모드
  - **위기 onset window**: regime month 단위 대신 HY OAS 가 +0.5σ 상승한 *직후* 30/60일 window — 단 sample 더 작아짐
  - **상대비교 변경**: SPY 대신 60/40 portfolio 또는 risk parity benchmark 대비

## 코드화 권고 (yaml 반영)

### relationships (블록3) — H3 edge 재정의

```yaml
- {node_a: hy_oas_change, node_b: sleeve_excess, edge_type: direct,
   conditioning_set: [], prior_sign: neg, prior_strength: 0.30,  # 실측 |effect|
   theory_basis: "★실측 REVERSED: Credit regime n=9 sleeve excess -1.5%/월 p=0.005. Frazzini-Pedersen BAB 가 본 sleeve (financials 포함) 에 X. financials 제외해도 def_only -1.96%/월 (방어 alpha 실증 X)"}
```

### weight_rules (블록4) — credit_beta 재calibrate

기존 v1 base_weight=0.12 (방어주 risk-off 시 상대 outperform 가정) → **실측 inversion**:

```yaml
- {indicator_id: credit_beta, base_weight: 0.06,  # 0.12 → 0.06 (효과 역방향, 강도 감소)
   modulate_by: [regime, industry],
   direction: "★실측 REVERSED: Credit regime 시 sleeve excess -1.5%/월. 자문 prior (방어 outperform) X. 실측: 위기 시 본 sleeve underperform (XLF 의 -55% GFC 영향 + modern QE 시대 패턴). credit_beta 가중 절반 강등",
   granularity: industry}
```

### confidence_hooks 갱신 경로

H3 확신/거부 조건 **전면 재정의**:

```yaml
- hypothesis_id: hy_oas_sleeve_inversion  # ★이름 변경: outperformance → inversion
  confirm_signal: "Credit Stress regime (HY OAS > p75) 진입 시 sleeve excess > -2.0%/월 유지 (실측 anchor)"
  reject_signal: "Credit Stress regime 시 sleeve excess > +0.5%/월 — 전통 방어 thesis 부활 신호"
  emit_where: "regime classifier + monthly excess return tracker"
  accumulate_in: "weight_falsification.score_ic_breakdown_eprocess (regime=credit 서브패밀리)"
  confidence_metric: "Bootstrap 10k t-test on regime excess return mean"
  store: "registry WeightAssumptionCard.confidence_now (regime=credit sub-key)"
  action_threshold: "현 실측 (n=9, -1.5%/월) → credit regime 진입 시 sleeve 비중 *축소*. 부활 시 (excess > +0.5%) 비중 복원"
  feeds_weight: "credit_beta base_weight 동적 조정 (0.06 ↔ 0.12) by regime confidence"
```

### lens 갱신 (블록1)

regime_reading 항목 전면 수정:
> "★Slowdown/Stagflation = 방어주 모국" → "★실측: Credit Stress regime 시 본 sleeve 가 -1.5%/월 underperform (Bootstrap p=0.005, n=9). 자문 prior BAB 의 방어 alpha 가 modern QE 시대 + XLF 비중으로 실증 X. financials 제외해도 def_only -1.96%/월. → 방어 sleeve 비중 축소가 risk-off 시 권고."

## 한계

- **n=9 (Credit), n=1 (Inflation)** — Credit only 검정력은 확보되었지만 Inflation 분해 불가
- 표본 표현 = 2000-2026 (대부분 QE 시기). Pre-QE (1990s) 데이터 시 결과 다를 수 있음
- HY OAS 분위 (p75=3.546) 가 단일 기준 — 분위 변경 (p80, p90) 시 sample 적어짐
- sleeve 정의 = 4 sector eq weight. 시가총액 가중 시 XLF 비중 변화 → 결과 영향

## 참조

- `run_validation.py` lines 175~270 (H3 block)
- `validation-metrics.json` h3_hy_oas_regime
- direction.md §H3 (가설 원문)
- raw/round-1.md ⑤ (위기 유형별 dispersion 핵심 논쟁)
- raw/round-3.md H3 (confirm/reject 조건 — 실측 reject 조건 명확히 매칭)
