---
tags: [research, crypto, macro, volatility, spillover, papers]
date: 2026-06-03
type: reference
source: WebSearch/WebFetch native (2026-06-03), raw archive ~/.claude/docs/archive/research-raw/macro-vol-transfer-native-20260603.txt
verification: 핵심 논문 metadata는 다중 WebSearch 교차확인 + 저자 검색검증(IMF WP 저자 자기정정 1건). SSRN/IMF PDF는 WebFetch 403 → 검색 snippet + RePEc/저널 페이지 교차확인. 불확실 항목은 ★미확인 표기.
---

# 거시 변동성 전이 (VIX·MOVE → crypto vol) — 학술 문헌 / 우리 실측 대조

> 대상 지표: **coin_macro_vol_transfer** (거시 implied vol → BTC/crypto 변동성 전이/spillover).
> 6단계 SOP **S1(논문 ground)** 산출. 메커니즘 → 시대성 → regime 의존 3계층 정초.
> **대조 기준(우리 기존 실측·자산화)**: ① 거시 study에서 **MOVE가 VIX에 joint β→0로 흡수**(univariate β us −0.213 → 8-factor multivariate 붕괴, VIF≈1.26, VIX가 risk-off 분산 완전흡수) ② Benigno-Rosa SR1052 = 2017-22 BTC macro orthogonal ③ 2023+ BTC-DXY −0.4~−0.8 출현(기관화) ④ crypto factor instability = norm(AMH·시변 β) ⑤ 거시 신호는 sizing alpha 아닌 throttle overlay.

---

## 계층 1 — 메커니즘 (거시 vol → crypto vol 전이 경로)

| 논문 | 저자·연도·출처 | 표본기간·방법 | 핵심 발견 | 우리 적용 |
|---|---|---|---|---|
| **Volatility Transmission to Bitcoin: The Role of VIX Term Structure and Crypto Options Markets** | Luo, Tsai, Yen — SSRN 6233752 (2025/2026 working) ★metadata 검색확인, 본문 SSRN 403 | ★표본 미확인(2024 ETF 전후 포함), BTC IV/realized + VIX term structure | **★최온타겟**. BTC가 VIX·crypto-IV에 **전 만기에서 강한 음(−) 반응**. **VIX slope(term-structure) factor가 level보다 우월한 설명력**. Jan 2024 spot ETF 후 **BTC가 자기 IV에 대한 민감도는 약화, VIX에 대한 반응은 불변** → ETF 기관화가 내부 risk dynamics만 바꾸고 equity-vol 동조는 안 깸 | S2 직접 후보: VIX **level vs slope** 비교 + BTC vol 전이. ETF 전후 epoch split의 학술 근거 |
| **New Evidence on Spillovers Between Crypto Assets and Financial Markets** | **Iyer, Popescu** — IMF WP 2023/213 ✅저자 검색검증 | 대표 crypto+금융자산 set, **연결성(connectedness, Diebold-Yilmaz류) 시변** | 스필오버 magnitude가 **turbulence(부정 뉴스·crypto 이벤트·외생 충격) 시 증가**. **risk-off 시 상관 상승** → crypto가 금융시장 충격의 **전도체**. 평시엔 crypto→금융 전이 우세, **financial stress 시 방향 역전**(treasuries가 BTC로 vol 전이하는 국면 존재) | 전이가 **비대칭·국면 의존**임을 명시 — full-sample 상쇄 위험의 근거(계층3) |
| **Return and volatility spillover drivers among conventional cryptocurrencies** | Digital Finance 2025 (DOI 10.1007/s42521-025-00167-y) ★발견만 | 동적 연결성 + 드라이버 회귀 | **VIX·GPR(지정학)이 연결성 amplify**, **EPU·Fear&Greed는 weaken**. BTC/ETH가 main transmitter | VIX = crypto vol 시스템 amplifier 드라이버. driver 분리 시 VIX 부호 양(연결성↑) |
| **Tail spillover effects between cryptocurrencies and uncertainty in gold, oil, stock markets** | Financial Innovation 2023 (DOI 10.1186/s40854-023-00498-y) ★발견만 | quantile/tail 스필오버 | crypto↔불확실성 전이가 **tail(극단)에서 강화** | tail-conditional 전이 = 계층3 regime 의존 보강 |

**소결 (메커니즘)**: 경로는 **risk-off 자금흐름 + 레버리지 청산 + 유동성 동조**로 정리. VIX 충격 → BTC 음(−)반응(가격↓·vol↑)이 문헌 합의. ★핵심 = **VIX level보다 slope/term-structure가 우월**(Luo-Tsai-Yen) — 우리가 거시 study에서 VIX level만 쓴 것과 긴장(S2 검정 포인트). IMF(Iyer-Popescu)는 방향이 **국면 역전**(평시 crypto→금융, stress 시 금융→crypto)이라 단순 "거시→crypto 일방 전이" prior는 부적격.

---

## 계층 2 — 시대성 (epoch-dependence: 고립 → risk asset 전환)

| 논문 | 저자·연도·출처 | 표본기간·방법 | 핵심 발견 | 우리 적용 |
|---|---|---|---|---|
| **The Bitcoin–Macro Disconnect** | **Benigno, Rosa** — NY Fed Staff Report 1052 (2023), SSRN 4373434 ✅verified | **2017–2022**, intraday **event study**(거시 뉴스 announcement) | BTC는 **타 US 자산군과 달리 통화·거시 뉴스에 orthogonal**(반응 거의 없음). discount-rate 충격조차 BTC 가격에 안 잡힘 | **★시대 anchor**. 우리 "초기 epoch macro-null"의 동료심사 근거. 단 표본 2017-22 = ETF 전, **2023+ 반증 대조 의무** |
| **Institutional Adoption and Correlation Dynamics: Bitcoin's ...** | arXiv 2501.09911 (2025) ★발견만, 비-저널 working | 2020~2025, 상관 동학 | 2020 이후 기관화(BlackRock IBIT·Fidelity·spot ETF)가 BTC를 **equity와 같은 유동성 풀로 편입**. 2020-21 risk-on 시 BTC-SP500 **corr >0.8 빈번**, 2022 긴축서 일시 약화 후 반등, **Jan 2024 spot ETF 후 corr 유의 상승** | **★반증 대조**. Benigno-Rosa null의 시대 한정성 입증. 우리 "2023+ 동조 강화" framing 지지 |
| **The Crypto Cycle and US Monetary Policy** | IMF WP 2023/163 ★발견만(검색 노출) | ★미확인, 통화정책-crypto 사이클 | crypto 사이클이 US 통화정책과 연동(완화/긴축 cycle) | 거시 유동성 epoch 연동 보조 근거(★본문 미확인) |
| (시장 일화 마커, **비-동료심사**) | CoinDesk 2024-04-22 / arXiv 2501.09911 인용 | — | 2025-11 BTC −16.9% vs SP500/Nasdaq 상승 = **2014 이후 첫 반대 방향**(decoupling 일화) | 동조가 **상수 아닌 시변** 경고(점추정 박제 금지). 일화 1건은 prior 아님 |

**소결 (시대성)**: VIX/거시-crypto 전이는 **명백히 epoch-dependent**. 2017-22(Benigno-Rosa, orthogonal) ↔ 2020-21·2023+(기관화, corr↑·spot ETF 후 강화)가 정면 대조. ★Luo-Tsai-Yen의 "ETF 후 VIX 반응 불변"이 결정적 — **기관화가 자기 IV 민감도는 바꿔도 VIX 동조 채널은 유지**. 따라서 우리 S2는 **ex-ante epoch split(pre-2020 / 2020-2023 / post-ETF 2024+)** 필수, full-sample 단일 β 박제 금지.

---

## 계층 3 — regime 의존 (비대칭·비선형, full-sample 상쇄)

| 논문 | 저자·연도·출처 | 표본기간·방법 | 핵심 발견 | 우리 적용 |
|---|---|---|---|---|
| **A Quantile Spillover-Driven Markov Switching Model for Volatility Forecasting** | MDPI Mathematics 13(15):2382 (2025) ★발견만 | crypto, **Markov regime-switching + 분위수 스필오버** | 분위수별 스필오버를 regime-switching realized-vol 모델에 통합 → **국면별 이질적 전이 경로** 포착, vol forecast 개선 | **★직접 방법론 템플릿**. 전이가 regime별 다름을 명시 — full-sample β로는 못 잡음 |
| **Regime switching and causal network analysis of cryptocurrency volatility (pre/post-COVID)** | Springer Digital Finance 6(2), DOI 10.1007/s42521-023-00104-x ★발견만 | pre-COVID vs post-COVID split | vol 인과 네트워크가 **COVID 전후 구조 전환** | epoch×regime 결합 — pre/post 구조변화 |
| **Quantifying spillovers among commodities and cryptocurrencies: Quantile-VAR** | ScienceDirect S2405851324000047 ★발견만 | Quantile-VAR | **비대칭 스필오버**: 위기 시 bad news가 더 빠르고 넓게(TCI가 COVID·러우전쟁서 급등) | high-vol regime에서만 전이 강 = 비대칭. full-sample 희석 경고 |
| **DCC-GJR-GARCH high-freq crypto vol spillover** | Stejskalova, Krampla — SSRN 4743502 ★발견만 | 고빈도, DCC-GJR-GARCH | **비대칭 충격(leverage) 반영** 동적 상관 | GARCH-DCC 계열 = 우리 RegimeGlasso/cov 추정과 호환 비교군 |

**소결 (regime)**: 전이는 **risk-off/high-vol regime에서만 강하고 비대칭**(bad news 가속). full-sample IID 회귀는 평시 무전이 구간이 위기 구간을 희석 → β 과소·부호 불안정. 이것이 우리 study에서 **MOVE β가 multivariate에서 0으로 붕괴**한 한 원인일 수 있음(전이가 risk-off 국면 한정인데 full-sample 측정). 따라서 S2는 **regime-conditional(VIX 분위/risk-off 더미) 측정 + Markov-switching 또는 quantile** 가 1차 단위, full-sample은 보조.

---

## 핵심 질문 답변

**Q1. VIX vs MOVE — 어느 것이 crypto vol 예측에 우월? 흡수 관계?**
- 문헌 직접 비교는 희소. **VIX 쪽 증거가 압도적으로 두텁다**(Luo-Tsai-Yen, IMF Iyer-Popescu, Digital Finance 2025 전부 VIX/equity-vol 채널 중심). MOVE(국채 vol)는 IMF가 "treasuries가 BTC로 vol 전이하는 **국면이 존재**" 정도로만 언급 — 일관·robust한 독립 MOVE→crypto 채널의 동료심사 근거는 ★이번 라운드 확인 못 함.
- ★우리 거시 study 실측(MOVE univariate β us −0.213 → 8-factor multivariate **β→0 흡수**, VIX가 risk-off 분산 완전흡수)과 **문헌 방향 일치**: crypto vol 전이의 주채널은 **equity-vol(VIX)**, MOVE는 대체로 VIX에 흡수. → **S2 가설: crypto서도 MOVE는 VIX에 joint β→0로 흡수**(거시 study 전례 재현 예상). 단, 금리 tantrum/국채 stress 특정 regime에선 MOVE 잔여 가능성(IMF) → regime-conditional에서만 falsify.
- ★주의(Luo-Tsai-Yen): VIX **slope > level**. 우리 거시 study가 VIX level만 썼다면, MOVE 흡수 결론은 **VIX slope 미통제** 상태일 수 있음 — slope 추가 후 MOVE 잔여가 더 줄거나, 반대로 MOVE가 slope의 proxy였을 가능성 양쪽 검증 필요.

**Q2. lead-lag — VIX/MOVE가 BTC vol을 선행(예측)? 동시적?**
- IMF·spillover 문헌의 connectedness는 주로 **동시적(contemporaneous) 전이** 측정. **순수 예측(선행) 우월성**은 vol-forecasting 문헌(Kambouroudis 2021 JFM: "IV가 RV의 강한 예측자, HAR에 VIX 넣으면 RV forecast 개선")이 간접 지지 — 단 이건 자산 자기 IV→자기 RV이지 cross-asset VIX→BTC RV 선행을 직접 입증한 건 아님.
- ★정직한 prior: **동시적 전이 증거 강 / cross-asset 선행 예측 증거 약**. S2에서 **contemporaneous vs lagged(1d/5d) 분리 측정** 의무 — 선행성을 박제하면 spec/code drift 위험.

**Q3. crypto vol 측정 — realized vs implied(DVOL)?**
- 문헌 양쪽 다. **realized vol**(GARCH/HAR/실현변동성)이 spillover·forecasting 주류, **DVOL**(Deribit BTC 30d implied, VIX 방법론 차용)이 implied 측정 표준. Luo-Tsai-Yen은 BTC IV(옵션) + realized 둘 다 사용 정황.
- ★우리 적용: **realized vol(일봉/intraday 실현변동성)을 1차 종속변수**로 권고(데이터 무료·연속). DVOL은 2021+만 가용(Deribit) + 게이트 가능성 → 보조. ★MEMORY 정정 주의: SOPR/realized-cap류는 CM 유료게이트였음 — DVOL도 가용성 사전검증 의무(empirical-claim §1.1-ext).

---

## 우리 실측 대조 포인트 (S2 검정 가설로 번역)

> ⚠️ small-n rigor: 아래는 *후보 가설*. 채택 전 4게이트(G1 ex-ante regime / G2 Bonferroni→FDR / G3 walk-forward OOS / G4 Newey-West HAC) + epoch split 의무. 점추정 박제 금지, hedge 어휘.

1. **[주가설] VIX → BTC realized-vol 양(+)전이, regime-conditional.** falsifier: risk-off regime(VIX 상위 분위) 한정 BTC fwd realized-vol에 VIX β 유의(HAC), full-sample은 희석으로 약화 예상. epoch split(pre-2020/2020-23/post-ETF 2024+)서 post-ETF 구간 β 강화 확인(기관화).
2. **[흡수 검정] MOVE는 VIX에 joint β→0 흡수(거시 study 전례 재현).** falsifier: VIX+MOVE 동시 회귀서 MOVE β CI가 0 포함 + VIF로 collinearity 확인. ★단 **VIX slope/level 둘 다 통제** 후 측정(Luo-Tsai-Yen) — slope 미통제 시 MOVE가 slope proxy일 위험. 국채 tantrum regime에서만 MOVE 잔여 별도 falsify.
3. **[lead-lag] contemporaneous 전이 강 / 선행 예측 약.** falsifier: lag 0 vs lag 1d/5d 분리, 선행 β가 동시 β보다 작으면 "예측"이 아닌 "동조"로 라벨(spec 정합).
4. **[epoch] Benigno-Rosa null(2017-22) ↔ post-ETF 동조 반전.** falsifier: 달력 split이 아닌 ex-ante regime/이벤트(ETF 승인 2024-01) 마커로 구조변화 검정 — data-snooping 회피(MEMORY: 2023+ −0.86 달력컷은 ex-ante 아님 → rejected_provisional 전례).
5. **[측정축] realized vol 1차, DVOL 보조(가용성 사전검증).** DVOL 2021+ Deribit 게이트 여부 확인 후 사용.

★throttle overlay 위치: 거시 vol 전이는 **sizing alpha 아닌 risk throttle**(de-risk 타이밍)로만 — VIX spike → crypto vol↑ 예상 시 gross 축소. directional 가격 예측 아님(crypto 단기 가격신호=BTC momentum 1개로 수축 확정, 별 트랙).

---

## 환각 검증 메모
- ✅ verified(저자·venue 검색 교차확인): Benigno-Rosa "Bitcoin-Macro Disconnect" NY Fed SR1052 / SSRN 4373434 (2017-22 intraday event study). IMF WP 2023/213 저자 = **Iyer, Popescu**(처음 추정 저자명 오류 → 검색 정정, 날조 회피).
- ★metadata 검색확인·본문 미확인(SSRN/IMF PDF WebFetch 403): Luo-Tsai-Yen SSRN 6233752(제목·핵심발견은 검색 snippet, 표본기간 ★미확인) / Digital Finance 2025 / Financial Innovation 2023 / MDPI Mathematics 2382 / Springer Digital Finance pre-post COVID / Quantile-VAR / DCC-GJR-GARCH SSRN 4743502 / Kambouroudis 2021 JFM. 인용 시 본문 재확인 권장.
- ★비-동료심사(prior 아님, 배경만): arXiv 2501.09911 institutional correlation / CoinDesk 2024-04 / 2025-11 decoupling 일화 / IMF WP 2023/163(검색 노출만).
- ★MOVE→crypto 독립 robust 채널 = 이번 라운드 동료심사 직접 근거 못 찾음 → "VIX 우세, MOVE는 국면 한정 가능성"으로 hedge 보고(우리 거시 흡수 실측과 정합).
