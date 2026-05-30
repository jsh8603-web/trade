# Round 1 — gemini-web (Gemini Pro)

as_of: 2026-05-30
model: GeminiPro
response_len: 4668

---

[핵심 요약]

Crypto 자산군의 특수성(DCF 부재, 4시간 단위의 짧은 Half-life, 별도 렌즈 및 사이징 적용)을 고려할 때, 본 과제의 핵심은 '가짜 상관관계(Spurious Correlation)의 제거'와 '투자 시계(Horizon)별 Driver의 분리'입니다.

거시 유동성(Macro)과 온체인 가치(MVRV) 지표는 30∼90일 시계의 사이징 조절자(Sizing Modulator)로, 파생상품 미시구조(Funding rate)와 심리(FGI)는 4시간$\sim 7$일 시계의 Consensus Lens 정성 Prefix로 분리하여 검증해야 합니다. 아래에 이론적 근거, 검증 방법론(2가지 대안 포함), 그리고 시스템에 즉시 편입 가능한 5가지 핵심 가설을 제시합니다.

① 이론 수집방향 (Crypto Pricing Drivers)

펀더멘털이 부재한 자산의 특성상, 네트워크 효용, 시장 미시구조, 거시 유동성에 관한 계량적/경험적 연구 문헌을 우선 참조해야 합니다.

분류	참고 문헌 / 소스 (출처)	설명하는 핵심 Driver (1줄 요약)
(i) Valuation	CoinMetrics State of the Network (Carter & Baur, 2018)	MVRV는 실현가치(Realized Cap) 대비 시장가치로, 맹목적 투기 프리미엄의 Mean-reversion을 측정.
(i) Valuation	Glassnode Insights: SOPR & NUPL Frameworks	온체인 UTXO의 수익/손실 실현 비율(SOPR)을 통한 단기/장기 보유자의 항복(Capitulation) 임계점 정의.
(ii) Supply	Bitcoin's Halving and the Efficient Market Hypothesis (Academic Papers, NBER/SSRN)	공급 반감기가 가격에 선반영되는지(EMH), 혹은 유동성 경색 이후에 후행 반응하는지 통계적 검정.
(iii) Macro	Cryptocurrencies and Macroeconomic Shocks (BIS Working Paper No. 1066)	실질 금리(Real Rate)와 달러 인덱스(DXY)가 암호화폐 리스크 프리미엄에 미치는 탄력성 및 Transmission 구조.
(iv) Micro	Price Discovery in High Resolution (Alexander & Heck, 2020)	무기한 선물(Perpetual) 시장의 Funding Rate 및 OI 변화가 현물 시장의 가격 발견(Price Discovery)을 주도하는 메커니즘.
(v) Decoupling	Grayscale & Bitwise Research: Post-ETF Market Structure (2024)	현물 ETF 승인 이후 전통 금융권 기관 자금(Inflow) 채택으로 인한 '위험 자산(Risk-on)'과 '디지털 금(Safe-haven)' 간의 Regime Shift 시점.
② 이론 검증방향 (시계열 검증 방법론)

보유한 데이터를 활용한 검증은 N=4 (Halving)와 같은 통계적 한계를 회피하고, 체계적인 Partial-corr 추정을 통해 인과성을 발라내는 데 집중해야 합니다. 검증 설계에 대해 다음 2가지 대안을 제시합니다.

대안 비교 (검증 아키텍처)
구분	대안 A: Time-Series Aggregate (기본/안정적)	대안 B: Cross-Asset Rank-IC (도전적/예산 중)
특징	BTC 단일 자산 및 Sleeve 전체의 시계열 IC 분석	주식/매크로 자산과의 Cross-section Rank-IC 결합
장점	시스템 내 Orchestrator의 Crisis BTC Cap 모듈과 직접 호환.	Macro Risk-on/off 국면에서 자산군 간 상대 우위 평가 가능.
단점	멀티코인(Alt-season) 효과 측정 불가.	Crypto Sleeve Granularity 원칙과 일부 충돌 가능성.
구체적 검증 방법론 (대안 A 기준)

Partial-corr Edge 적용 가이드:

MVRV ⊥ Price | FGI: MVRV의 예측력이 단순한 시장 광기(FGI)에 의한 것인지 통제.

Stablecoin Supply ⊥ Price | Macro Real Rate: 암호화폐 내부 유동성이 거시 금리의 후행 지표에 불과한지 검증.

Regime 분해 단위:

데이터 희소성(Sparsity)을 막기 위해 핵심 차원 축소: Halving Phase (2단계: Pre/Post) × Macro (2단계: Risk-on/off) × Market Flow (2단계: Funding 양/음). 총 8개 국면(Regime)으로 압축하여 검증.

Rank-IC 산출 단위:

시스템 제약(Ticker 세분화 X)에 따라, BTC 단일 시계열 Information Coefficient (Time-Series IC)로 평가.

검정력 한계 극복:

N=4인 반감기 효과는 단순 회귀가 아닌, 블록 보상 감소가 온체인 채굴자 매도 압력(Miners' Net Position Change)으로 이어지는 '과정(Mechanism)' 자체를 검증.

짧은 시계열(FGI 등)은 Block-bootstrap 기법을 사용하여 CI(신뢰구간)를 보수적으로 산출.

Forward Return Horizon 매핑:

7d: FGI 극단값, Funding Rate Cascade, RSI/MACD.

30d: BTC Dominance 교차, MVRV 초기 과열.

90d: Macro 실질금리 변화, Stablecoin M2 확장.

무Lookahead 검증 (PIT):

knowable_from 타임스탬프를 절대적 기준으로 삼아, API 수신 지연(ex: FGI의 익일 업데이트)을 반영한 엄격한 OOS(Out-of-Sample) 백테스팅 수행.

③ 핵심 가설 초안 (반증조건 및 시스템 경로)

검증 대상인 5가지 핵심 가설입니다.

가설 1: 온체인 고평가 붕괴 (Valuation)

가설 텍스트: "MVRV >3.0 → 하방 압력(Negative Price Impact) in 거시 Risk-off 국면"

반증조건: 30d Forward Return에 대한 Time-Series IC의 e-CUSUM 통계량이 하방 단측 붕괴 임계점 돌파 시 기각.

Partial-corr Edge: Direct

Prior Sign / Strength: Neg / 0.8

Horizon: 30d

코드 경로: orchestrator.sizing_modulator.apply_mvrv_tail_penalty

가설 2: 파생상품 레버리지 청산 (Microstructure)

가설 텍스트: "Perpetual Funding Rate >95th percentile & RSI(14) 하락 다이버전스 → 급격한 하방 변동성(Cascade) in 모든 국면"

반증조건: hit rate <0.5 (Binomial p>0.05) 또는 Partial-corr 추정치 95% CI에 0 포함 시 기각.

Partial-corr Edge: Direct | conditioning_set: [Price Momentum]

Prior Sign / Strength: Neg / 0.9

Horizon: 7d

코드 경로: consensus_lens.derivatives_prefix_evaluator.compute_cascade_risk

가설 3: 안전자산 디커플링 (Decoupling)

가설 텍스트: "BTC Spot ETF Inflow 연속 5일 증가 → 상방 압력(Positive Price Impact) in 거시 Risk-off 국면 (Digital Gold 특성 발현)"

반증조건: ETF 승인(2024.01) 이후 구간에서 Partial-corr(ETF Inflow, Price) | SPX Returns 추정치가 양(+)이 아닐 경우 기각.

Partial-corr Edge: Common_cause (Macro 유동성) 통제 후 Direct

Prior Sign / Strength: Pos / 0.6

Horizon: 30d

코드 경로: weight_panel.crypto_exception.eval_digital_gold_regime

가설 4: 유동성 전이 (Macro)

가설 텍스트: "Stablecoin Total Supply 증가 → 상방 압력 in Halving Post-phase"

반증조건: 90d Forward Return 대상 OOS R
2
<0 발생 시 기각.

Partial-corr Edge: Direct | conditioning_set: [Macro M2, DXY]

Prior Sign / Strength: Pos / 0.7

Horizon: 90d

코드 경로: orchestrator.sizing_modulator.baseline_kelly_expansion

가설 5: 극단적 공포 매수 (Sentiment)

가설 텍스트: "FGI <15 (Extreme Fear) → 단기 상방 압력(Mean Reversion) in 장기 SMA(200) 상회 국면"

반증조건: Event-study 기반 7d 누적 초과수익률(CAR)의 t-test 결과가 유의수준 $5%$에서 기각 실패 시.

Partial-corr Edge: Undetermined (노이즈 강함)

Prior Sign / Strength: Pos / 0.5

Horizon: 7d

코드 경로: consensus_lens.fgi_qualitative_prefix.generate_buy_wall_signal