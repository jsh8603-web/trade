---
tags: [type/validation, study_id/reit, hypothesis/H4, phase/2-3]
date: 2026-05-30
hypothesis_id: H4
verdict: CONFIRMED
note: STUDY-KIT §2 v2 2-3단계 실데이터 시계열 검증. 합성·시뮬 데이터 미사용 — Yahoo Finance 실가격 OHLC.
---

# H4 (Window Flip meta-가설) — 실데이터 검증

## §1. 가설 (direction.md / round-3.md 출처)

**명제**: REIT sub-sector cross-sectional ranking 은 evaluation window 길이 (1d/30d/90d/365d/730d)
에 따라 *flip* 한다 — 단일 window regime 매핑은 본질적으로 noise.
- **confirm**: mean swap rate (1+ tier ranking 변동 비율) > 30% 또는 Kendall τ < 0.7.
- **reject**: window 길이 무관 일관 ranking (Kendall τ > 0.7).

## §2. 데이터 (실측, 합성·시뮬 미사용)

- **source**: Yahoo Finance (yfinance 1.4.1) — adjusted close (auto_adjust=True).
- **sample period**: 2018-01-02 ~ 2026-05-28 (n_days = 2112 trading days).
- **tickers** (9 REIT sub-sector 대표 종목):
  - Industrial: PLD (Prologis)
  - Apartment: AVB (AvalonBay)
  - Office: BXP (Boston Properties)
  - Healthcare: WELL (Welltower)
  - Datacenter: EQIX (Equinix)
  - Storage: PSA (Public Storage)
  - Retail: SPG (Simon Property)
  - Hotel: HST (Host Hotels & Resorts)
  - Specialty: AMT (American Tower) — cell tower
- **anchors**: monthly month-end 2020-01-31 ~ 2026-05-28 = **n = 77 anchor dates**.
- **windows**: 1d / 30d / 90d / 365d / 730d trading days lookback.
- **missing data**: 0 (full data for 9 ticker × 2112 day, ★ survivorship bias 없음 — 9 종목 모두
  현재 listed + 2018 이전부터 존재).

## §3. 결과 (★ verbatim from script output)

### §3-1. Window 쌍별 Kendall τ + Swap rate

| Window pair | n | mean τ | std τ | mean swap% (≥1 tier) | frac swap≥2 tier |
|---|---:|---:|---:|---:|---:|
| **1d vs 30d** | 77 | **0.043** | 0.306 | **89.3%** | 66.5% |
| 30d vs 90d | 77 | 0.364 | 0.326 | 77.3% | 52.1% |
| 90d vs 365d | 77 | 0.320 | 0.341 | 78.8% | 55.6% |
| 365d vs 730d | 67 | 0.424 | 0.283 | 72.1% | 46.9% |
| **1d vs 365d** | 77 | **0.043** | 0.328 | **87.4%** | 68.0% |
| 30d vs 730d | 67 | 0.143 | 0.324 | 87.7% | 59.0% |
| **1d vs 730d** | 67 | **0.051** | 0.326 | **88.9%** | 64.2% |

★ **단기 vs 장기 (1d↔365d, 1d↔730d) 의 Kendall τ ≈ 0.04~0.05 = 거의 random.** 인접 window (30d→90d,
90d→365d) 끼리는 약한 양의 상관 (0.32~0.36). 장 vs 장 (365d→730d) 만 의미 있는 양 (0.424).

### §3-2. Per-sector flip frequency (1d vs 365d ranking |Δrank| 분포)

| Sector | n | mean \|Δrank\| | frac \|Δ\|≥3 |
|---|---:|---:|---:|
| Specialty (AMT) | 77 | 3.29 | **63.6%** |
| Datacenter (EQIX) | 77 | 3.19 | 59.7% |
| Hotel (HST) | 77 | 2.87 | 55.8% |
| Storage (PSA) | 77 | 2.86 | 54.5% |
| Retail (SPG) | 77 | 3.23 | 53.2% |
| Office (BXP) | 77 | 2.84 | 51.9% |
| Industrial (PLD) | 77 | 2.57 | 50.6% |
| Healthcare (WELL) | 77 | 2.90 | 48.1% |
| Apartment (AVB) | 77 | 2.14 | **35.1%** |

★ 가장 큰 flip = Specialty (cell tower, AMT) + Datacenter (EQIX). 가장 안정 = Apartment (AVB)
하지만 그것도 35.1% 가 |Δrank|≥3 → 9 sector 중 3+ tier 변동 = 비-trivial.

### §3-3. Verdict

- Mean Kendall τ (short vs long window pairs avg): **0.077** ← essentially random
- Mean swap rate (≥1 tier): **88.0%**
- 둘 다 confirm threshold 만족 (swap > 30% AND τ < 0.7) → ✅ **H4 CONFIRMED**

## §4. 8축 self-audit (이 validation 본 결과만)

| 축 | 평가 | 메모 |
|---|---|---|
| A 이론실재성 | ✓ | direction.md/round-3.md 가설 명문 |
| B 실데이터검증 | ✓ | 실가격 시계열 (Yahoo, 합성 미사용), n=77, period 2020-01~2026-05 |
| C yaml 도출추적성 | (다음) | study_session.yaml v2 의 block1 lens regime_reading 단정 강등 + block4 modulate_by 에 'window_length' 추가의 root cause |
| D PIT·OOS | △ | anchor 시점 기준 lookback only (lookahead 없음). 단 같은 시계열 다회 sampling → block bootstrap autocorr 보정은 추가 보강 가능 |
| E 자문비판+환각cross-verify | ✓ | 본 결과는 Round 2 의 "2025 Dec healthcare top↔worst" 일관, primary 데이터로 cross-verified |
| F 반증가능+기각기록 | ✓ | reject 조건 (τ>0.7) 명문, 실측 τ=0.077 → 명확히 reject 조건 미달 → confirm |
| G 검정력한계 | △ | 9 sector 만 (representative 1 ticker each). 같은 sector 내 dispersion 미포함. 단 sector-level ranking 의 flip 명확. ticker-level 일반화는 별도 검증 필요 |
| H 미해결의문 | △ | (a) ticker 단일 대표가 sub-sector 전체 noisy proxy 가능 — sector ETF 또는 multi-ticker average 로 보강 가치 (b) survivor bias 부재 검증됨 (9 종목 모두 2018+ 생존) |

★ G/H 축의 ticker representativeness 보강 = 후속 validation 또는 v2 yaml 의 caveat 명기.

## §5. v2 yaml 반영 (study_session.yaml v2 의 어느 칸이 본 결과로 정해지는가)

1. **block1 lens.regime_reading**: 단순 "Reflation→industrial 강세" 류 단정 제거. "regime 라벨은
   window 길이에 강하게 의존 (Kendall τ ~ 0.04 short vs long) → 동일 regime 라벨 안에서도 1d/30d/
   12m ranking 이 random 에 가까움" 로 reframe.
2. **block3 relationships**: sub_sector_membership ↔ forward_return edge 의 lag_routing 가
   evaluation window 에 따라 다름 명시.
3. **block4 weight_rules**: modulate_by enum 에 `window_length` 추가 (regime / industry / size /
   name_specific / **window_length**). 또는 `regime × window_length` joint 명시.
4. **block5 confidence_hooks**: H4 의 confirm 결과를 lens.estimation_note 의 "단정 매핑은 본질적
   noise" 신뢰도 누적 path. ⚠ H4 가 confirm 되면 다른 가설 (H1, H2, H3, H5) 의 evaluation window
   를 명시적으로 보고하는 게 prerequisite.

## §6. 잔존 caveat (다음 validation 으로 보강)

- ticker-level representativeness: 9 대표 종목이 sub-sector 전체를 fully 대표하지 못함. ETF 또는
  sector-average 로 robustness 검증 후속.
- 거시 regime 라벨 conditioning 미적용: 본 결과는 unconditional cross-section. regime-conditional
  swap rate 는 H5 validation 에서 추가.
- anchor 의 시계열 dependence: monthly month-end anchor 가 가까운 시점일수록 상관. block bootstrap
  으로 보정한 effective-n 산출은 별도 분석.

## §7. 산출 파일

- script: `raw/scripts/h4_window_flip.py` (37 lines, 결정론, seed 무관)
- log: `raw/scripts/h4_window_flip.log` (verbatim stdout)
- 본 분석: `raw/validation-H4.md`
