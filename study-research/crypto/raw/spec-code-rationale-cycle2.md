---
tags: [type/spec-code-mapping, study/crypto, cycle/2, date/20260531]
date: 2026-05-31
study_id: crypto
cycle: 2
purpose: H7-H12 6 가설의 spec↔code 1:1 verify + proxy rationale + 자문원문 ref 종합. commodity validation-china 모범 패턴 mirror.
audit_relevance: AUDIT-GUIDE §1 axis E (자문 cross-verify) + axis B (spec/code drift 명시)
---

# crypto cycle 2 spec↔code mapping + rationale + 자문 ref 종합

> ★main 점검 (2026-05-31): theory(이론섹션) + validation(spec↔code 1:1) + rationale(왜 이 proxy/변환/측정) + 자문원문 완비 점검.
> ★commodity validation-china (BIS stock proxy 한계 + spec↔code drift + falsifier 명시) 모범 mirror.
> 본 파일 = 6 validation md 공통 §spec↔code 보완 (각 validation md 의 11축 박제 + verdict 외에 본 종합 1건으로 모든 가설 매핑 정리).

---

## §0. 모범 패턴 (commodity-china 적용)

commodity/raw/validation-china-credit-impulse.md §④ 의 모범 3요소:
1. **데이터 proxy 한계** — BIS credit-to-GDP = stock 비율 vs 정통 TSF flow
2. **spec("TSF flow") ↔ code("BIS stock 비율 차분") drift 존재** — 신호 희석 가능성 명시
3. **falsifier** — empirical-claim rule 5단계 verdict 강제

cycle 2 6 가설 본 패턴 mirror 적용.

---

## §1. H7 — AdrActCnt → fwd_30d_ret (network value, Pagnotta&Buraschi 2018)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | 분산 네트워크 자산 균형 가치 ∝ N^α (N = active users, α ∈ [0.5, 1.2] sub-Metcalfe ~ Metcalfe), Pagnotta&Buraschi 2018 SSRN |
| **Code (실측 변수)** | `df["dlog_addr"] = log(AdrActCnt).diff()` → contemporaneous Spearman vs `fwd_30d_ret = log(close[t+30]/close[t])` |
| **★Spec↔Code drift** | (i) **Spec** = 균형 *level* 관계 (N^α ↔ market_cap). **Code** = *Δ-Δ* 관계 (Δlog(N) ↔ fwd_30d_ret). level vs Δ drift. (ii) Spec = level corr 가설, Code = lagged forward predictive — drift. |
| **Proxy 한계** | AdrActCnt = unique active addresses ≠ unique users. 거래소 hot-wallet cluster + custodian (ETF 도입 후) = 한 entity 가 다중 주소 발현 → N 과대평가. ★post-2024 ETF 시대 custodian 통합 = N 감소 but value 증가 (sub-Metcalfe 약화 직접 신호). |
| **rationale (왜 이 proxy)** | CoinMetrics community AdrActCnt = 무료 anonymous tier 가용 + 17년 시계열 (6357 daily 2009-01~). 정통 unique-user metric 없음 = active address 가 합리적 1차 근사. |
| **자문원문 ref** | round-1-claude §1(ii) "Pagnotta&Buraschi 균형해", round-3-claude §1(iv) "active address Metcalfe-like", round-2-gemini §sub-Metcalfe |
| **falsifier (반증조건)** | (i) β Block bootstrap CI95% 0 포함 (n=3178 → CI=[-0.0028, +0.0347] = ★0 포함 → REJECT) (ii) Rank-IC < 0.03 (실측 0.0085 → ★FAIL) (iii) post-2024 부호반전 |
| **verdict** | ★REJECTED (B threshold + CI 0 포함, F axis 기각 1건) |

---

## §2. H8 — TxCnt → fwd_30d_ret (utility count proxy, Catalini&Gans 2020)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | BTC 가치 = utility 사용량 (transaction *value-weighted USD*) + speculative demand 합성. utility 보조 = TxVolUSD value-weighted. |
| **Code (실측 변수)** | `df["dlog_tx"] = log(TxCnt).diff()` (★count proxy, value-weighted 아님) → fwd_30d_ret |
| **★Spec↔Code drift** | ★**핵심 drift**: Spec("TxTfrValAdjUSD" value-weighted USD) ↔ Code("TxCnt" count). **anonymous tier 403 (paid 권한 없음)** 으로 인한 강제 대체. value-weighted (큰 거래 가중) → count-weighted (모든 거래 1:1) = **average tx size 정보 손실**. mechanical co-move 신호 = 단순 count 가 가격과 함께 증가 (Yermack 2015 hot-wallet shuffle 도 1 count). 본 dirft 가 verdict 의 ★REJECTED 핵심 원인일 가능성 강함. |
| **Proxy 한계** | (i) value 정보 부재 — whale 거래 (10K BTC 송금 = 1 count) vs retail (0.01 BTC = 1 count) 등치. (ii) 거래소 hot-wallet shuffle (Yermack 2015) = utility 와 무관한 count 증가. |
| **rationale (왜 이 proxy)** | CoinMetrics community TxCnt = 무료 anonymous tier 가용. TxTfrValAdjUSD = 403 forbidden → 본 cycle 2 차선. cycle 3 paid tier 권고 (★main 별도 요청 후속). |
| **자문원문 ref** | round-1-gemini §utility, round-2-claude §micro, round-3-claude §1(ii) |
| **falsifier** | (i) Rank-IC < 0.03 (실측 0.0022 → ★FAIL) (ii) contemp Δlog_tx vs Δlog_close > 0.3 mechanical (실측 0.0262 < 0.3 = 약 mechanical 부재) (iii) partial-corr (tx \| blk) → fwd_30d (실측 -0.0042 → 잔존 신호 부재) |
| **verdict** | ★REJECTED (B threshold FAIL + partial 잔존 부재) |

---

## §3. H9 — BTC-Nasdaq rolling 60d corr regime → fwd_30d_ret (Baur 2018 risk-asset)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | BTC 상관 regime 시기별 변화 — pre-2017 무상관 / 2017-2020 risk-asset / digital-gold 서사 변동. regime 별 fwd outcome 차등 (decoupled 회복 길다 가설). |
| **Code (실측 변수)** | `df["corr_60d"] = ret_btc.rolling(60).corr(ret_nasdaq)` → regime label (corr>0.4 risk_asset / [-0.1, 0.4] mixed / <-0.1 decoupled) → fwd_30d_ret ANOVA / Kruskal-Wallis |
| **★Spec↔Code drift** | Spec ↔ Code 정합 (rolling Pearson corr 가설 = 실측 = standard Baur 2018 패턴). ⚠️ Code 의 regime threshold (0.4 / -0.1) = hand-tuned cutoff = backtest fit 아니나 사후 결정. ⚠️ rolling 60d window 길이 사전 박제 없음 (sensitivity 후속 의무). |
| **Proxy 한계** | (i) 영업일 only 매칭 (BTC 365일 vs Nasdaq 252일/년 inner join → BTC 주말 정보 손실) (ii) rolling 60d overlap = autocorr 강함, Newey-West HAC + Block bootstrap 강제 보정 의무. (iii) regime 전이 6.55/year = ★분기 1회 임계 초과 (regime label 신뢰성 약함). |
| **rationale (왜 이 proxy)** | yfinance ^IXIC 무료 + 4126 daily 2010-2026. Baur 2018 표본 직접 mirror (단 표본 기간 확장: 2010-2017 → 2010-2026). 60d window = Baur 표준. |
| **자문원문 ref** | round-2-claude §digital-gold "BTC-Nasdaq 2024 0.4~0.6 → 2025 0.2~0.5", round-3-gemini §decoupling, round-3-claude §1(v) |
| **falsifier** | (i) ANOVA p > 0.05 (실측 p=0.0006 → ★Bonferroni 보정 후 생존) (ii) regime 전이 < 분기 1회 (실측 6.55/year → ★FAIL regime 안정성 의문) (iii) continuous corr_60d mostly 0 oscillate (실측 mean 0.280 → 양으로 치우침) |
| **verdict** | **TENTATIVE DIRECTIONAL** — regime 통계 차이 유의 (Bonferroni 후 생존, decoupled mean -3.46% vs risk-asset +4.35%) but ★digital-gold 정반대 (decoupled = BTC 약). regime 전이 빈도 불안정. walk-forward strict OOS 후속 의무. |

---

## §4. H10 — BTC-Gold rolling 60d corr → digital gold thesis (Baur 2018 BTC≠gold)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | Baur 2018: BTC ≠ gold (corr near 0). 검증 = post-2020 risk-off (VIX>30) 시 BTC-Gold corr > 0.2 = digital gold 시그널. post-2024 ETF = institutional 채택 → corr 강화 prior. |
| **Code (실측 변수)** | `corr_60d = ret_btc.rolling(60).corr(ret_gold)` + VIX>30 subsample + pre/post 2024-01-11 ETF 비교 |
| **★Spec↔Code drift** | Spec ↔ Code 정합. ★단 Spec 의 "post-2024 ETF 채택 → corr ↑" prior 가 본 표본 실측 *역방향* (post-ETF 0.079 < pre-ETF 0.106, p=0.0002). prior 실측 부정 = ★자문 prior 박제 X 가 정당화 됨. |
| **Proxy 한계** | (i) GC=F gold futures = 영업일 only (London PM Fix 미가용 → discontinued FRED series 대체) — physical gold spot 보다 derivative noise 가능성. (ii) risk-off (VIX>30) subsample n=154 / N_eff=5 = ★INSUFFICIENT (LOO + autocorr 보정 후 검증력 거의 없음). |
| **rationale (왜 이 proxy)** | FRED GOLDAMGBD228NLBM 시리즈 404 (discontinued) → yfinance GC=F 무료 폴백. 4125 daily 2010-2026, Close range $1050-$5318 (정상). gold ETF (GLD) = futures 보다 retail flow noise → futures 가 institutional benchmark. |
| **자문원문 ref** | round-2-claude §gold "BTC-Gold 2024 0.1~0.3 → 2025 0.3~0.5", round-3-gemini §digital-gold, round-3-claude §1(v) |
| **falsifier** | (i) risk-off corr_60d > 0.2 (실측 0.18 < 0.2 → ★FAIL by 0.02 margin) (ii) risk-off > risk-on 통계 유의 (Welch p<0.0001 → PASS) (iii) post-ETF > pre-ETF (실측 ★역방향 -0.027, p=0.0002 → REJECT) |
| **verdict** | ★REJECTED — 3 gate 중 2 FAIL (gate_i 0.18<0.2 + gate_iii post-ETF 역방향). digital-gold thesis 본 표본 부정. 단 risk-off 시 약한 양 동행은 있음 (Baur 2018 BTC≠gold 의 약 prior 재확인). |

---

## §5. H11 — Google Trends 'bitcoin' attn z → fwd_1m_ret (Liu&Tsyvinski 2021)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | LTW 2021 RFS: BTC 두 predictor = momentum + investor attention. 2014-2018 표본 weekly attention 1σ ↑ → 1-week fwd return +1.2%~+2.4%. |
| **Code (실측 변수)** | PyTrends `interest_over_time(timeframe="all")` = **monthly aggregate** (268 obs 2004-01~). attn_z = (trends - rolling_mean(12m)) / rolling_std(12m). → fwd_1m_ret (monthly log return). |
| **★Spec↔Code drift** | ★**핵심 drift**: Spec("weekly attention 1-week fwd") ↔ Code("monthly attention monthly fwd"). frequency mismatch — weekly 신호 = retail attention burst sub-monthly noise capture. monthly = 평균화 → 신호 약화. LTW 의 정량 magnitude (+1.2~+2.4% / week) ↔ 우리 (+10.41% / month at attn_z>+1σ) 차원 다름. cycle 3 weekly base ("today 5-y" fetch) 후속 의무 명시. |
| **Proxy 한계** | (i) monthly aggregate = retail attention sub-monthly burst 손실. (ii) PyTrends 정규화 (100 max in window) = 절대값 아님, 상대 트렌드만. (iii) keyword "bitcoin" only = "btc" / "cryptocurrency" / 한국어 등 다언어 ambiguity. (iv) all-time timeframe = monthly aggregation. weekly base 후속 의무. |
| **rationale (왜 이 proxy)** | PyTrends 무료 (rate-limit 심함 but urllib3>=2 retries=0 우회 통과). LTW 2021 표본 매핑 1차 = monthly base 도 양 IC (0.1117) + post-2021 sign 일관 (0.0967) = 1차 confidence 부여 가능. weekly base 후속 권고. |
| **자문원문 ref** | round-1-claude §attention "LTW 2021 main predictor", round-3-gemini §retail-attention, round-3-claude §1(iv) |
| **falsifier** | (i) β CI 0 포함 (Rank-IC 0.1117 > 0.03 PASS) (ii) post-2021 부호반전 (실측 0.0967 sign 일관 → PASS) (iii) Granger lead 양방향 (★cycle 3 후속 endogeneity 검증 의무) |
| **verdict** | ★**PARTIAL CONFIRMED** — monthly small-N (n=94 / N_eff=61) hedge 의무. LTW 2021 weekly base 후속 + Granger lead endogeneity 후속 + walk-forward strict OOS 후속. cycle 2 유일 신호 가설. |

---

## §6. H12 — DefiLlama TVL Δlog z → fwd_30d_ret (Cong 2022 DeFi utility 매개)

| 요소 | 내용 |
|---|---|
| **Spec (이론 가설)** | Cong et al 2022 JFE: DeFi protocol token 가치 = on-chain 활동도 (TVL, fee, volume) 의 함수. BTC 자체 DeFi 작음 → ETH/L2 매개 가정 (stablecoin demand → BTC 매개 채널). |
| **Code (실측 변수)** | TVL z (252d rolling) marginal Rank-IC + partial (TVL_resid \| stablecoin z) → fwd_30d_ret |
| **★Spec↔Code drift** | ★**핵심 drift**: Spec("BTC 직접 효과 = ETH/L2 매개") ↔ Code("TVL 전체 aggregate → BTC 직접"). ETH 매개 정량 (Δlog ETH → Δlog BTC) 미수행 = **BTC 직접 가설 검증만, 매개 가설 비검증**. cycle 3 ETH-mediator 정량 분리 의무. |
| **Proxy 한계** | (i) DefiLlama TVL aggregate = all-chain 합산 = ETH 가 dominant (>60% historically), 다른 chain (BSC, Solana 등) 이미 합산. BTC sleeve 의 직접 영향 분리 불가. (ii) ★생존편향 — TerraUSD, FTX 등 ★상폐 protocols TVL 미포함 → 위기 시 TVL drop 의 약화. (iii) stablecoin Δlog z 와 multicollinearity = 0.17 (실측 약함, 이론 prior "강함" 부정). |
| **rationale (왜 이 proxy)** | DefiLlama 무료 API 3169 daily 2017-09~ + DEX 3680 daily 2016-04~. TVL = DeFi 활동의 표준 stock metric. Cong 2022 의 token-specific 분리 = cycle 3 후속. |
| **자문원문 ref** | round-2-gemini §defi, round-3-claude §1(iii) "DeFi 매개 stablecoin transmission" |
| **falsifier** | (i) partial-corr CI 0 포함 (실측 partial IC -0.012 → FAIL) (ii) multicollin > 0.7 (실측 0.17 < 0.7 → multicollin 약함, 정통 prior 부정) (iii) BTC 직접 vs ETH 매개 ETH dominant (★cycle 3 후속 미수행) |
| **verdict** | ★REJECTED — partial-corr 잔존 부재 + multicollin 약 (이론 prior "강함" 부정). cycle 3 = ETH 매개 정량 분리 우선 (BTC 직접 가설 자체가 약 prior). |

---

## §7. 6 가설 종합 spec↔code drift table

| 가설 | drift 유형 | drift 크기 | cycle 3 후속 |
|---|---|---|---|
| H7 | level ↔ Δ-Δ | medium | log-log level 회귀 cross-check |
| H8 | value-weighted ↔ count | **large** | TxVolUSD paid tier 의무 |
| H9 | regime threshold hand-tuned | small | window 길이 sensitivity |
| H10 | gold spot ↔ futures | small-medium | physical gold spot 추가 |
| H11 | weekly ↔ monthly | **large** | weekly base "today 5-y" |
| H12 | direct ↔ mediated | **large** | ETH 매개 정량 분리 |

★3 가설 (H8, H11, H12) = large drift = ★cycle 3 진입 시 우선 보완 의무.

---

## §8. 결론 (main 점검 응답)

- **theory (이론섹션)** ✓ — theory-notes.md §6 H7-H12 framework + §6.7 공통 small-N rigor 게이트
- **validation (spec↔code 1:1)** ✓ — 본 파일 §1-§6 가설별 mapping table + drift 명시
- **rationale (왜 이 proxy/변환/측정)** ✓ — 본 파일 가설별 "rationale" 행
- **자문원문 ref** ✓ — 본 파일 가설별 "자문원문 ref" 행 (round-{1,2,3}-{gemini,claude}.md mapping)
- **falsifier** ✓ — 각 validation md §F + 본 파일 가설별 "falsifier" 행
- **proxy 한계** ✓ — 본 파일 가설별 "Proxy 한계" 행 (commodity-china BIS stock proxy 모범 mirror)

→ **crypto 저장 clean** (cycle 2 6 가설 전부 commodity validation-china 모범 패턴 mirror 완료)
