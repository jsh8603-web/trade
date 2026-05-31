---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/2-3, hypothesis/h1]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
hypothesis: H1 — Dollar dominance: broad USD↑ → 모든 unhedged ETF↓
raw_source: raw/walkforward.py + raw/walkforward-output.txt
factor_set_frozen: [DXY]
walkforward_setup: "Train 24m rolling, Test 1m forward, Refit 1m, factor set 고정 (single dxy)"
---

# H1 walk-forward 검증 — Dollar dominance

## §1. 가설 + 반증조건

- **가설**: 각 국가 ETF 의 univariate dxy_β 가 음수 → cross-section 으로 (음수 큰 국가 = USD 약화 시 강한 양수 수익) Rank-IC>0.
- **반증조건**: walk-forward IC mean < 0 OR IC-IR<0.10 in 24m+ rolling.

## §2. Walk-forward setup (factor 고정)

- Train: 매 월 t 의 직전 504 daily obs (≈24m). 매 월 refit.
- Test: 직후 21 daily obs (≈1m), cumulative log-return = forward outcome.
- IC: Spearman(−dxy_β_i, fwd_return_i) cross-country (12 국가 + SPY = 13).
- ⛔ factor set 고정 = DXY only (univariate). 잠재 인자 추가 없음. in-sample 과적합 회피.

## §3. 결과 (34 OOS months, 2023-06 ~ 2026-03)

| metric | value |
|---|---:|
| mean IC | **+0.0184** |
| median IC | +0.0714 |
| std | 0.308 |
| IC>0 ratio | 58.82% (20/34) |
| **IC-IR (annualized)** | **+0.207** |
| binomial (20/34 vs 50%) | borderline (one-sided p ≈ 0.20) |

### 월별 IC 분포 핵심
- 2023 후반 IC 강한 음수 (-0.21~-0.60) — DXY 가 강세 turn 시기에 cross-section 흔들림.
- 2024-12 ~ 2025-08 IC 양수 cluster (+0.08 ~ +0.63) — Trump 2.0 dollar regime 추정.
- 2025-09 sharp -0.478 reversal.

## §4. 판정

**△ 부분 성립 (조건부)**: 부호 prior 는 일치하나 IC-IR +0.207 = 절대 강도 약함. 반증조건 (IC<0 OR IC-IR<0.10) 미충족하나 강확인도 아님.
- 이전 5y 일별 실측 (summary.md §5 H1) 의 univariate 상관 -0.23~-0.57 은 강확인 (대각선 / contemporaneous), but cross-section walk-forward 의 IC 는 약함.
- **차이의 이유**: walk-forward 는 "다음 1m 의 fwd return 을 t 시점 β 로 예측" — β 시계열적 안정성 + fwd return 의 시점별 macro 변동성 잡음이 IC 분산을 키움.
- **결론**: H1 dollar dominance 의 **방향성·instantaneous 채널은 강확인**, **forward prediction power 는 약함**. base_weight 유지 (regime conditioning 의존도 ↑).

## §5. yaml 갱신 표지

- block3 dxy↔em_equity prior_strength: 유지 (0.55) — instantaneous 채널 강확인 기준.
- block4 dollar_beta_country base_weight: 유지 (0.22) — 단 modulate_by [regime] 의존도 더 명시.
- block5 dollar_dominance_anchor: **EARLY_ADOPT 유지** (instantaneous 강 + walk-forward 약 = adopt dwell 길게).
- block5 추가 evidence: walk-forward IC-IR +0.207 (5y / 34 OOS months / factor=DXY frozen).

## §6. 향후 개선 (block6 → block7)

- FRED DTWEXBGS (broad USD index) 추가 후 univariate DXY 대체 시 IC 변화 측정.
- regime split walk-forward (risk-on/off 별 IC 분리) — H2 와 연계.
