---
name: crypto-regime-dependence-papers
description: 암호화폐 factor-수익률 연관의 time-varying / regime-dependent 특성에 관한 학술 문헌 정리 + 우리 실측(M2/funding/momentum subsample 붕괴) 대조 verdict + regime-conditional 신호 채택 기준
type: reference
date: 2026-06-02
tags: [research, crypto, regime, time-varying, factor-instability, market-efficiency, papers]
source: WebSearch/WebFetch native (2026-06-02). raw archive = ~/.claude/docs/archive/research-raw/crypto-regime-dependence-native-20260602.txt
verification: 논문 metadata(저자·연도·저널)는 다중 WebSearch 교차확인 + RePEc/SSRN/arXiv id 박제. 정량 magnitude는 검색 요약 기반 → 본문 직접 미확인 항목은 ★미확인 표기. 산업/블로그 출처는 "non-peer-reviewed"로 별도 구분.
---

# 암호화폐 Factor 예측력의 Time-Varying / Regime-Dependent 특성 — 학술 문헌 + 우리 실측 대조

> **핵심 질문**: crypto에서 지표-수익률 연관이 전기간(full sample) 일관되기 어렵고 regime마다 부호·강도가 바뀌는 게 **정상인가**? 그렇다면 어떻게 다루고 활용하나?
>
> **결론 선요약**: 문헌의 압도적 다수가 **"crypto factor instability = the norm"** 을 지지한다. 효율성 자체가 시간가변(AMH), beta가 시간가변(IPCA), 거시연동이 regime-shift(2023+ 출현), funding carry가 시변(>40% 변동). 따라서 **full-sample 비유의 + subsample 유의**는 crypto에선 결함이 아니라 기대되는 패턴. 단, 그것을 "살아있는 신호"로 채택하려면 **ex-ante regime 식별 가능성 + multiple-testing 보정 + walk-forward OOS** 라는 별도 게이트를 통과해야 하며, 그 게이트 없이는 "regime-conditional alpha"와 "in-sample regime fishing"이 구별 안 된다.

**우리 실측 대조 기준 (재조사 X, ckpt-202606022350 / handoff-p2-signal-study)**:
- ① 거시유동성 M2/real rate/DXY → BTC forward 6-24M: 전체표본(2017-2026) **전부 비유의**, 2023+ 서브샘플 M2 rank-IC **−0.6~−0.86**(유효표본 작음). 우리 기각 사유 = "단일 상승사이클 spurious".
- ② funding rate: H1(2019-22) 강 → H2(2022-26) 소멸, BTC/ETH 부호 반대. 우리 = "robust 아님" 기각.
- ③ 단기 momentum: 글로벌 Binance 2022 후 소멸(효율화), Upbit(한국 자본통제)만 잔존.

---

## 0. 논문 마스터 테이블 (저자·연도·저널·핵심결과·우리 관련성)

| # | 논문 | 저자·연도·저널 | 핵심 정량 결과 | 우리 실측 관련성 |
|---|---|---|---|---|
| P1 | On the Evolution of Cryptocurrency Market Efficiency | **Noda, Akihiko 2019(rev 2020)**, arXiv 1904.09403 | GLS 기반 sample-size-독립 시변 모델. (1) 효율성 **시간가변** (2) BTC 효율성 > ETH 대부분 기간 (3) 고유동성 시장 진화. AMH 지지 | 효율성 자체가 시변 = 우리 "전기간 일관 안 됨"이 정상이라는 **1차 근거** |
| P2 | Adaptive market hypothesis and evolving predictability of bitcoin | **Khuntia & Pattanayak 2018**, Economics Letters 167:26-28 ★magnitude 미확인 | BTC return predictability **시간에 따라 등장-소멸 반복** (AMH) | momentum H1강→H2소멸이 AMH의 "episodic predictability"와 정합 |
| P3 | The adaptive market hypothesis in the high frequency cryptocurrency market | **ScienceDirect S1057521919300821** ★저자 미확인 | 고빈도서도 효율성 시변, AMH 지지 | 효율화 메커니즘(글로벌 momentum 소멸) 지지 |
| P4 | Common Risk Factors in Cryptocurrency | **Liu, Tsyvinski, Wu 2022**, J. of Finance 77(2):1133-1177 (DOI 10.1111/jofi.13119) ✅ | 3-factor(market/size/momentum). 표본 2014-2020/07, 1827 coins | factor 자체는 존재하나 **표본 종료 2020/07** = 효율화 이전. 시대 caveat 핵심 |
| P5 | Risks and Returns of Cryptocurrency | **Liu, Tsyvinski 2021**, RFS 34(6):2689-2727 ✅(MEMORY 기존) | TS momentum 강(1-4주). **macro/stock/통화/원자재 factor 노출 거의 없음(null)** | macro null = 우리 ①의 학술 선례. 단 **표본 2021 이전** → 2023+ BTC 거시연동과 시대 충돌 |
| P6 | The Bitcoin-Macro Disconnect | **Benigno & Rosa, Feb 2023**, NY Fed Staff Report No 1052 (SSRN 4373434) | 인트라데이 event study 2017-2022. **BTC는 통화·거시 뉴스에 orthogonal**(타 미국 자산군과 달리) | 우리 ① "거시 full-sample 비유의"의 **가장 강한 동료 선례**(연준). 단 2017-2022 표본 = 2023+ 미포함 |
| P7 | Exploring the Predictability of Cryptocurrencies via Bayesian Hidden Markov Models | **2021**, Research in International Business and Finance (S0275531921001756, arXiv 2011.03741) ★저자 미확인 | 다중상태 HMM(BTC/ETH/Ripple). **regime-switching factor loadings**가 random-walk를 다수 케이스서 outperform. state-dependent 외생 예측변수 | regime마다 factor loading이 바뀌는 걸 **명시적으로 모델링** = 우리 부호반전(funding BTC/ETH)의 방법론 틀 |
| P8 | A Factor Model for Cryptocurrency Returns (risk-based explanation) | **Bianchi & Babiak** (Lancaster wp / SNB seminar 2023) ★저널화 미확인 | **IPCA**: factor beta **시간가변**, 자산 특성에 의존. Fear&Greed shock이 기대수익 변화(시변 behavioral) | "beta가 시변"의 직접 근거. full-sample 단일 beta 추정이 부적절하다는 방법론 정당화 |
| P9 | Crypto carry | **Schmeling, Schrimpf, Todorov**, BIS WP No 1087 (RePEc bis/biswps/1087) | crypto carry 때때로 **>40% p.a.**, 큰 **시간 변동**. 원인 = trend-chasing 소액투자자 레버리지 수요 + 제한된 차익자본(limits to arbitrage) | funding/carry가 risk-premium 아닌 **crowding/inconvenience yield** = 우리 ② "directional 부호 불안정"의 메커니즘 |
| P10 | (Crypto Carry Trade) | **Christin 외**, andrew.cmu.edu CarryTrade.v1.0 ★워킹페이퍼, 저널화 미확인 | crypto carry trade 미시구조·funding 차익 | P9 보완 |
| P11 | Conditional beta and uncertainty factor in cryptocurrency pricing | arXiv 2010.12736 ★저자 미확인 | macro 변수를 **uncertainty factor + 자산 특성**으로 치환한 조건부 모델 | conditional factor model의 crypto 적용 사례 |
| P12 | Markov and HMM for Regime Detection in Crypto Markets (BTC 2024-2026) | Preprints.org 202603.0831 ★프리프린트, 미동료심사 | BTC regime detection HMM (2024-2026) | 최신 표본 regime 식별 도구. ⚠️프리프린트 |
| P13 | Designing funding rates for perpetual futures | arXiv 2506.08573 (2025) ★저자 미확인 | perp funding 메커니즘 설계. 170 return predictor(basis/momentum/liquidity/size/vol) 중 63 유의 | funding 신호 zoo의 **다중비교 함정** 직접 노출 |
| P14 | Taming the Factor Zoo: A Test of New Factors | **Feng, Giglio, Xiu 2020**, J. of Finance (dachxiu ZOO.pdf) ✅(주식 일반) | 새 factor 검정 시 기존 zoo 통제. data-snooping 보정 후 다수 무유의 | regime-conditional 채택 시 multiple-testing 게이트의 표준 |
| P15 | (factor zoo / data snooping general) | Harvey-Liu-Zhu 계열, t>2.78 임계 ★일반 finance | data-snooping 보정 후 **anomaly 80% 무유의화** | 우리 subsample 유의를 채택하기 전 임계 상향 근거 |

> ⚠️ **산업/블로그 출처(non-peer-reviewed, 정량 인용 주의)**: Coinbase Institutional, VanEck(DXY-BTC corr 0.7→0.45), Onramp(M2 6-24M 강화), CF Benchmarks, K33(4년 사이클 사망), Amberdata. **BTC-M2 "0.9 correlation", "Liquidity Gate", "BTC-gold 92%"** 류 수치는 전부 산업 출처 → 동료심사 아님, 보고서 본문서 학술 결론과 분리.

---

## 주제 1 — 왜 crypto factor가 전기간 불안정한가

**문헌 합의: 불안정성은 결함이 아니라 시장의 구조적 속성이다.**

1. **효율성 자체가 시간가변(AMH)**. Noda(2019, arXiv 1904.09403)는 sample-size-독립 GLS 시변 모델로 BTC/ETH 효율성이 **시간에 따라 오르내림**을 보였고 AMH를 지지. Khuntia & Pattanayak(2018, Economics Letters)은 BTC predictability가 **등장-소멸을 반복**한다고 보고. → 효율적인 시기엔 어떤 signal도 죽고, 비효율 시기엔 살아난다. **full-sample 단일 verdict가 부적절**한 근본 이유.

2. **Structural break / market maturation**. 효율성 문헌(Wiley IJFE Li, Nature Sci Rep 2023, Financial Innovation 2023)은 event shock과 structural break가 효율성 급변을 일으키고, **break 반영 후 persistence가 줄어든다**고 보고. 시장 성숙(2014 초기 → 2020 기관화 → 2024 ETF)은 break의 연쇄.

3. **기관화 / ETF / 4년 halving 사이클(2020·2024 전후)**. ★이 부분은 **동료심사 부재**가 두드러진다 — "4년 사이클 사망" 논의는 전부 산업/뉴스(K33, Amberdata, CNBC). 공통 주장: 현물 ETF 유입(>$500M/day, 월 단위로 채굴 발행 초과)이 post-halving 가격발견을 front-run, BTC가 macro(인플레/금리)에 더 연동되는 high-beta risk asset으로 이행. **동료심사 증거로는 미성숙 → 우리 시스템서 halving 더미를 factor로 쓰기엔 근거 약함**.

4. **Beta 자체가 시간가변**. Bianchi & Babiak(IPCA)는 crypto factor beta가 시변·자산특성 의존임을 보였고, Fear&Greed shock이 기대수익을 바꾸는 **시변 behavioral factor**를 보고. → 단일 full-sample beta 추정은 misspecified.

**소결**: 우리가 본 "전기간 비유의 + subsample 유의"는 P1·P2·P5·P6·P8 전부와 정합. crypto에서 이건 **예외가 아니라 디폴트**. "전기간 일관성"을 채택 기준으로 쓰면 거의 모든 진짜 신호도 탈락한다.

---

## 주제 2 — Regime-Dependence를 다루는 방법론

| 방법 | crypto 적용 논문 | 우리 활용 함의 |
|---|---|---|
| **Markov / Hidden Markov regime-switching** | P7 (Bayesian HMM, RIBF 2021): regime-switching factor loading이 RW를 다수 outperform. P12 (HMM BTC 2024-26, 프리프린트) | factor loading을 regime별로 분리 추정. 부호반전(funding BTC/ETH)을 한 모델서 수용 |
| **Rolling-window factor estimation** | 효율성 문헌 다수(Noda GLS 시변, arXiv 1902.09253 dynamic) | 우리가 이미 쓰는 EWMA/rolling cov와 동형. full-sample 대신 시변 추정 |
| **Time-varying parameter (TVP) / conditional factor model** | P8 (IPCA), P11 (conditional beta + uncertainty factor) | beta = f(자산특성, regime). 정적 SEED beta의 시변 확장 후보 |
| **Structural break test (Bai-Perron 등)** | 효율성 문헌이 break 후 persistence 감소 보고 ★Bai-Perron crypto 직접적용 논문 이번 라운드 미확정 | subsample 경계를 **데이터가 결정**하게(2020 QE, 2022 긴축, 2024 ETF가 후보 break) |

**핵심**: regime을 다루는 정석은 (a) regime을 **ex-ante 관측가능 변수**(유동성 상태, 변동성 상태, F&G)로 정의하고 (b) 그 안에서 factor loading을 분리 추정하는 것. P7의 HMM, P8의 IPCA가 crypto서 이게 작동함을 보였다(RW 대비 개선).

---

## 주제 3 — Macro Liquidity(M2/global liquidity) ↔ BTC 관계의 regime shift

**문헌 상태: 시대 분기가 명확. 동료심사는 "old regime(2017-2022) = macro 무반응", 산업은 "new regime(2023+) = 강한 유동성 연동".**

- **Old regime 동료심사**: P6 Benigno & Rosa(NY Fed SR1052, 2023)는 인트라데이 event study(2017-2022)서 **BTC가 통화·거시 뉴스에 orthogonal**이라고 명시. P5 Liu-Tsyvinski(2021 RFS)도 macro factor 노출 거의 없음(null). → **2022 이전엔 BTC-macro 연결이 동료심사 수준서 거의 없었다.**
- **New regime 산업(비동료심사)**: Onramp/Coinbase/Canary는 2023+ 6-24M horizon서 M2-BTC 상관 강화, BTC가 high-beta 유동성 표현으로 이행, "digital gold ↔ risk asset" 사이를 regime별로 오감을 주장. ⚠️전부 산업 출처.
- **DXY**: VanEck(산업) DXY-BTC corr 2014-2020 ≈0.7 → 현 사이클 ≈0.45 약화. 극단 fear/euphoria서 상관 붕괴.

**판정 함의**: 동료심사 문헌은 우리의 ① "거시 full-sample 비유의"를 **강하게 지지**한다(연준 SR1052가 정확히 같은 결론, 같은 시대). 그러나 그 표본이 2017-2022이고, 우리가 본 subsample 신호는 **2023+** 에서 나온다 — 즉 **동료심사가 비유의라고 한 표본 이후에 새 regime이 출현했을 가능성**이 산업 데이터로 제기된 상태. 이건 "spurious"의 증거도, "regime shift"의 증거도 아닌 **시대 경계의 미확정 구간**이다.

---

## 주제 4 — Funding rate / Perpetual basis의 regime-conditional 사용

**문헌 합의: funding/carry는 directional predictor로 전기간 일관되지 않으며, 그게 정상이다 — carry는 risk-premium이 아니라 crowding/inconvenience yield이기 때문.**

- **P9 Schmeling-Schrimpf-Todorov "Crypto carry"(BIS WP 1087)**: crypto carry가 때때로 **>40% p.a.**, 큰 시간변동. 원인 = trend-chasing 소액투자자의 레버리지 수요 + 차익자본 제약(limits to arbitrage). → carry/funding은 **포지셔닝(crowding) 신호**지 안정적 위험프리미엄이 아니다. (MEMORY 기존 = 같은 trio Mgmt Sci 2024 "carry는 crowding 신호" 일치.)
- **P13 Designing funding rates(arXiv 2506.08573)**: 170개 return predictor(basis/momentum/liquidity/size/vol) 중 63개 유의 — **다중비교 미보정 시 funding zoo가 거짓양성 양산**.

**판정 함의**: funding이 **directional 부호로 H1↔H2 반전, BTC↔ETH 반전**한 우리 ②는 carry=crowding 해석과 정확히 정합. crowding은 레버리지 사이클(불장 롱과밀 → 양funding → 역추세 / 약장 숏과밀 → 음funding)에 따라 **부호가 regime-conditional로 뒤집히는 게 정상**. 따라서 funding은 **directional alpha가 아니라 regime/crowding 게이트 변수**로 써야 한다 — 우리 handoff의 "funding crowding 게이트형" 방향과 일치.

---

## 주제 5 — '전기간 비유의지만 특정 regime에서 유효' 신호의 정당한 채택·검증 (★핵심)

**문제: 어떻게 "가설이 죽었다"와 "regime-conditional로 살아있다"를 구별하는가?**

문헌이 제시하는 게이트 (전부 충족해야 "살아있다"로 채택):

1. **regime을 ex-ante로 식별 가능해야 한다**. regime을 사후(in-sample 수익률 보고)에 그으면 = **in-sample regime fishing = data snooping**. P7(HMM)·P8(IPCA)이 정당한 이유 = regime을 관측가능 상태변수(유동성/변동성/특성)로 ex-ante 정의. ⛔ "2023년부터 좋았다"처럼 **달력으로 자른 subsample은 ex-ante 아님** → 우리 M2 2023+ 가 정확히 이 함정.

2. **Multiple-testing 보정**. P14 Feng-Giglio-Xiu(2020 JF)·Harvey-Liu-Zhu 계열: data-snooping 보정(t>2.78 등) 후 anomaly **80%가 무유의화**. regime × factor × horizon 격자를 다 뒤지면 우연 유의가 쏟아진다 → Bonferroni/FDR 의무.

3. **Walk-forward OOS, parameter lock**. arXiv 2603.09219(IS/WFA/OOS 프로토콜)·2512.12924(walk-forward microstructure): regime을 ex-ante 식별한 룰을 **purge gap 둔 rolling window서 반복 증명**. regime-conditional Sharpe가 OOS 분기마다 부호 유지하는지.

4. **Conditional Sharpe / 부호 일관성**. regime 안에서 OOS 분기별 부호가 뒤집히면 = regime 정의가 noise 흡수. P15·우리 small-n rigor와 동형.

**문헌이 주는 균형**: arXiv 2511.12490("Drift Regimes Unlock Hidden Cross-Sectional Predictability")은 **올바르게 regime-conditioning하면 full-sample서 숨은 alpha가 OOS로 살아난다**는 긍정 사례(13-Sharpe 주장 ★프리프린트, 과대 의심) — 즉 regime-conditional 채택은 *원리적으로는* 정당하다. 단 그 문턱이 위 1-4. 문턱 없이는 "살아있다" 주장이 곧 overfit.

---

## 6. 우리 실측 대조 — verdict (논문 관점)

### ① 거시유동성 M2/real rate/DXY → BTC 6-24M (full 비유의, 2023+ M2 IC −0.6~−0.86)

**우리 기각("단일 상승사이클 spurious")은 — 절반 맞고 절반 성급.**

- **맞은 부분**: full-sample 비유의는 P5·P6(특히 연준 SR1052)가 **같은 시대 같은 결론**으로 강하게 지지. 그리고 2023+ subsample은 **달력 컷 = ex-ante regime 아님 + 단일 상승사이클 + 유효 n 작음 + overlapping 자기상관** → 주제5 게이트 1·2·3을 **전부 위반**. 이 상태의 −0.86을 "유효 신호"로 채택했다면 그게 오히려 in-sample regime fishing. **채택 보류는 정당.**
- **성급한 부분**: "spurious라서 기각(=영구 폐기)"은 과하다. 문헌(P1 AMH, 산업 new-regime, P6의 표본이 2022까지)은 **2023+에 BTC-거시 연동이 진짜 출현했을 가능성**을 열어둔다. 이건 "죽은 가설"이 아니라 **"regime shift 후보, 아직 검증 미달"**. → **rejected_permanent가 아니라 rejected_provisional**(재평가 트리거 = 데이터 누적 후 ex-ante 유동성 regime 정의 + walk-forward OOS)로 분류해야 문헌 관점과 정합.

### ② funding rate (H1 강 → H2 소멸, BTC/ETH 부호 반대)

**우리 "robust 아님" 기각은 정당, 단 "directional alpha"로서만. 신호 자체는 버리지 말 것.**

- P9(BIS carry)가 정확히 예측하는 패턴: carry=crowding이라 **directional 부호가 regime/레버리지 사이클 따라 반전**하는 게 정상. H1↔H2, BTC↔ETH 반전은 "robust 아님"의 증거이자 동시에 **"이건 directional이 아니라 crowding 게이트"라는 증거**.
- → **directional predictor로는 reject_provisional 옳음.** 그러나 **regime/crowding 게이트 변수**(극단 양funding = 롱과밀 = de-risk 신호)로는 살아있을 수 있음 → ledger에 "directional reject / gate candidate" 이중 라벨.

### ③ 단기 momentum (글로벌 소멸, Upbit 잔존)

**문헌과 완전 정합, 기각 아니라 "효율화 + 시장분절"로 정확.**

- P1·P2·P3(AMH 효율화) + Han-Kang-Ryu(net-of-cost 청산, MEMORY 기존)가 글로벌 소멸을 설명. Upbit 잔존 = 한국 자본통제로 차익 제약(P9의 limits-to-arbitrage와 동형 메커니즘) → 비효율 잔존. **이건 "신호 죽음"이 아니라 "효율화된 시장 vs 분절 시장"의 정상 차이.** Upbit momentum 채택 + 글로벌 미채택은 문헌적으로 옳은 분기.

---

## 7. 실행 권고 — regime-conditional 신호 채택 기준 (우리 시스템 적용)

**원칙: crypto factor instability는 디폴트다. "전기간 일관성"을 1차 채택 기준으로 쓰면 진짜 신호도 다 죽인다. 대신 아래 4게이트로 "regime-conditional 생존"을 판정한다.**

1. **regime을 ex-ante 관측변수로 정의 (달력 컷 금지)**. 유동성 상태(M2 yoy 부호 2개월 지속 등), 변동성 상태, F&G, 레버리지(funding) 상태로 regime 라벨 → 그 안에서 IC 측정. ⛔ "2023년부터"는 금지.
2. **multiple-testing 보정 의무** (regime × factor × horizon 격자 → Bonferroni/FDR, t-임계 상향). small-n rigor rule과 결합.
3. **walk-forward OOS + parameter lock + purge gap**. regime-conditional IC가 OOS 분기마다 부호 유지하는지(conditional Sharpe). 우리 falsification 사전등록(trailing OOS rank-IC K분기≤0 → prior 기각)과 직결.
4. **autocorr 보정** (overlapping forward return → Newey-West/block). 6-24M horizon은 유효 n이 작음을 명시.

**ledger 반영 (CLAUDE.md §지표 ledger 규칙 ⑤)**:
- **M2/거시유동성 → BTC 6-24M**: `candidate → rejected_provisional`. reason = "full-sample 비유의(P6 NY Fed SR1052 동일시대 orthogonal 지지). 2023+ IC −0.86은 달력컷=ex-ante regime 아님 + 단일사이클 + 유효n 작음 → in-sample fishing 위험. 영구폐기 아님(P1 AMH·new-regime 가능성)". 재평가 트리거 = data-event(데이터 누적) + ex-ante 유동성 regime 정의 + walk-forward OOS. research_ref = 본 파일 주제3·6①.
- **funding rate (directional)**: `rejected_provisional`. reason = "directional 부호 H1↔H2/BTC↔ETH 반전 = P9 BIS carry crowding 해석과 정합(robust 아님)". **별 행으로 `funding crowding gate: candidate`** = "극단 funding = crowding de-risk 게이트 후보". research_ref = 주제4·6②.
- **단기 momentum**: Upbit `adopted`(분절시장 비효율 잔존, P9 limits-to-arb) / 글로벌 `rejected_provisional`(효율화, P1-P3 AMH + Han-Kang-Ryu). reason에 "효율화 = 시장분절 차이지 신호 자체 사망 아님". research_ref = 주제1·6③.

---

## 8. 미확인 / 후속 검증 필요 (환각 방지)

- ★Bai-Perron 등 **structural break test를 crypto factor에 직접 적용한 단일 동료심사 논문**은 이번 라운드서 확정 못 함(효율성 break 문헌은 있으나 factor 대상 직접은 미확정).
- ★ETF/halving 4년사이클 break = **전부 산업/뉴스, 동료심사 부재**. factor로 쓰기엔 근거 약함.
- ★P8 Bianchi-Babiak 저널화 여부, P2 Khuntia-Pattanayak 정량 magnitude, P7/P11/P13 저자명 = 미확인(metadata만 교차확인).
- ★산업 출처 수치(M2 0.9 corr, BTC-gold 92%, DXY 0.7→0.45)는 본문 결론서 분리 — 동료심사 아님.
- 본 파일은 자매 파일 [crypto-factor-papers.md](crypto-factor-papers.md)(factor 선택)와 상보 — 이쪽은 time-variation/regime 전담.
