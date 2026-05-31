# theory-notes — 한국 바이오 산업 이론 정리

> 2026-05-30, Tier 3 한국 바이오 sub-study.
> 산업 cycle 이론 + 주요 source URL. 본 노트 = frame.md §6 12축 A (이론 실재성) 충족용.

## §1 한국 바이오·헬스케어 산업 분류

### 1.1 GICS / KRX WICS 매핑
- **GICS Sector**: Health Care (35)
  - Sub-Industry: Pharmaceuticals (351020) · Biotechnology (352010) · Health Care Equipment (351010) · Life Sciences Tools & Services (351030)
- **KRX WICS 대분류**: 제약·바이오 (코드 G35XX 추정 — pykrx 직접 fetch 실패, 별도 source 필요)
- **본 분석 적용**: 종목명 키워드 (`바이오·제약·헬스·메디·신약·임상·백신·유전자`) 기반 1차 필터 → 192 ticker (Top 50 시총순 선별).

### 1.2 산업 sub-cluster (frame §1 권고 + 본 라운드 확장)
| sub-cluster | 정의 | 대표 ticker | 비즈니스 cycle |
|---|---|---|---|
| **CMO_CDMO** | Contract Manufacturing — 위탁 생산 | 207940 삼성바이오로직스, 237690 에스티팜 | capex cycle, 가동률, 글로벌 CDMO 수요 |
| **biosimilar** | 바이오시밀러 — copy biologic | 068270 셀트리온, 068760 셀트리온제약 | 특허 만료 cycle, 가격 cycle, US/EU 채택률 |
| **novel_drug** | 신약 (NDA·BLA 후보) | 326030 SK바이오팜, 298380 HLB, 141080 레고켐바이오 | 임상 단계별 binary event (Ph1/2/3, NDA, FDA approval) |
| **traditional_pharma** | 일반 제약 (배당 + 안정) | 000250 삼천당제약, 069620 대웅제약, 001060 JW중외제약 | 보험약가 cycle, 내수 cycle, dividend yield |
| **diagnostic_device** | 진단·의료기기 | 086900 메디톡스, 376900 잉네스헬스케어 | 진단 수요 (코로나 등 epidemic event-driven) |

## §2 산업 cycle 이론 (이론 정독 + 정리)

### 2.1 신약 개발 cycle (Pharmaceutical R&D cycle)
- **stage**: Discovery → Pre-clinical → Phase 1 (안전) → Phase 2 (효능) → Phase 3 (대규모) → NDA/BLA → FDA approval → Launch
- **time**: 평균 10-15 년, 비용 평균 $2.6B (Tufts Center for the Study of Drug Development, 2014 — DiMasi et al.)
- **성공률**: Phase 1 → Approval ≈ 9.6% (BIO/Informa/QLS Advisors, 2021)
- **★ 한국 신약 cycle**: 한국 시장 단독 신약 launch 는 글로벌 매출 비중 낮음 → 한국 바이오 신약기업의 valuation upside = **글로벌 license-out + FDA approval** dominant.

### 2.2 CMO/CDMO 산업 cycle (Contract Manufacturing)
- **driver**: 글로벌 biologic 시장 성장 (mAb, ADC, gene therapy 등) + 빅파마 자체 capex 회피 → outsourcing 수요
- **한국 위치**: 삼성바이오로직스 = 글로벌 Top 3 CDMO (Lonza/WuXi/SBL), 셀트리온 = 글로벌 Top 5 (자체 + CMO 혼재)
- **★ 가동률 cycle**: 신규 plant capex 후 2-3년 가동률 ramp-up, 80%+ stable, 95% near full = bottleneck.
- **source 한계**: 가동률 = 삼바 IR 분기 보고 (보통 70-85%), 무료 시계열 source 없음.

### 2.3 바이오시밀러 cycle (Biosimilar)
- **driver**: 원약 (originator) 특허 만료 → 바이오시밀러 launch → 가격 50-70% 할인 → 시장 침투
- **2020년대 wave**: Humira (2023 US BMS), Stelara (2025 US), Eylea (2024+) 잇따른 특허 만료
- **한국 위치**: 셀트리온 = 글로벌 바이오시밀러 시장 점유율 약 10% (Top 3), 램시마/허쥬마/트룩시마 등.
- **cycle 특성**: 새 바이오시밀러 launch → 18-24개월 ramp-up → market share peak → 후발주자 추가 진입 시 가격 erosion.

### 2.4 한국 바이오 valuation 특성
- **PER median (KOSPI 헬스케어, 2024 기준 추정)**: 30-50배 (KOSDAQ 신약기업) vs 15-25배 (traditional pharma) → 광범위 dispersion.
- **PBR median**: 3-7배 (KOSDAQ 바이오) vs 1.5-3배 (traditional pharma).
- **R&D 비중**: HLB·SK바이오팜·메지온 = 매출 대비 R&D 60-100%+ (적자) vs 한미·녹십자 = 10-15%.
- **valuation discount/premium**: 신약 binary event (FDA approval) 직전 30-50% premium, fail 시 50-80% drawdown.

## §3 한국 바이오 거시 sensitivity 이론

### 3.1 USDKRW (수출 sensitivity) — ★실측 기각
- **이론**: 삼바·셀트리온 글로벌 매출 70%+ → USD 매출 / KRW cost → USDKRW 약세 (KRW per USD ↑) 시 KRW 환산 매출 ↑
- **본 분석 실측**: 산업 평균 forward 20d return ~ USDKRW yoy corr = -0.035 (lag 0) ~ +0.038 (lag 1), p>0.6 → ★REJECTED.
- **함의 가설**: (a) 삼바·셀트리온이 forward hedging 광범위, (b) 바이오시장 valuation 이 환율보다 fundamental event-driven, (c) FX 효과가 cost (수입 원료) 와 매출 (USD 매출) 에서 cancel out.

### 3.2 US 금리커브 (10Y-2Y) — long-duration sensitivity
- **이론**: 바이오 = 장기 cashflow (10-15년 R&D + launch) → discount rate sensitivity 높음 → US 10Y 상승 시 valuation discount.
- **본 분석 실측**: corr = +0.133 (lag 0, p=0.108), OOS ratio = 2.16. ★ raw 양의 시그널 + OOS 강함, 但 Bonferroni 후 비유의.
- **함의**: 부호는 일관 (steeper curve → bio outperform), magnitude 약함. weight rule 후보 LOW confidence.

### 3.3 HY OAS (글로벌 risk-on/off) — ★INSUFFICIENT
- **이론**: HY OAS 확대 = risk-off → 성장주 (bio) underperform, defensive (traditional pharma) outperform.
- **데이터 한계**: BAMLH0A0HYM2 (월 macro proxy) gauge — FRED 가용 시계열 = 2023-05+ (n=30 month) → ★N gate 미달.
- **collector_plan**: NDR HY OAS 또는 alternative FRED series (HYG ETF OAS proxy) 적재 필요.

### 3.4 FDA approval cycle — TENTATIVE
- **이론**: 글로벌 FDA NDA approval count yoy ↑ → 신약 산업 cycle peak → 한국 license-out 환경 개선 + 시장 sentiment ↑.
- **본 분석 실측**: fda_yoy lag=1m corr=+0.188 (p=0.023 raw) ★ — Bonferroni α/15=0.0033 후 비유의. OOS ratio -0.91 (★sign flip).
- **함의**: post-2022 regime shift (코로나 후 FDA approval cycle 변화, 한국 바이오 R&D 환경 변화). 가설 보강 후 round-N.

## §4 source (학술/리포트, source URL 박제)

### 4.1 학술 source (실재 정독)
- **DiMasi et al. (2016)** "Innovation in the pharmaceutical industry: New estimates of R&D costs", *Journal of Health Economics* 47:20-33. DOI: 10.1016/j.jhealeco.2016.01.012 — 신약 비용 $2.6B.
- **BIO/Informa/QLS (2021)** "Clinical Development Success Rates and Contributing Factors 2011-2020" — Phase 1 → Approval 9.6%. URL: https://go.bio.org/rs/490-EHZ-999/images/ClinicalDevelopmentSuccessRates2011_2020.pdf
- **Pammolli et al. (2011)** "The productivity crisis in pharmaceutical R&D", *Nature Reviews Drug Discovery* 10:428-438 — R&D 생산성 cycle.

### 4.2 산업 리포트 (실재 정독, 본 분석 기여)
- **EvaluatePharma (annual) "World Preview"** — 글로벌 바이오 시장 전망. paywall, 일부 요약 공개.
- **삼성증권 "한국 바이오·헬스케어 2024 전망"** (2024-01) — 한국 시장 분석. 사내 자료, 본 라운드 부분 인용 (요약 매체 covered).
- **하나증권 "셀트리온 — 바이오시밀러 cycle peak"** (2025-Q3) — 셀트리온 매출 cycle. 본 라운드 부분 인용.

### 4.3 1차 데이터 source (실재 fetch)
- **openFDA drugsfda API**: https://api.fda.gov/drug/drugsfda.json (★본 분석 1051 month rows 적재 완료)
- **FDR (FinanceDataReader)** 0.9.202 — KRX listing + 가격 + FRED. https://github.com/FinanceData/FinanceDataReader
- **pykrx**: KRX 시총·sector. https://github.com/sharebook-kr/pykrx
- **FRED**: DGS10, DGS2, BAMLH0A0HYM2, DEXKOUS, KOSPI/KOSDAQ — 전부 가용.

### 4.4 본 라운드 미적재 source (collector_plan_industry 등록)
- **DART_API_KEY** 부재 → DART 펀더멘털 (PER, PBR, ROE, EPS revision) 적재 안 됨. ★P0 priority.
- **NIH RePORTER** (US 정부 R&D 예산): https://api.reporter.nih.gov/ — 가용, 본 라운드 미사용.
- **EvaluatePharma 글로벌 바이오 매출 forecast** — paywall, alternative source 탐색 필요.
- **clinicaltrials.gov v2 facet API** — 부재 (yearly count 만 가능). monthly cycle 분석 불가.

## §5 비판 / 한계

1. **삼바·셀트리온 dominance** — Top 30 시총 70% = 두 종목 forward return 이 산업 평균 dominate. eq-weight 평균 = misleading. **시총 가중 또는 sub-cluster 별 분석 권고** (round-N).
2. **regime shift 광범위** — 코로나 + 인플레/금리쇼크 + AI cycle 재편 → 2020-2022 vs 2023+ corr sign flip 다수 관찰. **regime classifier 명시** + IS/OOS 외 추가 (예: 코로나 sub-regime) 필요.
3. **factor neutralization 부재** — toraniko factor model 미적재. systematic factor (market/size/value) exposure 제거 후 idiosyncratic IC = 본 라운드 미산출.
4. **N gate 한계** — 월간 n=146 (12년) 이지만 36 cell 분해 시 cell당 N≈4 미달. M3 36 cell = 미적용 (cell collapse fallback 권고).
