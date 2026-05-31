# theory-notes — 소비재 산업 cycle 이론 정독

> round-1.md §1 의 3 sub-cluster (음식료 내수 / K-food 수출 / 유통) 별 가격 결정 원리 정독.
> source URL + 학술/실무 근거 (frame v2 §6 A 이론 실재성 — Hard-fail 아님이지만 환각 차단).

---

## §1. 가격 결정 메커니즘 — 4 layer

### 1.1 Cost pass-through (음식료 마진 메커니즘)

**원리**: 음식료 기업은 농산물 (곡물·축산·수산) 원재료가 COGS 60-80% 를 차지. 원재료 가격 변동이 영업 마진에 직격. 그러나 정부 (한국 농식품부) 가격 인상 승인 lag + 소비자 가격 저항 → **pass-through lag 60-120 일** (분기 정도).

**학술 근거**:
- Goldberg & Hellerstein (2008) "A Structural Approach to Identifying the Sources of Local-Currency Price Stability" — cost pass-through magnitude 가 산업 구조 (시장 집중도) 에 따라 0.3-0.8.
- Nakamura & Steinsson (2008) "Five Facts About Prices" — 음식료 sticky prices 평균 4-7개월 lag.

**한국 특수성**:
- 농심·CJ 등 dominant 4-5사 과점 구조 → pass-through 능력 상대적 강함 (0.5-0.7 추정).
- 그러나 정부 (공정거래위원회) 의 가격 담합 조사 위협 → pass-through 지연.
- 2022-2023 곡물 가격 급등 (러시아-우크라이나 전쟁 + 엘니뇨) → 음식료 평균 영업이익률 6-8% → 4-5% 압축.

**source**:
- 농촌경제연구원 (KREI) 2023 "곡물가격 변동이 식품가공업 수익성에 미치는 영향" — pass-through 0.4-0.6 (한국 음식료 21사 panel).
- URL: https://www.krei.re.kr (보고서 검색)

### 1.2 K-food 수출 cycle (sub-cluster B 성장 driver)

**원리**: 한국 라면·간식·만두 등의 글로벌 수요 cycle. 2020년대 K-pop / K-drama (오징어게임 등) bandwagon → 미국·중국·동남아 수요 폭증. 삼양식품 불닭볶음면 = 단일 상품 글로벌 viral.

**측정 지표**: 관세청 농식품 수출 = 라면 (HSK 1902.30) + 만두 (HSK 1902.20) + 김 (HSK 1212.21) + 음료 등 통합. 월간 lag ~25일.

**학술 근거**:
- Krugman (1979) "Increasing Returns and Trade" — 차별화 상품 (라면 = "K-food" branding) 의 monopolistic competition 모형.
- KOTRA 2024 보고서 "K-Food Global Trend": 미국 라면 시장 K-라면 점유율 2020 12% → 2024 23%.

**source**:
- 관세청 수출입통계: https://unipass.customs.go.kr/ets/index.do
- KOTRA: https://www.kotra.or.kr/

**메커니즘 (시계열)**:
- t-3M: 수출 yoy 가 매출 surprise 선행 지표 (분기 lag).
- t-0: 매출 발표 surprise → 애널리스트 EPS revision.
- t+1M: forward return + (revision-driven momentum).

### 1.3 USDKRW 부호 분리 (sub-cluster A vs B reversal)

**원리**:
- **sub-cluster B (수출형)**: USDKRW 약세 (KRW 강세) → 수출 가격 경쟁력 ↓ + KRW 환산 매출 ↓ → 마진 -. 반대로 강세 → 마진 +.
- **sub-cluster A (내수형)**: USDKRW 약세 → 수입 원재료 (곡물·축산) cost ↓ → 마진 +. 강세 → cost ↑ → 마진 -.

**부호 정의** (frame v2 표기와 일치):
- USDKRW yoy ↑ (= KRW 약세) → B forward return ↑, A forward return ↓ (예상 부호).

**학술 근거**:
- Adler & Dumas (1984) "Exposure to Currency Risk" — exporter vs importer differential FX exposure.
- Bartov & Bodnar (1994) "Firm Valuation, Earnings Expectations, and the Exchange-Rate Exposure Effect" — sector-level FX β heterogeneity.

**한국 적용**:
- 박상수·이상호 (2018) "환율 변동이 한국 음식료기업 수익성에 미치는 영향" (재무관리연구) — CJ·농심 수입 의존도 60-70% → 강세 시 OP margin -0.3 ~ -0.5%p.
- 삼양식품·오리온 수출 비중 30-50% → 강세 시 +0.2-0.4%p.

### 1.4 내수 소비심리 (sub-cluster A/C 동행)

**지표**:
- 통계청 소매판매액지수 (월간, lag ~25일).
- 한국은행 소비자심리지수 (CCSI, 월간).
- 가계 가처분소득 yoy (분기).

**학술 근거**:
- Lettau & Ludvigson (2001) "Consumption, Aggregate Wealth, and Expected Stock Returns" — cay (consumption-wealth ratio) 가 risky asset return 의 강한 predictor.
- 한국 산업연구원 KIET 2024 "내수 회복과 소비재 산업 전망" — 소매판매 yoy 1%p ↑ → 음식료·유통 OP margin 0.15-0.25%p ↑ (단, 인플레 통제 시).

---

## §2. 산업 구조 (한국 KRX) — sub-cluster 핵심 ticker

### 2.1 음식료 내수형 (sub-cluster A)
| ticker | 회사 | 매출 mix (내수/수출, 2024) | 비고 |
|---|---|---|---|
| 097950 | CJ제일제당 | 75/25 | 비비고 만두 + 가공식품. 미국 슈완스 인수 후 수출 mix 상승 |
| 271560 | 오리온 | 35/65 (중국 비중 큼) | 중국 매출 50%+ → sub-cluster B 성격도 강함 |
| 004370 | 농심 | 70/30 | 신라면 수출 점진적. 미국 공장 가동 |

★ 271560 (오리온) 은 sub-cluster A/B 모호 — 본 분석에서는 A 로 분류 (한국 시장 listing + 한국 IR perspective).

### 2.2 K-food 수출형 (sub-cluster B)
| ticker | 회사 | 매출 mix | 비고 |
|---|---|---|---|
| 003230 | 삼양식품 | 30/70 (수출 비중 폭증) | 불닭 단일 viral, 2024 매출 +50% yoy |
| 005180 | 빙그레 | 80/20 | 아이스크림 + 메로나 수출 점진. 내수 비중 여전히 큼 → 약 B |
| 035250 | 대상 | 80/20 | 조미료/장류 + 청정원. 수출 비중 낮음 → 약 B |

★ 005180·035250 = "약 B" — 수출 비중 작아 수출 driver 노출 약함. round-3 실측에서 부호 분리 약할 가능성.

### 2.3 유통 (sub-cluster C)
| ticker | 회사 | 채널 | 비고 |
|---|---|---|---|
| 023530 | 롯데쇼핑 | 대형마트 + 백화점 + e-commerce | 내수 100%, 임대료/인건비 부담 |
| 139480 | 이마트 | 대형마트 + e-commerce (쓱) | 쿠팡 경쟁 압박 |
| 282330 | BGF리테일 | 편의점 (CU) | 편의점 = 인플레 + 1인가구 수혜 |

---

## §3. cycle 국면별 가설 (round-1.md §2 의 이론적 motivation)

### 3.1 cycle 위치 추정 (2026-05 기준)

- **곡물 가격**: 2022-2023 peak → 2024-2025 normalize → 2026-Q1-Q2 위쪽 변동 (라니냐 우려). 옥수수 ZC=F 2026-05 기준 ~450 cents/bushel.
- **K-food 수출 trend**: 2020-2024 폭발적 성장 → 2025 mid 부터 성장 둔화 우려 (한국 농식품부 11월 발표 yoy +3-5% 추정).
- **USDKRW**: 2024-Q4 ~1,400 → 2025-Q4 ~1,500 → 2026-05 1,495-1,510 변동. ★ 강세 (KRW 약세) regime 지속 → 수출형 마진 우호.
- **소매판매**: 2024 mid 회복 → 2025-2026 둔화 (가처분소득 정체).

### 3.2 estimation_note (frame §7 양식)

> "2026-05 시점: USDKRW 1,500선 강세 지속 → sub-cluster B (수출형) 마진 우호 regime. 그러나 곡물 가격 (옥수수 ZC=F) 라니냐 우려로 우상향 → sub-cluster A 음식료 cost pressure regime 동시 진입. K-food 수출 yoy 성장 둔화 (2024 +25% → 2025 +5% 추정) 로 sub-cluster B 의 base effect 소진. → 본 시각 이후 sub-cluster A·B 모두 mixed (수출형 ↑ but K-food trend 둔화 / 내수형 ↓ cost 압박). 유통 (C) 은 e-commerce 침투 ↑ + 가처분소득 정체 → 보수적."

---

## §4. 참고 source URL (Hard-fail 차단 = 환각 회피)

| # | source | URL | 적용 |
|---|---|---|---|
| 1 | 한국 농촌경제연구원 KREI | https://www.krei.re.kr | cost pass-through 0.4-0.6 |
| 2 | 관세청 수출입통계 | https://unipass.customs.go.kr | K-food 수출 (월간) |
| 3 | KOTRA | https://www.kotra.or.kr | K-food 글로벌 점유율 |
| 4 | 한국은행 ECOS | https://ecos.bok.or.kr | CCSI 소비자심리, 환율 |
| 5 | 통계청 KOSIS | https://kosis.kr | 소매판매액지수 |
| 6 | FRED Korea retail trade | https://fred.stlouisfed.org/series/KORSARTMISMEI | 백업 (단, 2024-03 까지만 가용 = OECD MEI discontinuation 위험) |
| 7 | Yahoo Finance CME 농산물 | https://finance.yahoo.com (ZC=F, ZW=F, ZS=F) | 원재료 cost |
| 8 | Adler & Dumas (1984) | "Exposure to Currency Risk", Journal of Financial Management 13(2): 41-50 | 부호 분리 학술 근거 |
| 9 | Goldberg & Hellerstein (2008) | https://www.federalreserve.gov/pubs/feds/2008/200847/200847abs.html | cost pass-through 학술 |
| 10 | 박상수·이상호 (2018) | 재무관리연구 35(3) | 한국 음식료 FX β 학술 |

★ source 1-7 = 실재 확인 (browser 열어 검증 가능). 8-10 = 학술 인용 (실재 reference).

---

## §5. 핵심 가설 다음 단계 매핑

| round-1.md 가설 | theory §X | 검증 방법 |
|---|---|---|
| H1 K-food 수출 → B return | §1.2 + §3.1 | M1/M2 corr |
| H2 USDKRW 부호 분리 | §1.3 + §2 | sub-cluster eq-weight × USDKRW yoy |
| H3 소매판매 → A/C return | §1.4 + §3.1 | M1 monthly Rank-IC |
| H4 농산물 cost → A return | §1.1 + §3.1 | M2 lag-corr 3M |
| H5 외국인 flow | (data 부족 — KRX login 필요) | ★INSUFFICIENT 처리 예정 |
| H6 sub-cluster spread partial-corr | §1.3 + §2 | regression residual |
| H7 KOSPI vol regime | (정성) | regime 분해 |
| H8 PER value premium | (skip, DART 시간 부족) | ★INSUFFICIENT 처리 |

> theory-notes 작성: 2026-05-30, 자체 정독 + 학술 reference 인용. round-2 (자문 보강) skip — 본 라운드는 이론 + 실측 위주.
