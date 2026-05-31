---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h12]
date: 2026-05-31
hypothesis: H12 — DefiLlama TVL z → BTC fwd_30d (Cong 2022 DeFi utility, partial-corr stablecoin 직교화)
audit_axes: [A, B, D, F, G, I, K, L]
---

# validation-h12 — DefiLlama TVL utility → BTC

## Data Coverage
- DefiLlama TVL daily 3169 obs (2017-09 ~ 2026-05)
- DefiLlama stablecoin total 3105 obs (2017-11 ~ 2026-05)
- Binance BTC daily (2017-08~)
- inner join + 252d z-score warmup 후: **n_total = 2748**

## H12 검증 결과
- marginal TVL z → fwd_30d Rank-IC = **-0.0119** (n=2748, N_eff=43)
- multicollin Rank-IC (TVL z vs stable z) = **0.1703** (약함)
- partial Rank-IC (TVL_resid | stable → fwd_30d) = **-0.0120**
- Newey-West HAC SE (lag=30d) = 1.706834e-02

## 12축 박제
- **A 학술**: Cong et al 2022 JFE, Aramonte 2021 BIS, Schär 2021 FRBSL
- **B SE**: NW HAC lag=30d. partial |-0.0120| ≤ 0.03
- **D PIT**: DefiLlama daily T+1
- **F 반증조건**: (i) partial CI 0 포함 신호 부재 (ii) multicollin>0.7? NO (iii) BTC 직접 vs ETH 매개 ETH dominant? cycle 3
- **G effective N**: full N_eff=43
- **I 생존편향**: surviving DeFi protocols TVL only (★상폐 protocols 누락)
- **K 시도횟수**: K=12. 본 라운드 = marginal + partial + collin = 3. Bonferroni α/12=0.00417
- **L 통합 상관**: TVL ↔ stablecoin 공통인자 (USD funding) — main 통합 중복 회피 박제

## verdict
**★REJECTED (Rank-IC<0.03 hard B 미달)**

## 후속 의문
- (i) ETH 매개 검증 (BTC 자체 DeFi 작음)
- (ii) DEX volume 별도 (TVL stock vs flow)
- (iii) walk-forward strict OOS