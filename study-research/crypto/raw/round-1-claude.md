# Round 1 — claude-web (claude.ai basic)

as_of: 2026-05-30
model: Opus 4.8 High
response_len: 10523

---

먼저 솔직한 총평 하나. 이 작업의 가장 큰 제약은 **"가장 풍부한 신호일수록 독립 관측치가 가장 적다"**는 점이다. MVRV 사이클은 14년 데이터라도 독립 cycle top/bottom은 한 손에 꼽고, halving은 N=4로 사실상 검정 불가다. 반대로 funding/OI는 관측치는 많지만 메커니즘이 공개·crowded돼 edge가 얇다. 그래서 prior_strength를 의도적으로 낮게 박고, 대부분의 on-chain 지표를 factor가 아니라 regime oscillator로 취급하는 게 정직한 설계다. 아래 ③에서 이 입장을 수치로 반영했다.

① 이론 수집 방향

채널별 핵심 자료. 괄호는 그 자료가 설명하는 driver.

(i) 펀더멘털 없는 자산의 realized-value cycle indicator

Coin Metrics — "Introducing Realized Capitalization" (Carter & Le Calvez, 2018) + State of the Network 시리즈 → realized cap = on-chain 평균 취득원가(cost basis), MVRV = 시총/realized = 집계 미실현손익 → 평균회귀 cycle 진동자. 이게 너희 MVRV PIT의 정의 근거다.
Glassnode Academy (SOPR / NUPL / MVRV-Z) → SOPR = 실현 차익실현 압력, NUPL = 미실현손익 regime 밴드. 유료 게이트 뒤 자료지만 정의·band 해석은 학습 가치 있음.
PlanB "Modeling Bitcoin's Value with Scarcity" (2019, Stock-to-Flow) → 희소성=가격 모델. 반례로 읽어라. 2021 이후 out-of-sample 붕괴, N=4 cointegration이 spurious였던 전형적 케이스. 너희 halving 가설의 prior_strength를 왜 낮춰야 하는지 보여주는 교보재.

→ 처리 방침: MVRV/NUPL/SOPR는 선형 factor가 아니라 regime 분류용 conditioning 변수로만. point price 예측이 아니라 extreme band(top/bottom) tail 신호로. realized cap의 정의 drift(소실 코인, 거래소 클러스터링, ETF 커스터디 이동)를 항상 의심.

(ii) 공급 schedule

Pagnotta & Buraschi "An Equilibrium Valuation of Bitcoin and Decentralized Network Assets" (2018) → 네트워크 효과(Metcalfe)×채굴 보안 균형으로 내생 가격, 공급 schedule은 한 입력일 뿐.
솔직히 할빙에 대한 신뢰할 만한 계량 논문은 없다. N=4 + cycle 간 비독립성 때문에 식별 불가. 최선의 자료는 deterministic schedule 그 자체 + 너희 자체 regime 분석. 할빙 alpha를 주장하는 논문/리포트는 전부 overfitting 의심하고 거른다.

→ 처리 방침: 할빙은 factor 아니고 regime label. across-phase 비교 금지(관측 4개), within-phase 조건부 행동의 interaction term으로만.

(iii) 거시 유동성 transmission

Liu & Tsyvinski "Risks and Returns of Cryptocurrency" (Review of Financial Studies, 2021) → 중요한 null 결과: (pre-2020) crypto 수익은 전통 macro/주식 factor로 설명 안 되고, 자체 momentum + investor attention이 지배. macro driver에 과한 prior 두지 말라는 경고.
Michael Howell "Capital Wars: The Rise of Global Liquidity" (2020) + CrossBorder Capital → global liquidity(중앙은행+민간)가 risk asset/BTC 사이클의 선행 driver. real rate·DXY·M2의 transmission 프레임.

→ 처리 방침: macro는 regime-conditional driver. pre-2020 약함 → post-2020/2021 주식 상관 상승. 너희가 가진 가장 깨끗한 crypto-native 유동성 게이지는 **stablecoin supply(DefiLlama)**다. 이걸 macro real_rate와 분리 검증.

(iv) 시장 미시구조

Makarov & Schoar "Trading and Arbitrage in Cryptocurrency Markets" (Journal of Financial Economics, 2020) → 시장 분절, arbitrage spread, order flow, venue 간 price discovery.
Liu, Tsyvinski & Wu "Common Risk Factors in Cryptocurrency" (Journal of Finance, 2022) → 3-factor(시장 CMKT, 규모 CSIZE, 모멘텀 CMOM). dominance rotation / alt-season의 cross-section 근거.
BitMEX Research + perpetual swap 가격결정 문헌(Alexander 등) → funding rate = 레버리지·포지셔닝 압력 → liquidation cascade 메커니즘.

→ 처리 방침: funding = 포지셔닝 평균회귀 + cascade tail 게이지. dominance = rotation 게이지(상승=alt 상대 약세). Binance public funding/OI 시계열로 고빈도 검증.

(v) digital gold vs risk asset 디커플

Baur, Hong & Lee "Bitcoin: Medium of Exchange or Speculative Asset?" (2018) → BTC는 주로 투기자산, hedge/safe-haven 속성 약함.
Biais, Bisière, Bouvard, Casamatta & Menkveld "Equilibrium Bitcoin Pricing" (Journal of Finance, 2023) → 거래 편익+투기 균형, bubble 동반.
post-2024 ETF 실증 → spot ETF 승인(2024.1)으로 marginal buyer 구조 변화. BTC-Nasdaq 상관은 regime-의존. on-chain reserve 지표의 의미가 구조적으로 약해졌을 가능성(코인이 ETF 커스터디/콜드로 이동) — 역사적 on-chain IC를 down-weight할 진짜 이유.

→ 처리 방침: 고정 regime 가정 금지. BTC-주식/BTC-금 rolling 상관을 macro regime 조건부로 추정. ETF break date는 알려져 있으니 knowable_from으로 누수 차단하며 structural break 검정.

OSS / 도구

coinmetrics-api-client (PIT community data), Glassnode API(유료 게이트).
alphalens-reloaded(유지보수 fork — 원본 deprecated) → factor IC/quantile.
vectorbt 또는 bt → walk-forward 백테스트.
confseq(Howard & Ramdas) → anytime-valid CI/e-process. 개념 근거 Ramdas, Grünwald, Vovk & Wang "Game-theoretic statistics and safe anytime-valid inference" (Statistical Science, 2023) — 너희 e-CUSUM의 이론 토대.
sklearn.covariance.GraphicalLassoCV — partial-corr. 근거 Friedman, Hastie & Tibshirani "Sparse inverse covariance estimation with the graphical lasso" (Biostatistics, 2008).
② 이론 검증 방향

데이터 시계열을 두 개로 쪼개라 (가장 중요).

장기 트랙 (cycle/macro): CoinMetrics PIT 일별 BTC realized/MVRV (~2011+, daily). MVRV·NUPL·halving·macro 가설은 전부 여기서. Upbit 30일 4h봉으로 MVRV 사이클 검증하는 건 무의미하다 — 사이클이 다년 스케일인데 표본이 30일이면 0개 사이클이다.
단기 트랙 (microstructure): Upbit 4h봉 42개 + 오더북/체결 + Binance funding/OI. funding·RSI·OI·FGI 단기 swing만 여기서.

적용 가능 partial-corr edge (glasso/pairwise, 전부 장기 트랙에서 일별):

edge	conditioning_set	검증 의도	내 사전 예상
MVRV ⊥ fwd_ret | FGI	{FGI}	MVRV가 sentiment와 별개 신호인가	partial이 0 쪽으로 크게 수축 (공통원인 강함)
dominance ⊥ alt_excess | BTC_ret, real_rate	{BTC_ret, macro real_rate}	rotation이 BTC-beta/macro와 독립인가	약하게 독립 잔존
funding ⊥ fwd_ret | RSI, OI	{RSI(14), OI_change}	funding이 momentum/포지션과 별개인가	단기 cascade 채널 일부 잔존
stablecoin_supply ⊥ fwd_ret | real_rate, DXY	{real_rate, DXY}	crypto-native vs macro 유동성	crypto-native 일부 잔존, 단 역인과 위험
MVRV ⊥ fwd_ret | halving_phase	{halving_phase}	cycle 지표가 halving 시계만 추종하는가	상당 부분 흡수

regime 분해 단위 — 조합 belief의 차원의 저주를 명시적으로 끊어라.

FGI 5밴드: Extreme Fear 0–24 / Fear 25–44 / Neutral 45–55 / Greed 56–75 / Extreme Greed 76–100.
halving 4-phase: post-halving 0–6mo(accumulation) / 6–18mo(markup) / 12–24mo(distribution) / 24–36mo(bear). 경계는 너희 schedule로 deterministic 라벨링.
macro: real_rate 추세 + DXY + 주식 vol로 risk-on / neutral / risk-off 3-state.
금지: 5×4×3=60셀 full cross-product를 IC 추정 단위로 쓰는 것. 대부분 셀이 비어 추정 불가다. 규칙: FGI·macro는 단기 신호의 conditioning으로, halving은 별도 coarse interaction으로만. FGI×halving 교차로 IC 산출 금지.

Rank-IC 산출 단위 — 너희 "sleeve granularity only" 제약을 그대로 반영:

wiring용: BTC 단일 time-series IC (MVRV/NUPL/SOPR — BTC 체인 지표) + sleeve aggregate composite(cap-weighted basket) time-series IC (funding/dominance/FGI).
검증용(미배선): top 20–50 mcap universe cross-sectional Rank-IC — momentum/size factor의 존재 자체를 offline 확인만. 트레이딩에 ticker-level로 안 들어감.
한 줄 매핑: MVRV·NUPL·SOPR → BTC time-series IC. funding·dominance·FGI·stablecoin → sleeve aggregate time-series IC.

검정력 한계 — 수치로 박아라:

halving N=4 → across-phase 어떤 검정도 power 0. 게다가 cycle 간 비독립(regime 자기상관). 결론: standalone IC 가설 금지, 라벨/interaction만.
MVRV: ~14년 daily ≈ 5000+ obs지만 독립 cycle 극단(top/bottom)은 3~4쌍. extreme 신호 effective N 미미 → CI 매우 넓음, prior_strength 낮게, "0 포함 CI"를 디폴트로 예상.
FGI: 2018.2~ daily ≈ 2900 obs. 일별 신호, extreme 이벤트 study 가능.
funding/OI: 고빈도 다관측 → 단기 horizon power 양호. 여기가 통계적으로 가장 견고.

forward return horizon 매핑:

7d: funding extreme, RSI, OI, FGI 단기 swing → 평균회귀 가설.
30d: dominance rotation, stablecoin supply 변화, sentiment regime, macro 상관.
90d: MVRV/NUPL regime, macro 유동성, halving phase 맥락.
mismatch(예: MVRV를 7d로 검증)는 신호를 죽인다. horizon은 가설 고유 속성으로 박는다.

무lookahead 검증 (knowable_from):

CoinMetrics PIT: 결정시점 t에서 knowable_from(value) ≤ t 인 MVRV vintage만. realized cap은 reorg/방법론 vintage로 사후 revised됨.
FGI: 발행 timestamp(UTC EOD)에 정렬, 당일 close로 당일 예측 금지.
funding: Binance 8h settle 기준, 결정시점 known 값만.
ETF break: break date는 알지만 post-break 파라미터를 pre-break 백테스트에 누수 금지 → expanding-window walk-forward. e-process는 본질적으로 anytime-valid라 이 누수를 구조적으로 막아준다.
run_mvrv_closed_loop가 PIT을 강제하고, score_ic_breakdown_eprocess는 knowable_from 필터링 시계열만 consume.
③ 핵심 가설 초안 (반증조건 포함)
#	가설	반증조건	edge 분류 + conditioning_set	prior_sign	prior_strength	horizon	코드 경로
H1	MVRV-Z top extreme(≈>7) → BTC 음(-) 수익 / bottom(≈<0.5) → 양(+). 임계는 너희 시계열로 재교정	extreme decile fwd hit rate < 0.55 & binomial p>0.05; OR sign-flipped Rank-IC 95% CI가 0 포함; OR e-CUSUM 단측 wealth가 walk-forward에서 1/α 미돌파	undetermined → 사실상 FGI/cycle와 common_cause 의심. {FGI, halving_phase}	top:neg / bottom:pos	0.45	90d	run_mvrv_closed_loop → score_ic_breakdown_eprocess (BTC TS-IC)
H2	FGI 조건부로도 MVRV가 BTC 90d에 독립 예측력 보유	partial Rank-IC(MVRV,fwd|FGI) 95% CI 0 포함; OR |partial| < 0.5×|marginal| (50%+ 흡수)	conditioning test 자체. {FGI}	unsigned	0.30	90d	glasso partial-corr layer → belief; score_ic_breakdown_eprocess partial 트랙
H3	perp funding top pct(>95th, 과열 long) → sleeve 음(-) 7d (long squeeze)	short-leg hit rate < 0.52 & binomial p>0.05; OR Rank-IC(−funding,7d) CI 0 포함; OR e-process collapse	direct (포지션→청산), 단 RSI/OI와 일부 common. {RSI(14), OI_change}	neg	0.60	7d	consensus lens funding → Orchestrator sizing modulator; sleeve TS-IC
H4	crypto risk-off 중 BTC dominance 상승 → alt sleeve가 BTC 대비 30d 열위	partial Rank-IC(dom_chg, alt_excess_30d|BTC_ret) CI 0 포함; OR 부호가 4 phase 중 ≥2에서 뒤집히고 hit rate<0.5	undetermined → BTC-beta/macro와 분리 검증. {BTC_fwd_ret, macro real_rate}	neg(alts)	0.40	30d	consensus lens dominance prefix; BTC vs alt sleeve
H5	stablecoin supply 순확장 → crypto sleeve 양(+) 30d, real_rate와 독립	partial Rank-IC(stbl_growth,30d|real_rate,DXY) CI 0 포함; OR partial<0.4×marginal (macro 흡수)	undetermined, 역인과(가격→발행) 위험 명시. {real_rate, DXY}	pos	0.50	30d	신규 crypto-native 유동성 feature → belief modulator
H6	BTC-Nasdaq 30d rolling 상관은 regime-의존: risk-off에서 상관 상승(=hedge 아님, risk asset 유지)	risk-off 상관이 risk-on 상관보다 유의하게 크지 않음(two-sample); OR safe-haven 성립(stress 상관≤0 & CI가 양 배제)이면 "risk asset" prior 거부. post-ETF sup-Wald break 검정 walk-forward	undetermined, macro regime 조건부. {real_rate_regime, equity_vol}	pos(stress 상관)	0.55	30d	macro regime classifier → belief → crisis BTC cap (Kelly+HRP) 변조
H7	halving phase는 다른 신호의 부호/강도를 변조할 뿐, standalone IC 없음	standalone 검정 불가(N=4). interaction으로만: MVRV의 within-phase 조건부 IC가 phase 간 차이 없음(interaction CI 전쌍 0 포함)이면 interaction drop, 라벨만 유지	undetermined, standalone {} / interaction {MVRV}	unsigned	0.20	90d 신호와 interact	regime label만 belief mix 주입, score_ic_breakdown_eprocess에 standalone factor로 불가
H8 (유료 게이트)	SOPR가 1 하회 후 상향 돌파 → distribution phase에서 차익실현 재개로 BTC 7–30d 음(-) drift	hit rate<0.52 & p>0.05; Glassnode SOPR 미확보 시 미발화	direct-ish, {MVRV regime}	맥락의존(distribution:neg)	0.35	7–30d	조건부 run_sopr_* (paid gate)

우선순위에 대한 내 솔직한 의견 (다른 모델과 갈릴 수 있음):

H2가 사실 가장 결정적인 검증이다. MVRV와 FGI는 같은 reflexive cycle/sentiment의 두 측정치라 공통원인이 강할 것. H2에서 partial이 0으로 수축하면 H1의 MVRV는 독립 alpha가 아니라 sentiment proxy로 재분류하고 prior를 더 깎아야 한다. 둘 다 belief에 풀 가중으로 넣으면 double-counting이다.
funding(H3)이 통계적으로 가장 견고하지만 가장 crowded다. 디렉셔널 alpha보다 cascade tail 사이징(crisis BTC cap, HRP tail)에 쓰는 게 정직하다.
halving(H7)에 real prior 주지 마라. N=4 + 비독립 = 반증 불가 = 과학적 가설 아님. 라벨로만. S2F의 사후붕괴가 그 증거다.
post-ETF 구조변화로 exchange reserve / on-chain reserve 지표의 역사적 IC를 적극 down-weight하라. 코인이 ETF 커스터디로 이동하며 reserve 신호의 의미가 바뀌었을 가능성이 높다 — break 이전 IC를 그대로 신뢰하면 안 된다.

임계값 주의: 위 MVRV-Z 7 / 0.5, funding 95th 같은 숫자는 일반 관행값이다. 너희 자체 시계열로 재교정해서 박아라 — 외부 band를 그대로 쓰면 그 자체가 미묘한 lookahead다.

세 섹션 중 어디를 코드 레벨로 더 파고들까? H2의 partial-corr 추정을 score_ic_breakdown_eprocess에 어떻게 두 트랙(marginal vs partial)으로 wire하는지, 아니면 H6의 structural-break를 walk-forward e-process로 누수 없이 짜는 구체 구현을 잡아줄 수 있다.