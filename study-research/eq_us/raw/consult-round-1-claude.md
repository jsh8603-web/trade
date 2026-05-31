---
tags: [type/consult-raw, domain/inv, study/eq_us, phase/3-R1, channel/claude-web]
date: 2026-05-31
study_id: eq_us
round: 1
channel: claude-web basic (Opus 4.8 High, fresh session)
brief: raw/consult-round-1-brief-claude-v2.md (DIRECT ANSWER MODE 헤더)
session_url: https://claude.ai/chat/66186a5b-c780-41af-9aa2-41ce73b510ba
response_chars: 14765
note: 첫 시도 (v1 brief, 219 chars thinking-only) → v2 brief (DIRECT ANSWER MODE 명시) 재전송 성공
---

# Claude R1 응답 (eq_us Phase 3, Opus 4.8 High fresh)

> 두괄식 + 총괄 표 + 10 Q × 5 필드 (답변·근거·정량·반증·confound). tentative 라벨 정직. R2 권고 3 자체 제시.

## 총괄 표

| Q | Headline 결론 | confound |
|---|---|---|
| Q1 | GICS 11 Tier 는 기술 (데이터·ETF) 레이어로만 유효, 가중 레이어는 macro/factor 구조 필요. ★Mag7 이 3 GICS 로 파편화 (XLK/XLC/XLY) 되어 시총 Tier 가 집중 risk 격리 못 함 | medium |
| Q2 | 1) earnings revision breadth 2) total shareholder yield 3) HY OAS regime. Fed path·AI capex 는 base driver 아닌 regime conditioner | med-high |
| Q3 | ★cyclical dollar 우위 = 2022-24 긴축·강달러 collinearity artifact. defensive rate-direct = sub-sleeve 기계적 구조 (구조적). default = 2-channel (rate-duration + dollar), dollar weight 는 ρ(Δrate,Δdollar) 조건부 | high |
| Q4 | 5 archetype 골격 OK, 단 XLF·XLV 가 부호 반대 mech 혼재 → XLF 4분할, biotech/payments 는 defensive 에서 누출 | medium |
| Q5 | ★(a)격리+(b)factor-neutral+(c)cap 조합. ★(d) capex>30% regime weight-up 금지 (reflexive trap) | high |
| Q6 | (b) 분리 (eq_us=GICS 10), REIT study 출력은 exogenous prior 로만 수용. 중복 금지 | low-med |
| Q7 | ★EDGAR 는 filer 등급별 마감 (대형 60d/40d). flat 45/90 = 비-accelerated case. 실무는 filing timestamp 사용. OSS-only PIT = 펀더멘털 yes, survivorship-free 가격은 무료론 불충분 | medium |
| Q8 | 현 stack 정답 backbone. + Ken French FF5+Mom, QMJ, BAB 를 neutralize 대상으로, alphalens 추가 | low |
| Q9 | 핵심 가설 7개 초안 (반증조건 포함) | medium |
| Q10 | 2021-24 = 긴축×강달러×AI capex 삼중 collinear regime → 채널 분리 불가가 최대 confound | high |

## Q1. GICS 11 Tier 차등 분류 적합성

**답변**: Tier 분류는 데이터 수집·ETF 매핑·관측 레이어로는 적합하지만, 가중 (wᵢ) 레이어로는 **부적합**. 결정적 결함: **Mag7 이 GICS 상 3개 섹터로 파편화** (Apple/MSFT/NVDA → XLK, Alphabet/Meta → XLC, Amazon/Tesla → XLY/Consumer Disc). 즉 "시총 50% T1 = XLK+XLC" 라는 전제 자체가 **2018 GICS 재분류로 깨짐** — 집중 risk 가 T1 에 격리되지 않고 Consumer Disc (T2) 로 새어나감.

사용자 측정 (within-cyclical mean corr 0.617, Kish eff_N 1.47) 이 보여주듯 GICS 11 은 11 개 독립 bet 이 아니라 사실상 **3-5 macro 축**. GICS 는 business-model 분류이지 return-driver homogeneity 분류 아님.

**권고**: 하이브리드. 관측·collection = GICS 11 (ETF·Damodaran 매핑 깔끔), 가중 = alt (c) 변형 — **Mag7/concentration sleeve 격리 + 나머지 macro-channel 그룹핑**.

**근거**: GICS Methodology (MSCI/S&P, 2018 Comm Services 신설) [tentative 연도]; sector return PCA 3-4 PC 로 cross-sectional 분산 70-85% 설명 = 표준 실무 결과 [tentative]; 1차: SPDR 섹터 ETF 구성, 사용자 M3 corr 측정치.

**정량**: within-cyclical mean corr 0.617 → eff_N 1.47 (사용자 실측). 80% 분산 PC 수 ≤5 가정 (반증대상). Mag7 ~30-35% S&P cap [tentative].

**반증조건**: PCA on 11 sector returns 가 80% 분산에 >7 PC 필요 → "GICS≈독립" 가설 부분 인정, Tier 가중 정당화.

**confound**: medium — 시총분포 time-varying, Mag7 cross-sector 파편화 구조적 잡음.

## Q2. 미국 alpha driver 1-3 순위

**답변**: cross-sectional 종목/섹터 alpha 시스템 (시장 타이밍 아님) 기준 순위:
1. **Earnings revision breadth** — US 에서 가장 문서화·안정적인 cross-sectional alpha (revision momentum, PEAD). 한국 외국인 net buy 의 가장 가까운 지속적 flow-유사 대응물
2. **Total shareholder yield (buyback+div)** — buyback 은 한국 대비 US 특유 feature. value/quality 하이브리드. 단 저회전 = regime signal 아니라 전략 tilt
3. **HY OAS regime** — risk-on/off·cyclical-defensive rotation 최강 분류기. 신용 spread 가 주식 선행. 단 regime conditioner 이지 종목 selector 자체 아님

**Fed funds path (a) · AI capex (b) = base driver 아니라 regime conditioner**. Fed path 의 cross-sectional alpha = OIS 가격화 후 surprise 성분만 episodic alpha. AI capex 는 IC 높으나 regime-unstable·reflexive·실질 single-factor 집중 bet → rule #1 위반 위험.

**근거**: Chan-Jegadeesh-Lakonishok 1996 JF (momentum/revision); Stickel 1991 (analyst revision) [tentative]; Boudoukh-Michaely-Richardson-Roberts 2007 JF "payout yield"; McLean-Pontiff 2016 JF (factor decay). 1차: I/B/E/S revision, FRED BAMLH0A0HYM2, EDGAR buyback (10-Q cash flow).

**정량**: revision breadth monthly IC ~+0.03~0.06 (비교적 안정) [tentative]; net payout yield L/S premium 역사적 ~2-4%/yr, post-2010 t-stat 약화 (decay); HY OAS +100bps/Q 확대 → cyclical 음 (방향 robust, magnitude regime 의존).

**confound**: med-high — crowding/decay (McLean-Pontiff: 출판 후 alpha ~58% 감소 [tentative]).

## Q3. cyclical (dollar) vs defensive (real rate) reconcile

**답변**:
- (a) cyclical β_dxy 우위는 상당 부분 **표본 한정**. 2022-2024 = 40년래 최속 긴축으로 rate ↔ dollar 거의 collinear (rate↑→dollar↑). 이 window 에서 dollar 가 multicollinearity 를 통해 rate 의 분산을 "먹은" 것이지 rate 무관 아님. **epoch R² decay (긴축 0.21→완화 0.07)가 결정적 tell** — collinearity 가 깨지는 완화 epoch (E4) 에서 dollar 설명력이 0.07 로 붕괴. 따라서 dollar 채널은 구조 상수 아니라 **긴축-regime artifact**.
- (b) defensive 의 real-rate-direct = sub-sleeve 기계적이고 구조적. bank = asset-sensitive 대차대조표 → NIM 부호 +; utility/REIT = bond-proxy (DCF duration + 배당 의 Treasury 경쟁) 부호 −. cash-flow-mechanical → 부호 regime 무관 (magnitude 만 가변).
- (c) **통합 sleeve default = 2-channel 모델**. ① real-rate/duration 채널 (부호 sub-sleeve 별: bank +, utility/REIT/long-duration-growth −) ② dollar/global-revenue 채널 (고-해외매출 multinational −, 국내·commodity exporter +). 핵심: **dollar 채널 weight 를 ρ(Δrate,Δdollar) 조건부로** — 高 collinearity (긴축) 시 dollar term 축소 (double-count 방지), 低 collinearity (완화·divergence) 시 dollar 독립 허용.

**근거**: Newey-West 1987 (collinear regressor SE); multicollinearity → β 귀인 불안정 = 표준 econometrics. 1차: FRED DGS10·DFII10·DTWEXBGS·BAMLH0A0HYM2; 사용자 M3 epoch R².

**정량**: β_dxy cyclical −0.58~−1.62, β_us10y ≈ 0 (사용자); ρ(ΔDXY,ΔUS10y) 2022-24 ~0.7-0.8 on changes [tentative] = collinearity 원인. bank rate-beta +0.3~0.8 / utility −0.3~0.8 [tentative].

**반증조건**: Q9 H4·H5.

**confound**: high — 표본기간 confound 정통 사례. **2015-2019 (dollar·rate decoupled) sub-sample 재검 강력 권고**.

## Q4. 5 archetype → GICS 11 매핑·sub-sleeve

**답변**: 5-archetype 골격 타당하나 XLF·XLV 가 부호 반대 mechanism 혼재가 문제. **XLF 최소 3분할 필요**:
1. lending-rate-sensitive (은행 + 생보, rate/curve +)
2. market-beta (asset manager, AUM·equity beta +, rate 중립)
3. payments (Visa/MC) = quality-growth (소비·결제량 play, rate 무감 → financials 아니라 quality 클러스터로 이동)

즉 XLF → staples 식 "방어" 가정 깨짐.

**XLV sub**: pharma (방어·patent-cliff idiosyncratic), biotech (고-duration, rate-sensitive, growth-유사 → defensive 에서 누출), medical device (quality-growth), managed care/HMO (정책·규제 idiosyncratic). 즉 biotech 도 방어 sleeve 에서 샘.

**T1 sub-cluster** (AI semis/hyperscaler/software) = GICS 축 아니라 growth-duration 축으로 모델링: ① 반도체 = 고-duration cyclical-growth + capex-cycle ② hyperscaler = AI-capex 지출자 (capex = 비용 → margin risk) ③ software/platform = AI-capex 수혜/피교란. 확립된 factor 없어 가장 가까운 baseline = equity-duration 문헌.

**근거**: Damodaran industry classification (Bank/Insurance Life·P&C/Asset Mgmt 분리) [tentative]; Weber 2018 JFE "cash flow duration & term structure of equity returns" [tentative 연도]; Gormsen-Lazarus equity yield [tentative]. 1차: GICS sub-industry, EDGAR SIC.

**정량**: SOXX epoch swing −50%→+89% (사용자); biotech rate-beta ~−0.5~−1.0 (고-duration) [tentative]; bank vs utility 부호 반대 (사용자).

**반증조건**: Q9 H5.

**confound**: medium — XLF 4분할·XLV sub 분할 시 cell N 급감 → rule #5 (N<24 유의 주장 금지) 주의.

## Q5. Mag7 / AI capex reflexive loop

**답변**: **(a) + (b) + (c) 조합 채택, ★(d) 명시적 기각**. (d) capex yoy>30% regime 에서 Mag7 weight 상승은 **reflexive trap 그 자체** — 군집·crowded trade 에 procyclical momentum 을 거는 것이라, unwind risk (2024-08 엔 캐리 mini-crash) 가 최고일 때 weight 기계적으로 올림.

**방어 가능 아키텍처**:
1. (a) Mag7 격리 sleeve — 나머지 493 종목 cross-sectional IC 오염 방지 (Mag7 dominance 시 회귀의 "tech beta" 는 사실 Mag7 idiosyncratic 가장무도회)
2. (b) factor-neutral (toraniko 로 market+size+Mag7-concentration factor regress-out 후 residual IC) — sector signal 이 진짜 alpha 인지 concentration beta 인지 분리
3. (c) per-ticker shrinkage cap 0.2 — eff_N 붕괴 방지 hard cap
4. ★**reflexivity monitor** — intra-Mag7 mean corr ↑ AND breadth 협소화 동시 발생 = cascade-risk regime → concentration exposure **축소** ((d) 의 정반대)

**근거**: Soros reflexivity (General Theory of Reflexivity); toraniko characteristic-based neutralization (OSS); concentration → eff_N 붕괴 = Kish 공식. 1차: FRED VIXCLS (2024-08 spike), Mag7 capex (10-Q), index weight (S&P 공시).

**정량**: Mag7 ~30-35% S&P cap [tentative]; 2024-08-05 VIX 장중 ~65 [tentative]; shrinkage cap 0.2 = eff_N target 기준 calibrate 필요.

**confound**: high — US 최대 구조 risk, concentration regime non-stationary.

## Q6. Real Estate XLRE vs REIT study 중복

**답변**: **(b) 분리** — eq_us = GICS 10 (Real Estate 제외), 기존 REIT study 출력은 **exogenous prior/regressor 로만 수용** (partial-corr dedup 명시). XLRE 를 Tier 3 native sleeve 로 넣으면서 REIT partial-corr 도 끌어오면 동일 exposure 이중 계상 → 외견상 독립성·eff_N 과장 (rule 위반). REIT study H1 REJECT 이력 자체가 정보 — naive REIT alpha 가 생존 못 했다 → 약/zero prior import 적절 (강 sleeve 금지). 또 XLRE 의 duration/bond-proxy 정보는 XLU (utility) 와 heavily overlap → rate-duration 채널은 이미 포착. XLRE ~2-3% 비중이라 제외 cost 미미.

**근거**: 사용자 REIT study (H1 REJECT) 내부 이력; REIT-utility 둘 다 bond proxy 상관 ~0.5-0.7 [tentative]. 1차: XLRE/XLU SPDR holdings, FRED DFII10.

**정량**: XLRE ~2-3% S&P weight [tentative]; REIT-utility corr 0.5-0.7 [tentative].

**반증조건**: REIT study 산출 signal 을 eq_us regressor 로 넣었을 때 incremental R² 가 utility 대비 유의 (ΔR² CI 하한 >0) → 단순 중복 아님, 별도 채널 정당화.

**confound**: low-med — 주로 system hygiene/dedup, 데이터 risk 낮음.

## Q7. PIT/lookahead 미국 인프라

**답변**: ★**EDGAR 마감 = filer 등급별 차등 → 45/90 flat 는 부정확**.
- Large accelerated filer (S&P 500 대부분): **10-K 60d, 10-Q 40d**
- Accelerated: 10-K 75d, 10-Q 40d
- Non-accelerated (최소): **10-K 90d, 10-Q 45d** — 사용자 45/90 = 이 최소 filer case

가장 robust PIT rule = **실제 EDGAR filing acceptance timestamp 사용** (가정 불필요, 진짜 point-in-time).

**OSS-only PIT universe**: 펀더멘털은 yes, survivorship-free 가격은 무료론 **불충분**. yfinance 단독 = survivorship-biased (delisted 누락). EDGAR XBRL + SEC Financial Statement Datasets = filing date 포함 PIT 펀더멘털 OK. 그러나 delisted-inclusive 가격은 **Sharadar (SEP/SF1, 유료지만 저렴, survivorship-free)** 가 실무 답. Norgate 유료. FinanceDatabase = 메타데이터지 PIT universe 아님. 결론: 무료 OSS 만으로 partial (펀더멘털 PIT 가능, 가격 survivorship-free 불가 → bias 명시 의무).

**근거**: SEC filing deadline 규정 (Exchange Act Rule, accelerated filer 정의) — regulatory fact, 확신도 중상 [verify 권장]; survivorship literature (backtest 과대 ~1-4%/yr) [tentative]. 1차: EDGAR full-text/submissions API, ALFRED vintage (yes).

**정량**: 마감: 대형 60d/40d. survivorship bias backtest 과대 ~1-2%/yr (주식), 분포 sleeve 는 더 큼 (은행 2023 SVB 사례) [tentative].

**confound**: medium — survivorship = 정통 backtest killer, 데이터 소스 선택이 결과 좌우.

## Q8. Validate 인프라 OSS

**답변**: 현 stack (skfolio CombinatorialPurgedKFold + toraniko + Newey-West HAC + block bootstrap) = **정답 backbone**. 추가 필수:
- **Ken French FF5+Mom** (pandas-datareader/French data lib) — 모든 alpha 를 FF5+Mom residual intercept 로 보고 = "진짜 alpha 인가" 표준 test
- **QMJ·BAB 추가** (quality·low-beta) — shareholder-yield·defensive sleeve 가 QMJ/BAB 에 heavy load → alpha 가 그냥 quality/low-vol 재포장인지 확인용
- **alphalens** — IC tearsheet (decile spread, IC decay, turnover) 권고
- pyportfolioopt — MVO/Black-Litterman 필요할 때만, scoring 시스템엔 부차적

**핵심 방법론 move** (rule #1·#4 준수): 각 sleeve alpha = FF5+Mom+QMJ+BAB time-series 회귀 intercept, NW-HAC SE, CV = CPCV (overlapping-label leakage 방지). block bootstrap 으로 IC 분포 (점추정 아님) → "분포+CI+게이트" mandate 직결. multiple-testing = **Benjamini-Hochberg + deflated Sharpe (Bailey-López de Prado)**.

**근거**: Fama-French 2015 JFE (FF5); Asness-Frazzini-Pedersen 2019 RAS (QMJ); Frazzini-Pedersen 2014 JFE (BAB); López de Prado 2018 AFML (CPCV); Newey-West 1987; Bailey & López de Prado 2014 (deflated Sharpe). 1차: French data library, OSS skfolio/toraniko/alphalens.

**정량**: CPCV embargo ~1-5% sample + purging; HAC lag ~T^(1/4) 또는 monthly 5-10; block length ~T^(1/3).

**confound**: low — 확립 방법론, risk 는 오적용 (purge 누락·HAC lag 오류).

## Q9. 핵심 가설 7 (반증조건 포함)

| # | 가설 | signal | 반증조건 |
|---|---|---|---|
| H1 | revision breadth → fwd 1-3M cross-sec return (+) | I/B/E/S revision | rolling 3y IC CI 하한 ≤0, OR FF5+Mom intercept NW t<2. e-value 목표 >1.5 |
| H2 | shareholder yield → value alpha, real-rate regime 조건부 | EDGAR buyback+div, DFII10 | L/S spread CI 가 高·低 rate regime 양쪽 0 포함, OR 부호 flip |
| H3 | HY OAS regime → cyclical↔defensive rotation | BAMLH0A0HYM2 | regime-conditional 수익차 CI 0 포함, OR OAS→sector Granger 실패. transition signal = OAS +X bps/Q |
| H4 | dollar 채널 = 긴축-regime 조건부 (구조 아님) | DTWEXBGS, DGS10 | 2015-19 low-corr sub-sample 에서 β_dxy 가 −0.5~−1.6 유지 시 → H4 기각 (구조적). transition = ρ(Δrate,Δdollar)<threshold |
| H5 | bank(+) vs utility/REIT(−) rate-beta 부호 regime-안정 | DGS10, sub-sleeve | N≥24 epoch 에서 부호 flip, OR CI 양방향 0 cross |
| H6 | AI-capex → Mag7 fwd EPS lag 1-2Q, IC regime-unstable | Mag7 10-Q capex | lagged-capex IC 가 capex-peak 후 regime 포함 전 regime CI 하한 >0 → durable factor (=H6 기각, but 위험). + reflexivity: intra-Mag7 corr·IC 동반 상승 시 crowding flag |
| H7 | Fed funds path surprise → duration-sorted event-study CAR | OIS vs FOMC dot | FOMC 주변 CAR 이 duration sort 에 monotonic 아님, OR e-value <1.5 |

선택 H8: sector eff_N ≤5 — PCA 80% 분산에 >7 PC 필요 시 기각.

**근거**: 위 Q1-Q8 인용 종합 + VanderWeele-Ding 2017 (E-value, Annals Intern Med) [tentative].

**confound**: medium — H4·H6 가 표본·reflexivity 에 가장 취약.

## Q10. 미해결 confound / bias (7)

1. **표본기간 regime confound (최대 risk)** — 2021-2024 = 긴축×강달러×AI-capex-boom 삼중 collinear regime. dollar/rate/capex/concentration 효과 깨끗이 분리 불가. dollar 채널 finding (Q3) 특히 취약. pre-2021 sub-sample 재검 강력 권고, 단 AI/Mag7 대표성 상실 — irreducible tension
2. **Survivorship·delisting bias (Q7)** — yfinance 류가 실패 종목 누락 → backtest alpha 과대, 특히 value·distress-인접 sleeve (은행 2023 SVB!)
3. **Mag7/concentration non-stationarity** — cross-sectional 구조 자체가 변함 (GICS-파편화 Mag7) → 역사적 sector beta 표본 전체 비교 불가, eff_N time-varying
4. **Factor crowding/decay** — McLean-Pontiff 2016: 출판 후 alpha ~58% 감소 [tentative]. revision breadth·shareholder yield well-known → 역사 IC 가 미래 IC 과대
5. **Multiple-testing/data-snooping** — KR 12 가설 미러링 + US 신규 + sleeve/regime 다중 cut → false-discovery 팽창. BH + deflated Sharpe + e-value 규율 필요
6. **Multicollinearity 귀인 confound (Q3)** — collinear regressor 시 β 불안정 (VIF 팽창). dollar 가 rate 분산 "먹은" 게 정확히 이것
7. **Analyst data look-ahead** — revision breadth (I/B/E/S) 벤더 snapshot 에서 추정치 소급 수정 PIT 문제 — EDGAR 엔 analyst 데이터 없어 OSS 로 PIT 무결성 검증 더 어려움

**근거**: McLean-Pontiff 2016 JF; Bailey-López de Prado 2014; survivorship literature [tentative]. 1차: EDGAR (PIT 펀더멘털), I/B/E/S (PIT 취약).

**정량**: decay ~58%; survivorship ~1-4%/yr; ρ(rate,dollar) 2022-24 ~0.7-0.8 [모두 tentative].

**confound confidence**: high — 정직한 headline: 2021-2024 US 데이터는 rate·dollar·AI-capex·concentration 이 near-collinear 라 채널 분리 자체가 불가. R2-R3 에서 out-of-regime 재검이 수렴의 핵심.

---

## ★Claude R2 권고 (자체 제시)

1. **Q3 의 2015-2019 sub-sample 재검** (dollar 구조성 판정)
2. **Q5 reflexivity monitor 구체 spec**
3. **Q1 PCA-eff_N 실측** (Tier vs macro-sleeve 결정)

**direction.md 핵심가설 N 1차 후보**: Q9 의 H1·H3·H4·H6 4개로 좁히기 제안.

---

## supervisor 메모 (R2 빈틈 보충 / 환각 cross-verify)

- ★단정 어휘 약함 (Claude 가 hedge 어휘 사용 + tentative 라벨 정직 — Gemini 대비 epistemic discipline 우월)
- ★점추정 magnitude 모두 range/CI 명시 (예: revision breadth IC 0.03~0.06 / Mag7 30-35% / ρ 0.7-0.8 / bank rate-beta +0.3~0.8 / utility -0.3~0.8) — rule #1 위반 0
- ★Q3 (cyclical dollar 표본 한정) vs Gemini Q3 (구조적) = **큰 disagree, R2 핵심**
- ★Q5 (d) 기각 vs Gemini (c+d) 권장 = **정 반대, R2 핵심**
- ★Mag7 GICS 3 파편화 finding (Q1) = Gemini 안 언급, R2 에서 사실 확인 의무 (2018 GICS Comm Services 신설 정확?)
- ★Claude R2 권고 3 = direction.md design 핵심 input
- 환각 cross-verify 후보 (Claude reference):
  - Chan-Jegadeesh-Lakonishok (1996) JF — 실재 가능 ("Momentum Strategies")
  - Boudoukh-Michaely-Richardson-Roberts (2007) JF "payout yield" — 실재 가능
  - McLean-Pontiff (2016) JF "Does Academic Research Destroy Stock Return Predictability?" — 실재 확인됨
  - Weber (2018) JFE "cash flow duration & term structure of equity returns" — 실재 가능 [Claude tentative]
  - Gormsen-Lazarus equity yield — 실재 가능
  - Fama-French (2015) JFE FF5 — 실재
  - Asness-Frazzini-Pedersen (2019) RAS QMJ — 실재 (실제 RFS / 또는 JFE 게재 확인 필요)
  - Frazzini-Pedersen (2014) JFE BAB — 실재
  - López de Prado (2018) AFML — 실재 (Wiley)
  - Newey-West (1987) — 실재 (Econometrica)
  - Bailey-López de Prado (2014) deflated Sharpe — 실재 (JoPM)
  - VanderWeele-Ding (2017) E-value Annals Intern Med — 실재 확인됨
  - Stickel (1991) "analyst revision" — 실재 확인 필요
- **Claude epistemic discipline 우위** — Gemini 대비 hedge 어휘 + tentative 라벨 + R2 권고 자체 제시 → R2 에서 두 채널 비교 시 Claude 가설 frame 우선 채택 권장
