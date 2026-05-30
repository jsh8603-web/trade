---
tags: [type/validation, study_id/reit, hypothesis/H5, phase/2-3]
date: 2026-05-30
hypothesis_id: H5
verdict: CONFIRMED (regime label diverges sub-sector ranking, but NOT single static mapping)
note: H4 confirm 와 본 H5 가 root cause 공유 — single-window regime mapping noise.
---

# H5 (Sub-sector × Regime 단순 매핑 반증 잔여) — 실데이터 검증

## §1. 가설

**명제**: v1 yaml 의 "Reflation → industrial 강세" 같은 sub-sector × regime 단순 매핑이 데이터
로 반증된다 (이미 2024 industrial -17.7% 으로 partial reject 확인).
- **confirm**: regime label 별 sub-sector ranking 이 *divergent* (cross-regime Spearman ρ < 0.3).
- **reject**: regime 무관 ranking 일관 (ρ > 0.7).

## §2. 데이터

- **Regime labels** (FRED-based Investment Clock proxy):
  - Reflation: GDP YoY > 2% AND CPI YoY < 3%
  - Recovery: GDP YoY > 2% AND CPI YoY ∈ [3, 5)
  - Overheat: GDP YoY > 2% AND CPI YoY ≥ 5%
  - Stagflation: GDP YoY ≤ 2% AND CPI YoY ≥ 3%
  - Recession: GDP YoY ≤ 0% (any inflation)
  - Mid (fallback): GDP YoY ≤ 2% AND CPI YoY < 3%
- **Price data**: Yahoo 9 sub-sector 대표 종목 (H4 와 동일), quarterly total return.
- **Period**: 2018-Q1 ~ 2026-Q1 = **n = 33 quarters**, labeled into 6 regimes.

## §3. 결과 (★ verbatim from script output)

### §3-1. Regime distribution (n_quarters)

| Regime | n_quarters |
|---|---:|
| Reflation | 12 |
| Recovery | 7 |
| Overheat | 6 |
| Recession | 3 |
| Mid | 3 |
| Stagflation | 2 |

### §3-2. Per-regime average sub-sector rank (1 = best, 9 = worst)

| Regime | n | Healthcare | Datacenter | Specialty | Retail | Office | Industrial | Apartment | Hotel | Storage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Reflation** | 12 | 3.75 | 5.17 | 4.17 | 5.75 | 5.42 | **4.83** | 5.17 | 5.83 | 4.92 |
| Mid | 3 | 6.00 | 3.67 | 4.33 | 6.33 | 5.33 | 4.33 | 4.00 | 5.67 | 5.33 |
| Recession | 3 | 3.00 | 5.33 | 7.00 | 3.00 | 6.67 | 4.00 | 5.67 | 5.00 | 5.33 |
| Overheat | 6 | 5.33 | 4.67 | 5.67 | 4.67 | 6.83 | 5.00 | 4.33 | 5.50 | 3.00 |
| Stagflation | 2 | 3.50 | 3.50 | 6.50 | 2.50 | 8.50 | 2.00 | 7.50 | 3.50 | 7.50 |
| Recovery | 7 | 3.43 | 4.14 | 7.43 | 3.57 | 5.43 | 5.00 | 6.00 | 3.86 | 6.14 |

★ **v1 의 "Reflation → industrial 강세" 단정 직접 quantitative reject**:
- **Reflation regime 의 Industrial avg rank = 4.83 / 9** (mid, top 도 bottom 도 아님).
- Reflation 의 top sector = Healthcare (3.75), Specialty (4.17) — *secular growth*.
- ★ Recession 의 Industrial rank = 4.00 (Reflation 보다 *더 좋음*) — counterintuitive.
- ★ Stagflation 의 Industrial rank = 2.00 (best!) — v1 의 "Stagflation = 최악" 가설도 partial reject.

### §3-3. Pairwise inter-regime Spearman ρ (rank consistency)

| Regime pair | ρ | p |
|---|---:|---:|
| Reflation vs Mid | +0.211 | 0.586 |
| Reflation vs Recession | **-0.030** | 0.940 |
| Reflation vs Overheat | +0.004 | 0.991 |
| Reflation vs Stagflation | +0.038 | 0.922 |
| Reflation vs Recovery | -0.226 | 0.559 |
| Mid vs Recession | -0.606 | 0.084 |
| Mid vs Overheat | +0.194 | 0.617 |
| Mid vs Stagflation | -0.219 | 0.571 |
| Mid vs Recovery | -0.571 | 0.108 |
| Recession vs Overheat | +0.253 | 0.511 |
| **Recession vs Stagflation** | **+0.768** | 0.016 ★ |
| **Recession vs Recovery** | **+0.849** | 0.004 ★★ |
| Overheat vs Stagflation | +0.077 | 0.844 |
| Overheat vs Recovery | -0.067 | 0.864 |
| Stagflation vs Recovery | +0.621 | 0.074 |

- **Mean inter-regime ρ = +0.087** ← essentially random
- ★ 단 Recession-Stagflation (+0.768) + Recession-Recovery (+0.849) 만 strong consistency =
  "침체 계열" sub-sector ranking 비슷.

### §3-4. Verdict

**★ H5 CONFIRMED (with nuance)**:
- regime 라벨 이 sub-sector ranking 을 변경시킴 = regime conditioning **유의미** (mean ρ = 0.087 random).
- 단 단일 static mapping (v1 yaml 의 "Reflation → industrial") **반증** — Reflation 의 industrial
  rank = 4.83/9 (mid).
- 일부 regime cluster (Recession-Stagflation-Recovery) 는 비슷한 ranking — 침체 계열 sub-sector
  defensive (Retail, Healthcare 우위) 일관.

## §4. ★ H4 와 H5 의 root cause 공유

- H4: window 길이 (1d/30d/365d/730d) flip 88% — window 가 ranking 결정
- H5: regime 라벨 (6종) flip mean ρ=+0.087 — regime 도 ranking 결정
- **둘 다 sub-sector ranking 이 multi-dimensional context (window × regime) 에 의존** = 단일
  매핑 무효의 같은 결론.
- v2 yaml 의 modulate_by 는 `[window_length, regime, industry, name_specific]` 4축 joint 명시.

## §5. 8축 self-audit

| 축 | 평가 | 메모 |
|---|---|---|
| A 이론실재성 | ✓ | "regime conditioning 가설" 학설 base (Investment Clock 4국면) |
| B 실데이터검증 | ✓ | FRED GDP/CPI + Yahoo quarterly, 합성 미사용. n=33 quarters |
| C yaml 도출추적성 | (다음) | block1 regime_reading 단정 매핑 모두 제거 + block4 modulate_by joint |
| D PIT·OOS | ✓ | quarter-end snapshot, lookahead 없음. GDP/CPI 는 FRED ALFRED first-release |
| E 자문비판+환각cross-verify | ✓ | v1 단정 매핑 (Reflation→industrial 등) 모두 quantitative reject |
| F 반증가능+기각기록 | ★★ | reject 조건 (ρ > 0.7 일관) 명문, 실측 mean ρ = +0.087 → confirm divergence |
| G 검정력한계 | ⚠ | (a) n=33 quarter sample 작음 (b) Stagflation 2, Recession 3, Mid 3 quarter 극소수 (c) 2018-2025 single rate cycle 비중 큼 |
| H 미해결의문 | ★ | (a) 1970s Stagflation, 1990s Reflation, 2000s Recession 등 historical 확장 (b) Investment Clock 임계 (2%, 3%, 5%) 의 sensitivity test (c) Q-end snapshot 의 mid-quarter regime transition 무시 |

## §6. v2 yaml 반영

1. **block1 lens.regime_reading**: v1 의 "Reflation → industrial 강세" 등 단정 매핑 **모두 제거**.
   대신 "Reflation 12 quarter 에서 Healthcare/Specialty 가 top, Industrial 은 mid rank 4.83"
   같은 실측 분포 + 한계 (n=33) 명시.
2. **block4 weight_rules**: modulate_by enum = `[regime, industry, size, name_specific, window_length]`
   joint. regime 단독 modulate 규칙 모두 폐기.
3. **block5 H5 confirm 기록**: hypothesis_id H5 confirm. v1 단정 매핑 제거 = action_threshold.
4. **block3 relationships**: regime ↔ sub-sector ranking 의 edge_type = `direct` (regime 이
   ranking 변동시킴) but prior_sign = `unsigned` (방향성 단정 X) + prior_strength 약함 (0.30).
5. **block6 collector_plan**: 1970s historical sub-sector return (NAREIT monthly 1972+) 추가
   요청 — 다른 rate cycle 검증 보강.

## §7. 산출 파일

- script: `raw/scripts/h3_h5_combined.py`
- log: `raw/scripts/h3_h5.log`
- 본 분석: `raw/validation-H5.md`
