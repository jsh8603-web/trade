---
tags: [handoff, inv, p2, test2a, signal-alpha, study, self-contained]
date: 2026-06-02
session: btn-Inv
purpose: P2 Test2a 진단 완결 + 신호 재설계 스터디 자문 수렴 핸드오프. 다음=trend-gate 검증
entry: 이 파일 1독 → progress-test-readiness.md §P2 → .p2-signal-alpha.py
---

# 핸드오프 — P2 Test2a 진단 완결 + 스터디 자문 수렴 (자기완결)

> **push 금지**. Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`. risk_gate 상수 무수정(env만).

## 0. 한 줄 현황
P2 Test2a(결정론 수익률 진단) **완결** — 손실 원인 2축 분리: ①코드(`MAX_WEIGHT_SINGLE=10%`가 단일자산 NAV 압살) ②방법론(코어 지표 매수점수가 BTC 단기 forward와 **음의 rank-IC −0.10**=역방향). 신호 재설계 스터디 자문 2모델 수렴(B=trend-gate). 다음 = **trend-gate 검증**(자문→채택 verification).

## 1. P2 진단 결과 (실측)
### 코드축 — `MAX_WEIGHT_SINGLE=0.10` (risk_gate.py:47)
- 강세장 시뮬: 시장 +44% → ON(use_risk_pipeline=True) +3.75% / 시장 +34% → +2.88%. 매수 반복해도 10% 천장서 누적 안 됨(58회 REJECT).
- gross clip(`target_vol=0.15`)은 **무죄**: median 0.56, lo(0.10) 붙음 0%, MDD −46%→−7.6% 완화(유익).
- 진범 = `risk_gate.py:316` max_weight 단일 축소(REDUCED→adjusted). **단 scale-invariant 지표엔 무관**(NAV 절대수익만 압살).
- 판정: 코드 결함 아니라 **컨텍스트 미스매치**(멀티에셋 분산용 10%를 단일자산 백테스트에 적용). 상수 무수정, 백테스트만 env `RISK_MAX_WEIGHT_SINGLE=0.95` 오버라이드(라이브 무손상).

### 방법론축 — 코어 지표 매수점수 역방향 (★진짜 숙제)
- `.p2-signal-alpha.py`: 진짜 coin 에이전트 3종(Conservative/Moderate/Aggressive) `calculate_buy_score`(SACRED, 호출만)를 BTC 일봉 ~800일에 적용 → forward-return rank-IC(forecasting-object, 사이징/cap 무관).
- **결과**: 전 에이전트·전 horizon rank-IC 음. Moderate fwd10d −0.108(p=0.003, Bonferroni α/9=0.0056 통과 유의), Aggressive fwd10d −0.101(p=0.005 유의). hit<base, expectancy≈0/음. **fwd20d는 역IC 약화**(−0.03 비유의, hit 0.545>base 0.530).
- 메커니즘: 코어점수=공포+RSI과매도+SMA하향이탈=mean-reversion("쌀때사기")인데 BTC 단기는 momentum 우세→"떨어지는 칼날 잡기"=역효과.
- ★한계(over-claim 차단): (1) overlapping forward 자기상관 미보정(fwd10d 유효 n~77, Newey-West/block 필요) (2) **external_bonus(뉴스·소셜·온체인) 제외** 순수 지표 코어만(외부 레이어가 알파 원천일 수 있음) (3) 단일자산·단일국면(2024-2026).

## 2. 스터디 자문 수렴 (gemini-web + claude-web, 1R 만장일치)
브리핑=`.consult-study-meanrev-briefing.md`. raw=`~/.claude/.gemini-web-last.md`/`.claude-web-basic-last.md`.

- **채택 B = trend filter gates reversal**: 장기 추세(50/200일 MA, 8~12주 trailing return 부호)가 방향 허가 → 그 안에서만 oversold dip을 진입 타이밍으로. **상승추세 눌림목 매수 정당, 하락추세 역행 눌림목 매수 금지**(현 신호가 정확히 금지 사분면=below MA20 매수).
- **A 기각**(fwd20d −0.03 비유의=multiple-testing 인공물 위 건축). **C 보류**(regime 판별 과적합·lagging·n<30 부족, trend-gate가 거친 regime proxy로 정신 흡수). **D 보류**(단일국면 −IC 하나로 아키텍처 갈아엎기=과잉반응).
- 학술: Liu-Tsyvinski-Wu(2022 JF)·Liu-Tsyvinski(2021 RFS) crypto momentum robust(주~월), Moskowitz-Ooi-Pedersen(2012) TSMOM, Jegadeesh-Titman momentum/reversal term structure. **단기(<3-5일)=노이즈/reversal, 1주~3개월=momentum 지배, 6-12개월+=valuation reversal**.
- 핵심 지표(레버리지 순): ①trend filter/sign conditioning(최고, −IC→0~+ 가능성 최대 단일 수) ②vol normalization/vol-targeting(crypto vol clustering, Sharpe 개선) ③TS-momentum core(trailing return 부호·MA crossover·Donchian) ④volume/on-chain=confirmation(standalone 아님, PIT 위에서만). 단일 BTC=TS-momentum만(XS=멀티코인 sleeve 성숙 후 별도 alpha).
- 과적합 방어: Newey-West/block bootstrap(Bonferroni는 overlap 미보정), walk-forward/anchored OOS, **cross-asset 검증(ETH/주식 등 sleeve, 진짜 factor면 다자산 출현)**, 파라미터 ≤3, falsification 사전등록("trailing-return OOS rank-IC K분기 ≤0이면 momentum prior 기각"=기존 e-process/e-CUSUM kill 직결).
- ⚠️ naive sign-flip(과매수/MA20상향서 매수)은 inverse-overfitting 위험 → 별도 OOS 가설로.

## 3. ★다음 = trend-gate 검증 (자문→채택 verification, decision-quality-protocol)
- **무엇**: `.p2-signal-alpha.py`에 trend filter 추가 — "price > MA50(또는 MA200)" 또는 "8-12주 trailing return >0" 일 때만 buy_score 매수 승인(아니면 기각). rank-IC 재측정해 −0.10이 0~+로 전환되는지 확인.
- **방어**: 동시에 (a) Newey-West로 유효 p 재검정 (b) ETH·다른 코인 cross-asset 부호 일관성 (c) walk-forward half-split.
- **이후**: external_bonus 포함 재평가(한계 2 해소) → 전환 확정 시 신호 study(지표 가중치·방향 재설계, study yaml + 12축 audit). go-live=사람 게이트.

## 4. 진입 (다음 세션)
1. 이 파일 → 2. `progress-test-readiness.md §P2`(Working Notes ckpt) → 3. `.p2-signal-alpha.py`(score_series·evaluate, trend filter 추가 지점) + `.p2-test2a.py`(코드축 진단).
- 임시 산물: `.p2-signal-alpha.py`·`.p2-test2a.py`(진단), `.p2-btc-daily.csv`·`.p2-fgi-daily.csv`(캐시), `.consult-study-meanrev-briefing.md`·`.consult-cap-briefing.md`(자문 브리핑).
- ★ledger 박제 대기(CLAUDE.md ⑤ 신규): coin 코어 지표(FGI/RSI/SMA) forecasting rank-IC −0.10 실측 → indicator-ledger candidate/rejected_provisional(2026-06-02). external_bonus 미포함·단일국면 caveat 명기.
- ⛔ risk_gate 상수 무수정, push 금지, go-live=사람 게이트.

## 6. 코드 진입점 상세 (다음 세션 즉시 착수)
- **`.p2-signal-alpha.py` 구조**: `fetch_btc_daily`(캐시 `.p2-btc-daily.csv`) / `fetch_fgi`(캐시 `.p2-fgi-daily.csv`, Alternative.me limit=0) / `rsi_wilder`(ewm alpha=1/14) / `build_features`(rsi·sma_dev·chg24·fgi 컬럼 DataFrame) / `score_series(agent, feats)`(agent별 `calculate_buy_score(fgi,rsi,sma_deviation,news_negative=F,external_bonus=0,macd=F,fast=True,price_change_24h)`→`["total"]`) / `evaluate(score,prices,threshold,k)`(forward k-day, `spearmanr`로 rank-IC + hit/expectancy/base_rate).
- **★trend filter 추가 지점**: `build_features`에 `ma50=prices.rolling(50).mean()`(또는 ma200/8-12주 trailing return 부호) + `trend_up = prices > ma50` 컬럼 추가 → `score_series`에서 `trend_up==False`면 buy 신호 기각(total→0 또는 NaN). rank-IC를 trend_up=True subset에서 재측정.
- **재측정 비교 표**: 현 rank-IC(전체, fwd5/10/20) vs trend-gated rank-IC. 음(−0.10)→양/0 전환 여부가 B안 채택 verification 게이트. 동시 Newey-West/block로 overlapping 보정 + ETH cross-asset 부호.
- **첫 명령**: `RISK_MAX_WEIGHT_SINGLE=0.95 /c/.../Python312/python.exe .p2-signal-alpha.py`(현 baseline 재현) → trend filter 버전 비교. (코드축 진단 재현은 `.p2-test2a.py`.)
- **진짜 coin_track 백테스트는 부적합**: BacktestEngine은 보유를 PortfolioState로 추적하나 Orchestrator는 고정 override portfolio를 봐서 sell 동기화 안 됨 → forecasting-object(buy_score rank-IC)로 격리한 이유. Orchestrator 통째 위임 경로(core/coin_track.py:119)는 엔진에 태우지 말 것.

## 5. 변경 사항 (이번 세션)
- CLAUDE.md ledger 규칙 강화: 갱신 의무 시점 ⑤(study 밖 탐구) + "탐구 누적(계속 기록)" 원칙. (커밋 안 함, 사용자 지시 편집)
- 신규 임시 진단 스크립트 2개 + 자문 브리핑 2개. **엔진/부품 코드 무수정**.

---

## 7. ★후속 진행 (2026-06-02 오후) — 신호 풀 확장 + 자문 3R 수렴 + 15축 audit + yaml 카드 교체

### 7.1 trend-gate 검증 (B안 verification) — 부분지지/완전입증 실패
- `.p2-trend-gate.py`: MA50_up subset rank-IC −0.10→~0 **무해화만**(양전환 실패), MA200_up/trail12w_up **정반대 더 음**(−0.20~−0.29, 강세장 oversold 더 위험), ETH cross-asset 무해화 약함, non-overlap thin 비유의. → B안 robust 구원 아님.
- external_bonus 부분 재평가(`.p2-ext-partial.py`): PIT 가능분(macro±15+eth/btc z±5)만 → core+ext rank-IC Δ +0.001~0.010 미미. 핵심소스(뉴스/RSS/X/social)=라이브 스냅샷만 PIT 불가 → 정면 미검증.

### 7.2 신호 풀 확장 측정 (사용자 "신호 적다" 우려)
- `.p2-momentum.py`: TS momentum +rank-IC. BTC donch20 fwd10d **+0.144**(p=0.0001)·tr7-30d +0.09~0.12, ETH tr30d **+0.177**. ma50_200 음(추세 끝물). ★코어 mean-rev −0.10과 **부호 정반대**.
- `.p2-volvol.py`: vol-targeting collinear(donch corr 0.85 무가치)·realized vol BTC+/ETH− 부호불일치(directional 아님, sizing만)·volprice_corr +0.13~0.16(thin 유의, momentum 변형 ρ0.51).
- `.p2-xsection.py`: cross-sectional 20코인 winner−loser tr7d→fwd10d **full t=4.2(overlap 신기루)·thin t=1.69(정직, marginal)**·long-only winner excess +2%/10d(survivorship 상방). → 독립 breadth지만 Upbit long-only면 beta-neutral 소멸.

### 7.3 자문 3R 수렴 (gemini-web + claude-web, `.consult-momentum-R1~R3.txt`)
- **메타결론**: 단기 가격기술 공간 = **momentum 1차원**(채널/vol-targeting/volprice/cross-sectional 전부 momentum 붕괴). 추가 독립차원 = microstructure(funding/basis/OI **1순위**)·온체인·거시.
- **Track A 코어(즉시)**: TS momentum 채널위치 **단일 carrier**, 사전등록 동결, default=null, 3-kill(e-process/down-regime IC<0/net-cost decile≤0), de-overlap·regime-split·net-cost decile estimator 봉인.
- **Track B(병행 데이터)**: 2022 약세장(LUNA/FTX) PIT·survivorship sealed 반증블록(fitting 금지).
- **Track C(우선 사전등록)**: cross-sectional `pos=max(0,TS_시장)×CS_랭크`(베타=TS only, CS=롱북 내 비중 tilt). 게이트=non-overlap 유의+long-only-as-executed(survivorship 보정)+2022 OOS.
- **vol-managed sizing**: 신호단 아닌 포지션 스케일링 레이어(risk parity persistence), ablation+net-cost 게이트.
- **Track D**: Tail-MR(청산캐스케이드), 2022 기반.

### 7.4 15축 독립 audit (subagent ab64711, opus) — verdict 부분/hard-fail 0
- Provenance 통과(실데이터, result.json 재현 ±0% 일치), B축 통과(de-overlap 정직·thin 자가검증·p-hacking 차단), 9통과/4부분(G·I·J·K)/0불충분.
- **5개 ledger 라벨 전부 현 status 박제 가능**(rejected_provisional 2: coin_core_buyscore·coin_realized_vol / candidate 3: coin_tsmom·coin_xs_momentum·coin_volprice_corr). weight 0·런타임 미결선 → M~O 무관.
- **adopted 승격 게이트**: J(net-cost decile)·K(momentum 27·volvol 42 비교 Bonferroni 보정→donch20만 생존)·I(survivorship-free OOS)·G(eff-N 명기).

### 7.5 산출물 변경
- ledger `study-research/_wire/indicator-ledger.md` crypto 섹션: coin_core_buyscore·coin_tsmom·coin_xs_momentum·coin_volprice_corr·coin_realized_vol 5행 박제 + 자문 3R 메타결론 주석.
- ★**카드 교체** `study-research/crypto/study_session.yaml`: lens.report_relations에 단기 기술 트랙 2항목 추가(mean-rev 코어 폐기·momentum carrier 후보), estimation_note·btc_price indicator·as_of(→06-02) 갱신. **거시 본체(MVRV/funding/stablecoin/ETF/halving weight_rules)=불변(별 트랙)**.
- 신규 임시 스크립트: `.p2-trend-gate.py`·`.p2-ext-partial.py`·`.p2-momentum.py`·`.p2-volvol.py`·`.p2-xsection.py` + result.json. 자문 브리핑 `.consult-momentum-R1-briefing.md`·R2/R3 txt.

### 7.6 ★다음 (자율/게이트 구분)
- **자율 가능**: (a) microstructure funding/basis/OI forecasting 측정(자문 1순위, funding 시계열 수집 필요) (b) 2022 약세장 데이터 수집(Track B, survivorship-free universe)
- **게이트(go-live 경계)**: Track A 코어 신호 재설계 코드 구현(calculate_buy_score 교체/신규 momentum 엔진) = 사람 게이트. adopted 승격 = J/K/I/G 통과 후.
- ⛔ risk_gate 상수 무수정·push 금지·go-live=사람 게이트.

---

## 8. ★microstructure/venue 라운드 (2026-06-02 저녁) — 단기 price 트랙 최종 처분

`.p2-micro.py`(Binance perp funding/basis/OI) + KRW 페어 cross-pair + BTC-직교화 잔차 검정 + 자문 2R(`.consult-micro-R1/R2.txt`).

### 8.1 결정적 발견 (전부 실측)
1. **momentum 거래소 특수성**: donch20 fwd10d가 Upbit KRW-BTC +0.144(USD환산 +0.111, 환율 효과 아님 USDKRW corr 0.055)인데 **Binance 글로벌 spot/perp 2024-26 ≈0**(−0.01~+0.01). 전 신호 H1(2019-22) 강→H2(2022-26) 글로벌 소멸 = 시장 효율화.
2. **KRW cross-pair 복제 실패**: BTC +0.174·ETH +0.129·SOL +0.153 양 / ★XRP −0.090(2025-26 **−0.270**)·ALGO/ATOM/DOT/XLM 음. 한국 리테일 최애 XRP가 최강 역추세 = "venue 전반 리테일 momentum" 가설 붕괴(claude 예측 적중).
3. ★**BTC-직교화 잔차 momentum 붕괴(가장 결정적)**: ETH raw+0.129→잔차−0.012·SOL+0.153→−0.042·AVAX+0.123→+0.019·DOGE+0.102→−0.063. 대형 momentum 양은 **전부 BTC 베타 상속**, 직교화 시 붕괴. 소형 잔차 음(idio 역추세). → 단기 price 독립신호 = **BTC 시장 momentum 1개뿐**(effective n=1).
4. **funding(Binance perp 2458일)**: BTC fwd10d 음(역추세) ↔ ETH 양(추세) 부호 cross-asset 반대 + regime H2 소멸 + 최근334일↔전기간 부호 뒤집힘. 일봉 directional 무알파. basis도 momentum 동조(corr 0.39)·cross-asset 불일치. OI=Binance 30일 제한 측정불가.

### 8.2 자문 2R 수렴 (gemini+claude, claude 4점 수정안이 데이터로 확정)
- 단기 price 트랙 = 독립 알파 sleeve에서 **폐기/강등**. 잔존 = BTC 시장팩터 momentum 단일 directional 노출뿐(ETH 중복 사이징 금지).
- 게이트: BTC-직교화 잔차검정(완료, 붕괴 확인) + net-of-cost rolling IR(KRW long-only 10-20d 회전 비용이 +0.11~0.17의 binding constraint, sleeve 0 될 수 있음).
- size/알트-reversion = deploy 금지, 2024-26 BTC우위 regime 가설로 **로깅만**(falsifier=alt-season 부호 반전).
- funding = directional 폐기, 극단 crowding(p99 롱쏠림) **진입차단 리스크필터로만** 격하(자문 "1순위 직교 리드" 승격 철회).
- intraday perp funding = venue·infra 불일치(우리=Upbit spot)로 **명시 defer**.
- ★**알파 예산 거시·온체인으로 전면 이전** — 정보 비대칭 지속 + horizon이 우리 운영 제약(spot/KRW/no-leverage/zero-intervention)과 정합하는 유일 영역.

### 8.3 ledger 박제 (crypto 섹션)
coin_micro_funding·coin_micro_basis(rejected_provisional) 신규 + coin_tsmom에 거래소 특수성·직교화 붕괴 박제. 임시 스크립트 `.p2-micro.py` + `.p2-micro-*.csv` 캐시 + `.consult-micro-R1/R2.txt`.

### 8.4 ★다음 (자율/게이트)
- **자율 가능**: 거시·온체인 forecasting 트랙 착수(stablecoin 발행·거래소 순유입·active address·SOPR·글로벌 유동성·금리민감도 = crypto yaml 거시 본체와 연결). microstructure 단기 트랙은 결론 완료(BTC momentum 1개 옵션, 게이트 대기).
- **게이트**: 단기 BTC momentum sleeve 코드 구현 = net-cost rolling IR 통과 후 사람 게이트. 거시/온체인 신규 데이터 파이프라인 = 사용자 방향 확인.
- ⛔ risk_gate 상수 무수정·push 금지·go-live=사람 게이트.

---

## 9. ★ledger 자문지표 누락방지 + kimchi measured + 논문 리서치 (2026-06-02 심야)

> [ckpt-202606022350:btn-Inv] 마지막 결정=단기 가격트랙 BTC momentum 1개로 수축 확정+자문언급 13지표 ledger 박제+논문 문헌대조. 다음 의도=거시(M2/real rate FRED) measured 우선. 동기화 필요=indicator-ledger.md crypto 18 candidate / crypto-factor-papers.md.

### 9.1 ledger 자문지표 누락방지 (consult-raw-output-mapping, 사용자 지시)
momentum R1-R3 + micro R1-R2 자문 언급 지표 **13개 전수 candidate 박제**(indicator-ledger.md crypto): coin_perp_oi·coin_liquidation·coin_exchange_netflow·coin_exchange_reserve·coin_active_addresses·coin_sopr·coin_miner_flow·coin_whale_flow·coin_global_liquidity_m2·coin_real_rate·coin_dxy_sensitivity·coin_kimchi_premium·coin_breadth_altseason. 각 수집기 유무·collector_plan 표시. crypto 카운트 adopted 6/candidate 18/rejected_provisional 4.

### 9.2 kimchi premium measured (claude 지목 "Upbit momentum 별 차원")
김프=(Upbit_KRW/USDKRW/Binance_USD−1). kimp **level → Upbit fwd10d rank-IC −0.211(p<.005)** = 과열(프리미엄 확대)→하락 역추세. donch momentum과 corr −0.36(부분 직교=보완). 김프 자체 mean-revert(−0.274, 자본통제 차익수렴). kimp_z/mom ~0. → momentum 보완 역추세 보조 후보(coin_kimchi_premium candidate, J/OOS 게이트). caveat=USDKRW Yahoo 환율 노이즈·단일국면.

### 9.3 BTC/ETH 논문 리서치 (subagent ad2f7b1, 14편, 3계층 저장)
**★subagent 결과 원문 (3계층, 필독)**:
- 메인 보고서(132줄, frontmatter): `D:/projects/Inv/study-research/crypto/raw/crypto-factor-papers.md`
- memory 요약: `C:/Users/jsh86/.claude/memory/research/crypto-factor-papers.md` (MEMORY.md 인덱스 line 3 연결)
- raw archive(native): `C:/Users/jsh86/.claude/docs/archive/research-raw/crypto-factor-papers-native-20260602.txt`

**관련 subagent 결과 (이전 단계)**:
- 15축 독립 audit (ad-hoc subagent ab64711, verdict=부분/hard-fail 0): 본 handoff §7.4 박제. coin 측정 5라벨 박제 자격 검증.

★문헌이 우리 결론 다수 지지:
- TS momentum 강·XS 약(Liu-Tsyvinski-Wu 2022 JF) + ★Han-Kang-Ryu 2023=거래비용 반영 시 momentum 포트폴리오 청산=우리 "글로벌 효율화 소멸" 학술근거. 단기신호 소멸=AMH(Adaptive Market Hypothesis).
- funding 무알파 지지(Crypto Carry=Schmeling-Schrimpf-Todorov BIS WP1087/Mgmt Sci 2024=carry·crowding 신호지 directional 예측 아님). low-vol anomaly crypto 부재(우리 vol β:=0 정합).
- 시대반박 1: Liu-Tsyvinski 2021 RFS macro null은 2021 초기표본 한정 → 2023+ 기관화로 BTC-DXY −0.4~−0.8·6-24M 거시유동성 상관 출현(horizon 분리 핵심).
- ★신규 factor top3: ①**USDT 거래소 net inflow**(유일 동료심사 robust, Chi-Chu-Hao 2024 arxiv 2411.06327, ★단 intraday 1-6h→일봉 전이 검증 필수) ②**funding crowding contrarian**(directional 아닌 게이트형 재정식화, funding-z 극단=크라우딩 해소 역추세, trend-gate 결합) ③**6-24M 거시유동성**(M2+real rate, 단기와 별 horizon 직교).

### 9.4 ★다음 measured 우선순위 (논문 결과 반영)
1. **거시유동성 M2 + real rate**(coin_global_liquidity_m2/coin_real_rate) — FRED 무료, 6-24M horizon, 즉시 측정 가능. 자율.
2. **USDT exchange net inflow**(coin_exchange_netflow) — 데이터 게이트(Glassnode/CryptoQuant 유료 or mempool 부분). 일봉 전이 검증.
3. **funding crowding 게이트형 재측정**(coin_micro_funding) — funding-z 극단 → 단기 역추세 재정식화(directional 아님).
- ⛔ risk_gate 상수 무수정·push 금지·go-live=사람 게이트.

---

## §10. ★자문 R1 수렴 + net-cost 데이터 검증 → 최종 트랙 설계 (2026-06-02, ckpt-202606xxxx)

> §9.4 measured 우선순위 전부 측정 완료 + 코인 트랙 종합 설계 자문 R1(gemini+claude 병렬) 1R 수렴 + 데이터 재검증 완료. **코인 신호 study 사실상 결론.**

### 10.1 §9.4 measured 결과 (4종 전부 ledger 박제)
| 지표 | 결과 | status | research_ref |
|---|---|---|---|
| 거시유동성 M2/real/dxy | BTC forward 6-24M **재현 실패**(전체표본 비유의, 2023+ eff_n<6 단일사이클 spurious, real level ADF I1). 논문 6-24M prior 미재현 | candidate→**rejected_prov** | .p2-macroliq-result.json |
| funding 게이트형 | 역추세 게이트 가설 **기각**(spread 전부 비유의). z>2 추세지속은 momentum 중복 | rejected_prov 유지 | .p2-funding-gate-result.json |
| breadth alt-season | alt-BTC MR rank-IC −0.13 발견(directional) / regime gate 가설 기각 | candidate(보조) | .p2-breadth-result.json |
| active addresses | 단순 활성도 무신호, metcalfe_resid lookahead+MVRV 중복 | candidate→**rejected_prov** | .p2-onchain-addr-result.json |

### 10.2 자문 R1 수렴 (gemini ∩ claude, 1R 조기종료) — raw=.consult-cointrack-R1-{gemini,claude}.txt, briefing=.consult-cointrack-R1-briefing.md
- **Q1 트랙 정당성**: 트랙 세움+자본 작게+풀사이즈/유료대기 거부. Upbit 비효율=bias(입력) 아닌 finding(출력)=결백. claude: **3신호=1개 구조 베팅(공통인)**, regime 분산은 환상, family-wise FDR pre-register, "닫히는 창" 경고.
- **Q2 독립성**: 부분 독립(다른 측정축·수익대상), sleeve 분리하되 합산 risk budget 축소.
- **Q3 아키텍처**: 합성점수 **단호 기각**. **2-sleeve**(S1 BTC dir=momentum base+kimchi throttle / S2 alt-BTC=breadth 독립병렬). kimchi=throttle(노출축소, short 아님).
- **Q4 우선순위**: net-cost+survivorship-free+2022 OOS **1순위**, 유료 온체인 후순위. claude: breadth net-cost 탈락 1순위 예측. gate=경제가치 ≥50% 보존∧2022 비파국적.

### 10.3 데이터 재검증 (자문→데이터, 자문 예측 전부 적중)
- **독립성**(.p2-overheat-indep.py): kimchi↔breadth corr −0.206·부분IC 유지 = **독립 알파 확증**(자문 Q2 양쪽 falsify 통과). kimchi=BTC절대방향(KRW경계 패닉)/breadth=alt-BTC상대(내부순환).
- **net-cost+2022 OOS**(.p2-netcost.py): **S1 BTC momentum donch20 net Sharpe 1.39~1.52(보존 73~78%), 2022 net −37.6%이나 BH −63.5% 대비 26%p 방어=비파국적 → gate 통과**. vs Buy&Hold(net Sharpe 0.99/MDD−74%) 우위, ★핵심가치=drawdown 방어(MDD 절반).
- **kimchi throttle**(top decile×0.5): 전구간 MDD↓+2023+ Sharpe 1.43→1.52 = claude Q3 falsify 통과(risk-adjusted 개선, 효과 marginal=자리값).
- **breadth rotation**(.p2-netcost-breadth.py): **net Sharpe 0.39 ≪ BTC 단순보유 1.13(보존 25%<50%) → 탈락**(claude 예측 적중). 연41회전환×0.40% drag로 rank-IC 소멸, survivorship 미보정인데도 탈락.
- **family-wise FDR**(claude Q1): 전라운드 N≈200+ 검정, 기대FD 0.05N≈10 > survivor 3 → BTC momentum만 학술 TSMOM prior+economic robustness로 면제, breadth net탈락 자연정리, kimchi=약한 throttle.

### 10.4 ★최종 트랙 설계 (확정)
**코인 단기 가격 트랙 = BTC momentum 단일 carrier(donch20, net Sharpe 1.42, drawdown 방어) + kimchi throttle(top decile 노출축소 보조).**
- breadth/거시유동성/funding/온체인(무료) = 전부 실행불가or무재현 → 단기 트랙 신호 추가 0.
- 거시 본체(crypto yaml MVRV/stablecoin/ETF/halving adopted)=별 트랙, 불변(단기와 horizon 직교).
- 2-sleeve(자문) → **1-sleeve로 축소**(breadth 탈락 = claude "실패 아닌 정확한 사이징").

### 10.5 다음 (미완·게이트)
- **driver-level kill pre-register**(claude): kimchi 구조 ~0 수렴(한국 자본통제 완화/법인 허용) 시 트랙 전체 정지 = 정책 박제(코드 아님).
- **유료 온체인**(SOPR/exchange netflow/청산) = 별도 탐색 라인(후순위, 무료 proxy null로 prior 약화).
- **코드 배선**(BTC momentum+kimchi throttle을 실 엔진에) = ⛔ go-live=사람 게이트. 현재 forecasting-object 검증만(코드 미배선).
- ⛔ risk_gate 상수 무수정·push 금지·go-live=사람 게이트.
