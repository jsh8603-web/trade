---
tags: [type/notes, domain/inv, phase/study-system, topic/crypto-theory]
date: 2026-05-30
study_id: crypto
phase: 2-2 (이론 학습)
source: round-1-{gemini,claude}.md + round-2,3 정정 + 학술 표준 정의
---

# crypto 이론 학습 노트 (2-2 산출)

> direction.md §1 5채널 × 핵심 문헌의 학술적 압축. 단순 자문 인용이 아니라 각 이론의 *원리·가정·한계*를 정리하고 우리 시스템 어디에 wire 되는지 매핑한다. 후속 2-3 실데이터 검증의 이론적 토대.

## §0. 학습 원칙 (claude r1 통찰 채택)

> "가장 풍부한 신호일수록 독립 관측치가 가장 적다."

- on-chain cycle 지표 (MVRV·NUPL·SOPR) = 14년 daily 수천 obs 처럼 보이지만 **독립 cycle top/bottom 은 3~4쌍**. effective N 극도로 작음.
- halving = N=4, 각 사이클이 다른 macro epoch (2012 태동 / 2016 ICO / 2020 COVID 유동성 / 2024 ETF) 와 **confound** — halving 효과는 macro epoch 와 분리 불가.
- 반대로 funding/OI = 고빈도 다관측이지만 메커니즘 공개·crowded → **edge 얇음**.
- → 결론: prior_strength 의도적 보수, on-chain 은 factor 아니라 **regime oscillator** 로 취급.

---

## §1. 5채널 × 핵심 문헌 정독 정리

### (i) 채널 1 — Realized-value cycle indicator (Valuation 채널)

#### 문헌 1: Carter & Le Calvez, "Introducing Realized Capitalization" (Coin Metrics, 2018)

**핵심 정의** (학술 표준):
```
realized_cap(t) = Σ_i (UTXO_i 의 마지막 on-chain 이동 시점 가격 × UTXO_i 의 BTC 수량)
market_cap(t)   = current_price(t) × circulating_supply(t)
MVRV(t)         = market_cap(t) / realized_cap(t)
```

**해석**:
- `realized_cap` = 모든 UTXO 의 마지막 이동가 (= 마지막 거래 시점 가격) 의 합 ≈ **on-chain 집계 평균 취득원가 (cost basis)**.
- `MVRV > 1` = 평균 보유자가 미실현 이익 보유 / `MVRV < 1` = 평균 보유자가 미실현 손실 (capitulation 영역).
- `MVRV` 의 cycle 진동: 고점 매도 압력 누적 → 가격 하락 → MVRV 압축 → bottom 매집 → 상승 반복.

**가정과 한계** (학술 정직):
- (a) UTXO 의 "마지막 이동" = "최종 보유자의 취득" 으로 등치되지만 거래소 핫월렛 cluster, 채굴 풀 분배, ETF 커스터디 transfer 등은 실 거래 없는 이동 → realized cap drift.
- (b) lost coins (Satoshi 추정 100만 BTC 등) 의 처리 — 이동 안 됨 → realized cap 의 분모 효과 (시간이 지나면 점점 lost coin 의 영향이 희석돼야 하지만 실제로는 가격 기준 freeze).
- (c) ETF 시대 (2024+) post — institutional buyer 가 ETF custodian 으로 직접 입금 → on-chain 에선 "거래소 → custodian cluster" 이동으로만 보임. realized cap 의 "최종 보유자 취득가" 의미가 약화.
- (d) MVRV cycle 의 *공정 임계* (예: 2.4) 는 backtest fit 아니라 hand-tuned heuristic. mvrv_hi=2.4 는 우리 instrument_source.run_mvrv_closed_loop 에 박혀 있지만 사후 결과론.

**우리 시스템 wire**:
- `core/data/instrument_source.CoinMetricsMvrvProvider` — vintage·knowable_from 지원 PIT provider 로 이미 구현. CapMVRVCur 메트릭 사용.
- `core/data/instrument_source.run_mvrv_closed_loop` — mvrv_hi=2.4, horizon=7d, mean-revert "down" 예측, FDR_DECISION binomial p<0.05 reject. fixture 검증 완료.
- `core/structure/commodity_assumptions.crypto.mvrv_mean_reverts` 가정 카드 — parametric, scope=asset, domain=crypto.

#### 문헌 2: Glassnode Academy (SOPR / NUPL / MVRV-Z framework)

**SOPR (Spent Output Profit Ratio)**:
```
SOPR(t) = Σ_i (sold_price_i / acquired_price_i) for UTXO_i moved at t
         (가중 평균, value-weighted)
SOPR > 1 = 평균 이익 실현 / SOPR < 1 = 평균 손실 실현 (capitulation)
aSOPR (adjusted) = SOPR 에서 short-lived (24h 미만) UTXO 제외 — 거래소 hot-wallet 노이즈 제거
```

**NUPL (Net Unrealized Profit/Loss)**:
```
NUPL(t) = (market_cap(t) - realized_cap(t)) / market_cap(t)
       = 1 - 1/MVRV(t)
```
- regime band: > 0.75 Euphoria / 0.5~0.75 Belief / 0.25~0.5 Optimism / 0~0.25 Hope / < 0 Capitulation.

**MVRV-Z**:
```
MVRV-Z(t) = (market_cap(t) - realized_cap(t)) / σ(market_cap)
```
- σ 정규화로 historical level 의존성 감소. extreme band 검출 통계량.

**해석 한계**: 세 지표 (MVRV/NUPL/SOPR) 는 **같은 realized-value 잠재 인자에서 파생** — partial-corr 에서 multicollinearity 강함 (R3 의 D4 partial-corr edge 표 중 "SOPR ~ MVRV common_cause" 예상의 학술 근거).

**우리 시스템 wire**:
- direction.md §1 (i) collector_plan: SOPR 신규 collector 요청 (CoinMetrics Community 가능 여부 확인 / Glassnode 유료 폴백).
- 향후 SOPR + MVRV 합산 시 cap (중복 신호 페널티) 필요.

#### 문헌 3: PlanB, "Modeling Bitcoin's Value with Scarcity" (Medium, 2019, Stock-to-Flow 모델) — **★반례 교보재**

**모델**:
```
ln(market_cap) = α + β · ln(S/F) + ε
S/F = circulating_supply / annual_issuance  (희소성 측정치)
```
- in-sample (2010-2019): R² ≈ 0.95, cointegration test (Johansen) 유의.
- 예측: 2021-2024 cycle 가격 100만 USD 수렴 예언.

**OOS 붕괴 (2021-2024)** — 학술적 결정 증거:
- 실제 가격: 2021 peak ~69k → 2022 trough ~16k → 2024 recovery ~70k 횡보. 100만 USD 예언 완전 실패.
- 사후 분석 (Bhambhwani 2021 등): cointegration 은 N=3 (2012/2016/2020 halving) 데이터에서 우연 일치, **OOS 안정성 = 0**.
- 통계적 진단: cycle 간 비독립 (regime 자기상관) + 공통 trend (BTC 가격 자체 자기상관 강 + halving schedule deterministic) → cointegration test 의 spurious 잡음.

**교훈 — 우리 prior 설정에 직접 적용**:
- halving event N=4 → **standalone factor 박제 금지**.
- 우리는 halving prior_strength **0.1** 박음 (direction.md D1 합의) — PlanB OOS 붕괴 분석이 그 이유.
- halving phase = **belief regime label only** (D2 합의), Rank-IC standalone 산출 X.

#### 문헌 4: Pagnotta & Buraschi, "An Equilibrium Valuation of Bitcoin and Decentralized Network Assets" (2018)

**모델**:
- BTC 가격 = (네트워크 효과 / Metcalfe-like 사용자 함수) × (채굴 보안 균형) 의 균형해.
- 공급 schedule = 한 입력 변수 (충격 시 reprice) 이지만 dominant driver 가 아님.

**학술적 함의** — claude r1 통찰 그대로:
> "공급 schedule 은 한 입력일 뿐. 진정한 driver 는 네트워크 효과 × 채굴 보안 균형."

**한계**:
- 균형해 모델은 *비교 정태* 분석. 짧은 horizon (7~30d) 의 mean-revert / cascade 같은 *동적* 신호 설명 불가.
- 네트워크 효과 측정 어려움 (활성 주소 / 거래량 / DeFi TVL 등 proxy 들이 모두 noisy).

**우리 시스템 wire**: 직접 wire 없음. **이론적 baseline 만**. lens 의 pricing_principle 문장에 (5) "네트워크 가치 (Metcalfe-like)" 채널 포함의 근거.

---

### (ii) 채널 2 — 공급 schedule (Supply)

> 별도 standalone 문헌 부재 (할빙 alpha 주장 논문은 PlanB 류 spurious 가 대부분). 신뢰 가능한 학술 결론:

**결론 1: N=4 사실상 검정 불가**
- across-cycle 회귀: power 0 (자유도 부족).
- within-cycle 효과 측정: 각 cycle 의 macro epoch confound 통제 불가능.

**결론 2: 그러나 *연속 메커니즘* (채굴자 매도 압력) 은 검증 가능**
- halving event 시점 (N=4) 이 아니라 *연속 시계열* 에서 관측.
- 변수: network hashrate (daily), miner outflow (CoinMetrics MinerNetTransfers), miner reserve change.
- 가설: halving 후 block subsidy 50% 감소 → miner revenue compression → marginal miner capitulation / hashrate temporary down → on-chain miner outflow 증가.
- 측정 단위: daily, ~5000+ obs (장기), effective N 충분.

**우리 시스템 wire** (direction.md D2 합의):
- halving event → belief regime label, RegimeGlasso 의 regime_ids 입력
- miner_outflow / hashrate change → on-chain 채널 별도 연속 보조 지표 (prior 0.3~0.5)
- collector_plan 추가 후보 (현재 우리 시스템 미보유): CoinMetrics MinerNetTransfers·HashRate (Community tier 일부 무료)

---

### (iii) 채널 3 — 거시 유동성 transmission (Macro)

#### 문헌 5: Liu & Tsyvinski, "Risks and Returns of Cryptocurrency" (Review of Financial Studies, 2021) — **★null result 채택**

**연구 디자인**:
- 1/2011 ~ 12/2018 BTC + 7/2017 ~ 12/2018 Ethereum / Ripple 일별·주별 수익률.
- Fama-French 3-factor / 5-factor / momentum / 거시 변수 (industrial production, money supply, T-bill, term spread, default spread, inflation, agriculture commodities, gold) 회귀.

**핵심 결과**:
- (a) crypto 수익은 전통 stock/macro factor 로 설명 안 됨 — 회귀계수 거의 모두 무의미, 상수항(α) 만 유의.
- (b) crypto-specific 변수 (자체 momentum, investor attention proxy = Google Trends, Twitter mention) 만 유의한 예측력 보유.
- (c) crypto 의 risk premium 은 traditional asset 과 부분 분리.

**우리 결정에 적용**:
- pre-2020 데이터로 macro → crypto 학습 시도 = 학술적으로 null. 학습해도 무의미한 계수.
- **macro 채널 fit start = 2020-03 (one-sided)** (direction.md D2 합의).
- 2020-03 break 위치 = COVID shock + 글로벌 유동성 패러다임 전환 (Fed 무제한 QE) 이 표준 break event.

**한계**:
- 2020-03 split 자체가 사후 selection bias (researcher degree-of-freedom).
- post-2020 도 sub-regime 불안정 (2022 고상관 / 2023 부분 decoupling / 2024 재커플링) → 단일 macro β 는 fiction.

#### 문헌 6: Howell, "Capital Wars: The Rise of Global Liquidity" (Palgrave, 2020) + CrossBorder Capital framework

**핵심 framework**:
- Global Liquidity (GL) = 중앙은행 자산 + 민간 신용 + cross-border flow + collateral velocity 의 합성 지수.
- GL 의 변동 → risk asset cycle 의 선행 지표 (12~18개월 lead).
- BTC 같은 high-beta risk asset 은 GL 의 가장 민감한 surrogate.

**transmission 경로**:
```
중앙은행 BS (M2) ─┐
미국채 real rate  ├─→ 글로벌 risk premium ─→ stablecoin demand ─→ on-chain dry powder ─→ BTC
DXY (달러 funding)│                                                                      ↑
일본 BOJ YCC ────┘    엔캐리 ───────────────────────────────────────→ 글로벌 leverage ─┘
```

**우리 시스템 wire**:
- macro_orchestrator (이미 구현) 의 real_rate·DXY·M2 signals → coin_track_macro 의 macro_view 주입.
- direction.md H3 stablecoin net creation 가설의 *이론적 transmission* — Howell framework 의 GL → crypto-native liquidity (stablecoin) → 가격 채널.

**한계**:
- GL 지수 자체가 합성 — 우리는 부분 변수 (DXY·real rate) 만 보유.
- 12~18M lead 는 long-horizon, 우리 7~30d horizon 가설과 시간 스케일 mismatch.

#### ★거시 transmission 관계도 (직접 정리, 우리 보유 변수 기준)

```
                    [매크로 (장기, 12-18M lead)]
                              │
   ┌──────────────────────────┼──────────────────────────┐
   ↓                          ↓                          ↓
M2 yoy↑                  real_rate (10Y TIPS)         DXY↑
(USD 공급량)              ↑=긴축 / ↓=완화           (달러 펀딩 비용)
   │                          │                          │
   │                          ├────→ 미-일 금리차 ────→ │
   │                          │      (엔캐리 채널)      │
   ↓                          ↓                          ↓
스테이블코인 시총↑         risk premium                BTC 펀딩 비용↑
(USDT+USDC+DAI)           = HY OAS·VIX                   │
   │                          │                          │
   ↓                          ↓                          ↓
                  [크립토 (단기, 7-30d 영향)]
                              │
   ┌──────────────────────────┼──────────────────────────┐
   ↓                          ↓                          ↓
stablecoin net creation    BTC dominance              ETF net flow
("dry powder")             (rotation 채널)             (post-2024 only)
   │                          │                          │
   ↓                          ↓                          ↓
            ★ BTC/altcoin 가격 ★
                              │
   ┌──────────────────────────┼──────────────────────────┐
   ↓                          ↓                          ↓
on-chain cycle              microstructure            sentiment
(MVRV·NUPL·SOPR)            (funding·OI·whale)        (FGI 5단계)
   │                          │                          │
   └─→ cycle top/bottom       └─→ 청산 cascade           └─→ contrarian extreme
       (long horizon 30-90d)      (short horizon 7d)         (short horizon 7-14d)
```

**핵심 transmission 가설** (위 그림의 화살표 해석):
1. M2 ↑ → stablecoin demand ↑ → stablecoin net creation ↑ → BTC 매수 압력 ↑ (7~30d)
2. real rate ↑ → 위험자산 멀티 압박 → BTC 약세 (post-2020, pre-2024 ETF 강) / post-2024 부분 디커플
3. DXY ↑ → 달러 funding 비용 ↑ → leverage 청산 → BTC funding 음수 / 약세 (7d)
4. 미-일 금리차 축소 → 엔캐리 청산 → 글로벌 risk asset 동반 약세 → BTC

**검증 우선 순위** (2-3 우선 실측 대상):
- (1) stablecoin net creation → BTC (Granger / CCF lead-lag) — direction.md H3 핵심
- (2) real rate → BTC (post-2020 fit start, sub-regime 분해)
- (3) DXY → BTC funding (단기 채널)

---

### (iv) 채널 4 — 시장 미시구조 (Microstructure)

#### 문헌 7: Makarov & Schoar, "Trading and Arbitrage in Cryptocurrency Markets" (JFE, 2020)

**연구 디자인**: 2017-2018 글로벌 거래소 (Bitfinex/Bittrex/Coinbase/Kraken 등 15+) BTC/ETH/XRP 가격 분초 단위.

**핵심 결과**:
- (a) Cross-exchange arbitrage spread = 평균 1% (peak 10%+), traditional asset (0.01% 이하) 대비 100~1000배.
- (b) 차익 거래 제약: 자본 통제 (한국 김치 프리미엄 사례), KYC/AML, 거래소 신용 위험.
- (c) Price discovery 는 가장 큰 거래소 (Bitfinex/Coinbase 등) 가 leader, 작은 거래소가 follower.

**우리 시스템 wire**:
- Upbit 단일 거래소 가격만 사용 → 김치 프리미엄 효과 인지 필요 (한국 한정 premium/discount 박스권).
- coin_consensus_lens 의 funding/whale 입력은 Binance global 기준 — Upbit 가격과 lag 가능.

#### 문헌 8: Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency" (Journal of Finance, 2022)

**모델**: cross-section 3-factor:
- CMKT (crypto market) = value-weighted top 100 coin return.
- CSIZE = small-cap minus big-cap return spread.
- CMOM = winner minus loser (1~4 week momentum).

**결과**:
- 3-factor 가 cross-section coin return의 95%+ 설명.
- CMOM 은 stock momentum 보다 강함 (autocorr 더 길게).

**우리 시스템 적용 한계** (direction.md D6):
- 우리 ticker 세분화 X → CSIZE / CMOM 의 *cross-section 구성* 불가.
- 대안: BTC time-series TS-MOM (= CMOM 의 single-asset 변형) + dominance proxy (BTC.D ↓ = alt-season = CSIZE 방향) + CMKT = sleeve 보유 자동 노출.
- **주의**: TS-MOM 을 cross-section CMOM 으로 부르지 말 것 (학술 혼동).

**중복 신호 cap** (claude r3 강조):
- RSI / 12-1 price momentum / funding rate = 같은 latent "momentum/positioning" 적재.
- 단순 z-sum 위험: funding 은 extreme 에서 mean-reversion (과열 롱→반전) 신호 → trend momentum 과 부호 반대 → flat 평균 시 상쇄.
- → **regime-conditional 처리**: extreme funding 시 momentum 신호 cap 또는 부호 반전.

#### 문헌 9: BitMEX Research + perpetual swap 학술 (Alexander & Heck 2020 등)

**Perpetual swap funding rate 메커니즘**:
```
funding_rate (8h) = clamp(premium_index + interest_rate, -0.75%, +0.75%)
premium_index    = (mark_price - spot_price) / spot_price
양수 funding     = 롱 우세, 롱이 숏에게 지불 (롱 over-leverage 정황)
음수 funding     = 숏 우세, 숏이 롱에게 지불
```

**Cascade 메커니즘**:
- 극단 funding (>0.05% / 8h = 연 ~55%+) → 롱 포지션 마진콜 임계 근접.
- 가격 -3~-5% 하락 → 누적 청산 시작 → forced selling → 가격 추가 하락 → cascade.
- **liquidation 데이터** (Binance public, Bybit public) 가 직접 신호.

**우리 시스템 wire**:
- direction.md H2 funding cascade 가설.
- coin_consensus_lens.CoinLensData.funding_rate (이미 wire).
- coin_sizing.size_coin_portfolio belief modulator 에 extreme funding → Kelly 0.5x 보수화 (D1 prior 0.6).

---

### (v) 채널 5 — Digital gold vs Risk asset 디커플 (Decoupling)

#### 문헌 10: Baur, Hong & Lee, "Bitcoin: Medium of Exchange or Speculative Asset?" (2018)

**결과**: BTC 의 hedge/safe-haven 속성 약함. 주식 stress 시 BTC 가 *오히려* 동반 하락 → speculative asset 본성.

#### 문헌 11: Biais, Bisière, Bouvard, Casamatta & Menkveld, "Equilibrium Bitcoin Pricing" (JoF, 2023)

**모델**: 거래 편익 (transaction utility) + 투기 동기 (speculative motive) 의 균형. bubble 동반 가능 (다중 균형).

**시사**: BTC 가격은 fundamental + bubble 의 혼합 — fundamental 식별 어려움. **prior 박제 위험**의 학술 근거.

#### post-2024 ETF 구조 변화 (2024-01 spot ETF 승인, BlackRock IBIT 등 11 ETF)

**실증 관찰** (2024-2026):
- BTC-Nasdaq 일별 상관: 2024 0.4~0.6 → 2025 0.2~0.5 (변동 크지만 평균 하향).
- BTC-Gold 상관: 2024 0.1~0.3 → 2025 0.3~0.5 (digital gold 서사 강화).
- ETF net inflow cumulative: 2024 ~37B USD, 2025 보합 → 2026-Q1 재유입.

**구조적 변화의 함의**:
- on-chain reserve / whale 지표 의미 약화: 코인이 ETF custodian (Coinbase Custody / Fidelity) 로 이동 — on-chain 에선 "거래소 → 콜드월렛" 으로만 보임.
- ETF net flow = institutional demand 의 깨끗한 surrogate (Farside Investors daily 무료).

**우리 시스템 wire** (direction.md D3 합의):
- 신규 collector `farside_etf_flow.py` (post-2024 only).
- prior = **observe-only 0.05 (probation)** — 짧은 표본 (~2년).
- glasso 노드 미포함 (complete-case window 수축 회피), standalone gated indicator.

---

## §2. 도구 학습 (검증 단계 2-3 도구)

### §2.1 confseq (Howard & Ramdas) — e-process anytime-valid CI

**참조**: Ramdas, Grünwald, Vovk & Wang, "Game-theoretic statistics and safe anytime-valid inference" (Statistical Science, 2023).

**핵심 개념**:
- 전통 p-value: 단발 검정 (sample size 사전 고정). optional stopping 시 type-I error 부풀음 (peeking 문제).
- e-value / e-process: 모든 시점 t 에서 동시 valid. `E_t ≥ 1/α` 발화 시 type-I error ≤ α 보장 (Ville's inequality).
- **anytime-valid** = "데이터가 추가 누적될 때마다 검정 가능, 결론 그대로 유지".

**우리 시스템 wire** (이미 구현):
- `core/structure/eprocess_backbone.e_cusum(s, baseline, sd, tau2, alpha)` — 단측 E-CUSUM, log_R reset (개선만 floor=0).
- `core/assume/weight_falsification.score_ic_breakdown_eprocess` — score IC 시계열 단측 붕괴 검정.
- Ville's inequality 적용: `P(거짓 kill) ≤ α`, optional-stopping robust.

**우리 가설 적용** (direction.md confidence_hooks 5종):
```python
# 의사 코드 (실제 호출 패턴)
from core.structure.eprocess_backbone import e_cusum

# H1 MVRV mean-revert
ic_series = [rank_ic(scores[w], fwd_ret[w]) for w in rolling_windows]
max_r = e_cusum(ic_series, baseline=0.0, sd=ic_std, alpha=0.05)
if max_r >= 1.0/0.05:  # 20
    # PRIMARY kill → retract crypto.mvrv_mean_reverts
```

### §2.2 graphical lasso (Friedman/Hastie/Tibshirani 2008) — partial-corr 추정

**핵심**:
- 정밀행렬 Ω = Σ^{-1}. Ω_ij ≠ 0 ↔ i 와 j 가 다른 모든 변수 통제 후에도 연관 (partial-corr).
- L1 penalty: `min_Ω -log det(Ω) + tr(SΩ) + λ ‖Ω‖_1` → 희소 Ω (entry-wise sparsity).
- λ 선택: EBIC (Extended BIC) 또는 cross-validation.

**우리 시스템 wire** (이미 구현):
- `core/structure/conditional_correlation.RegimeGlasso.fit(X, regime_ids)` — nonparanormal 전처리 → EBIC glasso → EB shrinkage.
- `corr_prior` 인자 = identity 아닌 행렬일 때 force-include 후보 (이론 강한 ≤4 엣지).
- `effective_precision(models, belief)` — belief 가중 regime-mix Σ_eff (1회 역행렬).

**coin 적용** (direction.md D4 hybrid):
- 신규 인스턴스 `core/coin_track/internal_corr.py` (제안 위치): `RegimeGlasso(X=[MVRV, FGI, funding, OI, dominance, RSI, SMA_dev, SOPR, fwd_ret], regime_ids=vol⊗macro, corr_prior=offline_partialcorr_table, npn=True)`.
- offline 표 = R3 합의 5 partial-corr edge (warm-start prior, shrinkage target).
- **stability gate** (claude r3 추가): per-regime effective N threshold + bootstrap edge stability — 못 넘으면 admit X.

### §2.3 Granger causality / CCF (cross-correlation function)

**Granger causality 정의**:
```
H0: Y_{t+k} ⊥ X_t | (Y_{t-1}, Y_{t-2}, ..., Y_{t-p}, X_{t-1}, ..., X_{t-p})
거부 시: X 가 Y 를 (k+p) 시점 Granger-cause 한다고 표현
```
- VAR(p) 모델에서 X 계수 joint 0 가설 F-test.
- **필요조건일 뿐** (sufficient X). 잠재 공통 인자 존재 시 false positive.

**CCF (cross-correlation function)**:
```
CCF(k) = corr(X_t, Y_{t+k})  for k ∈ {-K, ..., 0, ..., K}
CCF(k) 가 k>0 에서 강 → X 가 Y 선행 (lead)
CCF(k) 가 k<0 에서 강 → Y 가 X 선행 (lag, 역인과 정황)
```

**stablecoin lead-lag 검증** (direction.md H3 핵심):
- 변수: X = stablecoin_net_creation (Δsupply growth z-score), Y = BTC fwd_ret.
- ADF stationarity 선행 — growth 변환 (level 비정상). 양방향 Granger.
- 양의 lag (k=7,14,30d) 에서 CCF(k) 유의 + 음의 lag 에서 무의 → dry powder 가설 지지.
- 음의 lag 에서 강 (Y 선행 X) → 역인과 (가격 → 발행 demand) 정황 → 신호 비활성.

**의사 코드**:
```python
from statsmodels.tsa.stattools import adfuller, grangercausalitytests, ccf
# ADF
p_adf = adfuller(stablecoin_growth)[1]
assert p_adf < 0.05, "non-stationary, transform 재검토"
# 양방향 Granger
g_xy = grangercausalitytests(np.c_[btc_ret, stablecoin_growth], maxlag=7)
g_yx = grangercausalitytests(np.c_[stablecoin_growth, btc_ret], maxlag=7)
# CCF lead-lag
ccf_vals = ccf(btc_ret, stablecoin_growth, adjusted=True)[:30]
```

### §2.4 nonparanormal (Liu, Lafferty, Wasserman 2009) — Gaussian copula 전처리

**문제**: 우리 변수 중 다수가 비-Gaussian:
- funding rate: spike fat-tail.
- FGI: bounded [0, 100].
- returns: fat-tail.

**해결**: nonparanormal = 각 변수를 marginal 순위 → CDF 변환 → Gaussian 분포로 정규화. partial-corr 는 monotonic transform invariant → glasso 적용 가능.

**우리 시스템**: `RegimeGlasso(npn=True)` 옵션 — 이미 지원.

### §2.5 Block bootstrap (BB) — 시계열 의존성 보존 CI

**문제**: i.i.d. bootstrap 은 시계열 autocorrelation 깨뜨림 → CI 과소평가.

**Block bootstrap**:
- 길이 L blocks 로 시계열 split → resampling.
- L = O(n^{1/3}) 표준 (Hall 1985).
- 우리 MVRV cycle 같은 long-memory 변수: L 충분히 길게 (~30-90 day).

**우리 가설 적용** (검정력 한계 명시):
- halving N=4 effective N → bootstrap 가능하지만 사실상 4 block resample.
- MVRV extreme event (top/bottom) N=3~4쌍 → bootstrap CI 매우 넓음 (claude r1 예상 "0 포함 CI 디폴트").

---

## §3. 2-3 우선 실측 항목 (main 추가 조건 반영)

direction.md §5 미해결 의문 8건 중 **main 이 우선 지정** 2건:

### ★우선 1 — prior 채널 차등 숫자 backtest (의문 #1)

**검증 목적**: micro 0.6 / on-chain 0.4 / macro 0.3 / halving 0.1 ladder 가 OOS edge 안정성과 일치하는가?

**방법**:
- 각 채널 대표 가설 1개 선정 (H2 funding / H1 MVRV / 가설 없음(macro 직접)→stablecoin H3 / H5 halving).
- 같은 rolling window (3년) 로 standalone Rank-IC + e-CUSUM 시계열 산출.
- IC volatility (Std), max drawdown, breakdown frequency 계산.
- prior 0.6 대응 funding 의 metric vs prior 0.1 대응 halving 의 metric 의 *비율* 이 6배 차이 나는가 확인.

**기각 조건**: micro 와 halving 의 OOS metric 비율이 2배 미만 → channel ladder over-spread (재캘리브 필요).

### ★우선 2 — internal glasso effective-N gate 영구폐쇄 위험 (의문 #4)

**검증 목적**: funding-limited (2020-09~, ~5년) + 일봉 autocorr 로 per-regime effective N 이 stability gate 를 *상시* 못 넘는지.

**방법**:
- per-regime (FGI 5단계 × vol regime 3단계 = 15 regime) 의 complete-case window 길이 측정.
- autocorrelation-adjusted effective sample size N_eff 산출 (Newey-West 표준).
- N_eff threshold 후보 (예: 50, 100, 200) 별 admit 빈도 시뮬레이션.

**기각 조건**: N_eff threshold 200 에서 admit 빈도 < 10% → gate 영구폐쇄 위험 = high → hybrid 의 internal glasso 부분 보류 (offline 박제만으로 fallback).

---

## §4. 2-3 진입 준비 — 우리 시스템 구체 코드 경로

> 검증 단계에서 즉시 실행할 분석 .py 의 진입점.

| 가설 | 분석 코드 (Bash python 직접 실행) | 입력 데이터 |
|------|----------------------------------|-------------|
| H1 MVRV mean-revert | `core/data/instrument_source.run_mvrv_closed_loop` (이미 존재) + 실 PIT 데이터로 fixture 대체 | CoinMetrics CapMVRVCur PIT + BTC price |
| H2 funding cascade | 신규 `scripts/validate_funding_cascade.py` (event study, 95th percentile 진입 후 24/72h OI·가격 변화) | Binance funding history + OI history (무료 public) |
| H3 stablecoin lead-lag | 신규 `scripts/validate_stablecoin_lead_lag.py` (ADF + 양방향 Granger + CCF) | DefiLlama daily total + BTC fwd_ret |
| H4 ETF flow probation | 신규 `scripts/validate_etf_flow.py` (post-2024 rolling Rank-IC + e-CUSUM) | Farside daily net flow + BTC fwd_ret |
| H5 halving regime | 신규 `scripts/validate_halving_phases.py` (phase 별 H1 IC 안정성 간접 검증) | halving schedule (deterministic) + 위 H1 결과 |
| H6 macro_abstain | 신규 `scripts/validate_macro_abstain.py` (H29 차단 시점 + 7~14d 가격 outcome) | coin_track_macro 의 macro_abstain emit log + price |
| ★우선 1 prior backtest | 신규 `scripts/validate_prior_ladder.py` | 채널별 대표 가설 IC 시계열 |
| ★우선 2 effective N gate | 신규 `scripts/validate_eff_n_gate.py` | regime split + autocorr-adjusted N_eff |

partial-corr 검증 (offline 표):
- `scripts/validate_partial_corr_table.py` — `RegimeGlasso` 직접 fit + 5 edge (MVRV⊥fwd_ret|FGI, dominance⊥alt_excess|... 등) partial corr 값 + bootstrap CI 산출.

---

## §5. 학습 마무리 자기 평가

**잘 정리된 부분**:
- (1) 5채널 핵심 문헌 11개 학술 압축 (자문 raw 의 인용을 *원리·가정·한계* 형식으로 재정리).
- (2) 거시 transmission 관계도 (M2 ↔ 미·일 국채 ↔ 환율 → coin) — STUDY-KIT §2 거시 깊이 기준 충족.
- (3) 5 도구 (confseq / glasso / Granger·CCF / nonparanormal / block bootstrap) 우리 시스템 wire 포함 정리.
- (4) main 추가 조건 2건 (§5 의문 #1·#4) 2-3 우선 검증 항목으로 명시.

**솔직한 약점**:
- (a) 원전 PDF/논문 본문 직접 접근 불가 (WebFetch 차단). 자문 raw (gemini/claude r1-r3) + 학술 표준 정의 압축. 일부 미세 수치 (Liu&Tsyvinski 2021 회귀 R² 등) 는 abstract 수준.
- (b) 거시 transmission 관계도는 본인 학술 지식 기반 — Howell Capital Wars 의 GL 지수 수식까지는 미접근.
- (c) 도구 학습은 우리 시스템 이미 구현된 부분 (confseq/glasso) 중심. 외부 라이브러리 (statsmodels Granger 등) 는 일반 사용법 — 우리 시스템과 동조 wire 는 2-3 진입 후 결정.

**다음 단계 (2-3) 예고**:
- 위 §4 진입점 표대로 분석 .py 직접 실행 → numeric 산출 → `raw/validation-{지표}.md` 누적.
- prior 채널 ladder + effective-N gate 두 우선 항목 먼저 실측 → 결과에 따라 D1 prior 값 또는 D4 hybrid 의 internal glasso 부분 조정.
- 검증 결과 + 본 theory-notes 종합 → study_session.yaml 7 블록 (lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan).
