---
tags: [research, crypto, factor, papers]
date: 2026-06-02
type: reference
source: WebSearch/WebFetch native (2026-06-02), raw archive ~/.claude/docs/archive/research-raw/crypto-factor-papers-native-20260602.txt
verification: 핵심 논문 metadata는 WebFetch(RePEc/arxiv) 또는 다중 WebSearch 교차확인. 불확실 항목은 ★미확인 표기. 환각 1건 자기정정(Crypto Carry 저자).
---

# 암호화폐 Factor / 예측 학술 문헌 — 우리 실측 대조

> 목적: 우리가 코드로 실측한 결과(coin-core mean-rev 역IC, TS momentum 글로벌 소멸, BTC베타 상속, funding 무알파 등)를 동료심사 문헌과 매핑하고 신규 factor 후보를 발굴.
> **대조 기준(우리 실측, 재조사 X)**: ① coin-core mean-rev(공포+RSI+SMA하향) BTC일봉 fwd10d rank-IC **−0.108** ② TS momentum(donch20) Upbit +0.144 / Binance 글로벌 2024-26 ≈0 ③ 대형코인 momentum = BTC베타 상속(직교화 시 붕괴), 독립 size 없음 ④ KRW-XRP 역추세 −0.27 ⑤ funding 일봉 directional 무알파(BTC역추세/ETH추세, regime의존).

---

## 주제 1 — Crypto Momentum

| 논문 | 저자·연도·저널 | 1줄 발견 | 우리 실측 판정 |
|---|---|---|---|
| Common Risk Factors in Cryptocurrency | Liu, Tsyvinski, Wu **2022 J. of Finance 77(2):1133-1177** (DOI 10.1111/jofi.13119) ✅verified | 3 factor = **market, size, momentum** 가 cross-section 설명. 10개 char 기반 long-short 전부 3-factor로 흡수 | **보완/부분반박**. 우리도 momentum이 살아남은 유일 신호(BTC 시장 momentum). 단 우리 "독립 size 없음"은 이 논문 size factor와 ★긴장 — 아래 §3 참조 |
| Risks and Returns of Cryptocurrency | Liu, Tsyvinski **2021 RFS 34(6):2689-2727** ✅verified | **강한 time-series momentum (1~4주 horizon)**. network factor 노출 O, production factor X. **macro/stock/통화/원자재 factor 노출 거의 없음**(null). investor attention이 미래수익 예측 | **지지(horizon) + 지지(macro null)**. 우리 TS momentum 주~월 horizon 일치. macro null은 §7 우리 BTC 거시연동과 ★시대 차이(2021 표본 vs 2023+) |
| TS & XS Momentum in Crypto under Realistic Assumptions | Han, Kang, Ryu **Dec 2023, SSRN 4675565** (AUT 워킹페이퍼) ★metadata 검색확인, 본문 PDF 403 | **거래비용+일중 변동 반영 시 momentum 포트폴리오 다수 청산**. **TS momentum 강, cross-sectional momentum 약** | **강한 지지**. 우리 "대형 XS momentum = BTC베타 상속(직교화 붕괴)" = XS 약 일치. "거래비용 반영 시 소멸"은 우리 글로벌 효율화와 동일 메커니즘 |
| Cryptocurrency momentum has (not) its moments | Springer FMPM 2025 (DOI 10.1007/s11408-025-00474-9) ★발견만, 저자 미확인 | momentum이 **severe crash / tail risk**에 노출 | 보완. 우리 directional 신호 약화의 한 원인(momentum crash) |

**소결**: Liu-Tsyvinski 계열이 보고한 momentum은 (a) TS > XS (b) 주~월 horizon — 둘 다 우리 실측과 정합. Han-Kang-Ryu(2023)는 **거래비용 현실화 시 청산**을 명시적으로 보고 = 우리 "글로벌 효율화로 소멸"의 학술 근거. ★2022 이후 효율화를 *직접* 측정한 단일 동료심사 논문은 이번 라운드에서 확정 못 함(미확인). Han-Kang-Ryu의 net-of-cost 청산이 가장 근접.

---

## 주제 2 — Market Efficiency 시계열 변화 (H1 강→H2 소멸)

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| Informational Efficiency of Cryptocurrency Markets | JFQA, Cambridge ✅search | crypto 효율성은 **time-varying** (Adaptive Market Hypothesis) | **지지**. "초기 비효율 → 성숙 후 효율" = 우리 H1→H2 소멸 framing의 정확한 학술 언어(AMH) |
| The dynamics of returns predictability in crypto markets | European J of Finance 2022 (DOI 10.1080/1351847X.2022.2084343) ★발견만 | 예측력이 시간에 따라 동적으로 변화 | 지지 |
| On the Evolution of Cryptocurrency Market Efficiency | arxiv 1904.09403 ★발견만 | 효율성이 시간에 따라 진화(개선 추세) | 지지(방향) |

**소결**: 우리 "가격신호 2022 이후 글로벌 소멸"은 **Adaptive Market Hypothesis** 프레임으로 학술 정당화 가능. 효율성 = 고정값 아닌 regime/유동성 의존 → 우리 trend-gate 채택(과거 ckpt) 논리와 정합(신호가 항상 죽은 게 아니라 국면 의존).

---

## 주제 3 — Cross-Sectional Factors / Size

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| Common Risk Factors (위 §1) | Liu/Tsyvinski/Wu 2022 JF ✅ | **size factor 유의**(소형 코인 프리미엄) | ★**부분 긴장**. 우리 "독립 size 없음"과 충돌처럼 보이나 → 우리는 *대형코인(ETH/SOL/AVAX)* 내에서 측정. JF size는 **롱테일 소형코인** 포함 cross-section. 표본 universe 차이로 양립 가능 |
| Impact of Size and Volume on Crypto Momentum and Reversal | Fičura, Colak, SSRN 4378429 ★발견만 | size·volume이 momentum/reversal 강도 조건화 | 보완. size를 *조건변수*로 쓰는 접근 — 우리 universe엔 직접 미측정 |
| Cryptocurrencies and the low volatility anomaly | Finance Research Letters 40 (2021) ✅search | **유의한 low-vol 프리미엄 없음** (1000코인 2013-2019) | **반박(equity 대비)**. 주식 low-vol anomaly가 crypto엔 부재 |
| Is idiosyncratic volatility priced? / jump-diffusive risks | J. Banking & Finance, JFE ★발견만 | IVOL이 기대수익과 **양(+)** 관계(주식과 반대) 보고하는 논문 존재. mixed | ★미측정. crypto IVOL 부호가 주식과 반대일 수 있음 |

**소결**: JF size factor와 우리 "독립 size 없음"은 **universe 정의 차이**(소형 롱테일 vs 대형 5종)로 양립. ★우리가 안 본 것 = 소형코인 롱테일까지 확장한 cross-sectional size sort. low-vol anomaly는 crypto에서 부재(반박) → 우리가 vol factor를 directional alpha로 쓰지 않은 건 정합.

---

## 주제 4 — Funding Rate / Basis / Perpetual 예측력

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| Crypto Carry | **Schmeling, Schrimpf, Todorov** — BIS WP 1087 + **Management Science 2024** (DOI 10.1287/mnsc.2024.05069) + SSRN 4268371 ✅verified(저자 교차확인) | crypto carry(선물-현물 basis)가 **연 40% 초과**까지, 변동 큼. 동인 = (i) 추세추종 리테일 레버리지 수요 (ii) 규제·증거금 마찰로 **arb 자본 제한** | **강한 지지 + 보완**. 우리 "funding directional 무알파"와 정합: carry는 **carry/arb 수익(시장중립)이지 directional 예측 alpha 아님**. funding 높음 = 크라우딩 신호(역추세 압력)지 미래 수익 예측 X |
| Predictability of Funding Rates | Inan, SSRN 5576424 ★발견만 | model 기반이 no-change보다 **다음 기 funding 자체**를 예측(방향정확도↑) | 보완. **예측 대상이 funding rate지 asset return 아님** — 우리 "directional 무알파"와 모순 아님 |
| Designing funding rates for perpetual futures | arxiv 2506.08573 ★발견만 | funding rate 메커니즘 설계론 | 배경 |

**소결**: 문헌 합의 = funding/basis는 **carry·crowding 신호**지 directional return 예측자 아님. Schmeling et al.의 "추세추종 리테일 + arb 마찰"은 우리 "funding regime 의존, BTC역추세/ETH추세"를 설명(크라우딩 해소 = 역추세). ★신규: **funding을 z-score crowding contrarian**(추세 게이트와 결합)로 쓰는 건 문헌 지지 — directional이 아니라 risk-off 타이밍.

---

## 주제 5 — 온체인 Factor Forecasting (collector_plan 우선순위)

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| Return & Volatility Forecasting Using On-Chain Flows | **Chi, Chu, Hao** — arxiv 2411.06327, Nov 2024(rev Sep 2025) ✅verified | **★USDT 거래소 net inflow가 BTC·ETH 수익 (+)예측 + 변동성 (−)예측 = robust**. **BTC net inflow는 BTC 수익 예측력 거의 없음**(4h 예외). ETH net inflow는 ETH 수익 (−)예측 | **혼합·중요**. 직관과 달리 *코인 netflow보다 스테이블코인(USDT) inflow*가 robust. intraday(1-6h) 표본 |
| (실무) MVRV/SOPR/NVT/flow 멀티팩터 | 헤지펀드 실무 보고 + ML 연구(Bitcoin price direction, 2025) ★non-peer-reviewed 다수 | 단일 지표보다 **MVRV+SOPR+flow 조합 ML**이 가격·변동성 예측 개선. MVRV high+SOPR하락+inflow상승 = 리스크 / MVRV low+SOPR<1+outflow = 축적 | ★대부분 **실무·블로그·ML 논문**(동료심사 robust 근거 약). 단일 지표 robust 증거는 USDT inflow가 가장 강함 |

**소결 (collector_plan 우선순위 권고)**:
1. **USDT(스테이블코인) 거래소 net inflow** — 유일하게 동료심사로 robust(Chi-Chu-Hao). 우선순위 1순위.
2. **MVRV / SOPR** — 실무 합의는 강하나 동료심사 robust 근거 약, regime 신호(과열/축적)로 적합 — directional alpha보다 **regime/타이밍 조건변수**.
3. **exchange netflow(BTC/ETH 자체)** — Chi-Chu-Hao가 **예측력 약**으로 보고 → 우선순위 하향.
4. NVT / active addresses — 이번 라운드 robust 동료심사 직접 확인 못 함(★미확인), candidate 유지.

---

## 주제 6 — 시장 분절 / 거래소 효과 (kimchi premium)

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| The Kimchi premium and bitcoin-cashing outlets | Finance Research Letters, S1544612322004056 ★발견만 | kimchi premium = 자본통제·청산경로 마찰의 함수 | 지지(배경) |
| Nonlinear dynamics of Kimchi premium | Economic Modelling, S0264999324000828 ★발견만 | premium이 **비선형** 동학, 국면 의존 | **지지**. 우리 "KRW-XRP 역추세 −0.27, cross-pair 복제 실패" = 분절시장 비선형성 |
| Crypto carry: market segmentation (위 §4) | Schmeling et al. ✅ | arb 자본 제한이 분절·가격왜곡 유발 | **강한 지지**. kimchi = 분절의 한 사례, 우리 한국 리테일 venue 특이성 |

**소결**: 한국 시장 비효율·리테일 지배는 문헌상 **자본통제 + arb 마찰**로 정당화. 우리 "Upbit momentum +0.144 vs Binance ≈0"은 **venue별 분절**(분절 시장에 잔존 alpha) — 단 ★실거래 가능성은 자본통제로 제한(arb 불가 = 우리가 못 먹는 alpha일 수 있음). KRW 알트 역추세는 비선형 분절 동학과 정합.

---

## 주제 7 — 거시 연동 (DXY·real rate·M2 유동성)

| 논문 | 출처 | 1줄 | 판정 |
|---|---|---|---|
| Risks and Returns of Crypto (위 §1) | Liu/Tsyvinski 2021 RFS ✅ | **crypto는 macro/stock/통화/원자재 factor에 노출 없음(null)** | ★**시대 의존 반박**. 2021 표본 null이지만 2023+ 기관화 이후 변함 |
| Bitcoin's Macro Liquidity Cycle / Coinbase·Fidelity·JPMorgan 보고 | 기관 리서치(비동료심사) ★ | 2023-25 BTC vs DXY **−0.4~−0.8**. 6-24개월 horizon서 macro 상관 강화. JPMorgan 2026: BTC-DXY **양(+)으로 전환** | 보완. **horizon 의존**: 단기 약·중기(6-24M) 강 |
| Global liquidity / TimeXer | arxiv 2512.22326 ★non-finance-journal | Global liquidity가 BTC 움직임 41% 설명, 65개월 부채 refinancing 사이클 | ★미검증(동료심사 아님) |

**소결**: Liu-Tsyvinski 2021의 macro null은 **표본시대 한정**(초기 시장). 2023+ 기관화로 BTC가 **유동성 민감 risk asset**화 → DXY/real rate/M2 상관 출현(단 기관 리서치 중심, 동료심사 약). **horizon 분리 핵심**: 단기 가격신호는 죽었지만(주제1-2), **중기(6-24M) 거시 유동성**은 살아있음 → 우리 시스템의 거시 sleeve와 정합. ★주의: JPMorgan 2026 DXY 부호전환 보고 = 거시 β도 시변(regime), 점추정 박제 금지.

---

## ★ 신규 Factor / 신호 아이디어 (우리 미측정 + 문헌 robust)

> n<30·소표본 주의. 아래는 *후보*이며 채택 전 우리 표본 재현 + walk-forward OOS + Newey-West 의무(empirical-claim rule).

### Top 3 (우선순위순)

1. **★USDT(스테이블코인) 거래소 net inflow** — Chi-Chu-Hao(2024, arxiv 2411.06327) **동료심사 robust**. BTC/ETH 수익 (+)예측, 변동성 (−)예측. 우리가 *코인 netflow*는 봤을 수 있으나 **스테이블코인 inflow가 robust한 쪽**. collector_plan 1순위. **falsifier**: 우리 BTC일봉 표본서 USDT exchange inflow rank-IC > 0 + walk-forward 분기 부호 일관. (주의: 원논문 intraday 1-6h → 일봉 전이 시 약화 가능, horizon 검증 필수)

2. **★Funding-rate crowding contrarian (directional 아님, 게이트형)** — Schmeling-Schrimpf-Todorov(2024 Mgmt Sci) carry = 추세추종 리테일 크라우딩. funding을 **z-score 극단 = 크라우딩 해소(역추세) 신호**로, 우리 trend-gate와 결합. 우리는 funding을 directional로 봐서 무알파 결론냈으나 — **crowding/risk-off 타이밍**으로 재정식화하면 문헌 지지. falsifier: funding-z 상위 decile 후 fwd return 음(crowding unwind).

3. **★중기(6-24M) 거시 유동성 factor (M2 + real rate, horizon 분리)** — 기관 리서치 합의 + Liu-Tsyvinski는 *단기* null. 우리 단기 가격신호 소멸과 **별 horizon**이므로 직교 추가 가치. BTC를 "고베타 유동성 표현(시차)"으로. falsifier: 6M forward BTC return ~ ΔM2/Δreal-rate 회귀 β 유의 + OOS. ★단, 점추정 박제 금지(DXY 부호 시변), regime-conditional + CI.

### 보조 후보 (robust 근거 약 → candidate)
- **MVRV / SOPR regime 조건변수** — 실무 강합의·동료심사 약. directional alpha 아닌 과열/축적 *국면 게이트*로만(MVRV high+SOPR하락 = de-risk).
- **소형코인 롱테일 cross-sectional size sort** — JF size factor. 우리 대형 5종 universe엔 없음. universe 확장 시 측정 가치(단 유동성·실거래성 caveat).
- **investor attention (검색량/소셜)** — Liu-Tsyvinski 2021 "attention forecasts returns". 우리 external_bonus(뉴스/온체인)와 겹칠 수 있음, 분리 측정 필요.

### 채택하지 말 것(문헌 반박)
- **low-volatility anomaly** — crypto서 유의 프리미엄 부재(FRL 2021). vol을 directional alpha로 쓰지 말 것(우리 vol β:=0 lock과 정합).
- **순수 가격 cross-sectional momentum(대형 universe)** — Han-Kang-Ryu net-of-cost 청산 + 우리 BTC베타 상속. 독립 alpha 없음.

---

## 환각 검증 메모
- ✅ verified(WebFetch/RePEc/arxiv 원문 또는 다중 검색 교차): Liu-Tsyvinski-Wu 2022 JF / Liu-Tsyvinski 2021 RFS / Chi-Chu-Hao 2024 arxiv 2411.06327 / Schmeling-Schrimpf-Todorov Crypto Carry(BIS 1087 + Mgmt Sci 2024).
- ★**자기정정 1건**: Crypto Carry 저자를 처음 "Roche/Schnabel"로 추정했으나 검색 교차확인서 **Schmeling/Schrimpf/Todorov**로 정정(날조 회피).
- ★미확인(저자·정확 발견 미검증, 제목·venue만 검색 노출): Han-Kang-Ryu 본문(SSRN 403) / Fičura-Colak / Springer FMPM 2025 momentum-crash / European J Finance 2022 / IVOL·jump 논문들 / kimchi 2편 본문 / 기관 거시 리서치(비동료심사) / arxiv 2512.22326. 이들 인용 시 본문 재확인 필요.
- BIS WP 1087 PDF = binary-corrupt(WebFetch 실패), 발견은 검색 + CEPR voxeu 칼럼 + Mgmt Sci DOI로 교차확인.
