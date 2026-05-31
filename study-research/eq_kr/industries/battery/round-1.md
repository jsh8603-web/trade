# round-1 — 2차전지 산업 이론·가설 (2026-05-30, Tier 2 subagent)

> SSOT = frame.md v2 §1 Tier 2 / §3 Layer 3 / §M4 5게이트. as_of = 2026-05-30.
> 본 라운드 = 이론 정리 + 가설 5-10 + Layer 3 cycle 지표 후보 list. round-N 은 자문 추가 시 (필요 시만).

## §1. universe (frame §1 Tier 2)

| ticker | 회사명 | sub-cluster | 시총 비고 |
|---|---|---|---|
| 373220 | LG에너지솔루션 | 셀 (가장 큰 pure-play) | 2022-01-27 상장, KOSPI 1-3위 |
| 006400 | 삼성SDI | 셀 + ESS | 2020-2024 EV 둔화로 -50% drawdown |
| 247540 | 에코프로비엠 | 양극재 (NCM/NCA) | KOSDAQ → KOSPI 이전, 2023 메가랠리 후 -70% |
| 003670 | 포스코퓨처엠 | 양극재 + 음극재 (수직통합) | POSCO 그룹 cycle 동조 |

★ 동적 universe = `KrxSectorProvider.get_sector_map(as_of, market='KOSPI'/'KOSDAQ')` WICS 매핑 시점별. 정적 4종목 = round-1 분석 기준.

★ sub-cluster 분할 명시 (Tier 2 권고, 4종 내부 이질성 큼):
- **셀** = 373220 (LG에솔), 006400 (삼성SDI) — OEM 직판매, USDKRW 강세 수혜
- **양극재** = 247540 (에코프로비엠), 003670 (포스코퓨처엠) — 원자재 cost-pass-through, 리튬 가격 yoy 직접 노출

## §2. 산업 cycle 이론 (theory-notes.md 후속 정독)

### 2.1 EV adoption S-curve + cycle dynamics

- **글로벌 EV 침투율** = 2020 4% → 2024 18% (BloombergNEF EVO 2024). 침투율 곡선 = S-curve (early adoption → mainstream → saturation).
- **EV 판매 사이클** = 2-3년 model refresh + 5-7년 정책/보조금 cycle. IRA 2022-08 (US 보조금 $7,500), EU CO2 cap 2025, 중국 2024-04 보조금 종료.
- **배터리 가격 deflation** = 평균 $/kWh 2010 $1,200 → 2023 $139 (-89%, BNEF) → 2030 $80 예상. yoy decline 가속 시 양극재 마진 압박.

### 2.2 원자재 cycle (LME)

- **리튬 carbonate (Li2CO3)** = 2021 $7/kg → 2022-11 peak $80/kg → 2024 $14/kg (-83%). yoy yoy 변동 변동성 ★極大.
- **니켈 (LME)** = 2022-03 squeeze $100k/t → 2024 $17k/t. 인도네시아 supply (中) 영향.
- **코발트 (LME)** = 2018 peak $95k/t → 2024 $27k/t. 콩고 supply + LFP shift 영향.
- **이론 가설**: 양극재 종목 (247540, 003670) 매출/마진 = 리튬 가격 lag 0~1Q. 가격 급락 시 재고평가손실 (NRV write-down).

### 2.3 정책 cycle

- **IRA 2022-08 (US)** = North America 생산 + 추출/가공 sourcing 요건. 한국 셀 → US JV (LG-GM, SK-Ford 등) 직접 수혜.
- **IRA 2025-2026 변경 위험** = Trump 행정부 EV credit 폐지 우려 (2026-Q1-Q2). 한국 셀 multiple 디레이팅 risk.
- **EU 배터리 패스포트** = 2027 시행, 탄소발자국 의무. 한국 EU 공장 (LG에솔 폴란드 등) 직접 영향.

### 2.4 한국 vs 중국 cluster dynamic

- **중국 CATL/BYD** = 글로벌 시장 점유율 2024 60%+ (LFP 주도). 한국 NCM/NCA 점유율 -15pt yoy.
- **GWh 출하 yoy** = 한국 셀 3사 합산 2023 yoy +60% → 2024 -8% (NCM 둔화). EV 둔화 + 중국 LFP shift 영향.

## §3. Layer 3 cycle 지표 후보 list (frame §3 Tier 1+2 권고)

| # | 지표 | 정의 | 무료 소스 | 5게이트 통과 가능성 |
|---|---|---|---|---|
| **B1** | LIT ETF yoy | Global X Lithium ETF (LIT.US) yoy | yfinance | ★★★ 리튬 가격 proxy, 6년 표본 충분 |
| **B2** | BATT ETF yoy | Amplify Lithium & Battery (BATT.US) yoy | yfinance | ★★★ 배터리 통합 proxy, 2018-06~ |
| **B3** | TSLA price yoy | Tesla 주가 yoy (EV 수요 sentiment proxy) | yfinance | ★★ proxy, 단 Tesla idiosyncratic 한계 |
| **B4** | USDKRW yoy | 환율 yoy (한국 셀 수출주 베타) | FxStore PIT | ★★★ frame Layer 2 기본 4종, 자동 |
| **B5** | DRAM yoy ($SMH proxy) | 반도체 cycle (배터리 BMS 반도체 수요 동조) | yfinance SMH | ★★ 산업 간 spillover, conditioning 필요 |
| **B6** | IRA event flag | 2022-08 (시행) / 2024-03 (FEOC 규정) / 2026-Q1 (Trump 행정부 변경) | 수동 event ledger | ★ event study, N 부족 (3-4 event) |
| ★B7 | LIT / SMH ratio | 리튬 cluster vs 반도체 상대 강도 | 계산 | ★ 실험적 |
| ★B8 | KRW × export_share | (USDKRW yoy) × 종목 수출비중 교호 | DART + FxStore | ★★ direction.md H3 직접 매핑 |

★ 채택 우선순위 = B1, B2, B4 (★★★) + B3, B5, B8 (★★) → 6 지표 실측 시도. B6 (IRA event) = 별도 event study, B7 = 탐색.

★ LME 리튬·니켈·코발트 현물 가격 = 무료 API 부재 (LME 유료). LIT/BATT ETF 가 LME 가격 추종 proxy 로 충분 (correlation > 0.85 알려진 사실, claim 의무 — round-N 검증).

## §4. 핵심 가설 8 (frame §10 — H1~H8)

### H1. USDKRW 강세 → 한국 셀 (373220, 006400) outperform (수출주 베타)

- **메커니즘**: 한국 셀 매출 90%+ 해외 (US, EU, 중국). 원화 환산 매출 증가 → 영업이익 확대.
- **측정**: 종목 패널 회귀 — y_20d ~ β1·USDKRW_yoy + β2·SMH_yoy + ε (sub-cluster=셀 한정).
- **반증조건**: β1 < +1.96 t-stat OR 부호 음 → 가설 기각 (수출 베타 무효).
- **5게이트 prior**: N 충분 (월간 60+ months) / SE OK / Power high / FDR 적용 / OOS 2023-2026.

### H2. 리튬 가격 yoy ↑ → 양극재 (247540, 003670) outperform lag 0~1Q

- **메커니즘**: 양극재 = cost-pass-through, 리튬 가격 상승 시 ASP 상승 (lag 0-1 분기) + 재고평가차익.
- **측정**: 월간 lag-corr — y_60d (양극재 sub) vs LIT_yoy lag 0/1/3M.
- **반증조건**: lag-corr 모든 lag |ρ| < 0.10 → 가설 기각 (리튬 cycle 무관).
- **5게이트 prior**: LIT 2018-2026 = 96 months (n 충분) / power OK / regime 분해 필수 (리튬 hyper-volatile = single regime 부적격).

### H3. EV cycle (TSLA yoy proxy) → 2차전지 산업 평균 동조

- **메커니즘**: Tesla 주가 = global EV sentiment 1순위 proxy. EV 수요 둔화 우려 시 한국 배터리 동조 하락.
- **측정**: 산업 평균 (4종 동등가중) 월간 return yoy vs TSLA_yoy lag 0~3M.
- **반증조건**: corr < +0.30 → Tesla 단독 proxy 무효, alternative proxy 필요.
- **5게이트 prior**: 96 months / 단 TSLA idiosyncratic (FSD, Cybertruck 등) → conditioning 필요.

### H4. IRA event → 한국 셀 multiple re-rating (event study)

- **메커니즘**: 2022-08 IRA 시행 시 LG에솔 +20% (1주일), 삼성SDI +15%. 2026 Trump 행정부 변경 risk.
- **측정**: 2022-08-16 (시행) / 2024-03-29 (FEOC 규정) ± 5d, ±20d CAR 측정. 4종 평균 + 셀 한정 분리.
- **반증조건**: CAR ±5d |값| < 3% AND p > 0.10 → IRA 무관 (예상 mismatch).
- **5게이트 prior**: ★ N 부족 (event = 2-3건). 5게이트 통과 어려움 → "탐색적 finding" 분류, weight_rule 후보 아님.

### H5. 외국인 flow regime → 2차전지 (Tier 1 = 반도체와 동일) 강한 effect

- **메커니즘**: 외국인 = 한국 시총 상위 wholesale. 2차전지 4종 = MSCI Korea ex-반도체 비중 상위. flow 강매수 regime → 동조 매수.
- **측정**: foreign_net_buy 28일 z-score regime (강매수/매도/중립) × 4종 평균 y_20d Rank-IC.
- **반증조건**: regime 차이 < 0.05 IC OR p > 0.10 → flow 무효.
- **5게이트 prior**: ★ pykrx KRX_ID/PW 인증 부재 → fallback = ETF flow (KODEX 2차전지 ETF flow) 사용. round-2 데이터 시도.

### H6. 12-1 모멘텀 (한국 약효, direction.md H5 baseline)

- **메커니즘**: 한국 시장 12-1 모멘텀 = US 대비 약효 (NCBI PMC11023228). 2차전지도 동일.
- **측정**: 4종 월간 t-12 ~ t-1 cumulative return → 분위별 t+20d Rank-IC.
- **반증조건**: IC > 0.05 → 한국 약효 통설 반박 (2차전지 한정 모멘텀 alpha).
- **5게이트 prior**: N=4 종목 × 60 months = 240 obs (작음). 산업 sub 한정 단정 위험 → "탐색적".

### H7. 양극재 sub vs 셀 sub spread

- **메커니즘**: 247540/003670 (양극재) vs 373220/006400 (셀) 부호 반대. 리튬 cycle ↑ 시 양극재 ↑, 셀 ↓ (raw material cost).
- **측정**: spread (양극재 평균 - 셀 평균) vs LIT_yoy corr.
- **반증조건**: corr < +0.30 → spread 무효, sub-cluster 분할 무의미.
- **5게이트 prior**: ★ frame §1.6 분석 unit vs portfolio label 분리 의무 → sub-cluster 별도 측정.

### H8. PIT 펀더멘털 (e-KJFS R&D 양극) — 2차전지 한정

- **메커니즘**: e-KJFS R&D/TA 양극 (한국 학술 baseline) → 2차전지 R&D-heavy (LG에솔 7%, 에코프로비엠 3%).
- **측정**: 4종 R&D/TA z-score (분기 vintage_policy=PIT, DART) → t+1Q forward return.
- **반증조건**: 분위 양극 무차이 → R&D 가설 2차전지 한정 무효.
- **5게이트 prior**: N=4 × 분기 25 = 100 obs (적음). Tier 3 산업 (AI tech, 바이오) 와 cross-check 권고.

## §5. 막힘 처리 plan (frame §11 라운드 가이드)

| # | 막힘 케이스 | 처리 |
|---|---|---|
| 1 | pykrx 외국인 flow KRX 인증 필요 | KODEX 2차전지 ETF (305720) flow 대체 |
| 2 | LME 리튬 가격 유료 | LIT ETF 95% correlation proxy (round-N 검증) |
| 3 | DART API 키 부재 | Public XBRL → DART 공시검색 수동 fallback (R&D, 매출 yoy 기본) |
| 4 | toraniko 한국 KOSPI universe 적용 어려움 | numpy/pandas Fama-French 회귀 fallback (frame §M5 허용) |
| 5 | regime 36 cell N<24 cell collapse | 외국인 flow 3 cell 만 분해 (Macro 무관) → 3 cell fallback (frame §M3) |

## §6. 진행 다음 라운드

- ★ round-1 → round-2 사이: 데이터 수집 → 실측 (Layer 1/2/3 validation-*.md) → 5게이트 → summary.yaml → 12axis-audit.md
- ★ 자문 필요 시점: H4 IRA event study N 부족 → claude-web/gemini-web 1회 폴백 (event study 표본 부족 시 alternative metric 추천).
- ★ 본 round-1 = 이론 + 가설 + Layer 3 후보 list 완성. round-N.md = 검증 라운드에서 데이터 부족 시만 생성.
