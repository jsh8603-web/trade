---
tags: [type/validation, hypothesis/H2, study/eq_us_defensive, phase/2-3]
date: 2026-05-30
hypothesis: H2 — Yield Curve Slope NIM Leading
verdict: ★REJECTED (3-6M lag prior 실측 falsifier)
---

# validation-H2.md — Yield Curve Slope NIM Leading 실측

## 가설 (direction.md §H2)

**(DGS10-DGS2) 월별 변화량이 3~6M lag 로 XLF 내 은행 sub-group 의 excess return (vs SPY) 의 양의 leading 신호**

- Anchor: Stigum's Money Market (2007) — 은행 borrow short, lend long
- Prior: CCF 최적 lag 3~6M, 해당 lag 부호 양 + p<0.05

## 데이터

- **FRED DGS10, DGS2** — 2000-01 ~ 2026-05 (월별 평균 n=317 개월)
- **XLF, SPY** 월별 수익률 (Yahoo Finance)
- **Slope** = DGS10 - DGS2 (월말 평균), Δslope = 월별 차분

## 방법

1. 월별 Δslope_{t-k}, XLF_excess_t = (XLF_ret - SPY_ret)
2. Lag scan: k = 0, 1, 2, 3, 4, 5, 6, 8, 12 — Spearman rank-IC + p

## 결과

### Lag-lag scan (slope_{t-k} → XLF_excess_t)

| lag k (months) | rankIC | p | n | 평가 |
|---:|---:|---:|---:|---|
| **k=0** | **+0.171** | **0.0023** | 317 | ★유일 유의 |
| k=1 | -0.007 | 0.9082 | 316 | 무효 |
| k=2 | +0.015 | 0.7860 | 315 | 무효 |
| k=3 | -0.014 | 0.7985 | 314 | 무효 (prior anchor) |
| k=4 | -0.078 | 0.1673 | 313 | 음의 무유의 |
| k=5 | -0.086 | 0.1306 | 312 | 음의 무유의 |
| k=6 | +0.025 | 0.6625 | 311 | 무효 (prior anchor) |
| k=8 | -0.048 | 0.3991 | 309 | 무효 |
| k=12 | +0.054 | 0.3498 | 305 | 무효 |

### Verdict

★**Best lag = k=0 (contemporaneous), IC = +0.171 (p=0.002)**
- Stigum 의 3-6M lag 효과 **실측 X**
- k=3, k=4, k=5, k=6 모두 무유의 또는 *반대 부호*
- 시장이 slope 변화를 즉시 가격에 반영 — efficient market hypothesis 적합

## 평가

### ★REJECTED — 자문 prior (Stigum lag) 실측 falsifier

이 결과는 **자문 의존 prior 의 위험성을 직접 노출**:
- R1 자문 (Gemini Pro) 이 Stigum 인용해 "3~6M lag" 강조
- R2 검증 design 이 "단일 robust lag k*=4M 고정" 권고
- R3 H2 가설이 "최적 lag 3~6M + p<0.05" 확신 조건 명시
- **실측: lag=0 만 유의 (+0.171), lag=3~6 전부 무효 또는 음수**

R3 가 정의한 H2 의 **reject 조건 정확 매칭**:
> "최적 lag 0 또는 음으로 이동 (선행성 소멸)"

→ 가설 자체 **재정의 필요**: H2 → "slope 변화는 *contemporaneous* 로 XLF excess 와 양의 상관" (lag 없음)

### 시사점

1. **시장 효율성**: 시장이 slope 변화를 실시간 가격 반영. NIM 의 미래 변화는 *이미 가격* 에 있음
2. **NIM 자체 (펀더멘털) vs 가격**: NIM 펀더멘털은 lag 3-6M 일 수 있으나 *주가는 즉시 반응*. EDGAR 실 NIM 데이터 와 가격 분리 검증 필요 (현재 미보유)
3. **시간 가변성**: 전체 표본 (2000~2026) 평균 결과. QE 시기 vs 정상화 시기 별 분해 시 lag 효과 살아날 가능성 (검증 미수행)

## 코드화 권고 (yaml 반영)

### relationships (블록3) — H2 edge 재정의

```yaml
- {node_a: yield_curve_slope, node_b: XLF_excess_return, edge_type: direct,
   conditioning_set: [], lag_routing: contemporaneous,  # ★ lagged → contemporaneous
   prior_sign: pos, prior_strength: 0.17,  # 실측 IC
   theory_basis: "★실측 contemporaneous IC=+0.171 p=0.002 (n=317 월). Stigum 의 3-6M lag 효과는 가격 X, NIM 펀더멘털만 가능"}
```

### weight_rules (블록4) — yield_curve_slope_beta 재calibrate

기존 v1 base_weight=0.10 (Stigum 3-6M lag 가정) → **실측 lag=0 기반**:

```yaml
- {indicator_id: yield_curve_slope_beta, base_weight: 0.08,  # 실측 effect size 반영
   modulate_by: [regime, industry],
   direction: "★실측 contemporaneous 양 IC=+0.171 (lag=0 만 유의). Stigum 의 3-6M lag 가격엔 미반영 (시장 효율성). XLF banks 한정 작동",
   granularity: industry}
```

### confidence_hooks 갱신 경로

- **confirm**: 분기별 (rolling 60M) contemporaneous IC > +0.1 + p < 0.10 유지
- **reject (이미 진입)**: prior lag 3-6M 시점 IC > +0.1 + p < 0.05 가 24M 이상 지속 — 시장 비효율 시기 (이론 부활)
- **action**: 실측 기반 lag=0 운영 + 분기 모니터로 lag 부활 감지

### lens 갱신 (블록1)

estimation_note 에 추가:
> "★2-3 실측: 2-10Y slope 가 XLF excess 와 contemporaneous 양 상관 (IC=+0.171 p=0.002 n=317 월). Stigum 의 3-6M lag 효과 실데이터 미관측 (시장 효율성). 가설 자체를 lag=0 로 재정의."

## 한계

- 가격 (XLF return) ≠ 펀더멘털 (NIM). NIM 자체의 lag 3-6M 가능성 존재 (EDGAR 직접 검증 미수행)
- 전체 표본 평균. QE 시기/정상화 시기 분해 미수행 — lag 효과의 regime-conditional 가능성
- XLF = banks + insurance + payments 통합 ETF. 순수 bank index (KBW BKX) 사용 시 결과 차이 가능성

## 참조

- `run_validation.py` lines 120~165 (H2 block)
- `validation-metrics.json` h2_yield_curve_lead_lag
- direction.md §H2 (가설 원문)
- raw/round-2.md (R2 단일 robust lag k* 권고 — falsifier)
