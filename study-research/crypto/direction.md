---
tags: [type/direction, domain/inv, phase/study-system, topic/crypto-lens]
date: 2026-05-30
study_id: crypto
asset_scope: [coin]
phase: 2-1 (방향성·자문 다회)
rounds: 3
converged: true
gate: awaiting-main-approval
---

# crypto 스터디 — 방향성 (2-1 산출, ★main 승인 대기)

> STUDY-KIT v2 §2 2-1단계 산출. /gemini-web + /claude-web 3 라운드 수렴.
> raw 누적: `raw/round-{1,2,3}-{gemini,claude}.md` (총 6 파일, ~52KB).
> ⛔ main(btn-Codlearn) 승인 전 2-2(이론학습) 진입 금지.

## 0. 메타 — 수렴 경로 요약

| Round | 작업 | 미수렴 → 수렴 |
|-------|------|---------------|
| R1 | ①②③ 광범위 답변 수집 | 두 모델 답변에서 7 차이 식별 |
| R2 | 7 차이 좁히기 | 4 합의 (prior 채널차등 / halving 분리 / momentum composite / stablecoin net creation) + 3 미수렴 |
| R3 | 3 미수렴 좁히기 + 2 부수질문 | **5 결정 모두 수렴, 두 모델 "추가 round 불필요" 명시** |

claude 모델이 R3 끝에 미세 정정 2건 제안 — 본 direction 에 반영: ①partial-corr 의 "prefix 우선" → "stability-gated bounded modulation" ②ETF flow prior 0.3-0.4 → **observe-only 0.05 (probation)**.

---

## §1. 이론 수집 방향 (①)

> 코인 가격결정을 깊이 이해하는 데 필수 자료. 5 채널 × 핵심 문헌.

### (i) 펀더멘털 없는 자산의 realized-value cycle indicator
- **Coin Metrics — "Introducing Realized Capitalization" (Carter & Le Calvez, 2018)** + State of the Network 시리즈 → realized cap = on-chain 평균 취득원가, MVRV = 시총/realized = 집계 미실현손익 → 평균회귀 cycle 진동자. **우리 시스템 MVRV PIT(instrument_source.CoinMetricsMvrvProvider) 의 정의 근거.**
- **Glassnode Academy (SOPR/NUPL/MVRV-Z)** → 실현 차익실현 압력 + 미실현손익 regime 밴드. 정의·band 해석 학습 가치.
- **PlanB "Modeling Bitcoin's Value with Scarcity" (2019, Stock-to-Flow)** → **반례 교보재.** 2021 이후 OOS 붕괴, N=4 cointegration spurious 의 전형. 우리 halving 가설 prior_strength 를 낮춰야 하는 이유.

→ 처리 방침: MVRV/NUPL/SOPR = **선형 factor 아니라 regime 분류용 conditioning 변수**. point price 예측 X, extreme band(top/bottom) tail 신호로만. realized cap 의 정의 drift(소실 코인·거래소 클러스터링·ETF 커스터디 이동) 항상 의심.

### (ii) 공급 schedule
- **Pagnotta & Buraschi "An Equilibrium Valuation of Bitcoin and Decentralized Network Assets" (2018)** → 네트워크 효과(Metcalfe) × 채굴 보안 균형, 공급은 한 입력일 뿐.
- 솔직한 한계 인정: 할빙에 대한 신뢰할 만한 계량 논문 없음. N=4 + cycle 간 비독립성 → 식별 불가. **할빙 alpha 주장 논문/리포트 전부 overfitting 의심 거른다.**

→ 처리 방침: **두 객체 분리** — (a) halving event(N=4) = belief regime label only / (b) 채굴자 매도 압력(hashrate/miner outflow) = 연속 시계열, daily 검정 가능 보조 지표.

### (iii) 거시 유동성 transmission
- **Liu & Tsyvinski "Risks and Returns of Cryptocurrency" (Review of Financial Studies, 2021)** → ★중요한 null result: **pre-2020 crypto 수익은 전통 macro/주식 factor 로 설명 안 됨**, 자체 momentum + investor attention 지배. macro driver 과대 prior 경고.
- **Michael Howell "Capital Wars: The Rise of Global Liquidity" (2020)** → global liquidity(중앙은행+민간)가 risk asset/BTC 사이클 선행 driver. real rate·DXY·M2 transmission.

→ 처리 방침: macro = regime-conditional driver. **pre-2020 학습 금지 (LTW null), macro 채널 fit start = 2020-03 (one-sided)**. 가장 깨끗한 crypto-native 유동성 게이지 = **stablecoin supply (DefiLlama 무료)**.

### (iv) 시장 미시구조
- **Makarov & Schoar "Trading and Arbitrage in Cryptocurrency Markets" (JFE 2020)** → 시장 분절, arbitrage spread, order flow.
- **Liu, Tsyvinski & Wu "Common Risk Factors in Cryptocurrency" (JoF 2022)** → 3-factor(CMKT/CSIZE/CMOM). cross-section 학술 factor. **우리는 ticker 세분화 X 라 cross-section 구성 불가**, 대신 BTC time-series TS-MOM + dominance proxy 로 활용.
- BitMEX Research + perpetual swap 문헌(Alexander 등) → funding rate = 레버리지·포지셔닝 압력 → liquidation cascade.

→ 처리 방침: funding = 포지셔닝 평균회귀 + cascade tail 게이지. dominance = rotation 게이지(상승=alt 상대 약세). Binance public funding/OI 시계열로 고빈도 검증. **여기가 통계적으로 가장 견고 (effective N 가장 큼).**

### (v) digital gold vs risk asset 디커플
- **Baur, Hong & Lee "Bitcoin: Medium of Exchange or Speculative Asset?" (2018)** → BTC = 주로 투기자산, hedge/safe-haven 속성 약함.
- **Biais, Bisière, Bouvard, Casamatta & Menkveld "Equilibrium Bitcoin Pricing" (JoF 2023)** → 거래 편익+투기 균형, bubble 동반.
- post-2024 ETF 실증 → spot ETF 승인(2024.01) marginal buyer 구조 변화. BTC-Nasdaq 상관은 regime-의존. **on-chain reserve 지표 의미 구조적으로 약화** (ETF 커스터디/콜드 이동).

→ 처리 방침: 고정 regime 가정 금지. BTC-주식/BTC-금 rolling 상관을 macro regime 조건부 추정. ETF break(2024-01) = **watch flag only (fit split 아님, 1.5yr 짧음)**. on-chain (exchange_reserve/whale) 의 down-weight 대신 **Farside ETF net flow 신규 collector 로 institutional demand 신호 교체**.

### OSS / 도구
- `coinmetrics-api-client` (PIT community data) — 이미 wire (instrument_source)
- `alphalens-reloaded` (factor IC/quantile, 원본 deprecated)
- `vectorbt` 또는 `bt` (walk-forward 백테스트)
- `confseq` (Howard & Ramdas, anytime-valid CI/e-process) — **우리 e-CUSUM 의 이론 토대** (Ramdas, Grünwald, Vovk & Wang "Game-theoretic statistics and safe anytime-valid inference" Statistical Science 2023)
- `sklearn.covariance.GraphicalLassoCV` — partial-corr (Friedman/Hastie/Tibshirani 2008 Biostatistics)
- DefiLlama public API (stablecoin supply 무료)
- Farside Investors public daily (BTC ETF net flow 무료, post-2024 only)

---

## §2. 이론 검증 방향 (②)

> 보유 데이터로 시계열 검증. ★핵심 원칙: "가장 풍부한 신호일수록 독립 관측치가 가장 적다" (claude r1). prior 의도적 보수 + regime oscillator 취급.

### 데이터 시계열 두 트랙 분리
- **장기 트랙 (cycle/macro)**: CoinMetrics PIT 일별 BTC realized/MVRV (~2011+, ~14yr daily). MVRV·NUPL·halving·macro 가설 전부 여기서. **Upbit 30일 4h봉으로 MVRV 사이클 검증 무의미 (0개 사이클).**
- **단기 트랙 (microstructure)**: Upbit 4h봉 42개 + 오더북/체결 + Binance funding/OI. funding/RSI/OI/FGI 단기 swing 만.

### 적용 가능 partial-corr edge 표 (장기 트랙 일별)

| edge | conditioning_set | 검증 의도 | 사전 예상 (claude r1) |
|------|------------------|----------|---------------------|
| MVRV ⊥ fwd_ret \| FGI | {FGI} | MVRV 가 sentiment 와 별개 신호인가 | partial 이 0 쪽으로 크게 수축 (공통원인 강함) |
| dominance ⊥ alt_excess \| BTC_ret, real_rate | {BTC_ret, macro real_rate} | rotation 이 BTC-beta/macro 와 독립인가 | 약하게 독립 잔존 |
| funding ⊥ fwd_ret \| RSI, OI | {RSI(14), OI_change} | funding 이 momentum/포지션과 별개인가 | 단기 cascade 채널 일부 잔존 |
| stablecoin_supply ⊥ fwd_ret \| real_rate, DXY | {real_rate, DXY} | crypto-native vs macro 유동성 | crypto-native 일부 잔존, 단 역인과 위험 |
| MVRV ⊥ fwd_ret \| halving_phase | {halving_phase} | cycle 지표가 halving 시계만 추종하는가 | 상당 부분 흡수 |

★검증 결과를 **offline 표** 로 박제 → 본 시스템 **신규 coin-internal RegimeGlasso 인스턴스의 corr_prior warm-start + shrinkage target** (R3 합의: partial-corr 학습 위치 = hybrid).

### Regime 분해 단위 — 차원의 저주 회피
- **FGI 5밴드**: Extreme Fear 0–24 / Fear 25–44 / Neutral 45–55 / Greed 56–75 / Extreme Greed 76–100
- **halving 4-phase**: post-halving 0-6mo(accumulation) / 6-18mo(markup) / 12-24mo(distribution) / 24-36mo(bear). 경계는 deterministic schedule
- **macro regime**: real_rate + DXY + 주식 vol → risk-on/neutral/risk-off 3-state

★ **belief b(t) primary 축 = FGI 5-state soft membership (R3 합의)**. macro·halving = low-dim parametric multiplier (cov modulator). **금지: 5×4×3=60셀 full cross-product** (셀 빈도 폭주, glasso instability). FGI×halving 교차 IC 산출 금지.

### Rank-IC 산출 단위
- **wiring 용**: BTC 단일 time-series IC (MVRV/NUPL/SOPR — BTC 체인 지표) + sleeve aggregate composite (cap-weighted basket) time-series IC (funding/dominance/FGI)
- **검증용(미배선)**: top 20-50 mcap universe cross-sectional Rank-IC — momentum/size factor 존재 자체 offline 확인만, 트레이딩 ticker-level 미진입

### 검정력 한계 — 수치 명시
- halving N=4 → across-phase 검정 power 0. cycle 간 비독립(regime 자기상관). **standalone IC 가설 금지, 라벨/interaction only**
- MVRV: ~14년 daily ≈ 5000+ obs but 독립 cycle 극단(top/bottom) 3~4쌍. extreme effective N 미미, CI 매우 넓음, **prior_strength 낮게, "0 포함 CI" 디폴트 예상**
- FGI: 2018.2~ daily ≈ 2900 obs. extreme 이벤트 study 가능
- **funding/OI**: 고빈도 다관측 → 단기 horizon power 양호. 통계적으로 가장 견고

### Forward return horizon 매핑
- **7d**: funding extreme, RSI, OI, FGI 단기 swing → 평균회귀 가설
- **30d**: dominance rotation, stablecoin supply 변화, sentiment regime, macro 상관
- **90d**: MVRV/NUPL regime, macro 유동성, halving phase 맥락

### 무lookahead PIT
- knowable_from 절대 기준 (API 수신 지연: FGI 익일·MVRV vintage·funding 8h lag 반영)
- 엄격 OOS 백테스팅 walk-forward

---

## §3. 핵심 가설 초안 (③) — 반증조건 포함

> 5개 후보 가설 + 1개 보조 메커니즘. 각각 검증 단계(2-3)에서 시계열 IC·partial-corr 로 실제 성립 확인.

### H1. MVRV mean-revert (Valuation cycle)
- 가설: "MVRV > 2.4 → 7~30d horizon mean-revert 하락" (우리 기존 instrument_source.run_mvrv_closed_loop mvrv_hi=2.4 임계 재사용)
- 반증조건: FDR_DECISION binomial p > 0.05 누적 + score_ic_breakdown_eprocess e-CUSUM 단측 붕괴
- partial-corr edge: **MVRV ⊥ fwd_ret | halving_phase, FGI** — direct 잔존시 확인 / 흡수면 common_cause
- prior_sign: neg / prior_strength: **0.4** (on-chain 채널 차등 0.3~0.5)
- horizon: 30d 우선 / 7d 보조
- 시스템 wire: `core/data/instrument_source.run_mvrv_closed_loop` (이미 ledger 운영) → `weight_falsification.score_ic_breakdown_eprocess` 누적 → `AssumptionRegistry.crypto.mvrv_mean_reverts.confidence_now`
- 활성 순서: **macro_abstain 다음 2번째** (claude r3 추천 — 14yr 최장·최청정)

### H2. Funding cascade (Microstructure)
- 가설: "|funding| > 0.05%/8h (95th percentile) & OI 급증 → 7d horizon 청산 cascade (가격 ±5%+ 급변)"
- 반증조건: hit rate < 0.5 binomial p > 0.05 OR partial-corr 추정치 95% CI 에 0 포함
- partial-corr edge: **funding ⊥ fwd_ret | RSI, OI_change** — direct 일부 잔존 예상
- prior_sign: neg (롱 누적 → 청산) / prior_strength: **0.6** (microstructure 채널 차등 0.5~0.7)
- horizon: 7d
- 시스템 wire: `coin_consensus_lens.CoinLensData.funding_rate` + `OI_change` 입력 → `coin_sizing.size_coin_portfolio` 의 belief modulator (extreme funding 시 Kelly 보수화 0.5x)
- 활성 순서: 4번째

### H3. Stablecoin net creation → dry powder (Macro liquidity)
- 가설: "stablecoin net creation (Δsupply growth z-score) > 1 → 7~30d horizon 가격 상승 in 거시 risk-on regime"
- 반증조건: **rolling Granger causality p > 0.05 OR CCF lag-dominant 역전 (가격 → 발행 demand 역인과 우세)**
- partial-corr edge: **stablecoin_growth ⊥ fwd_ret | real_rate, DXY** — direct 일부 잔존
- prior_sign: pos / prior_strength: **0.3** (macro 채널 차등 0.2~0.4)
- horizon: 7~30d (90d 는 다른 driver 매몰)
- ★ Wire 조건: **lead-lag 게이트 통과 시에만 활성** — rolling CCF 가 lag-dominant 로 뒤집히면 신호 비활성. **Level 사용 금지, net creation (Δsupply) 만**
- 시스템 wire: 신규 collector `core/data/collectors/defillama_stablecoin.py` (무료) → 신규 hypothesis `crypto.stablecoin_dry_powder` + `confidence_hooks.lead_lag_validity` 게이트

### H4. ETF net flow → digital-gold demand (Decoupling)
- 가설: "BTC ETF net inflow 5d 누적 > 0 → 30d horizon 가격 상승 in 거시 risk-off regime" (digital-gold 특성 발현)
- 반증조건: post-2024 (1.5yr) OOS Rank-IC e-CUSUM 단측 붕괴 OR ETF flow ⊥ fwd_ret | SPX_returns partial 추정치가 양 아닐 시
- partial-corr edge: common_cause (macro 유동성) 통제 후 direct
- prior_sign: pos / prior_strength: ★**observe-only 0.05 (probation, claude r3 정정)**
- horizon: 30d
- ★ Wire 조건: **probationary** — 데이터 누적되며 rolling reject_signal 발화 시 자동 down-weight. **glasso 노드 미포함** (post-2024-only complete-case window 수축 회피)
- 시스템 wire: 신규 collector `core/data/collectors/farside_etf_flow.py` (무료, fallback prev-value)

### H5. Halving phase regime conditioning (Supply schedule)
- 가설: ★**standalone IC 산출 X**. halving phase 4-state = belief regime label only, 다른 지표(MVRV·funding 등)의 conditioning 변수
- 반증조건: regime-conditional 다른 가설(H1·H2)의 phase 별 IC 안정성으로 *간접* 검증 (N=4 통계 power 0 명시)
- partial-corr edge: **regime label, edge 노드 아님**
- prior_strength: **0.1** (halving 채널 최하)
- 보조 메커니즘: **miner_outflow / hashrate change** 별도 연속 보조 지표 (on-chain 채널 prior 0.3~0.4) — daily 검정 가능

### H6. (보조) macro_abstain risk gate (Circuit breaker)
- 가설: "coin_track_macro.H29 abstain (macro unavailable / risk-off 극단) → 7~14d horizon buy→hold 차단이 drawdown 방어"
- 반증조건: abstain hit-rate < 0.5 OR missed-rally 누적 음의 알파 (Type II error)
- 시스템 wire: 기존 `coin_track_macro.generate_candidate` H29 차단 + `weight_falsification.score_ic_breakdown_eprocess`
- ★ **활성 순서 1번째** (claude r3: "신뢰도 데이터 없을 때 가장 가치, downside protection 우선")

---

## §4. 본 시스템 Wire 매핑 — 5 결정 종합

| 결정 | 합의 | 적용 위치 |
|------|------|-----------|
| **D1 prior_strength** | 채널별 차등 + force-include 임계 0.3 — micro 0.5~0.7 / on-chain 0.3~0.5 / macro 0.2~0.4 / halving 0.1~0.2 | `core/structure/conditional_correlation.RegimeGlasso(corr_prior=...)` — 신규 coin-internal 인스턴스, 채널 태그 → strength 매핑 테이블 |
| **D2 macro break** | 채널별 명시 — **macro 채널만 2020-03 fit start (one-sided)**, on-chain 채널 full history, 2024 ETF = watch flag only | `macro_orchestrator.fit(start_date="2020-03-01")` macro 채널 한정, on-chain lookback 무제한 |
| **D3 ETF flow** | 신규 collector ADD, prior = **observe-only 0.05 (probation)** | 신규 `core/data/collectors/farside_etf_flow.py` (post-2024 only) + standalone gated indicator (glasso 미포함) |
| **D4 partial-corr 학습 위치** | **hybrid** — offline 표 = shrinkage target, internal glasso = stability-gated bounded modulation, fwd_ret 노드 분리 | 신규 `core/coin_track/internal_corr.py` → `RegimeGlasso(corr_prior=offline_table, regime_ids=vol⊗macro, npn=True)`. cross-asset 인스턴스와 물리 분리, coin_consensus_lens(§4③ SACRED) 불침범 |
| **D5 belief primary 축** | FGI 5-state soft membership = primary / macro·halving = parametric multiplier (cov modulator, dict 키 추가 X) | `coin_track._fgi_to_belief` 신설 (FGI primary) + `_belief_conditional_cov` belief 인자 = FGI-state-keyed flat dict 유지. nested dict 확장 금지 |
| **D6 hooks rollout** | macro_abstain → mvrv → fgi → funding → halving phased | `confidence_hooks.macro_abstain` 활성 + 나머지 4 hook dormant 등록. OOS 검증 후 점진 활성화 |

---

## §5. 미해결 의문 (두 모델이 솔직히 인정한 약점)

> 2-3 (실데이터 검증) 에서 우선 확인할 항목.

1. **prior_strength 채널 차등 숫자 (0.6/0.4/0.3/0.1) 의 backtest 미검증** — 사전 educated guess. prior_strength → OOS 엣지 안정성 매핑 측정 전까지 잠정값.
2. **2020-03 break 위치의 사후 selection bias** — researcher degree-of-freedom. post-2020 도 sub-regime 불안정 (2022 고상관 / 2023 부분 decoupling / 재커플링) → 단일 macro beta 는 fiction.
3. **stablecoin 집계 Δsupply 의 노이즈** — DeFi 담보·OTC·cross-chain bridge 섞임. 거래소向 inflow 만이 깨끗한 dry powder 인데 DefiLlama 무료 단위로 불가. USDC·on-ETH/Solana 가중이 더 깨끗 (향후 refinement).
4. **internal glasso 의 effective-N gate 영구 폐쇄 위험** — funding-limited (2020-9~) + 일봉 autocorr 로 per-regime effective N 이 gate 상시 못 넘으면 "거의 안 터지는 비싼 보험". 사전 검증 필요.
5. **ETF flow 데이터 단일 free source 취약성** — Farside 스키마/티어 변동, 리던던시 없음. ETF flow ≠ total institutional demand (OTC·futures basis·non-US ETF 누락).
6. **macro_abstain 의 counterfactual 검증 어려움** — "correct abstention" 은 counterfactual. abstained 구간 shadow-mode log 필요.
7. **halving N=4 + macro epoch confound** — 2012 태동 / 2016 ICO 전야 / 2020 COVID 유동성 / 2024 ETF 각각 다른 macro epoch 와 완전히 confound → halving 효과는 macro epoch 와 분리 불가능.
8. **claude r2 핵심 미해결 의문**: 권고들 다수가 "in-sample 조건부 독립/lead-lag → OOS 안정" 가정에 의존. 암호자산은 그 가정이 가장 잘 깨지는 자산군 → 모든 숫자·엣지는 rolling refit 간 안정성 6 regression invariant 측정 전까지 잠정값.

---

## §6. 다음 단계 미리보기 (2-2 → 2-3, ★승인 후)

### 2-2 이론 학습 → `raw/theory-notes.md`
- §1 5채널 × 핵심 문헌 정독. 무료 자료 우선 (CoinMetrics SOTN 시리즈, PlanB S2F 반례, Liu&Tsyvinski 2021 null, Liu/Tsyvinski/Wu 2022, Howell Capital Wars).
- 거시 깊이 정합: M2 ↔ 미·일 국채금리 ↔ 환율 → coin 의 stablecoin ↔ real_rate ↔ DXY ↔ BTC 관계도.
- 도구 학습: confseq (e-process anytime-valid), graphical lasso (partial-corr), Granger/CCF.
- 산출: theory-notes.md (가격결정 원리 + 지표 의미·관계도 + 도구 사용법).

### 2-3 실데이터 시계열 검증 → 코드화 → `raw/validation-{지표}.md` + `study_session.yaml`
- 장기 트랙 검증 (CoinMetrics PIT 14yr):
  - H1 MVRV mean-revert: instrument_source.run_mvrv_closed_loop 확장 검증 (이미 fixture 검증 완료, real PIT 데이터로 재검증)
  - H5 halving phase: regime label only, phase 별 H1 IC 안정성 간접 검증 (N=4 power 0 명시)
  - 5 partial-corr edge 표 offline 산출 (graphical lasso, nonparanormal 전처리)
- 단기 트랙 검증 (Binance public funding/OI + Upbit + FGI):
  - H2 funding cascade: 95th percentile 진입 후 24~72h OI·가격 변화 event study
  - FGI extreme contrarian: regime별 7d forward return 검증
- 신규 collector 검증 (DefiLlama, Farside):
  - H3 stablecoin lead-lag: Granger + CCF (양방향, growth 정규화, ADF 선행)
  - H4 ETF flow probation: post-2024 1.5yr rolling IC
- 분석 코드 .py 는 Bash python 직접 실행 (산출 numeric → raw/validation-*.md)
- 모든 검증 결과로 study_session.yaml 7 블록 채움. lens/상관/가중 코드화 도출.

---

## ⛔ 게이트 — main 승인 대기

본 direction.md 의 5 결정 + 6 가설 후보 + 8 미해결 의문 + 2-2/2-3 미리보기를 main(btn-Codlearn) 에 보고. 승인 또는 보완 요청 받기 전 2-2 진입 금지.

> raw 누적: round-1-gemini.md / round-1-claude.md / round-2-gemini.md / round-2-claude.md / round-3-gemini.md / round-3-claude.md (총 52KB).
