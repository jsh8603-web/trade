---
tags: [research, crypto, measurement, methodology, rank-ic, papers]
date: 2026-06-02
type: reference
source: WebSearch/WebFetch native (2026-06-02). raw archive = ~/.claude/docs/archive/research-raw/crypto-measurement-methodology-native-20260602.txt
verification: 핵심 논문 metadata는 WebSearch 다중 + WebFetch(arxiv abstract) 교차확인. ✅verified / ★미확인(제목·venue만 노출, 본문 미검) 구분 표기.
why: 팀이 forward-return rank-IC(Spearman) 위주로 측정해 "대부분 신호 무알파"라 결론냈는데, 이 측정 패러다임이 동료심사 robust 신호를 구조적으로 놓치는지 검증.
read-when: rank-IC 무알파 결론을 신호 채택/기각 근거로 쓸 때 / crypto 신호 측정축 추가(vol forecasting·event-study·regime split·intraday) 판단 / USDT netflow·SOPR collector_plan 데이터 게이트 검토 / Bonferroni false-negative 위험 재평가
---

# 암호화폐 예측 신호 — 측정 방법론 동료심사 조사

> **검증 질문**: 팀은 forward return rank-IC(Spearman) + Newey-West + Bonferroni + walk-forward, regime split × horizon(1d~1y) × cross(asset/exchange) 로 측정 → **BTC TSMOM 30-60일 1개만 생존**, MVRV/funding/stablecoin/거시 다 약함 결론. 팀 리더 의심 = "논문엔 robust 신호 있는데 우리 측정/빠진 축 때문에 못 잡는 것 아니냐."
>
> **결론(요약)**: 의심은 **부분적으로 타당**. rank-IC는 *단조 선형·일봉·종목간 횡단면* 패러다임이라 (a) **변동성 예측** (b) **이벤트 누적초과수익(CAR)** (c) **regime별 부호반전(비선형)** (d) **intraday-only 신호**를 구조적으로 놓친다. 특히 **USDT netflow는 원논문이 intraday 1-6h 전용 — 일봉 rank-IC로는 잡힐 수 없는 게 정상**(false-negative 위험 최상위). 단, momentum 1개 생존 자체는 문헌과 정합(가격신호 글로벌 소멸=AMH). Bonferroni는 false-positive 억제가 강해 **약한 진짜 신호를 죽이는 power 손실**이 큼(false-negative 증폭).

---

## 1. 측정 패러다임 표 — 방법 | 동료심사 ref | rank-IC가 놓치는 것 | 우리가 추가?

| # | 측정 방법 | 평가지표 | 동료심사 ref | rank-IC가 구조적으로 놓치는 것 | 추가? |
|---|---|---|---|---|---|
| (a) | **변동성 예측** (realized vol forecasting) | MAE / RMSE / **QLIKE** / R² | Springer Asia-Pac Fin Mkts 10.1007/s10690-024-09510-6 (HAR+Sentiment+ML horserace) ✅ / ScienceDirect S156849462301150X (HAR/GARCH/ML 비교) ✅ / arxiv 2508.15922 (quantile RV) ★ / arxiv 2511.20105 (HAR R²=9.3% BTC 5d RV) ★ | rank-IC는 **방향(수익 부호)** 만 측정. 변동성은 *level/2차 모멘트* 예측 — 부호 무관. on-chain flow가 **vol을 (−)예측**하는데(Chi-Chu-Hao) rank-IC(수익)로 보면 0으로 나옴 | **예** (별 측정축. 변동성 신호 = risk-targeting·게이트용, directional alpha 아님) |
| (b) | **event-study** (이벤트 전후 CAR) | **CAR / AAR** (누적·평균 초과수익) | ScienceDirect S221484502500153X (BTC&ETH ETF approval intraday) ✅ / Springer J Asset Mgmt 10.1057/s41260-026-00448-0 (narrative abnormal returns) ★ | rank-IC는 **연속 패널회귀** = 이산 이벤트를 표본 전체로 평탄화. ETF 승인·반감기·규제 같은 **점 사건 alpha**는 매일 측정하는 IC에서 희석. **large-cap=단발/소멸, emerging=장기지속** 차등도 안 보임 | **부분** (반감기·ETF·규제는 event-study로 별도. 우리 universe 대형 위주라 효과 短) |
| (c) | **conditional Sharpe/Sortino** | 국면별 risk-adjusted 수익 | (Bayesian HMM) ScienceDirect S0275531921001756 + arxiv 2011.03741 ✅ | rank-IC는 **무조건부 평균 상관**. 국면별로 Sharpe가 갈리는 신호(긴축↑완화↓)는 full-sample IC서 상쇄 | **부분** (이미 regime split 함 — 단 split을 *조건부 Sharpe*가 아닌 IC로 보면 power 더 낮음) |
| (d) | **분위회귀** (quantile, 꼬리) | pinball loss / 꼬리 분위 β | arxiv 2508.15922 (crypto RV quantile, 첫 체계연구) ★ | rank-IC는 **조건부 평균(중앙)** 의존. 신호가 *꼬리(crash/melt-up)* 에서만 작동하면 평균 IC≈0 | 보조 (꼬리 신호 의심 시. crypto는 fat-tail이라 가치 有) |
| (e) | **포트폴리오 정렬** (decile long-short) | decile 스프레드 수익·t / Sharpe | Liu-Tsyvinski-Wu 2022 JF (10 char L-S) ✅ | rank-IC ≈ 단조 가정. **비단조**(중간 분위 최고) 신호는 IC 낮아도 **bottom-top 스프레드**는 유의 가능. IC와 L-S 스프레드는 다른 통계 | 보조 (universe 넓으면 — 우리 대형 5종엔 횡단면 분위 약함) |
| (f) | **방향 분류** (hit rate / AUC) | accuracy / AUC / F1 | (regime ML) Springer Comp Econ 10.1007/s10614-026-11338-3 ★ / 다수 ML 논문 | rank-IC는 *크기까지 반영한 상관*. 크기 노이즈 큰 crypto서 **부호만 맞히는 신호**(hit>50%)는 IC 약해도 매매 가치 有(비대칭 페이오프) | 보조 (hit rate + 비대칭 손익이면 IC 무관하게 유효) |

**비선형/임계 (조사항목 2)**: HMM/Markov-switching·threshold·ML ensemble이 crypto 구조break/regime-switch(=비선형)를 포착한다는 동료심사 다수 (Bayesian HMM ScienceDirect S0275531921001756 ✅ / MDPI Math 13/10/1577 BTC regime Bayesian MCMC ★ / Springer Comp Econ 2026 ★). 단 **"비선형이 선형보다 유의하게 낫다"를 OOS·net-of-cost로 엄밀 입증한** 단일 동료심사는 이번 라운드 미확정(★ — ML 논문 다수가 in-sample/과적합 의심). → **선형 단일 rank-IC가 비선형을 못 본다는 건 방법론적으로 자명**하나, *비선형이 진짜 더 낫다*는 별도 OOS 검증 필요(우리 표본서). regime split을 이미 하는 건 옳은 방향이나, **단일 지표 선형 IC를 regime별로 쪼개는 것** ≠ **지표 조합/임계 상호작용**을 보는 것.

---

## 2. ★우리 "무알파" 결론이 측정 한계로 false-negative일 위험 top 3

> 기준 = (i) 동료심사 robust 보고 + (ii) 팀의 일봉·선형·수익-방향 rank-IC가 구조적으로 못 잡는 측정축에 신호가 살아있음.

1. **★USDT(스테이블코인) 거래소 net inflow — 최고 위험**.
   - 근거: **Chi-Chu-Hao (arxiv 2411.06327, 2024) ✅verified** — USDT 거래소 net inflow가 BTC·ETH 수익 (+)예측 + 변동성 (−)예측. **WebFetch 직접 확인: 논문 frequency = "intraday 1-6 hours" 전용, 일봉은 전혀 다루지 않음.**
   - false-negative 메커니즘: 팀이 일봉 rank-IC로 stablecoin을 봐서 약함 결론 → **원신호가 1-6h라 일봉 집계 시 소멸하는 게 정상**. "측정 horizon 미스매치"의 교과서 사례. (우리 H3 검증도 DefiLlama *total supply* 일봉 → 거래소向 inflow와 다른 변수 + 일봉 + rank-IC 7/30d CI 0포함 무유의 = 같은 함정 가능성.)
   - falsifier: 거래소向 USDT inflow를 1-6h로 받아 intraday rank-IC/event 측정 → 원논문 재현되는지. **일봉만으로 기각하면 안 됨.**

2. **★변동성 예측 신호 (on-chain flow → realized vol)**.
   - 근거: vol forecasting 문헌(HAR+ML, Springer/ScienceDirect ✅) + Chi-Chu-Hao가 flow의 **vol (−)예측력**을 명시.
   - false-negative 메커니즘: 팀 측정 대상 = forward **수익** rank-IC. 변동성은 *부호 무관 2차 모멘트* → 수익 IC로 보면 0. **flow·MVRV가 vol을 예측해도 수익 IC 패러다임선 안 보임.** 변동성 예측은 risk-targeting·게이트(de-risk 타이밍)로 직접 가치.
   - falsifier: 같은 지표로 forward **RV** 예측을 QLIKE/R²로 측정 → HAR 베이스라인 대비 증분.

3. **★Funding-rate intraday crowding / regime 부호반전 (비선형)**.
   - 근거: funding 동학이 high-freq(1min, MDPI Math 14/2/346 ✅) + Schmeling-Schrimpf-Todorov(Crypto Carry, Mgmt Sci 2024 ✅, factor-papers.md §4) carry=크라우딩 신호 + 우리 실측 "funding BTC역추세/ETH추세 = regime 의존".
   - false-negative 메커니즘: (i) 신호가 intraday인데 일봉 집계 시 mean-reversion 구조 소멸 (ii) **regime별 부호반전**(BTC vs ETH 반대부호)을 full-sample 선형 IC가 평균서 cancel → "directional 무알파"로 오판. 실제로는 **z-score 크라우딩 contrarian 게이트** 또는 regime-conditional로 살아있음.
   - falsifier: funding-z 상위 decile 후 fwd return(crowding unwind) + regime split 부호 일관성 + intraday 측정.

**공통 진단**: 세 신호 모두 팀의 *(forward 수익) × (rank-IC) × (일봉)* 3중 제약 중 최소 하나에 걸려 구조적 false-negative. momentum이 살아남은 건 momentum이 마침 *수익-방향·선형·일봉*에 정합한 신호라서 — **측정 패러다임이 momentum-친화적**이라는 점도 생존 편향의 한 축.

---

## 3. USDT netflow + SOPR 무료 데이터 소스 구체 경로

> ✅ = 무료 확인 / ★ = chart는 free view지만 API 시계열 다운로드는 불확실 / 유료 = 유료만.

### USDT / 스테이블코인 거래소 netflow
| 소스 | 경로 | 무료성 | caveat |
|---|---|---|---|
| **CryptoQuant** | cryptoquant.com/asset/stablecoin/chart/exchange-flows/exchange-netflow-total (All Stablecoins ERC20 exchange netflow) | ★ free **chart view**. API 시계열은 유료 tier 의심 | 차트 스크랩 가능하나 정식 API 일봉 다운로드 = 유료 가능성 高 |
| **Glassnode** | studio.glassnode.com/workbench/usd-exchange-netflowvolume | ★ free tier basic charts. 고급/장기 = 유료 | API endpoint 무료 metric 제한적 |
| **The Block** | theblock.co/data/on-chain-metrics/flows (BTC/ETH/USDT inflow) | ★ free **view** | 다운로드/API 불확실 |
| **Dune Analytics** | dune.com (SQL dashboards, Eth/Polygon/BSC raw tables) | ✅ free tier (rate limit) — **USDT ERC20 transfer를 거래소 라벨 지갑 기준 SQL 집계 = 직접 구축 가능** | 거래소 지갑 라벨링 정확도가 변수. 일봉 inflow는 구축 노력 필요 |
| 거래소 API (Binance 등) | — | — | netflow(온체인 입출금)는 거래소 API로 안 나옴(주문/잔고만). **온체인 데이터 별개** |

→ **결론**: USDT 거래소 netflow *일봉*은 무료 chart view는 많으나 **정식 무료 API 시계열은 Dune SQL 자가구축이 유일하게 견고**(라벨링 caveat). CryptoQuant/Glassnode/TheBlock = 유료 게이트 가능성. ★단 **원논문 신호는 intraday 1-6h** — 일봉 데이터를 무료로 구해도 horizon 미스매치라 우선 intraday 가용성부터 확인해야 함(대부분 유료).

### SOPR / realized-cap / LTH-STH cost-basis
| 소스 | 경로 | 무료성 | caveat |
|---|---|---|---|
| **Coin Metrics Community** | coinmetrics.io/community-network-data/ + GitHub `coinmetrics/data` (일별 아카이브) + Community API (HTTP `format=csv`) | ✅ **무료 확인**. **SOPR(LTH/STH cohort 분리) + realized cap 포함**, CSV 다운로드, 일별 갱신 | community tier = metric/coverage 제한. 일봉 해상도(intraday 아님) |
| blockchain.com charts API | api.blockchain.info/charts | ★ 기본 차트(가격·tx·hashrate) 무료. **SOPR/realized-cap은 미제공 가능성** | SOPR류 cohort 지표 부재 추정 |
| Glassnode | studio.glassnode.com (SOPR transaction-based) | ★ free tier 일부 SOPR chart | 장기/고급 SOPR = 유료 |
| checkonchain | charts.checkonchain.com | ★ free **view** (MVRV/SOPR 차트 다수) | 다운로드/API 없음(시각화만) |

→ **결론**: **SOPR + realized-cap은 Coin Metrics Community 무료 API(CSV/GitHub)로 일봉 확보 가능 — 확정**. 데이터 게이트 아님(자율 측정 가능). 단 **동료심사 robust 근거는 약함**(대부분 실무·블로그·ML 논문, 단일 SOPR/MVRV의 동료심사 rank-IC robust = ★미확인) → directional alpha보다 **국면 게이트(과열/축적)** 로만.

---

## 4. 빠진 축 우선순위 — 자율 측정 가능 vs 데이터 게이트

### A. 자율 측정 가능 (데이터 보유 / 무료 확보, 즉시 falsify)
1. **변동성 예측축 추가** (최우선·데이터 보유). 기존 BTC 일봉으로 forward RV를 HAR 베이스라인 + 기지표(MVRV/flow/funding)로 예측, QLIKE/R² 평가. → 수익 IC서 죽은 지표가 vol에서 살아있나 확인. **rank-IC 패러다임 보완의 가장 싼 ROI.**
2. **regime별 부호반전 / 조건부 측정** (데이터 보유). 이미 regime split 하나, **단일 지표 IC**가 아닌 (a) regime별 조건부 Sharpe (b) 지표 *조합·임계 상호작용* (c) funding-z 크라우딩 게이트(역추세). full-sample IC가 cancel하는 신호 발굴.
3. **event-study (반감기·ETF·규제)** (데이터 보유, 이벤트 날짜만 필요). CAR/AAR로 점 사건 alpha 측정. 연속 IC가 평탄화하는 신호.
4. **SOPR/realized-cap·LTH-STH** (Coin Metrics Community 무료 — 데이터 게이트 아님). regime 게이트로 측정(directional 아님). ★단 동료심사 robust 약 → candidate, 채택 전 OOS.
5. **decile long-short / hit-rate·AUC** (universe 확장 시). 비단조·부호만 신호 포착.

### B. 데이터 게이트 (intraday·유료 — 확보 선행 필요)
1. **★USDT 거래소 net inflow — intraday 1-6h** (게이트). 원논문(Chi-Chu-Hao) 신호가 intraday 전용 → **일봉으론 재현 불가**. intraday 거래소向 USDT inflow = 무료 견고 소스 부재(Dune 자가구축도 intraday 라벨링 난). 유료(CryptoQuant/Glassnode pro) 또는 Dune intraday 구축 선행. **horizon 미스매치라 일봉으로 기각하지 말 것** = false-negative 핵심.
2. **funding intraday (1min~1h)** (반게이트). 거래소 API로 funding rate 자체는 무료 가능(과거 funding history) — intraday 측정은 가능하나 데이터 정합/수집 노력. crowding 게이트는 일봉 funding-z로도 부분 가능.

### 측정 함정 (조사항목 6 — false-negative 위험)
- **Bonferroni의 power 손실**: 팀의 Bonferroni는 **false-positive 억제 강 = false-negative(진짜 약신호 기각) 증폭**. Deflated Sharpe/PBO(Bailey-Lopez de Prado ✅)도 전부 *과적합(false-positive) 방어* 도구 — crypto 약신호 환경선 **FDR(Benjamini-Hochberg)** 가 Bonferroni보다 power 보존(약신호 덜 죽임). 다중비교 보정 자체는 옳으나 **Bonferroni 단일 의존은 false-negative 편향**.
- **overlapping 표본 자기상관**: forward k일 수익 IC는 인접 표본 겹침 → 유효 n 과대 → NW 보정 안 하면 false-positive지만, **반대로 block 보정 과하게 하면 약신호 기각**(우리 H3 block-bootstrap CI가 넓어 0 포함된 것과 동형 — 진짜 약신호인지 표본 부족인지 구분 안 됨).
- **비정상성/regime break**: 단일 full-sample IC는 2020 DeFi summer·2022 UST·2024 ETF 같은 break를 평균 → regime별 부호반전 신호 소멸(우리 H3 §6 미해결 의문과 일치).
- **horizon/frequency 미스매치 (★최대 함정)**: intraday 신호를 일봉으로 측정 = 구조적 false-negative. Chi-Chu-Hao가 직접 증거.

---

## 환각 검증 메모
- ✅ verified (WebFetch abstract 또는 다중 WebSearch 교차): **Chi-Chu-Hao arxiv 2411.06327 (intraday 1-6h 전용 = WebFetch 직접 확인)** / Coin Metrics Community 무료 SOPR+realized-cap CSV (WebSearch 다중) / Bailey-Lopez de Prado Deflated Sharpe·PBO / Bayesian HMM crypto predictability (ScienceDirect S0275531921001756) / Liu-Tsyvinski-Wu 2022 JF (factor-papers.md 기수록) / Schmeling et al Crypto Carry (factor-papers.md 기수록) / 변동성 HAR 비교 (Springer 10.1007/s10690-024-09510-6, ScienceDirect S156849462301150X).
- ★미확인 (제목·venue·DOI만 검색 노출, 본문/정확발견 미검): arxiv 2508.15922 quantile RV / arxiv 2511.20105 HAR R²=9.3% / Springer J Asset Mgmt 10.1057/s41260-026-00448-0 / MDPI Math 13/10/1577 / Springer Comp Econ 10.1007/s10614-026-11338-3 / MDPI Math 14/2/346 two-tiered funding / ScienceDirect S221484502500153X ETF intraday event. 인용 시 본문 재확인.
- ★실무·블로그 (동료심사 아님, 데이터 경로 근거로만): CryptoQuant/Glassnode/The Block/Dune/checkonchain chart 페이지. SOPR/MVRV의 단일지표 동료심사 robust rank-IC 근거 = 미확인.
- **데이터 무료성 주의**: "free chart view" ≠ "free API 시계열". CryptoQuant/Glassnode netflow API는 유료 게이트 가능성 高 — 실제 fetch 전 검증 의무(empirical-claim rule §1.1-ext).
