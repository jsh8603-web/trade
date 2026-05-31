---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h10]
date: 2026-05-31
hypothesis: H10 — BTC-Gold rolling 60d corr → digital gold thesis (Baur 2018 BTC≠gold prior 시험)
audit_axes: [A, B, D, F, G, I, K]
---

# validation-h10 — BTC-Gold rolling corr digital gold thesis

## Data Coverage
- yfinance GC=F Gold futures daily (2017-08-17 ~ 2026-05-29)
- Binance BTC daily (2017-08-17~)
- yfinance ^VIX daily (risk-off filter)
- inner join + 60d warmup: **n_total = 2146**

## 변수 정의
- (a) 시제: contemporaneous rolling 60d Pearson corr
- (b) frequency: daily
- (c) transform: log return + rolling corr
- (d) conditioning: VIX > 30 (risk-off subsample) / pre vs post 2024-01-11 ETF
- (e) regime: digital_gold candidate (risk-off + corr > 0.2)

## H10 검증 결과
- full sample corr_60d: range [-0.328, 0.541], mean=0.0986
- risk-off (VIX>30) n=154: corr_60d mean = **0.1796** (N_eff=5)
- risk-on (VIX≤30) n=1992: corr_60d mean = 0.0923
- Welch t-test (risk-off vs risk-on corr): t=5.573, p=0.0000
- Mann-Whitney U: p=0.0000
- post-2020 risk-off only n=149, mean=0.1830
- pre-ETF (2024-01-11 이전) n=1549 corr mean=0.1061
- post-ETF n=597 corr mean=0.0790, Welch p=0.0002

## 12축 박제
- **A 학술**: Baur 2018 (BTC≠gold prior), Klein 2018 (BTC vol >> gold vol), Smales 2019 (speculative haven)
- **B SE**: ★중첩 rolling 60d → Welch t-test (raw IID), Mann-Whitney 비교 보고. autocorr 보정 = block-bootstrap 후속 (본 라운드 raw + hedge).
- **D PIT**: yfinance daily close T+1
- **F 반증조건**: (i) risk-off corr_60d > 0.2? **0.1796** FAIL (ii) risk-off > risk-on 통계 유의? p=0.0000 PASS (iii) post-ETF > pre-ETF? p=0.0002 FAIL
- **G effective N**: full N_eff=14, risk-off N_eff=5 — **risk-off N<100 small-N 경고**
- **I 생존편향**: BTC + Gold futures (둘 다 surviving largest)
- **K 시도횟수**: K=36 사전 공시 (VIX 3 regime × real_rate 3 × window 4). 본 라운드 = 3 비교 (risk-off vs risk-on + pre/post ETF). Bonferroni α/36=0.00139

## verdict
**★REJECTED (risk-off corr<0.2, digital-gold thesis 본 표본 부정)**

## hedge 어휘
- Baur 2018 prior (BTC≠gold 표본 2010-2015 corr≈0) 와 본 표본 결과: corr mean 0.0986 = 약 동행
- ★risk-off corr 0.1796 ≤ 0.2 digital-gold gate FAIL
- Bonferroni 보정 후 raw p=0.0000 생존

## 후속 의문
- (i) window 길이 민감도 4종 비교 + Bonferroni
- (ii) real_rate (DFII10) 추가 conditioning — real_rate < 0 시 BTC-Gold corr 증폭 가설
- (iii) walk-forward strict OOS
- (iv) Block bootstrap (block=90d) 자기상관 보정 후 재평가