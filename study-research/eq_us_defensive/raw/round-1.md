# Round 1 — eq_us_defensive 이론 수집 방향 (Gemini Pro 자문 원문)

**일시**: 2026-05-30
**자문 채널**: Gemini Pro (gemini-search.js promo) — gemini-web/claude-web 채널 경합 우려에 따른 직접 호출
**아카이브**: `~/.claude/docs/archive/research-raw/eq_us_defensive-round1-20260530.txt`
**프롬프트**: `C:/Users/jsh86/AppData/Local/Temp/search-r1-eq-us-defensive.md`
**응답 길이**: 11877 chars, 148 lines

---

## 핵심 발견 (R1 요약)

### ① 가격결정 학술 prior — 6 카테고리 14 reference

**방어주 일반 valuation**:
1. **Damodaran NYU Stern** *Sector-Specific Valuation* — utilities = stable growth DCF, staples = brand equity 무형자산 기반 pricing power, 각 섹터별 multiple/beta/COE 범위 제시
2. **Frazzini & Pedersen (2014)** *Betting Against Beta* JFE — 저베타 주식의 알파. 레버리지 제약 투자자가 고베타 과대평가 → 방어주 = "안전 자산" 프리미엄 학술 근거
3. **Asness, Frazzini & Pedersen (2019)** *Quality Minus Junk* RFS — 수익성/성장성/안정성/배당 기준 quality factor. 방어주 본질 quality 특성 → 초과 성과 = "퀄리티 프리미엄"
4. **Ilmanen (2011)** *Expected Returns* Defensive Equity 챕터, Wiley — ★방어주 = "채권 대리 자산(bond proxy)". 안정 배당 + 긴 cash flow duration → 실질금리 민감 메커니즘의 *교과서 anchor*

**금융주 valuation**:
5. **Damodaran (2012)** *Investment Valuation* Ch16 Financial Services, Wiley — 은행 = 잔여이익 모델 (RIM). `V = BV + Σ[(ROE-COE)·BV] / (1+COE)^t`. ROE-COE 스프레드가 핵심 동인
6. **Society of Actuaries** EV/MCEV — 생명보험 = Embedded Value (Adjusted NW + Value of In-force). 부채 duration·자산 duration 매칭이 가치 평가 핵심
7. **업계 KBW/MS 표준** — 자산운용 AUM×Fee Rate, 결제 명목GDP×카드사용률 모델, 영업 레버리지 高

**유틸리티 특화**:
8. **FERC/PUC rate case filings** — `EPS = Rate Base × Allowed ROE`. capex 사이클이 Rate Base 성장의 핵심
9. **Congressional Research Service (2022)** *IRA* — ITC/PTC 신재생 세액공제 → utility Rate Base 성장 5-10년 driver

**헬스케어 특화**:
10. **Kaiser Family Foundation (KFF)** *IRA Prescription Drug Provisions* — Medicare 가격 협상권 = pharma multiple 디레이팅. 블록버스터 약품 미래 CF 할인 시 risk premium 상향 필수
11. **Census Bureau / CMS projections** — 65+ 인구 증가 → Medicare 등록자 구조적 증가. HMO·medical device·pharma 모두 demographic tailwind
12. **Goldman/JPM 헬스케어 sub-sector**: pharma(방어+규제) / biotech(임상 변동성) / medical device(elective procedure 경기민감) / HMO(고용·금리 sensitive). ★sub-archetype 매크로 민감도 극명 갈림

**Comm Services mature**:
13. **New Street / MoffettNathanson** — 통신 = 유틸리티형 구독 CF + 5G/fiber capex 부담. FCF + 배당수익률 평가, capex 정점 통과가 변수
14. **Leichtman Research Group** *Pay-TV* — 케이블(CMCSA) cord-cutting 구조적 감소. 광대역 가입자/ARPU 상승 상쇄 여부 핵심

**Consumer Staples**:
15. **Bernstein/Barclays CPG** — 마진 = pricing power vs commodity input cost 힘겨루기. KO/PG 같은 강브랜드 = 원가 전가 성공, 약브랜드 = 마진 압박
16. **NielsenIQ/IRI 시장 데이터** — WMT private label + Amazon 이커머스 disruption
17. **10-K Geographic Segment** — KO/PG/PEP/PM 신흥시장 매출 비중 高 → DXY 강세 시 환차손 직접 노출

### ② 거시 driver - sector 분기 메커니즘 (정량 관계도)

| Driver | 메커니즘 | 방어주 부호 | 금융주 부호 | 학술 anchor |
|---|---|---|---|---|
| **Real rate (DFII10)** | 할인율 핵심 + duration | **음 (-)** util/staples bond proxy | **양 (+)** NIM·book yield 개선 | Ilmanen (2011); Boyd-Gertler (1994 FRB Minn) |
| **2-10Y slope** | 은행 borrow short lend long | 직접 영향 약 | **양 (+)** NIM 3-6M lag | Stigum's Money Market (2007) |
| **HY OAS** | risk-off flight-to-quality | **양 (+) 상대** outperform | **음 (-)** provisioning Q+1~2 lag | Frazzini-Pedersen BAB |
| **DXY** | 환산 매출 | **음 (-)** multinational staples (PG/KO/PM/PEP/CL) | mix (AUM 비달러 표시 감가) | 10-K Geographic Segment |
| **WTI** | 원가 input | util 단기 마진 압박 (요금승인 lag) / staples 종목별 부호 분기 | 약 | 업계 표준 |

### ③ 보고서·실무 표준 KPI (XLF/XLU/XLV/XLP 별)

- **XLF**: NIM 추이/가이던스, Loan Growth, NPL, CET1, ROE/ROA, Efficiency Ratio, BVPS
- **XLU**: Rate Base Growth, Allowed ROE, EPS·Dividend Growth, Payout Ratio, FFO/Debt
- **XLV**: R&D Pipeline, Patent Cliff, Drug/Device Sales, Medical Loss Ratio(HMO), Medicare/Medicaid 수가
- **XLP**: Organic Sales Growth, Pricing vs Volume, Margin, Brand Share, EM 매출 비중

Top-down→Bottom-up: Fed rate path → 매크로 시나리오 → sector KPI 전망 → 종목 EPS revision → 목표주가

### ④ Open-source 데이터/툴 평가

| 소스 | 용도 | 접근 난이도 |
|---|---|---|
| FinanceDatabase (MIT) | GICS sub-industry 매핑 | 하 |
| Ken French data library | 팩터 수익률·산업 포트폴리오 | 하 (vintage 주의) |
| FRED API (DGS10/DGS2/DFII10/BAMLH0A0HYM2/DTWEXBGS/WTISPLC) | 거시 모델링 핵심 | 중 (PIT 는 ALFRED) |
| EDGAR 10-K/Q/Y-9C 은행 파싱 | NIM/NPL/자본비율 추출 | 상 (regex+NLP) |
| NAREIT / SNL (S&P GMI) | REIT/금융기관 상세 | 상 (유료) |
| CMS.gov NHE | 약가·메디케어 데이터 | 중 |

### ⑤ 빈틈·논쟁 (R2~3 후속 질문 후보)

**핵심 논쟁: "Defensive 가 정말 risk-off 시 outperform 하는가" 의 시대별 변화**
- 2008 금융위기 = 전통 피난처
- 2020 팬데믹 = 기술주가 "신 방어주" 역할 일부
- 2022 금리 급등 = 방어주가 bond proxy 특성으로 *부진*
- → **"위기의 성격" 에 따라 방어주 역할이 동적 변동**?

→ **R2 질문 후보**: 위기 유형을 (1) 신용위기 (2) 전염병 (3) 인플레이션 으로 분류 + 각 유형별 방어주·금융주 상대 성과 실증 분석 가능한가? → regime split 의 axis 가 단순 HY OAS 가 아니라 위기 *유형* 일 수 있음 → 검증 design 의 핵심 인사이트

---

## R1 자가 점검 → R2 빈틈 질문

**R1 완수**:
- ① 학술 prior 17 ref 망라 (Damodaran·Frazzini-Pedersen·Asness·Ilmanen·Boyd-Gertler·Stigum·IRA·KFF·KBW)
- ② 5 거시 driver 부호 분기 메커니즘 (학술 근거 첨부)
- ③ 4 sector 표준 KPI + Top-down→Bottom-up 연결
- ④ 6 OSS/유료 데이터 접근 난이도
- ⑤ 핵심 논쟁 1건 → R2 질문 lead

**R2 (이론 검증 방향) 가 메워야 할 빈틈**:
1. **위기 유형별 방어주 역할 dispersion** — regime split 의 axis 가 단순 HY OAS z-score 인가, 아니면 "위기 유형" 분류가 필요한가?
2. **NIM lag 의 실증적 specification** — 3~6M lag 가 안정적인가, 금리 사이클 단계별로 lag 분포가 달라지는가?
3. **Bond proxy 의 시간 가변성** — 방어주 rate beta 의 시간 변동 (2010 이전 vs 2010-2020 QE vs 2022+ 정상화) — partial-corr 시계열로 어떻게 측정?
4. **Partial-corr conditioning set 설계** — defensive vs financial 분기 효과를 isolate 하려면 무엇을 통제해야 하나? (mkt beta? regime dummy? sector ETF own return?)
5. **Rank-IC 측정 design** — forward return window (1M/3M/6M/12M)? cross-sectional within sleeve vs time-series within ticker? z-score normalization 단위?
6. **falsification e-process baseline 설정** — score_ic_breakdown_eprocess 의 baseline_ic·sd·tau 를 본 sleeve 특화로 어떻게 calibrate?

→ R2 자문에서 이 6 빈틈을 메운다.

---

## 원문 reference (전문)

전문 → `~/.claude/docs/archive/research-raw/eq_us_defensive-round1-20260530.txt`
