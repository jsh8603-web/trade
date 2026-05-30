---
tags: [type/validation, study_id/reit, hypothesis/H1, phase/2-3]
date: 2026-05-30
hypothesis_id: H1
verdict: REJECTED (★ sign mismatch — long-WALT outperform, not underperform)
note: STUDY-KIT §2 v2 2-3단계 실데이터 시계열 검증. Yahoo Finance + FRED DGS10 실데이터.
---

# H1 (Long-WALT Rate-shock Cross-section Underperformance) — 실데이터 검증

## §1. 가설 (direction.md / round-3.md 출처)

**명제**: rate-shock window (DGS10 4w Δ > +50bp) 진입 후 60-90d, long-WALT REIT (top tertile)
가 short-WALT REIT (bottom tertile) 보다 cross-sectional total return 으로 낮다.
- **confirm**: cross-section Rank-IC (WALT_rank vs forward_60d_return_rank) < -0.05 평균
  → long-WALT 가 underperform (음 부호 = long-WALT 가 fwd return 낮음).
- **reject**: sign mismatch (Rank-IC > +0.05) 또는 inconclusive (|Rank-IC|<0.05).

**이론 mechanism (Round 2 학설 정리)**: long-duration cash-flow asset (긴 WALT) 의 discount rate
sensitivity 높음 → rate-shock 시 더 큰 multiple contraction.

## §2. 데이터 (실측, 합성·시뮬 미사용)

- **WALT proxy** (sector-average, practitioner standard):
  - Healthcare 12y > Datacenter 8y ~ Specialty 8y > Retail 7y > Office 6y > Industrial 5y >
    Apartment 1y ~ Hotel 1y ~ Storage 1y (month-to-month)
- **rate data**: FRED `DGS10` (10Y Treasury constant maturity, daily) — 1962-01-02 ~ 2026-05-28,
  n=16086. 4-week (20 trading days) rolling change in basis points.
- **price data**: Yahoo Finance adjusted close, 9 REIT sector 대표 종목 (PLD/AVB/BXP/WELL/EQIX/
  PSA/SPG/HST/AMT), 2018-01-02 ~ 2026-05-28, n=2112 trading days.
- **rate-shock entries**: DGS10 4w Δ > +50bp first crossing dates (consecutive day filter).
  - n = **23 events** (most concentrated in 2022 Fed hike cycle, with 2023-Mar/Aug/Oct + 2024-Oct
    + 2025-Jan extensions).
- **forward window**: 60d (trading days) cumulative return per ticker after entry.

## §3. 결과 (★ verbatim from script output)

### §3-1. Per-entry Cross-section Rank-IC

| Entry date | 4w_Δ (bp) | Rank-IC | p-value |
|---|---:|---:|---:|
| 2022-03-25 | 51 | +0.451 | 0.223 |
| 2022-04-01 | 65 | +0.477 | 0.194 |
| 2022-04-21 | 58 | +0.613 | 0.079 |
| 2022-04-29 | 57 | **+0.681** | 0.043 ★ |
| 2022-06-14 | 61 | -0.460 | 0.213 |
| 2022-06-21 | 53 | **-0.775** | 0.014 ★ |
| 2022-08-29 | 52 | +0.162 | 0.678 |
| 2022-09-01 | 58 | +0.094 | 0.811 |
| 2022-09-06 | 56 | +0.162 | 0.678 |
| 2022-09-08 | 51 | +0.332 | 0.383 |
| 2022-09-12 | 53 | +0.196 | 0.614 |
| 2022-09-22 | 59 | +0.077 | 0.845 |
| 2022-10-06 | 54 | +0.672 | 0.047 |
| 2022-10-13 | 52 | +0.681 | 0.043 |
| 2022-10-19 | 63 | **+0.860** | 0.003 ★★ |
| 2023-03-02 | 69 | -0.034 | 0.931 |
| 2023-08-16 | 53 | +0.400 | 0.286 |
| 2023-10-02 | 51 | -0.060 | 0.879 |
| 2023-10-06 | 52 | +0.136 | 0.727 |
| 2023-10-18 | 56 | +0.136 | 0.727 |
| 2024-10-29 | 54 | +0.162 | 0.678 |
| 2025-01-07 | 52 | +0.298 | 0.436 |
| 2025-01-10 | 55 | +0.264 | 0.493 |

### §3-2. Aggregate statistics

- Total entries: **n = 23**
- Mean Rank-IC: **+0.240** (★ confirm threshold = -0.05 미달, sign 정반대)
- Std Rank-IC: 0.362
- Median: +0.196
- Min / Max: -0.775 / +0.860
- Fraction negative: 17.4% (4/23 — 정반대 부호는 minority)
- Approx z (mean / SE): **+3.18** (one-sample, against null=0)

### §3-3. Verdict

**★ H1 REJECTED with strong sign mismatch**:
- 실측 mean Rank-IC = +0.240 → long-WALT 가 rate-shock 후 60d *outperform* (가설 가정의 정반대)
- approx z = +3.18 (∼ p<0.005 under null Rank-IC=0)
- 17.4% 만 음 부호 → 가설 방향 (long-WALT underperform) 은 sample minority

## §4. ★ Mechanism 가설 (왜 데이터가 직관 가설을 reject 했나)

직관적 mechanism (long-duration → rate sensitivity ↑) 은 *partial-equilibrium* perspective. 데이터의
정반대 결과는 *general-equilibrium* 효과 가능성:

1. **Defensive rotation hypothesis**: rate-shock 시 위험회피 → long-WALT REIT (장기 contractual
   rent escalator, stable cash flow) 가 defensive bid 받음. short-WALT (hotel, apartment,
   storage) 는 cyclical earnings risk 노출 → rate-shock + 동시 발생 경기둔화 우려 시 더 빠짐.
2. **Secular growth confounding**: AMT (cell tower 5G capex), EQIX (cloud/AI datacenter capex)
   같은 long-WALT 가 *secular growth* driver 강함. rate 효과보다 sector-specific demand 가
   60d window 에 dominant.
3. **Sample bias (2022 Fed hike)**: 23 entry 의 대부분이 2022 H1-Q4 (Fed 75bp 연속 인상기).
   이 시기 60d forward 가 rebound 시기 포함 (가장 큰 outperform 은 2022-10-19 후 = +0.860,
   이건 2022-Q4 trough 이후 강한 반등기).
4. **WALT × sector demand collinearity**: WALT 가 sector membership 과 강한 collinear. 본 검증
   은 WALT 의 *순효과* 가 아닌 WALT-correlated sector-specific 효과 측정. partial-corr 가 필요.
5. **2022-2025 specific regime**: 같은 mechanism 이 1994 hike, 2004 hike, 2013 taper tantrum
   같은 다른 cycles 에서도 성립하는지 별도 확인 필요 (Yahoo 2018+ 한계).

## §5. 8축 self-audit

| 축 | 평가 | 메모 |
|---|---|---|
| A 이론실재성 | ✓ | 가설은 long-duration discount rate sensitivity 학설 (Round 2) 기반 |
| B 실데이터검증 | ✓ | FRED DGS10 + Yahoo 실가격, 합성 미사용. n=23 entries, sample 2018-2025 |
| C yaml 도출추적성 | (다음) | v2 yaml block4 의 "rate-shock + long-WALT → beta_rate 가중↑" 규칙 폐기 |
| D PIT·OOS | ✓ | DGS10 = realized rate (lookahead 없음), forward 60d = strict forward (lookahead 없음) |
| E 자문비판+환각cross-verify | ✓ | 자문 (Round 2) 의 직관 가설이 데이터로 reject — 환각 cross-verify 자체임 |
| F 반증가능+기각기록 | ★★ | reject 조건 명문 (sign mismatch), 실측 reject 명확 (z+3.18). 본 노트 = 기각 기록 |
| G 검정력한계 | ⚠ | n=23 entry, 모두 single rate cycle (2022 Fed hike + 후속). 검정력은 single-regime 한정. |
| H 미해결의문 | ★ | (a) WALT × sector demand collinearity 미분리 (partial-corr 필요) (b) 1994/2004/2013 cycle 검증 부재 (data 한계) (c) 60d window 가 적절한지 / 30d 또는 180d 추가 검증 가치 |

★ G 축 한계: sample period 2018-2025 중 rate-shock 23 entry 가 거의 모두 2022 Fed hike 시기 → effective n ≪ 23 (autocorr 강함). single-regime sample 이라 generalize 한계.

## §6. v2 yaml 반영 (study_session.yaml v2 의 어느 칸이 본 결과로 정해지는가)

1. **block4 weight_rules**: 
   - v1 의 "rate-shock + long-WALT ticker → beta_rate 가중↑↑↑" 규칙 → **폐기**.
   - 새 가설 (v2): "rate-shock window 진입 → defensive long-WALT REIT (Healthcare/Datacenter/
     Specialty) 의 *outperform* 가설" 잠정 등록, but n=23 single-regime 검정력 한계 명시.
2. **block1 lens.regime_reading**: "long-duration = rate β 절대값 ↑ = rate-shock 시 더 빠짐"
   문장 제거. 대신 "rate-shock window 후 60d 의 cross-section 은 mean Rank-IC +0.24 로
   defensive rotation 가설 일관 (n=23, 2018-2025 single-regime caveat)" 추가.
3. **block3 relationships**: WALT ↔ rate-shock cross-section return 의 prior_sign 을 v1 의 'pos'
   (long-WALT 가 더 빠짐) 에서 **'neg' (long-WALT outperform)** 으로 변경. prior_strength 도
   single-regime sample 반영해 0.50 → 0.30 강등.
4. **block5 confidence_hooks**: H1 hypothesis_id 의 reject_signal 이 이미 trigger 됨 →
   action_threshold 명시: "v1 'long-WALT underperform' 가설은 2018-2025 sample 에서 reject.
   regime_reading 의 관련 문장 제거 + base_weight 0 으로 강등."

## §7. 잔존 caveat / 다음 단계

- WALT 와 sector-specific 효과 분리 = H3 (debt maturity stratify) + glasso partial-corr 가
  multi-feature 동시 조건화.
- 1994/2004/2013 rate cycle 검증 = NAREIT 1972+ historical 시계열 (가용 시 monthly 보강).
- 30d / 180d / 12m window 추가 검증 가능 — H1 의 60d 특수성 확인.

## §8. 산출 파일

- script: `raw/scripts/h1_long_walt_cross_section.py` (135 lines)
- log: `raw/scripts/h1_long_walt.log` (verbatim stdout, em-dash unicode 한 줄 cp949 인코딩 fail 외 본문 모두 정상)
- 본 분석: `raw/validation-H1.md`
