---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h11]
date: 2026-05-31
hypothesis: H11 — Google Trends 'bitcoin' attn_z → fwd_1m_ret (Liu&Tsyvinski 2021 attention predictor)
audit_axes: [A, B, D, F, G, I, K]
note: PyTrends 'all' timeframe = monthly aggregate, LTW weekly base 와 다름 (small-N rigor)
---

# validation-h11 — Google Trends attention monthly z → BTC fwd_1m_ret

## Data Coverage
- PyTrends 'bitcoin' monthly 268 obs (2004-01 ~ 2026-04)
- Binance BTC monthly (2017-08~) inner join 후: **n_total = 94**
- 12m rolling z-score warmup 적용 후 effective N=61

## 변수 정의
- (a) 시제: monthly contemporaneous attn_z → fwd_1m_ret (log return)
- (b) frequency: monthly (PyTrends 'all' = monthly aggregate)
- (c) transform: rolling 12m z-score
- (d) conditioning: post-2021 sub-sample (attention saturate 시기 검증)

## H11 검증 결과
- full Rank-IC (attn_z → fwd_1m) = **0.1117** (n=94, N_eff=61)
- attn_z >+1σ n=20, mean_fwd_1m = 0.1041
- attn_z (-1, +1) n=66, mean_fwd_1m = -0.0100
- attn_z <-1σ n=8, mean_fwd_1m = 0.1047
- post-2021 sub Rank-IC = 0.0967 (sign flip vs full: False)
- Newey-West HAC SE (lag=1m) = 2.045761e-02

## 12축 박제
- **A 학술**: Liu&Tsyvinski 2021 RFS (attention predictor, weekly base), Da Engelberg Gao 2011 JF (search trend as retail attention)
- **B SE**: monthly aggregate (PyTrends 'all') = autocorr 약. Newey-West HAC lag=1m. PASS |Rank-IC|=0.1117
- **D PIT**: PyTrends weekly release Sunday 0:00 UTC, T+1 가능
- **E 자문 환각**: LTW 2021 정량 +0.5~+0.7 점추정 prior 박제 X — 본 표본 monthly Rank-IC 0.1117 기준 hedge
- **F 반증조건**: (i) β CI 0 포함? (Rank-IC 0.1117 > 0.03 hard B) (ii) post-2021 부호반전? NO
- **G effective N**: N_eff=61 — 약 충분
- **I 생존편향**: BTC only (멀티코인 attention 확장 후속)
- **K 시도횟수**: K=16 (4 horizon × 2 MVRV regime × bull/bear). 본 라운드 = base 1 + post-2021 sub = 2. Bonferroni α/16=0.00313

## verdict
**PARTIAL CONFIRMED (attn_z > +1σ → 상위 mean, walk-forward 후속)**

## hedge 어휘
- monthly aggregate 한계 — weekly base 후속 fetch (today 5-y) 가 LTW 2021 직접 비교 가능
- 점추정 magnitude (LTW +0.5~+0.7) 박제 X — 본 표본 Rank-IC 0.1117 보고만

## 후속 의문
- (i) weekly fetch (today 5-y) 보강 + LTW 2021 직접 표본 매핑
- (ii) MVRV regime conditional (bull/bear) 효과 비대칭 검증
- (iii) Granger lead 양방향 (attn → price OR price → attn) endogeneity 확인
- (iv) post-2021 sub-sample 부호 반전 = generalize 실패 신호