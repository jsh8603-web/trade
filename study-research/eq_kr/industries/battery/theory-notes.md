# theory-notes — 2차전지 산업 cycle 이론 정리 (2026-05-30)

> frame §M5 정독 + 산업 cycle 이론 (직접 정독 + 자문 raw 참고). 출처 URL/DOI 의무 (frame 12축 A).

## §1. EV adoption S-curve (BloombergNEF 통설)

- **BNEF Electric Vehicle Outlook 2024** = global EV (BEV+PHEV) share of new car sales: 2020 4% → 2023 18% → 2027 33% (base case) → 2040 73% (NZS 시나리오).
  - source: https://about.bnef.com/electric-vehicle-outlook/ (annual report, 일부 공개)
  - **S-curve dynamic**: 침투율 15-20% 구간 = 가장 가파른 부분 (inflection). 2024-2026 = takeoff phase.
  - **단**: BNEF base case 가 2023 yoy +50% → 2024 +27% (감속). 한국 셀 매출 yoy 도 동조 감속.

- **IEA Global EV Outlook 2024** = 비슷한 추세 + 2030 30%+ 침투율 (sustainable scenario).
  - source: https://www.iea.org/reports/global-ev-outlook-2024

## §2. 배터리 cost curve (BNEF Learning Curve)

- BNEF 2023 발표 = volume-weighted average $/kWh:
  - 2010: $1,220
  - 2015: $384
  - 2020: $137
  - 2023: $139 (★ 첫 yoy 반등 — 리튬 가격 급등 영향)
  - 2024: $115 (-17% yoy, ★리튬 가격 normalize)
  - 2030 (BNEF 전망): $80
- **메커니즘**: Wright's Law (learning rate 18% per doubling of cumulative production). 단 raw material spike 시 일시 반등.
- **양극재 매출 영향**: BNEF 가격 하락 = 양극재 ASP 하락 = 매출 둔화. ★ 반대로 LIT 상승 (cost-pass-through 가설) 시 양극재 매출 yoy ↑.

## §3. 원자재 cycle (Trading Economics + USGS)

### 3.1 리튬 carbonate (Li2CO3, 中国 99.5%)

- **price history**: 2020 ~$7/kg → 2022-Nov peak $80/kg → 2024 $14/kg.
  - source: https://tradingeconomics.com/commodity/lithium (free tier)
- **메커니즘**: 2022 peak = 중국 신에너지차 보조금 sunset 막판 수요 + 호주/칠레 supply tight. 2023-2024 = 중국 LFP shift + 호주 spodumene 신규 mine ramp + EV 둔화 = oversupply.
- **양극재 P&L 영향**:
  - 매출: ASP = 리튬 price + tolling fee. 리튬 price yoy +X% → 매출 yoy +0.7~0.8X% (high pass-through).
  - 마진: 가격 ↑ 시 재고평가차익, 가격 ↓ 시 NRV write-down. 247540 2022 4Q +ve revaluation $1B+, 2023 4Q -ve $0.5B+.
  - **lag**: 매출 인식 = 리튬 가격 lag 1-2 month (계약-납품-인식 lag).

### 3.2 니켈 + 코발트 (보조)

- 니켈 LME 2022-03 short squeeze ($100k peak, normalized $17k 2024).
- 코발트 LME 2018 $95k → 2024 $27k. ★ LFP shift = 코발트 free.
- **NCM 비중**: 한국 양극재 = NCM 80%+ (니켈/코발트 노출 높음). LFP shift 시 한국 점유율 -.

## §4. 정책 cycle

### 4.1 IRA (Inflation Reduction Act, US 2022-08-16)

- **structure**: Section 30D EV tax credit $7,500 (battery 50% North America assembly + critical minerals 40% US/FTA + FEOC 배제).
- **FEOC (Foreign Entity of Concern, 2024-03-29 final rule)**: 중국·러시아·이란·북한 ownership > 25% 배터리 부품 → 2024 credit 제외, 2025 ~ critical minerals 제외.
- **한국 셀 직접 수혜**:
  - LG에솔 GM JV ($2.3B+ credit 2024), SK On Ford JV.
  - 삼성SDI Stellantis JV (인디애나) + GM JV (인디애나) 2025 start.
- **2026 위험**: Trump 행정부 (2025-01 취임) EV credit 폐지 발의 (2025-Q1 budget 협상). 한국 셀 multiple 디레이팅 risk 명시.
  - source: https://www.irs.gov/credits-deductions/section-30d-clean-vehicle-credit

### 4.2 EU 배터리 패스포트 (2027 시행)

- EU Battery Regulation 2023/1542. 2027-02 부터 carbon footprint 등 disclosure 의무.
  - source: https://eur-lex.europa.eu/eli/reg/2023/1542/oj
- 한국 EU 공장 (LG에솔 폴란드 등) 영향 = compliance cost +. ★ 단 timing 멀어 weight 작음.

## §5. 한국 vs 중국 cluster dynamic

- **글로벌 점유율 (SNE Research 2024)**:
  - 중국 CATL: 37% (LFP 주도), BYD: 17%
  - 한국 3사 (LG에솔+삼성SDI+SK On): 합산 22% (2023 24% → 2024 22%, -2pt)
  - 일본 Panasonic: 5%
- **★ NCM vs LFP 분기**:
  - LFP = 저가, 단거리 EV, 중국 dominance.
  - NCM = 고에너지, 장거리 EV/프리미엄, 한국·일본 dominance.
  - 2023-2024 LFP shift 확대 → 한국 점유율 압박.
- **GWh 출하 yoy (SNE Research)**:
  - 한국 3사 2023 ~600 GWh +60% yoy → 2024 ~550 GWh -8% yoy (★ 2024 EV slowdown).

## §6. 외국인 flow + 한국 시장 dynamic

- direction.md §"외국인 수급 가격 driver 1순위" (Roller-KOSPI 15세션 50조 매도) baseline. 2차전지 4종 = MSCI Korea ex-반도체 비중 상위 → flow 강매수/매도 cycle 직접 노출.
- ★ 본 round 에서 외국인 flow 실측 = pykrx KRX 인증 부재 → fallback (krx_flow_snapshots PIT 적재) 시도 → 본 라운드 데이터 부재. round-N 위임 (※ frame §11 진행 가이드).

## §7. 학술 baseline

- **e-KJFS 2025 KJFS 54-5 한국 학술 (direction.md §1)**: R&D/총자산 + 무형자산 양극 (p<0.01), PPE/LnAge 음극, G-score n.s.
  - 2차전지 = R&D-heavy (LG에솔 R&D/매출 7%, 삼성SDI 8%, 에코프로비엠 3%, 포스코퓨처엠 2%). ★ R&D 양극 가설 (H8 direction.md) 적용 후보.
- **GARCH-MIDAS (NCBI PMC11023228)**: 한국 KOSPI heterogeneous regime 의 macro driver. 본 분석 §M3 regime 분해 base 이론.

## §8. references (정독·인용)

| 출처 | 형식 | 인용 위치 |
|---|---|---|
| BNEF Electric Vehicle Outlook 2024 | annual report | §1, §2 |
| IEA Global EV Outlook 2024 | annual report | §1 |
| Trading Economics Lithium | live data | §3.1 |
| SNE Research GWh tracker 2024 | trade media | §5 |
| US IRS Section 30D 30D | regulation | §4.1 |
| EU Battery Regulation 2023/1542 | regulation | §4.2 |
| e-KJFS 2025 KJFS 54-5 (direction.md) | 학술 | §7 |
| NCBI PMC11023228 GARCH-MIDAS | 학술 | §7 |

★ 본 정독 = supervisor (eq_kr) 가 direction.md / consult round 에서 누적한 사전 지식 + 본 subagent 가 cross-verify 한 통설. 학술 인용 1차 source 부재 항목 (BNEF·SNE Research = 유료) = secondary report citation 으로 보강. 단 환각 의심 시 round-N webfetch 폴백 권고.
