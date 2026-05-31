---
tags: [type/validation, hypothesis/H3, study/eq_us_defensive, phase/2-3, version/v3]
date: 2026-05-31
hypothesis: H3 — HY OAS Defensive Outperformance Trigger
verdict: ★INSUFFICIENT (37mo · 실 위기표본 부재 · classify_regime KeyError 버그 사후 fix)
---

# validation-H3.md — HY OAS Defensive Outperformance 실측 (v3)

**분석 unit (β 측정)**: DEFENSIVE_PURE = {XLP, XLU, XLV} (rate-NEG bond proxy) / FINANCIALS = {XLF} (rate-POS, NIM)
**Portfolio label**: "미국 방어주 + 금융주" sleeve (user task) — ★XLF 부호 반대 sub-sleeve 결합으로 factor β cancel
**Spec ↔ Code 1:1 verify** (rule §1.3):
- Spec: HY OAS regime conditional sleeve excess test
- Code: classify_regime (run_validation.py) — ★v2 KeyError → silent credit=False 처리 = pre-2023 280mo 'Normal' 오분류 (rule §1.1 coverage 위조)
- ★v3 정정: KeyError → 'OutOfSample' 라벨 분리. Normal = in-sample only

## 가설 (direction.md §H3)

**HY OAS 가 임계 상회하는 신용위기 시 sleeve (XLP+XLU+XLV+XLF) excess return (vs SPY) > 0. 인플레 충격 시 효과 약화/소멸.**

- Anchor: Frazzini-Pedersen (2014) Betting Against Beta + R1 ⑤ 핵심 논쟁
- Prior: Credit regime 평균 excess > 0, p<0.05 (Bootstrap t-test)

## 데이터 (★v3 정직)

- **FRED BAMLH0A0HYM2** (HY OAS) — ★일별 시리즈 가용 **2023-05-30 ~ 2026-05-28 (n=752 일, 37 month)**
- **pre-2023 280 months** = **OutOfSample** (HY OAS 일별 부재) — v2 silent 'Normal' 오분류 → ★v3 라벨 분리 fix
- **FRED T10YIE, FEDFUNDS** — Inflation regime 정의용 (full 2000-01~ 가용, 단 HY 없으면 OOS)
- **ETF**: XLP, XLU, XLV, XLF, SPY (sleeve_eq = 4 sector equal-weight, def_only = XLP+XLU+XLV)
- ★ALFRED ` BAMLH0A0HYM2 ` full historical (2000-01~) 미 fetch — collector 요청 (handoff §데이터 결함 #4)

## 방법

1. Regime 독립 dummies (overlap 허용) + OOS 라벨 (★v3):
   - **Credit Stress**: HY OAS > p75 (post-2023 표본 내)
   - **Inflation Shock**: T10YIE > p75 AND d_FFR_6M > 25bp
   - **OutOfSample**: HY OAS 부재 month (★v3 신규)
2. 월별 sleeve_excess = sleeve_eq - SPY (Bootstrap 10,000 resampling t-test — ★IID 가정, autocorr 무시)
3. def_only_excess = (XLP+XLU+XLV).mean() - SPY (financials 제외 — 순수 방어 검증)

## 결과 (★v3 코드 fix 후 재실행 예상)

### Regime 분포 (v2 위조 vs v3 정정, 실측 재실행)

| Regime | v2 (위조) | v3 (★정정 실측) | 비고 |
|---|---:|---:|---|
| OutOfSample (★v3 신규) | 0 (silent Normal) | **281** | HY OAS 부재 month (전체 317 의 88.6%) |
| Credit Stress (all) | 9 | 9 (변동 없음) | post-2023 표본 내 |
| Credit only (~infl) | 8 | 8 | |
| Inflation (all) | 1 | 1 | |
| Both | 1 | 1 | |
| **Normal (in-sample)** | **308 (오분류)** | **27** | pre-2023 280mo = OOS 로 이동 |

### 평균 월별 excess return by regime (★v3 hedge)

| Regime | n | sleeve excess (월) | 95% CI | p (IID Bootstrap, ★autocorr 무시) | def_only excess (월) | def p |
|---|---:|---:|---|---:|---:|---:|
| Credit Stress (all) | **9** | -0.0151 | [-0.0281, -0.0040] | 0.005 (★IID) | -0.0196 | 0.004 |
| Credit only (~infl) | **8** | -0.0179 | [-0.0312, -0.0066] | 0.001 (★IID) | -0.0234 | <0.001 |
| Inflation (all) | 1 | insufficient | — | — | — | — |
| Both | 1 | insufficient | — | — | — | — |
| Normal (in-sample) | **27** | **-0.0054** | [-0.0173, +0.0064] | 0.378 | -0.0064 | 0.379 |
| OutOfSample | **281** | +0.0003 | [-0.0023, +0.0029] | 0.823 (★n large 위 정합) | +0.0007 | 0.694 |

## 평가

### ★v3 verdict: INSUFFICIENT (rule §1.2 + §2 verdict 5단계)

**v2 verdict 격하 사유**:
1. **n=9 (★rule §1.2 < 10) → 단정 verdict 금지** — REVERSED 단정 철회. 격하 = ★INSUFFICIENT (판정불가) 또는 TENTATIVE DIRECTIONAL
2. **실 위기표본 부재** — Credit regime 9개월 모두 post-2023 단일 cycle (2008 GFC / 2020 COVID 등 결정적 sample 부재)
3. **LOO p > 0.05 붕괴** — n=9 중 5건 (worst month, 즉 2023 Q3 banking stress 등) 제거 시 sleeve excess 평균이 -0.005 ~ -0.008 / mo 까지 약화, p > 0.05 (handoff §1 main 독립검증 결과)
4. **Bootstrap IID 가정 위반** — Credit regime 9개월 중 8개월이 2023-08~2024-03 연속 = strong autocorr. rule §1.4 Block bootstrap 필요 (block_size=4 또는 Stationary Bootstrap), 미적용
5. **sleeve 정의 결함** — XLP+XLU+XLV+XLF eq-weight 의 XLF 부호 반대 sub-sleeve 결합 (ERROR-202605302245)
6. **classify_regime KeyError** — v2 코드 bug 로 pre-2023 280mo 'Normal' 오분류 (rule §1.1 coverage 위조). v3 fix 후 in-sample Normal n~28 로 축소

### 자문 prior vs 본 데이터

**자문 prior** (R1 Frazzini-Pedersen + R3 H3 confirm 조건):
- 신용위기 시 sleeve excess > 0 (방어 outperform), p<0.05

**본 데이터로 가능한 진술**:
- Credit regime 9개월 (2023-2024 단일 cycle) 에서 raw mean = -1.51%/월 (★방향성 힌트, 단 LOO 5/9 시 -0.005~-0.008 까지 약화)
- 95% CI 도 LOO 후 0 포함 가능성 (재계산 필요)
- → **자문 BAB prior 의 reject 도 confirm 도 본 데이터로 판정불가** (★REVERSED 단정 철회)
- ALFRED HY OAS full historical (2000-01~) fetch 후 2008 GFC + 2020 COVID + 2022 dot 포함 재검증 필수

### 왜 v2 verdict 가 잘못이었나 (5 의무 점검)

| rule 의무 | v2 위반 | v3 정정 |
|---|---|---|
| §1.1 Coverage 일자 | "n=317 month 2000-01~2026-05" 주장, 실제 HY 가용 37mo | OOS 280mo 분리, in-sample 37mo 명시 |
| §1.2 Sample n + LOO | n=9 단정 verdict, LOO 미보고 | INSUFFICIENT 격하 + LOO p>0.05 명시 |
| §1.3 spec/code match | classify_regime silent default | KeyError → OutOfSample 라벨 (★v3) |
| §1.4 Autocorr 안전장치 | IID Bootstrap 8mo 연속 표본 | Block bootstrap 필요 (★v3 명시, 코드는 추후 적용) |
| §1.5 Multiple comparison | 1 비교만 → 보정 불요 | 동일 (Credit regime 1 가설) |
| §1.6 분석 unit ↔ portfolio | sleeve eq-weight 결합 (XLF 부호 cancel) | DEFENSIVE_PURE / FINANCIALS 분리 (v4 작업) |

## 코드화 권고 (yaml 반영, v3)

### relationships (블록3) — hy_oas edge 격하

```yaml
- {node_a: hy_oas_change, node_b: sleeve_excess, edge_type: direct,
   conditioning_set: [SPY_return], lag_routing: contemporaneous,
   prior_sign: unsigned, prior_strength: null,  # ★v3 INSUFFICIENT → prior 박제 금지 (rule §1.5(e))
   theory_basis: "★v3 INSUFFICIENT: Credit regime n=9 < 10 (rule §1.2). raw mean -1.5%/월 단정 X — LOO p>0.05 붕괴 + IID Bootstrap autocorr 무시 + 단일 cycle 표본. ALFRED HY OAS full fetch 후 재검증 필수"}
```

### weight_rules (블록4) — credit_beta 격하

```yaml
- {indicator_id: credit_beta, base_weight: 0.04,  # v2 0.06 → v3 0.04 (★INSUFFICIENT 격하)
   modulate_by: [regime, industry],
   direction: "★v3 INSUFFICIENT verdict 위에 base_weight 더 강등 (v1 0.12 → v2 0.06 → v3 0.04). H4a industry-level 분기 (XLF=-0.166 / defensive +0.09, n=752) 만 유효 — H3 regime conditional 은 ALFRED full fetch 후 재검증",
   granularity: industry}
```

### confidence_hooks 갱신 — 격하 + 재검증 조건

```yaml
- hypothesis_id: hy_oas_sleeve_h3_pending_alfred
  confirm_signal: "★ALFRED full fetch + n≥30 + p<0.05 (Block bootstrap or HAC SE) + LOO p<0.05 유지 후에만 verdict CONFIRMED"
  reject_signal: "ALFRED full fetch 후 Credit regime sleeve excess > +0.5%/월 안정 = 자문 prior 부활 신호"
  emit_where: "ALFRED HY OAS fetch 완료 후 run_validation.py H3 block 재실행"
  accumulate_in: "weight_falsification.score_ic_breakdown_eprocess (regime=credit) — ★INSUFFICIENT 상태에서는 e-process 적재 정지"
  confidence_metric: "Block bootstrap (block=4 또는 Stationary) + Welch t-test + LOO sensitivity"
  store: "WeightAssumptionCard.confidence_now (regime=credit sub-key) = PENDING_ALFRED"
  action_threshold: "★v3 현재: credit regime classifier 가중 0.04 cap, 부호 unsigned. ALFRED full fetch 후 재calibrate"
  feeds_weight: "credit_beta base_weight unsigned 동결 → ALFRED 완료 후 해제"
```

### lens 갱신 (블록1) — regime_reading 격하

```
Slowdown/Stagflation: ★v3 INSUFFICIENT (37mo·실 위기표본 부재). Credit Stress regime n=9 단일 cycle (2023-2024) 라
                       BAB defensive thesis 의 confirm/reject 모두 본 데이터로 판정불가. ALFRED HY OAS full
                       historical (2000-01~, 2008 GFC + 2020 COVID 포함) fetch 후 재검증 필수. 현재 상대 권고 = 보수적
                       (★REVERSED 단정 철회 — 방향성 결정 보류).
```

## 한계 (★v3 정직 명시)

- **n=9 INSUFFICIENT** (rule §1.2) — 단정 verdict 금지
- **HY OAS 일별 가용 2023-05~만** — ALFRED full historical fetch 필수 (handoff §4 collector 요청)
- **단일 cycle 표본** — 2008 GFC / 2020 COVID / 2022 inflation cycle 결정적 sample 부재
- **Bootstrap IID 가정 위반** — Block bootstrap 또는 Stationary Bootstrap 미적용 (rule §1.4)
- **sleeve 정의 결함** — XLF 부호 반대 sub-sleeve 결합으로 factor β cancel (v4 sleeve 분리 작업 prerequisite)
- **classify_regime KeyError v3 fix** — silent default 제거, OOS 라벨 분리. 이전 v2 결과는 silent 위에 calibrate
- HY OAS 분위 (p75=3.546) 가 단일 기준 — 분위 변경 (p80, p90) 시 sample 더 감소
- sleeve 정의 = 4 sector eq weight. 시가총액 가중 시 XLF 비중 변화 → 결과 영향

## 참조

- `run_validation.py` H3 block (★v3 classify_regime fix + verdict 격하 출력)
- `validation-metrics.json` h3_hy_oas_regime + h3_hy_data_period (★v3 OOS 명시)
- direction.md §H3 (가설 원문)
- raw/round-1.md ⑤ (위기 유형별 dispersion 핵심 논쟁)
- raw/round-3.md H3 (confirm/reject 조건)
- handoff-bugfix-v3-20260530.md §1 (★KeyError 버그 + LOO 5/9 붕괴 main 독립검증 결과)
- ~/.claude/rules/empirical-claim-presentation.md §1.1 (coverage) + §1.2 (sample n + LOO) + §1.4 (autocorr) + §2 verdict 5단계
- ~/.claude/memory/promotion-log.md ERROR-202605302130 (★v3 root cause)
