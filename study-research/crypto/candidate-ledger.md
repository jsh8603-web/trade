---
tags: [type/candidate-ledger, domain/crypto, purpose/easy-review]
date: 2026-05-31
purpose: 그동안 자문(R1~R3)·이론(theory-notes)·실측(validation)에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
note: direction.md / theory-notes.md §1 / 블록6 collector_plan / validation-*.md 미해결의문 / 자문 raw 6개 (round-{1,2,3}-{gemini,claude}.md) 에 흩어진 걸 1파일로 집약.
---

# crypto 지표 후보 원장 (candidate ledger)

> 자문 R1-R3 (gemini+claude) + theory-notes 5채널 11문헌 + 실측 7 validation 에서 거론된 *모든* 지표·신호 후보.
> 채택 8 / 이연 14 / 미채택 6 / 후속 재검증 5. v2 yaml indicators 8건 = 채택분.

---

## ✅ 채택 (yaml v2 블록2 등록 + 검증 통과)

| 지표 | family | tier | 근거 |
|---|---|---|---|
| **mvrv_btc** | macro_sens | structural→conditional | CoinMetrics CapMVRVCur PIT n=5795 (2010-07~). marginal trend 정반대 발견 → conditional only (FGI×halving) mean-revert |
| **fgi** | risk | conditional | alternative.me daily n=3037 (2018-02~). belief b(t) primary 축 (5-state soft) |
| **funding_rate** | risk | trend_follow | Binance USDT-M BTCUSDT 8h n=7363 (2019-09~). ★자문 cascade 가설 REJECT → 부호 반전 trend follow |
| **btc_price** | momentum | core | Binance spot 1d n=3209 |
| **stablecoin_total_supply** | macro_driver | reflexive_guard | DefiLlama daily n=3105 (2017-11~). Granger lead OK but bidirectional reflexive |
| **etf_net_flow_usd** | macro_driver | probation 0.05 | Farside daily n=613 (2024-01~). hit rate 56.7% p=0.006 |
| **halving_phase** | macro_driver | label_only | 결정론 schedule. N=4 standalone 금지, regime label only |
| **btc_dominance** | macro_driver | conditional | CoinGecko /global snapshot (현재). dominance ↓ = alt-season proxy (CSIZE 대체) |

---

## ⏳ 이연 (이론·후보 식별됐으나 미투입 — collector 미구축 / 라이브 snapshot 만 / proxy 대체 우선)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| **SOPR (Spent Output Profit Ratio)** | Glassnode framework, theory-notes §1(i) | CoinMetrics Community 가용여부 미확인. Glassnode 유료 게이트. MVRV 와 같은 realized-value 잠재인자 중복 의심 | CoinMetrics Community key 확인 또는 Glassnode 유료 도입 |
| **aSOPR** | Glassnode | 24h 미만 UTXO 제외 = SOPR refinement. 동일 유료 게이트 | 동상 |
| **NUPL (Net Unrealized P/L)** | Glassnode framework | NUPL = 1 - 1/MVRV (회계 동치) → 중복신호 cap. 별도 등록 X | 독립 정보량 입증 시만 |
| **MVRV-Z (σ 정규화)** | Glassnode | σ 정규화로 historical level 의존 감소. 우리는 mvrv_z = (mvrv - mean) / std 계산 가능하지만 fit-window 의 lookahead 검토 필요 | walk-forward σ 정의 확정 |
| **miner_outflow / miner_reserve** | theory-notes §1(ii), claude r3 | halving N=4 의 *연속 메커니즘 보조* — 채굴자 매도 압력. CoinMetrics MinerNetTransfers Community 일부 무료 | CoinMetrics community endpoint 확장 fetch |
| **hashrate change** | theory-notes §1(ii) | halving 후 marginal miner capitulation 신호. CoinMetrics HashRate Community 일부 | 동상 |
| **exchange_reserve_change** | direction.md, consensus_lens 입력 | 라이브 snapshot 만 (consensus_lens.CoinLensData), 시계열 무료 단위 없음. CryptoQuant 유료 | CryptoQuant 유료 또는 CoinMetrics community 확인 |
| **whale_inflow_usd** | direction.md, consensus_lens 입력 | 라이브만, 시계열 부재. ETF 이후 의미 약화 (claude r3: custodian 이동) | post-2024 정보가치 검증 후 도입 결정 |
| **OI history (시계열)** | direction.md | Binance public 30d max only. 장기는 paid 또는 매일 archive 누적 | 매일 archive ingest pipeline |
| **RSI(14)** | consensus_lens.CoinLensData | scripts/collect_market_data.py 의 라이브 계산만. 검증용 시계열 직접 계산 가능하지만 funding/12-1 과 중복 momentum 캡 | momentum composite 진입 시 |
| **SMA(20) deviation** | orchestrator drop_context | 라이브 regime 분류 입력만 (BaseStrategyAgent.detect_regime). 시계열 신호로는 미사용 | regime 분류 외 사용 시 |
| **macro_real_rate_proxy (10Y TIPS)** | direction.md, Howell framework | macro 방 산출 wire 예정 (coin_track_macro.macro_view 경유). coin sleeve 가 직접 수집 X | macro 방 산출 완료 후 wire |
| **DXY** | Howell framework, theory-notes §1(iii) | main 선구축 FxStore PIT 적재 예정 | FxStore wire 완료 후 |
| **M2 yoy (USD)** | theory-notes §1(iii) | FRED M2SL → macro 방 관할 | macro 방 wire |
| **JGB 10Y** | theory-notes §1(iii), 엔캐리 채널 | FRED IRLTLT01JPM156N → macro 방 관할 | macro 방 wire |
| **ECOS 한국 거시** | direction.md 부수 | 한국 BTC 시장 (Upbit) 관할 — 키 대기 | ECOS_API_KEY 발급 |
| **BTC-Nasdaq rolling corr** | theory-notes §1(v), Baur 2018, Biais 2023 | digital gold vs risk asset 디커플 검증 미수행. SPX/NDX daily 추가 fetch 필요 | yfinance / FRED SPX 추가 후 rolling 60d corr 계산 |
| **BTC-Gold rolling corr** | theory-notes §1(v) | digital gold 서사 검증. Gold (FRED GOLDPMGBD228NLBM) 추가 fetch 필요 | 동상 |

---

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| **PlanB Stock-to-Flow (S2F)** | ★반례 교보재로 명시 (theory-notes §1(i)). 2021 이후 OOS 붕괴, cointegration N=3 spurious. halving prior 0.1 의 근거. **모델 미채택, 학습 교훈만 채택** |
| **liquidation 데이터 직접** | Binance public liquidation stream 부분 (websocket only, history 미보존). Bybit / OKX 비포함. funding 신호로 proxy 대체 |
| **활성주소 (network address count)** | Pagnotta & Buraschi 2018 Metcalfe-like 이론. CoinMetrics AdrActCnt 있으나 reflexive (가격↑ → 활성주소↑) + 우리 시스템 가치평가 비주력 → 후순위 |
| **Google Trends / Twitter mention (LTW 2021 attention)** | Liu&Tsyvinski 2021 의 main predictor. PyTrends 무료 가능하지만 noisy + survey-effect. ★observe-only 도입 검토만, 본 cycle 미채택 |
| **ETH on-chain (MVRV / SOPR)** | 멀티코인 확장 시점에 도입. 현재 BTC 단일 sleeve focus. CoinMetrics community 가능 |
| **Crypto 3-factor cross-section (CMKT/CSIZE/CMOM, Liu/Tsyvinski/Wu 2022)** | ★ticker 세분화 X (coin §4③) 라 cross-section 구성 불가. BTC TS-MOM (funding/RSI/12-1 composite) + dominance proxy (CSIZE 대체) 로 part 흡수 |

---

## 🔬 후속 재검증 falsifier (채택했으나 조건부 — OOS / VECM / promotion gate)

| 가설 / 지표 | 미해결 의문 | unblock 조건 (validated 승격) |
|---|---|---|
| **mvrv_conditional_mean_revert** (H1) | marginal Spearman -0.071 / partial -0.085 BB95%CI=(-0.235,+0.073) → CI 0 포함 = direct edge 약. mvrv_hi=2.4 사후 fit 가능성 | 2017-2021 in-sample / 2022-2025 OOS strict 분리 재검증. CI 0 미포함 시 prior 상향 |
| **funding_trend_follow** (H2 ★자문 정정) | rolling sharpe 0.97 (positive) but daily aggregate 정보 손실 (intra-day cascade 미포착) | 8h 또는 분 단위 재검증. funding extreme + OI 급증 동조 시점만 분리 검증 |
| **stablecoin_lead_with_reflexive_guard** (H3) | BTC→supply Granger lag 7d p=0.014, lag 14d p=0.0000 → reflexive 위험. rolling sharpe -0.43 부호 반전 시기 다수 | VECM / 동시방정식 모델 도입. supply→BTC 단방향 유의 + reflexive 미유의 regime 식별 |
| **etf_flow_probation** (H4) | n=613 (1.5yr) 짧음. Rank-IC CI=(-0.16, +0.23) = 0 포함. Farside 단일 free source 의존 | 추가 1.5yr 누적 후 OOS rolling Rank-IC sharpe > 1 + binomial p<0.01 유지 시 prior 0.05 → 0.15 promotion |
| **halving_phase_conditional** (H5) | N=4 + macro epoch confound 식별 불가 (2012 태동/2016 ICO/2020 COVID/2024 ETF). effective N 모두 < 20 | 채굴자 압력 보조 지표 (hashrate / miner outflow) 도입 후 conditioning 효과 분리 |

---

## 📋 우선 검증 의문 (main 추가 조건 §5)

| 의문 | 검증 결과 | 미해결 |
|---|---|---|
| **#1 prior 채널 차등 ladder backtest** | ★실측 역방향 발견 (on-chain sharpe 1.27 > micro 0.97 > stablecoin -0.43) → ladder 재캘리브 (0.55/0.45/0.20/0.10) | backtest 누적 후 정확한 비율 결정, rolling window 길이·step 민감도 분석 |
| **#4 internal glasso effective-N gate** | 15/15 cell N≥24 100% / 11/15 N≥100 73% admit → gate threshold 100 권고, 영구폐쇄 위험 LOW | bootstrap edge stability 시뮬 미수행 (긴 연산). FGI 5→3 단계 통합 옵션 검토 |

---

## 🗂️ 미해결 의문 (direction.md §5 + validation 6번 섹션)

다음 세션 우선 작업 후보:

1. MVRV partial-corr conditioning_set 확장 (BTC dominance·real_rate·stablecoin 추가)
2. funding 8h or 분단위 cascade 재검증 (daily aggregate 정보 손실)
3. stablecoin VECM / 동시방정식 모델 (reflexive 분리)
4. ETF flow 1.5yr 추가 누적 후 promotion 게이트
5. halving 채굴자 압력 (hashrate / miner outflow) 보조 지표 collector 추가
6. rolling Rank-IC walk-forward strict 분리 (OOS PIT 강화)
7. post-2024 realized cap 의미 변화 (custodian 이동) 정량 측정
8. macro_abstain 가설 외부 macro proxy 시뮬 검증 (VIX>30 + DXY z>1)

---

## 📌 자산화 enum 분류 (다음 cycle 작업 분담 가이드)

| enum | 후보 | 목적 |
|---|---|---|
| **rule** | (없음) | 검증된 정량 규칙 (현재 v2 에서 새 rule 생성 X — 모든 가설 conditional/probation 라벨) |
| **memory** | mvrv marginal trend (자문 cascade 정정 사실), stablecoin reflexive 발견 | 다음 cycle 자문 prompt 의 prior 정정 입력 |
| **observe-only** | etf_flow_probation, halving_phase_conditional | 1.5yr 더 누적 후 promotion 결정 |
| **evt** | funding_trend_follow (★자문 부호 정반대 정정) | promotion-log ERROR 후보 (자문 가설 그대로 코드화 위험 사례) |
| **pointer** | direction.md §5, theory-notes §1, audit-guide 12축 (Hard-fail 4) | 다음 세션 SSOT 정독 우선순위 |
