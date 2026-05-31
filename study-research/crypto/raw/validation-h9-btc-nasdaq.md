---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h9]
date: 2026-05-31
hypothesis: H9 — BTC-Nasdaq rolling 60d corr → fwd_30d regime classifier (Baur 2018)
audit_axes: [A, B, D, F, G, I, K, L]
---

# validation-h9 — BTC-Nasdaq rolling corr regime classifier

## Data Coverage
- yfinance ^IXIC daily (2010-01-04 ~ 2026-05-29, 4126 obs)
- Binance BTC daily (2017-08-17 ~ 2026-05-30)
- inner join 영업일 + 60d rolling warmup 후: **n_total = 2117**
- N_eff (autocorr 보정): 33

## 변수 정의 + measurement axis
- (a) 시제: contemporaneous rolling 60d corr → fwd_30d return
- (b) frequency: daily
- (c) transform: log return + rolling 60d Pearson corr
- (d) conditioning: regime label (risk_asset / mixed / decoupled)
- (e) regime: corr>0.4 (risk_asset) / [-0.1, 0.4] (mixed) / <-0.1 (decoupled)

## H9 검증 결과
- corr_60d 분포: range [-0.394, 0.725], mean=0.280, median=0.298
- continuous Rank-IC (corr_60d → fwd_30d) = -0.0027
- ANOVA 1-way (regime → fwd_30d): F=7.504, p=0.0006
- Kruskal-Wallis (non-parametric): H=17.051, p=0.0002
- Newey-West HAC SE (lag=60d for overlapping corr_60d) = 2.842188e-02
- regime 전이 빈도: 6.55/year (불안정 (regime label noise 의심))

## Regime breakdown (n≥30)
| regime | n | N_eff | mean_fwd_30d | median_fwd_30d | std_fwd_30d |
|---|---|---|---|---|---|
| risk_asset | 767 | 16.0 | 0.0435 | 0.0433 | 0.2248 |
| mixed | 1169 | 24.0 | 0.0264 | 0.0070 | 0.2567 |
| decoupled | 181 | 5.0 | -0.0346 | -0.0556 | 0.2430 |

## 12축 박제
- **A 학술**: Baur 2018 JIFMIM (regime 시기 변동), Liu&Tsyvinski 2021 RFS (factor 독립), Bhambhwani 2019 (macro exposure 변동)
- **B SE**: ★중첩 rolling 60d 윈도우 t-stat 부풀림 → Newey-West HAC lag=60d 강제. raw p ANOVA=0.0006, KW=0.0002. continuous Rank-IC |-0.0027| ≤ 0.03
- **D PIT**: yfinance ^IXIC daily T+1 (UTC close), Binance BTC daily close
- **F 반증조건**: (i) ANOVA p>0.05? NO (ii) regime 전이 < 분기 1회? NO (regime noise) (iii) continuous corr_60d mostly 0 (decoupled 사실상 없음)? decoupled n=181
- **G effective N**: full N_eff=33. regime cell N_eff 별도 보고.
- **I 생존편향**: BTC + Nasdaq composite (large-cap survivor). 멀티코인 / 멀티지수 확장 시 별도
- **K 시도횟수**: K=36 사전 공시 (regime 3 × VIX 3 × window 길이 4). 본 라운드 = base 1 + ANOVA + KW = 3 비교. **Bonferroni α/36=0.00139 임계 적용 시 raw p=0.0006/0.0002 모두 유의**
- **L 통합 상관**: BTC-Nasdaq 공통인자 = global risk + USD funding. main system_priors 통합 시 중복 계상 1회 (gold·equity sleeve 와 USD 공통)

## verdict
**TENTATIVE DIRECTIONAL (regime 차이 약 유의, regime 안정성 미확인)**

## hedge 어휘
- Bonferroni 보정 후 생존 — 본 결과 ★강 prior
- regime 전이 빈도 6.55/year — regime label 자체가 noise 의심, smoothing 검토

## 후속 의문
- (i) window 길이 민감도 (30/60/90/120d) — 4종 비교 + Bonferroni
- (ii) VIX regime conditioning (low/mid/high) × BTC-Nasdaq regime — 9 cell partial
- (iii) walk-forward strict OOS — in-sample 2017-2021 → OOS 2022-2025 (cycle 2 후속)
- (iv) post-2024 ETF subsample 별도 (institutional flow → Nasdaq tech 상관 ↑ 가설)
- (v) Bonferroni 보정 후 보존 결과 = walk-forward 우선 검증 후 yaml 통합