---
tags: [type/validation, hypothesis/H4, study/eq_us_defensive, phase/2-3]
date: 2026-05-30
hypothesis: H4a — Credit Beta Sub-sleeve Sign Split (proxy for H4 quality factor)
verdict: PARTIAL CONFIRMED (partial-corr sign split 명확, 단 short window n=752 일)
---

# validation-H4.md — Credit Beta + Quality Factor 실측

## 가설 (direction.md §H4, R3 H4)

**원안 H4**: 2단계 정규화 Quality 복합 z (ROE·FCF/Asset·D/E) 가 Slowdown regime 에서 3M forward Rank-IC ≥ +0.08 (Asness QMJ).

**Proxy 변경 사유**: 종목 단위 ROE/FCF/D/E 데이터 부재 (EDGAR 자체 파싱 미수행 — direction.md TBD #2). 대안으로 **H4a 부호 분기 측면** 실측.

**H4a**: ΔHY OAS (credit cycle leading) 에 대해 sub-sleeve partial-corr 부호 분기
- 방어 (XLU/XLP/XLV): partial IC POS (시장 베타 흡수 후 회복력)
- 금융 (XLF): partial IC NEG (provisioning channel 시장 베타 초과)

## 데이터

- **FRED BAMLH0A0HYM2** 일별 — **2023-05-30 ~ 2026-05-28** (n=752 일, ★short window)
- **ETF**: XLU/XLP/XLV/XLF/XLC/SPY 일별 returns
- FRED BAMLH0A0HYM2 일별 시리즈가 2023-05 부터만 가용 (cyclical 방에서 가져온 데이터 한계 — 이전은 월별만)

## 방법

1. 일별 ΔHY OAS
2. 각 sector 의 β(ΔHY OAS) + Spearman rank-IC (전체)
3. SPY-controlled partial-corr (Spearman) — `partial(d_HY, r_sector | SPY)`

## 결과 (n=752 일, 2023-05-31 ~ 2026-05-28)

| sector | β(d_HY) | rankIC | p | partial IC \| SPY | partial p | n |
|---|---:|---:|---:|---:|---:|---:|
| XLU | -0.0218 | -0.099 | 0.007 | **+0.076** | 0.038 | 752 |
| XLP | -0.0120 | -0.057 | 0.121 | **+0.105** | 0.004 | 752 |
| XLV | -0.0308 | -0.177 | <0.001 | **+0.091** | 0.013 | 752 |
| **XLF** | -0.0774 | -0.448 | <0.001 | **-0.166** | **<0.001** | 752 |
| XLC | -0.0706 | -0.403 | <0.001 | +0.005 | 0.888 | 752 |
| SPY | -0.0798 | -0.521 | <0.001 | N/A | N/A | 752 |

## 평가

### ★Partial IC Sign Split CONFIRMED (Defensive vs Financial)

- **방어 3 sector (XLU/XLP/XLV) 모두 partial IC POS**: +0.076 ~ +0.105 (p < 0.04 전부)
- **XLF partial IC = -0.166** (p<0.001) — banks 가 시장 베타 흡수 후에도 *추가 부정적*
- 부호 차이: 방어 mean +0.091 vs financial -0.166 = **gap 0.257** (강력)
- XLC = 무유의 (+0.005, p=0.89) — Comm Services 가 credit cycle 채널과 무관

### 해석

1. **전체 β(d_HY) 음수**: risk-off 시 모든 자산 하락 (정상)
2. **partial-corr 후 부호 분기**: SPY (시장 베타) 가 risk-off 의 *공통 채널* 흡수 → 잔여 신호
   - 방어주 (+) = SPY 가 알아주는 risk-off effect 흡수 후, 방어주는 *상대적* 회복력 (residual POS)
   - **XLF 추가 NEG (-0.166)** = SPY beta 흡수 후에도 banks 특화 *provisioning channel* 잔여 (R2 H2 의 Q+1~2 lag 매개)

### prior vs 실측 비교

| prior (R3 H4 design) | 실측 (n=752) | 평가 |
|---|---|---|
| sub-sleeve credit beta 부호 분기 (defensive POS, financial NEG) | 정량 일치 (def +0.091 mean, fin -0.166) | ★CONFIRMED |
| 방어 + XLC 동일 그룹 | XLC partial IC ≈ 0 — 다른 archetype | XLC 분리 필요 |
| XLV 도 방어 그룹 | partial IC = +0.091 (XLP/XLU 와 동일) | XLV 방어 그룹 정합 |

### H4 원안 (Quality Factor) 검증 불가

- ROE/FCF/D/E 종목 단위 데이터 미보유 → Asness QMJ 직접 검증 불가
- **EDGAR 자체 파싱 (블록6 #5~#8) 가 critical path** — main TBD #2 의 결론에 따라 차기 cycle 검증

## 코드화 권고 (yaml 반영)

### relationships (블록3) — H4a edge 등록

```yaml
- {node_a: hy_oas_change, node_b: XLF_return, edge_type: direct,
   conditioning_set: [SPY_return], prior_sign: neg, prior_strength: 0.17,  # 실측 |partial IC|
   theory_basis: "★실측 partial IC=-0.166 p<0.001 (n=752 일). banks 의 provisioning channel 이 시장 베타 초과. defensive +0.09 평균 (XLU/XLP/XLV)"}

- {node_a: hy_oas_change, node_b: XLU_return, edge_type: direct,
   conditioning_set: [SPY_return], prior_sign: pos, prior_strength: 0.08,
   theory_basis: "방어 회복력 (시장 베타 흡수 후 residual POS). 실측 partial IC=+0.076 p=0.04"}
```

### weight_rules (블록4) — credit_beta industry-level 부호 분기

```yaml
- {indicator_id: credit_beta, base_weight: 0.06,  # H3 결과로 절반 강등
   modulate_by: [regime, industry],
   direction: "★실측 industry-level 부호 분기: banks partial IC=-0.166 (provisioning channel) / defensives partial IC=+0.09 (시장 베타 흡수 후 residual POS). XLC=무유의 (별도 archetype)",
   granularity: industry}
```

### confidence_hooks 갱신 경로

```yaml
- hypothesis_id: credit_beta_sub_sleeve_split
  confirm_signal: "전체 표본 (rolling 24M) partial IC|SPY 가 defensive > 0 AND XLF < 0 유지. gap > 0.15"
  reject_signal: "gap < 0.05 (sub-sleeve 분기 무효) 12M 지속"
  emit_where: "분기별 partial IC 측정 (FRED BAMLH0A0HYM2 일별 데이터 가용 확장 후)"
  accumulate_in: "weight_falsification.score_ic_breakdown_eprocess"
  confidence_metric: "Spearman partial IC gap (defensive mean - XLF)"
  store: "registry WeightAssumptionCard.confidence_now"
  action_threshold: "gap > 0.15 → credit_beta industry 분기 유지 / gap < 0.05 → industry 통합"
  feeds_weight: "credit_beta delta_arch_by_type 의 banks 부호 분기 강도 동적 조정"
```

## 한계

★**Critical**: HY OAS 일별 시리즈 가용 = 2023-05~만 (cyclical 방 데이터 한계). 실 검증 표본 = 3년만
- **권고**: FRED ALFRED 에서 BAMLH0A0HYM2 일별 historical 추가 fetch (2000-01 부터 가용) → n=5800+ 일 재검증

기타:
- partial-corr conditioning = SPY only. {SPY, ΔVIX, ΔDFII10} 다중 conditioning 시 정확도 향상
- H4 원안 (Quality QMJ Slowdown Rank-IC) 미검증 — 종목 단위 ROE/FCF/D/E 데이터 필요
- 단 sleeve 정의 = 4 sector (XLP/XLU/XLV/XLF). 시가총액 가중 시 결과 영향

## 참조

- `run_validation.py` lines 285~330 (H4a block)
- `validation-metrics.json` h4_credit_beta
- direction.md §H4 (가설 원문)
- raw/round-2.md (R2 conditioning set {SPY, HY_OAS_change} 권고)
- raw/round-4.md (R4 Spearman 즉시 도입 Priority 1 권고 — 본 검증에 적용)
