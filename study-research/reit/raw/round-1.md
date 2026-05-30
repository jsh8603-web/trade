---
tags: [type/raw-round, study_id/reit, round/1, source/websearch-native]
date: 2026-05-30
round_focus: ①이론 수집방향 — REIT 가격결정 핵심 framework 와 학술·실무 reference 식별
note: STUDY-KIT §2 v2 의 2-1단계 자문 다회 라운드 1. 직접 WebSearch 폴백 (gemini-web/claude-web 9세션 경합 회피).
---

# Round 1 — 이론 수집방향 (가격결정 framework 와 reference)

## A. 라운드 질문 설계

이 라운드의 목표 = **①이론 수집방향 빈틈 식별**. 두 각도 동시:
1. REIT 가격결정 academic / practitioner framework 핵심 — 어떤 이론·교과서·리포트를 봐야 하나
2. 2024-2025 sub-sector 실측 returns — 이론이 데이터와 어디서 어긋났나 (가설 반증 후보 식별)

## B. 사용 도구 / 폴백 사유

- 1차 시도: `/gemini-web` + `/claude-web` 병렬 자문 → **미선택 사유**: 9세션 경합 미검증, 본 작업이 직접 사실확인이 더 필요 (자문은 종합 단계에서).
- 2차 = 채택: native WebSearch 2 query (main 명시 폴백 경로).
- 결과 raw = `~/.claude/docs/archive/research-raw/reit-pricing-theory-native-20260530.txt` (hook 의무 3계층 저장).

## C. Query 1 발견 — REIT 가격결정 framework

**핵심 가치평가 4 접근**:
- **NAV (Net Asset Value)** — 보유 부동산 시가 − 부채. 사적시장 cap rate × NOI 평가로 산출.
- **P/FFO** — funds from operations 배수. accounting earnings 의 D&A 정화.
- **P/AFFO** — adjusted FFO = FFO − maintenance capex − straight-line rent. distributable cash 근접.
- **DCF** — discounted future cash flow.

**핵심 spread 관계 (이론과 데이터 cross)**:
- ★ implied cap rate (public REIT, NOI / EV) **−** private appraisal cap rate **=** public-private gap.
- 데이터: Q3 2022 peak 243 bp (rate-shock 직격), Q4 2024 = 120 bp (회복). [환각 검증 필요 — Nareit T-tracker primary source 재확인 예정]
- 이 gap = **mean-reverting anchor**. block5 hypothesis #2 의 정량 기준 후보.

**AFFO/FFO 비율 sector 별 (실무 standard)**:
- triple-net 95-100% (e.g. Realty Income, NNN)
- industrial / multifamily 85-95%
- office / retail / lodging 70-85%
→ **AFFO yield 의 sector 별 transform** 필요. 같은 FFO 라도 sector 가 다르면 AFFO 가 다름.

**Key reference 후보 (이론 학습 단계 = 2-2 에서 정독)**:
- **Green Street Advisors — REIT Valuation: NAV-based Pricing Model** (reit.com 호스트 PDF) — NAV anchor model 의 실무 standard. ★1순위.
- **CFA Level 2 REIT valuation chapter** (analystprep) — NAV / P-FFO / P-AFFO / DCF 4 approach 학술 정리.
- **Capidel — Real Estate Finance & REIT Valuation framework** — practitioner step-by-step.
- **Appraisal Economics — Why Buyers and Sellers Disagree on REIT Value** — public-private gap mechanism.
- Seeking Alpha "Win When The Logic of REITs Changes" — regime change perspective.

**검색에서 *부재* 한 영역 (Round 2 보강 대상)**:
- 학술 논문 직접 reference (Wachter 2013, Damodaran lecture 등) — 검색 synthesizer 가 "deep academic papers 부재" 명시.
- WALT (lease duration) 와 rate β 의 정량 관계 — 핵심 이론인데 1차 검색에서 직접 reference 없음.
- Stagflation regime REIT 행동 — 1970s 데이터 reference 없음.

## D. Query 2 발견 — 2024-2025 sub-sector 실측 returns

**2024 sub-sector total return (FTSE NAREIT US Real Estate Index)**:
- specialty: +35.9% (timber, cell tower, etc.)
- data centers: +25.2%
- health care: +24.2%
- office: **+21.5%** ★
- ...
- industrial: **−17.7%** ★

**Q4 2024**: data centers +7.5%, lodging/resorts +1.6% (leaders).
**2025 YTD (Q1 기준)**: health care +28.5%, industrial +17.0%, diversified +15.5%, apartment Dec +1.4%, regional malls +1.1%, shopping centers +0.7%.

## E. ★ 이전 v1 yaml lens 와의 차이 — 가설 *반증* 발견

v1 yaml block1 lens 의 `regime_reading` 에서:
> "Reflation (성장↑ 인플레↓): REIT 전반 강세. industrial / data-center / apartment 우위(growth × low rate)."

**2024 실측 데이터 (위 발견) 와 비교**:
- 2024 는 rate-cut anchor 형성 + 성장 양 → Recovery / 부분 Reflation 국면.
- 이론대로면 industrial 강세 예상.
- **실측 industrial = −17.7%**. office +21.5% (vs 이론 "structural -25%").
- 결론: v1 lens 의 sub-sector regime 매핑은 **단정 가설** — 데이터로 미검증.

**이게 v2 재작업의 핵심 결함**: 이론·자문을 그대로 lens 에 옮기고 데이터 cross-check 생략. 2-3 단계
의 실데이터 시계열 검증이 빠진 v1.

## F. Round 1 → Round 2 자가 점검 (두 모델에 더 물을 것 없나)

빈틈 식별:
1. **WALT 와 rate β 의 정량 관계** — 검색에 직접 reference 없음. Round 2 = WALT × rate 민감도 실증 논문.
2. **AFFO/FFO 비율 sector 차이의 기계적 transform** — Round 2 = 어떻게 시계열 cross-section 정규화.
3. **Stagflation regime 1970s data** — Round 2 = 인플레 shock REIT 행동 학술 reference.
4. **sub-sector regime 매핑의 데이터 근거** — 이론적 매핑 vs 2024 실측 어긋남 → Round 2 = NAREIT historical
   regime breakdown 직접 fetch.
5. **이론 검증 방법론** (다음 라운드 핵심) — partial-correlation·regime 분해·Rank-IC 어떻게 적용.

→ Round 2 focus = "**이론 검증방향**" — 위 빈틈을 데이터 시계열 검증으로 닫는 방법론 + 실측 reference.

## G. Round 1 결론 (요약)

①이론 수집방향 = **NAV-based pricing (Green Street model)** + **P-AFFO sector-adjusted** + **public-private
cap rate gap mean-reversion** + **sub-sector × regime 실측 historical** 4축.

★ 단순 매핑 (Reflation→industrial 강세 류) 은 *반증 가능 가설* 로 강등 — 2024 데이터로 이미 반증된 사례.
가설은 반증조건 명시 (Round 3 의 핵심 산출).

## H. 출처 (Sources — hook 의무)

검색 결과 raw 는 archive 저장 완료. 핵심 출처:

- [REIT Valuation: NAV, FFO, AFFO, Cap Rates (CFA Level 2)](https://analystprep.com/study-notes/cfa-level-2/reit-share-value-calculation-using-net-asset-value-p-ffo-p-affo-and-discounted-cash-flow-approaches/)
- [Green Street Advisors — REIT Valuation: NAV-based Pricing Model (PDF)](https://www.reit.com/sites/default/files/meetings/REITWise15/Key%20Drivers%20Impacting%20a%20REITs%20Stock%20Price/Full%20Document(s)/Green%20Street%20Advisors%20-%20Pricing%20Model%20Report.pdf)
- [Real Estate Finance & REIT Valuation Framework (Capidel)](https://capidel.com/real-estate-finance-reit-valuation-framework/)
- [Why Buyers and Sellers Disagree on REIT Value (Appraisal Economics)](https://www.appraisaleconomics.com/why-buyers-sellers-disagree-reit-value/)
- [FFO vs AFFO Explained (Private Equity Bro)](https://privateequitybro.com/ffo-explained-the-core-metric-behind-reit-valuation-multiples/)
- [Performance by Property Sector/Subsector (Nareit)](https://www.reit.com/data-research/reit-indexes/historical-reit-returns/performance-property-sector-subsector)
- [REIT Performance 2024 + 2025 Outlook (Nareit webinar recap)](https://www.reit.com/news/articles/reit-performance-in-2024-and-the-outlook-for-2025-webinar-recap)
- [REIT 2024 Review & 2025 Outlook (Uniplan)](https://uniplanic.com/alternative-thinking/doc/reit-outlook-2025)
- [REITs Post Narrow Gains in 2025 (Nareit)](https://www.reit.com/news/blog/market-commentary/reits-post-narrow-gains-2025)
- [Nareit T-Tracker Q1 2025 (PDF)](https://www.reit.com/sites/default/files/2025-05/Ttracker_2025Q1.pdf)

★ 환각 검증 대상 (Round 2 또는 theory-notes 단계에서 cross-verify):
- "243 bp / 120 bp" implied vs appraisal cap rate spread → Nareit T-tracker Q1 2025 PDF 직접 확인 예정
- "industrial 2024 = −17.7%" → Nareit subsector index 직접 확인 예정
