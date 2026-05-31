---
tags: [type/study-direction, domain/inv, study/eq_intl, phase/2-1]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
asset_scope: [equity.intl]
status: "2-1 종결 — main(btn-Codlearn) 승인 대상"
raw_rounds:
  - raw/round-1.md  # International CAPM + Adler-Dumas + segmentation + ETF liquidity + AQR TSM / 가설 9건
  - raw/round-2.md  # BIS dollar 채널 + walk-forward/drift regime/RankIC/2-level uncertainty / 가설 검증 setup 매핑
  - raw/round-3.md  # China decoupling 정량 (IMF/MS/AQR) + 메커니즘 + structural vs artifact + tug-of-war
prior_artifact:
  - study_session.yaml  # v1 — 7블록 lens·indicators·relationships·weights·hooks·collector·code_change_plan
  - summary.md          # v1 — 5y Yahoo daily 18 series 실측 (§5 H1~H8 결과)
  - raw/yahoo_cache/    # 5y daily TR (SPY/12 country ETF/DXY/WTI/VIX, 22595 row)
fallback_note: "/gemini-web + /claude-web 9-session 경합 / WebSearch hook research.block — main v2 가이드 폴백 허용. R1~R2 = WebSearch native, R3 = Gemini API (gemini-search.js pro). 모든 raw 3계층 저장."
hallucination_check: "R3 paper 명(IMF Jan 2023 / MS 2022-2023 / AQR 2023) 환각 검증 미실시 — 2-2 이론학습 단계 cross-check 의무"
---

# eq_intl Direction (2-1 산출, main 승인 대상)

## §0. 한 줄 결론

국가/지역 지수 ETF (EFA/VEA/EEM/VWO/EWJ/EWG/EWZ/INDA/EWY/EWT/FXI/VGK 등) = "**국가 = 한 자산**"
단위로 평가. **unhedged USD ETF return = 현지지수 + FX + 배당**이라 **broad USD 방향이 1차 driver**,
그 위에 국가 archetype × regime × 매크로 베타가 곱해진 구조. eq_intl 전문 애널리스트의 시각은
단일종목 §6 valuation/quality 가 아니라 **macro_sensitivity 1차축 + segmentation/decoupling**.

## §1. ★① 이론 수집 방향

### 1.1 학술 frame (정독 대상, R1)
| 우선순위 | frame | seminal source | 왜 |
|---|---|---|---|
| ★★★ | **International CAPM** | Dumas 1994 / Dumas-Solnik 1995 | 글로벌 MSCI + FX risk premium = unhedged ETF 분해의 기본축 |
| ★★★ | **Adler-Dumas FX risk channel** | Adler-Dumas 1995 | 외화표시 자산의 currency exposure — eq_intl 의 환 1차 driver 근거 |
| ★★ | **Market segmentation** | 2024 ScienceDirect ML (Insights from ML, Vol 244) | 법적 제한/repatriation/FX 규제가 World CAPM alpha 를 segmented effect 로 변환 — china/EM 적용 |
| ★★ | **Country risk premium** | Damodaran 류 | sovereign default risk → cost of equity → EM country alpha |
| ★ | **ETF liquidity premium** | Holden-Subrahmanyam / RFS 2024 Vol 37 #10 | broad vs 단일국 ETF tier 차이 → tracking error 분해 |

### 1.2 실무 frame (정독 대상, R2)
| 우선순위 | source | 학습 항목 |
|---|---|---|
| ★★★ | **BIS Quarterly Review Sep 2024** "US dollar and capital flows to EMEs" | broad USD 채널 (10y importance ↑) + portfolio inflow > bank lending |
| ★★★ | **BIS Working Paper 1042** EM bond flows & exchange rate | EM 환·flow 분해 실증 |
| ★★ | **BIS Bulletin 114** Financial channel weaker dollar | 약달러 시 EM 채널 발현 |
| ★★ | **BIS GLI (Global Liquidity Indicators)** quarterly | USD foreign-currency credit to EMDEs — 가용 indicator |
| ★ | **NBER WP 32329** Global transmission of Fed hikes | Fed → EM 채널 |

### 1.3 OSS / dataset (검증 활용, R1+R2)
| 우선순위 | source | 활용 |
|---|---|---|
| ★★★ | **AQR Time Series Momentum dataset** (monthly, 1985~) | TSM equity indices/curr/commod/sovbond — H7 검증 직접 입력 |
| ★★ | **macrosynergy.com** Cross-country equity risk allocation w/ statistical learning | GICS sector 별 학습 + country panel — eq_intl 적용 방법 |
| ★★ | **Hang Seng Indexes Co.** A-H Premium Index | H5 china segmentation 직접 지표 |
| ★ | **IIF Capital Flows Tracker** (monthly, partial-free) | EM portfolio flow ground truth |

### 1.4 China-specific 학습 (R3, 환각 검증 의무)
| 우선순위 | source | 학습 |
|---|---|---|
| ★★★ | **IMF "Geopolitical Fragmentation and the Future of Multilateralism"** Jan 2023 Fig 2.11 | MSCI China β 1.2→0.2 정량 |
| ★★ | **Morgan Stanley "Is China Becoming a Diversifier?"** 2022-2023 | R² 30%→10% 분해 |
| ★★ | **AQR "You Need to Rethink Emerging Markets"** 2023 | china 의 DXY 베타 ≈0 |
| ★ | **Dalio "Principles for Dealing with the Changing World Order"** 2021 | 구조적 분리 frame |
| ★ | **PIIE / PBoC quarterly** | CNY counter-cyclical factor 분석 |

⚠️ **2-2 이론학습 진입 시 R3 paper 명 원문 cross-check 의무** (Gemini 환각 가능성). 부재면 H5 신뢰도 보정.

## §2. ★② 이론 검증 방향 (실데이터 시계열)

### 2.1 우리 수집기 매핑 (§7 가용 indicator)
| frame | 우리 수집기 | 적용 indicator |
|---|---|---|
| International CAPM 분해 | `core/data/macro_market.fetch_daily` (Yahoo) | DXY (DX-Y.NYB), WTI (CL=F), VIX (^VIX), 국가 ETF TR (SPY/EFA/VEA/EEM/VWO/EWJ/EWG/EWZ/INDA/EWY/EWT/FXI/VGK) |
| Risk regime | `core/brain/fred_adapter.FRED_SERIES` | BAMLH0A0HYM2 (HY OAS), T10Y2Y (yield curve), STLFSI4 (stress) |
| FX risk channel | `core/data/fx.FxStore` (PIT bitemporal) | DXY/USDKRW 등록됨, 다국가 확장 필요 |
| Country fundamentals | (부재) → 블록6 | forward E/P, ROE aggregate, EPS revision breadth (MSCI 유료 / ETF 구성 프록시) |
| China-specific | (부재) → 블록6 / Hang Seng API | A-H Premium Index, CNH-CNY spread |

### 2.2 검증 methodology (2024 표준, R2)
| 방법 | 적용 가설 | source |
|---|---|---|
| **Walk-forward OOS (frozen params)** | H1/H3/H7 | arxiv 2511.12490 (13-Sharpe SP500 20y) |
| **Drift regime decomposition** | H2/H9 | 동상 |
| **Regime-dependent Granger causality** | H1/H2 (lag 0/1/3m) | arxiv 2601.10732 |
| **Partial correlation (cglasso 와 일치)** | 블록3 prior | arxiv 1402.1405 — 우리 시스템 §8 SSOT 와 직결 |
| **Cross-country statistical learning + panel regression** | H6 (segmentation) | macrosynergy.com — archetype 별 패널 |
| **Two-level uncertainty (safe deployment)** | 블록5 e-CUSUM | arxiv 2603.13252 "When Alpha Breaks" — hidden regime change |
| **RankIC degradation horizon scan** | H3/H9 horizon 선정 | arxiv 2603.13252 — 60d/90d 음수 전환 |

### 2.3 walk-forward setup (eq_intl 권장)
- Train 24~36m rolling / Test 1m forward / Refit 1m (drift 빠름) or 3m (안정).
- Regime label binary: VIX>25 / T10Y2Y<0 / HY OAS>400bp.
- Block4 weight freeze during test (prior_strength 고정).
- horizon ≤30d 권장 (60d/90d 에서 IC 음수 전환 회피).

### 2.4 검증 deficiencies (블록6 신규 요청)
| 미확보 | 영향 가설 | 우선순위 |
|---|---|---|
| 국가 forward E/P / ROE / revision breadth | H3/H4 의 fundamental cross-check | ★★ |
| China A-H Premium Index | H5 직접 지표 | ★★★ |
| 다국가 환율 panel (FxStore 확장) | H1/carry crash | ★★★ |
| FRED DTWEXBGS / DCOILWTICO / DFII10 | dollar/oil/real-yield 직접 (현재 부재) | ★★★ |
| China credit impulse (TSF YoY) | H4 commodity link (R1 메커니즘) | ★★ |
| IIF/EPFR EM flow | H5 capital control 측정 | ★ (유료) |

## §3. ★③ 핵심 가설 초안 (반증조건 포함)

> 9건 (R1 초안 + R3 보강). 우선순위 = 이론·실측 강도. 검증 가능성 = 우리 수집기 가용 여부.

| 우선순위 | ID | 가설 | 이론 근거 | 반증조건 | 검증 가능 (현재) |
|---|---|---|---|---|---|
| ★★★ | **H1** | Dollar dominance: broad USD↑ → 모든 국가 ETF↓ (특히 unhedged) | Adler-Dumas FX risk + BIS GLI dollar channel | dxy_β 5y rolling 부호 양수 전환 OR R²<0.05 지속 6m+ | ✓ (DXY DX-Y.NYB) |
| ★★★ | **H2** | Regime amplification: risk-off 시 dollar-EM coupling 강화 | Forbes-Warnock flight-to-quality + BIS portfolio risk appetite | risk-off (VIX>25) 와 risk-on 의 dxy-EM corr 차이 < 0.10 | ✓ (5y 실측 이미 확인 -0.640→-0.796) |
| ★★★ | **H5** | China partial decoupling (post-2018): MSCI China β < MSCI EM ex-China β | IMF/MS/AQR + Common Prosperity policy divergence | china rolling β > EM-avg 95% CI 회복 OR R² > 25% 재돌파 6m+ | ✓ (5y 실측 확인 + 학술 정량 보강) |
| ★★ | **H7** | TSM self-momentum: 각 국가 ETF 12m self-return → 다음 1m 양 predictor | Moskowitz-Ooi-Pedersen 2012 + AQR dataset | self-12m 부호 ↔ next-1m 부호 hit rate < 52% | ✓ (Yahoo monthly resample) |
| ★★ | **H4** | Commodity exporter oil link: oil↑ → 자원국 (brazil/uk/mexico) > 수입국 (india/korea/japan) | Adler-Dumas terms-of-trade + China credit impulse 매개 | exporter corr ≤ importer corr in 3y rolling | ✓ (5y 실측 부분 확인: brazil +0.123 / india -0.064) |
| ★★ | **H3** | Cross-country momentum (12-1, AQR): winner > loser cross-section | Asness-Moskowitz-Pedersen + AQR | Rank-IC mean<0 in 5y OR IC-IR<0.10 in 10y rolling | ✓ (5y 실측 IC-IR +0.13 — caution 필요) |
| ★★ | **H9** | Country momentum crash regime: risk-on 만 IC 양, risk-off 시 무력화/반전 | Daniel-Moskowitz 2016 + AQR carry/value crash | risk-on/off regime split Rank-IC 차이 < 0.05 | △ (walk-forward + regime split 미실시) |
| ★ | **H6** | Country segmentation: World CAPM alpha 의 일부 = segmented market 효과 | 2024 ScienceDirect ML + Damodaran country risk | unsegmented DM alpha vs segmented EM alpha 차이 무유의 | △ (지수집계 alpha 측정기 부재) |
| ★ | **H8** | ETF liquidity tier → tracking error: broad ETF > 단일국 ETF | RFS 2024 Vol 37 #10 | broad/단일국 tracking err 차이 < 5bp | △ (현지 index reference data 부재) |

### 보강 가설 (R3 → 새 발견)
| ID | 가설 | 이론 근거 | 반증조건 |
|---|---|---|---|
| **H5a** | China = em_china sub-archetype 분리 가치: dollar/oil/credit β 가 다른 EM 과 명확히 다른 부호/강도 | R3 IMF/MS/AQR + 5y 실측 +0.033 | em_china 와 EM avg 의 cross-sectional macro β cosine similarity > 0.7 |
| **H5b** | Decoupling 가역성 (regime-dependent): global 동시 위기 시 china β 재상승 (re-couple) | R3 artifact 주장 + Dalio re-couple 경로 | global crisis 6m window 에서 china rolling β >= EM-avg rolling β |

## §4. 라운드 누적 / 수렴 판정

| 라운드 | 채널 | 핵심 발견 | raw |
|---|---|---|---|
| R1 | WebSearch (폴백) | 학술 frame 5 + 가설 초안 9 | round-1.md |
| R2 | WebSearch (폴백) | BIS dollar 채널 + 검증 method 7 | round-2.md |
| R3 | Gemini API (폴백) | China decoupling 정량 (IMF/MS/AQR) + tug-of-war | round-3.md |

**수렴**: 3R 누적으로 ①②③ 모두 broad coverage. R4 marginal benefit 낮음 (carry crash / cglasso
cross-country 사례 = 2-2 이론학습 흡수 가능). main "3~7R" 의 하한 충족.

## §5. 2-2 이론학습 진입 시 의무

1. **R3 paper 환각 검증** (cross-check 의무):
   - IMF "Geopolitical Fragmentation and the Future of Multilateralism" Jan 2023 Fig 2.11 — 원문 확인
   - Morgan Stanley "Is China Becoming a Diversifier?" 2022-2023 — paper 명/내용 확인
   - AQR "You Need to Rethink Emerging Markets" 2023 — paper 명/내용 확인
   - 부재면 H5 정량 인용 신뢰도 보정 (★★★→★★)
2. **frame 우선순위 ★★★ 정독** (Dumas/Adler-Dumas 원문 + BIS Quarterly Sep 2024 + AQR TSM paper)
3. **검증 method 표준 정독** (arxiv 2511.12490 walk-forward + 2603.13252 two-level uncertainty)
4. **raw/theory-notes.md** 작성 (가격결정 원리·지표 의미·관계도)

## §6. 2-3 시계열 검증 진입 시 의무

1. **이전 5y 실측 (summary.md §5) 재활용**: H1/H2/H5 1차 확인된 가설에 walk-forward OOS 적용.
2. **블록6 신규 요청 우선순위**: FRED 3시리즈 추가 / 다국가 FxStore / Hang Seng A-H Premium.
3. **raw/validation-{지표}.md** 작성 (시계열 검증 근거 + 도표).
4. study_session.yaml 갱신 (블록3 prior_strength · 블록4 base_weight · 블록5 confidence_hook 보정).

## §7. main 승인 요청 항목

1. **R1~R3 폴백 적용 승인** (자문 채널 경합 / hook block → WebSearch + Gemini API).
2. **가설 우선순위 + 반증조건** 확정 (특히 H5/H5a/H5b 의 China sub-archetype 분리 방향).
3. **2-2 진입 허가** (paper 환각 검증 의무 동반).
4. **검증 deficiencies 우선순위 동의** (Hang Seng A-H Premium + 다국가 FxStore + FRED 3시리즈
   = 블록6 ★★★ 신규 요청).

⛔ **본 게이트 이전 2-2 진입 금지** (STUDY-KIT v2 §2 명시).
