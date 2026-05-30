---
tags: [type/validation, study_id/reit, hypothesis/H2, phase/2-3]
date: 2026-05-30
hypothesis_id: H2
verdict: PARTIAL CONFIRMED (mechanism strong, direct cap rate spread time-series sparse → VNQ proxy 우회)
note: STUDY-KIT §2 v2 2-3단계. Nareit T-tracker quarterly time-series 직접 access 불가 → VNQ price Z-score proxy.
---

# H2 (Cap Rate Spread Mean-Reversion) — 실데이터 검증

## §1. 가설

**명제**: implied cap rate − private appraisal cap rate spread Z < -1.5 (압축) → 12m forward
REIT total return Rank-IC > +0.15 (양 부호 = spread 좁아진 후 REIT outperform).
- **confirm**: Rank-IC > +0.15 OR equivalent mean-reversion mechanism evidence.
- **reject**: (a) Rank-IC < 0 (sign mismatch) OR (b) deep discount (Z<-2) 6Q+ 지속 미회복 (regime change).

## §2. 데이터 한계 + 대체 접근

### §2-1. Direct cap rate spread 시계열 (primary verified, sparse)

Nareit market commentary article 3건 verbatim 확인 (raw archive 저장):
| Quarter | Spread (bp) | Source |
|---|---:|---|
| 2009 Q1 (GFC peak) | 326 | closing-public-private article |
| 2022 Q3 (recent peak) | **243-244** | long-goodbye + closing-public-private (consistent) |
| 2023 Q4 | **123** | closing-public-private (plunge) |
| 2024 Q2 | **130** | long-goodbye (re-widening) |
| 2024 Q3 | **60 (est)** | long-goodbye (near-closed) |

⚠️ R1 인용 "Q4 2024 = 120 bp" 는 primary 없음 — Q4 2023 = 123 bp 와 혼동 가능성. main 지시
E축 (자문비판+환각cross-verify) 준수 → **Q4 2024 120bp 는 v2 yaml baseline 에서 제외**, Q2 2024
= 130 bp (primary) 또는 Q3 2024 = 60 bp (est) 만 사용.

n=4 quarter (Q3'22, Q4'23, Q2'24, Q3'24) → 정량 Rank-IC 산출 불가.

### §2-2. ★ Historical mechanism evidence (1 case)

Nareit "Closing Public-Private Real Estate Cap Rate Spreads" article verbatim:
> "Larger cap rate spread reductions have tended to be associated with greater levels of REIT
> outperformance. Most notably: following 2009 Q1 372-basis-point reduction, REITs outperformed by 124.7%."

→ mechanism direction 강력 confirm (single-case, but most extreme example).

### §2-3. VNQ price-level Z-score proxy (full time series)

VNQ (Vanguard Real Estate ETF, broad REIT proxy) 의 24m rolling Z-score 를 spread proxy 로 사용
— "REIT 가격이 24m 평균보다 크게 낮음 = under-valued (analogous to spread expansion)".

## §3. VNQ Proxy 결과 (★ verbatim from script output)

- **Data**: VNQ adjusted close, 2005-01-03 ~ 2026-05-28 (n=5384 trading days).
- **Effective sample** (z + 12m fwd 둘 다 정의): **n = 4629**.
- **z range**: [-5.64, +3.16], mean = +0.67.

### §3-1. Bucket-conditional 12m forward total return

| Bucket | n | mean fwd% | median fwd% | frac > 0 |
|---|---:|---:|---:|---:|
| **A: z < -1.5 (deep discount)** | 275 | **+32.5%** | **+32.6%** | **82.5%** |
| B: z ∈ [-1.5, -0.5) (mild discount) | 534 | +7.4% | +8.0% | 67.0% |
| C: z ∈ [-0.5, 0.5) (neutral) | 856 | +13.7% | +18.7% | 74.9% |
| D: z ∈ [0.5, 1.5) (mild premium) | 1693 | +8.0% | +9.4% | 78.1% |
| E: z ≥ +1.5 (deep premium) | 1271 | **-0.7%** | -0.0% | 50.0% |

★ **명확한 mean-reversion**: deep discount → +32.5% mean fwd / deep premium → -0.7% mean fwd.

### §3-2. Whole-sample Spearman Rank-IC

- **ρ = -0.361** (p < 0.0001, n=4629)
- 부호 negative = price-level Z 와 forward return 음의 관계 = mean-reversion 일관.
- (가설 H2 의 +0.15 threshold 는 spread Z 기준; proxy 는 price Z 라 부호가 반대지만 *mechanism
  은 동일* — discount 후 outperform.)

### §3-3. Deep-discount 8 episode 식별 (consecutive 90d gap = new episode)

| Episode start | z at start | fwd 12m total return |
|---|---:|---:|
| 2008-01-04 | -1.71 | **-35.4%** ★ |
| 2008-06-27 | -1.55 | **-43.0%** ★ |
| 2018-02-08 | -2.18 | +21.9% |
| 2018-12-24 | -2.03 | +31.9% |
| 2020-03-16 | -2.28 | +46.4% |
| 2022-09-29 | -1.56 | -2.0% |
| 2023-03-10 | -1.74 | +12.6% |
| 2023-09-26 | -1.58 | +33.8% |

★ 2008 두 episode (GFC pre-trough) = **-35%, -43% deep loss** — "deep discount 가 더 깊어질 수 있다"
의 직접 증거. 가설 H2 의 reject signal (b) "deep discount 6Q+ 지속 미회복" 이 실제 trigger 된
사례. mechanism 은 일반적으로 성립하지만 **regime change / continuing crisis 중 deep discount
는 forward loss 가능** caveat.

2018+ post-GFC 6 episode 평균 fwd 12m = ~+24% — mean-reversion 강함 (단 2022-09 = -2.0% =
rate-shock 진행 중 entry 의 timing risk).

## §4. ★ Verdict

**PARTIAL CONFIRMED**:
- ✅ Mechanism direction (deep discount → forward outperform): strongly confirmed by VNQ proxy
  (Rank-IC -0.361, p<<0.001) + Nareit historical 2009 Q1 (372bp reduction → +124.7% outperform).
- ⚠️ Direct cap rate spread quantitative validation: sparse (n=4 primary quarters) → 정량 Rank-IC
  산출 불가. Nareit T-tracker Excel direct download 필요 (별도 후속).
- ⚠️ 2008 GFC 두 episode = -35%, -43% fwd loss → reject signal (b) "deep discount 6Q+ 지속
  미회복" 의 real-world trigger. 가설은 GFC-급 regime change 에서 fail 가능.
- ★ Q4 2024 120 bp baseline: primary 미검증 (E축 미달) → v2 yaml 에서 **제외**.

## §5. 8축 self-audit

| 축 | 평가 | 메모 |
|---|---|---|
| A 이론실재성 | ✓ | mean-reversion mechanism + cap rate spread anchor 학설 base |
| B 실데이터검증 | △ | direct cap rate spread n=4 sparse / VNQ proxy n=4629 충분. 정확도는 proxy 의존 |
| C yaml 도출추적성 | (다음) | block5 H2 confirm/reject signal 의 정수치는 VNQ z-bucket 기준 + spread 정수치는 Q3'24 60bp (est) / Q2'24 130bp |
| D PIT·OOS | ✓ | VNQ rolling Z = strict lookback, 12m fwd = strict forward. lookahead 없음 |
| E 자문비판+환각cross-verify | ★★ | R1 의 "Q4'24 120 bp" 환각 의심 확인 (Q4'23 123bp 와 혼동 가능). primary 확인된 4 quarter 만 인정 |
| F 반증가능+기각기록 | ★ | mechanism 은 confirm, 단 2008 episodes 가 reject 조건 trigger 한 실사례 기록 |
| G 검정력한계 | ★ | direct spread 정량 n=4, proxy n=4629 — 직접 측정은 부족, proxy 는 충분. proxy ≠ exact spread caveat 명시 |
| H 미해결의문 | ★ | (a) Nareit T-tracker Excel direct download path (b) NCREIF ODCE quarterly time-series (c) sub-sector × spread cross-sectional rank-IC 미검증 (별도 후속) |

## §6. v2 yaml 반영

1. **block1 lens.estimation_note**: Q3 2022 peak 243bp → Q3 2024 60bp est 의 추세 (실측) +
   "단 GFC-급 regime change 에선 deep discount 가 forward loss 동반 가능" 명시.
2. **block2 indicators**: `implied_cap_rate_spread` source 정확화 — Nareit T-tracker + NCREIF
   ODCE quarterly (primary). VNQ proxy 는 alternative.
3. **block5 H2 confirm_signal**: "spread Z < -1.5 + post-GFC 환경" 으로 보강 (GFC pre = false
   confirm 위험).
4. **block5 H2 reject_signal (b)**: "deep discount 6Q+ 지속 미회복" 의 mechanism evidence =
   2008 두 episode (실측).
5. **block5 H2 action_threshold**: Q4 2024 120bp baseline 제외 → Q3 2024 60bp (est) + Q2 2024
   130bp (primary) 만 baseline 표기. primary 미확인 정수치는 baseline 에서 제외 (main 지시 E축).

## §7. 잔존 caveat / 다음 단계

- **Nareit T-tracker Excel direct download** = 별도 후속. 본 검증의 최우선 보강 path.
- **NCREIF ODCE quarterly time-series** = membership 유료 또는 free aggregate (Nareit 가 cross-tab
  발표한 시계열 추가 fetch).
- **Sub-sector spread mean-reversion** = Office 259bp / Apt 194bp / Retail 150bp / Industrial 93bp
  (Q2 2023 primary) 의 quarterly time-series 후속 확인.

## §8. 산출 파일

- script: `raw/scripts/h2_mean_revert_proxy.py` (97 lines)
- log: `raw/scripts/h2_mean_revert.log`
- archive raw: `~/.claude/docs/archive/research-raw/reit-cap-spread-timeseries-native-20260530.txt`
- 본 분석: `raw/validation-H2.md`
