---
tags: [type/study-research-raw, domain/inv, study/eq_intl, phase/2-1, round/2]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
round: 2
channel: WebSearch (폴백)
fallback_reason: "/gemini-web + /claude-web 9-session 경합 가능성, main v2 가이드 '1~2R 씩' 폴백 허용"
archive_raw: ~/.claude/docs/archive/research-raw/eq-intl-r2-native-20260530.txt
---

# eq_intl R2 — BIS dollar liquidity 분해 + 검증 methodology

## Q1: BIS dollar liquidity → EM 전달 채널 (실무 frame)

### R1 frame 보강 (Adler-Dumas → BIS 실증)
1. **BIS GLI (global liquidity indicators)** = USD-denominated foreign-currency credit to non-bank
   EMDEs. end-Mar 2024 = +1% (post-2y decline 종료). post-COVID Fed/ECB tightening 시작점이
   structural break.
2. **EM external financing 구조 변화 (20y)**: 외화 bank lending → local currency bonds/equities.
   GFC 이후 portfolio inflow > bank lending. → **eq_intl 의 1차 driver = portfolio flow + risk
   appetite**, bank lending 채널은 secondary.
3. **broad USD 채널 (10y importance ↑)**: USD 강세 ↔ EM local currency bond/equity flow.
   매개 = global investor risk appetite (Forbes-Warnock 와 일관).
4. **interest rate differential 축소 → EM capital flow 압박**: US-EM rate diff = carry. carry
   shrink → flow reversal → ETF price 부정적.

### eq_intl 코드 변환 가능성
- **BIS GLI 시리즈** (월별/분기별) → 우리 시스템 잠재 indicator. 무료 (BIS data portal).
- **US-EM interest rate differential** → FRED FEDFUNDS - EM 정책금리 (ECOS/외부) → carry proxy.
- **portfolio flow** → IIF/EPFR 는 유료. 무료 proxy = 국가별 IPO/ETF AUM 변화 (Yahoo holdings).

### Frame gap (R3 후보)
- China decoupling 의 정량 frame: A-H spread + capital flow + CNY peg effectiveness.
- carry crash regime: Lustig-Verdelhan FX risk premium 의 risk-off 시 발현.

## Q2: 검증 methodology (실증 표준 2024)

### 방법론 채택 후보 (eq_intl 적용)
| 방법 | source | eq_intl 적용 |
|---|---|---|
| **Walk-forward OOS (frozen params)** | arxiv 2511.12490 (13-Sharpe SP500 20y) | 5y eq_intl daily 를 24m train / 1m test rolling → Rank-IC stability |
| **Drift regime decomposition** | 동상 | dxy/vix regime 별 cross-section factor IC 분리 → H2/H9 검증 핵심 |
| **Regime-dependent Granger causality** | arxiv 2601.10732 | dollar → EM equity 의 regime별 causal precedence (lag 0/1/3m) |
| **Partial correlation (자기 SSOT 의 cglasso 와 일치)** | arxiv 1402.1405 | 블록3 prior 와 동일. R1 frame 직접 연결 |
| **Cross-country statistical learning + panel regression** | macrosynergy.com | GICS sector 별 학습 + country panel. 우리는 archetype 별 |
| **Two-level uncertainty (safe deployment)** | arxiv 2603.13252 ("When Alpha Breaks") | 블록5 e-CUSUM falsification 와 호환. hidden regime change 감지 |
| **RankIC degradation at longer horizon** | 동상 | 60d/90d 음수 전환 — 우리도 horizon ≤ 30d 권장 |

### Walk-forward 권장 setup (eq_intl)
- **Train**: 24~36m rolling
- **Test**: 1m forward
- **Refit cadence**: 매 1m (drift regime 빠른 적응) 또는 3m (안정)
- **Freeze block 4 weights during test**: prior_strength 고정
- **regime label**: VIX>25 / T10Y2Y < 0 / HY OAS > 400bp 등 binary indicator

## R1 가설 9건 → 검증 setup 매핑

| 가설 | 검증 방법 | 데이터 요구 | 반증 임계 |
|---|---|---|---|
| H1 dollar dominance | dxy_β walk-forward Rank-IC | DXY + 12 country ETF | mean IC<0 in 24m rolling, OR R²<0.05 6m+ |
| H2 regime amplification | risk-off vs risk-on split (VIX>25) | VIX | |corr diff| < 0.10 |
| H3 cross-country mom | cross-section Rank-IC walk-forward | country ETF monthly | IC-IR<0.10 in 10y rolling |
| H4 commodity oil link | brazil/uk/mexico vs india/korea diff | WTI + ETF | exporter corr ≤ importer corr |
| H5 china decoupling | china β vs EM-avg β 95% CI | DXY/VIX + FXI | china β in EM avg CI |
| H6 segmentation | unsegmented DM alpha vs segmented EM alpha | World CAPM alpha cross-section | alpha diff 무유의 |
| H7 TSM self-momentum | self-12m → next-1m hit ratio | ETF monthly | hit rate < 52% |
| H8 ETF liquidity tier | broad vs single-country tracking err | ETF + index data | diff < 5bp |
| H9 momentum crash regime | risk-on/off split IC | ETF + VIX | regime IC diff < 0.05 |

## R3 자가 점검

수렴 미달 — 다음 보강:
- **R3 Q1**: China decoupling 정량 (A-H spread / capital flow / CNY peg)
- **R3 Q2**: momentum crash regime — Daniel-Moskowitz 2016 이후 업데이트 + carry crash 연계
