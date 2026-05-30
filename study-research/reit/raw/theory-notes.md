---
tags: [type/theory-notes, study_id/reit, phase/2-2]
date: 2026-05-30
study_id: reit
phase: 2-2 (이론 학습)
note: STUDY-KIT §2 v2 2-2단계 산출 (강제). 가격결정 원리 + 지표 의미·관계도 + 학설 정리 + 환각 검증 결과 명기.
prior_phase_files: [direction.md, raw/round-{1,2,3}.md]
next_phase: 2-3 (실데이터 시계열 검증 → code 화 → study_session.yaml v2)
---

# REIT 이론 학습 노트 (2-2 산출)

> direction.md 의 ①이론 수집방향 + ③가설초안 (H1~H5) 을 *이론 정독*으로 보강.
> 환각 검증 2건 (main 필수조건) 결과 명기. raw 6 archive + memory 3 file 누적 후 종합.

---

## §A. 환각 검증 결과 (main 필수조건)

### A-1. 2024 industrial REIT total return = -17.7%
- **status**: ✅ **CONFIRMED**
- **primary source**: Nareit webinar recap "REIT Performance in 2024 and Outlook for 2025"
  - URL: https://www.reit.com/news/articles/reit-performance-in-2024-and-the-outlook-for-2025-webinar-recap
  - 인용 verbatim: "Industrial: down 17.7%"
- **함의**: v1 yaml 의 "Reflation → industrial 강세" 가설을 2024 데이터로 직접 반증.

### A-2. Implied-Private cap rate spread 243 bp Q3 2022 peak / 120 bp Q4 2024
- **status**: ✅ Q3 2022 peak 243 bp CONFIRMED / ⚠️ Q4 2024 120 bp PARTIAL (Q2 2024 = 130 bp primary, Q4 잠정)
- **primary source**: Nareit market commentary blog 시리즈 (T-Tracker + NCREIF ODCE)
  - URL: https://www.reit.com/news/blog/market-commentary/ (가족 10 article 시리즈)
- **verbatim**: "spread between REIT implied cap rates and private appraisal cap rates reached
  a peak of **243 basis points in Q3 2022**"
- **verbatim**: "As of **Q2 2024**, the cap rate spread remained wide at **130 basis points**."
- **caveat**: R1 의 "Q4 2024 = 120 bp" 정확 값은 primary 미확인. Q2 2024 = 130 bp + 회복 추세
  (private appraisal +15bp/Q × 7Q) 와 일관하므로 ±10bp 정확도로 잠정 채택.
- **★ baseline 처리**: H2 (cap rate spread mean-revert) 의 baseline 정수치는 H2 검증 시
  Nareit T-tracker 직접 fetch 로 fresh 산출 (Q4 2024 직접 시계열). v2 study_session.yaml 블록5 의
  confirm/reject signal 임계는 Q-end 값을 시계열로 매번 갱신.

---

## §B. NEW 발견 — sub-sector cap rate spread breakdown (Q2 2023)

primary source: Nareit "Office and Apartment Sectors Magnify Cap Rate Disparities"
URL: https://www.reit.com/news/blog/market-commentary/office-and-apartment-sectors-magnify-cap-rate-disparities

| Sub-sector | Cap rate spread (Q2 2023) | 시장 가격 함의 |
|---|---:|---|
| **Office** | **259 bp** (largest) | 시장이 가장 비관 가격 → 2024 +21.5% rebound 일관 |
| Apartment | 194 bp | 두 번째 비관 |
| Retail | 150 bp | 중간 |
| **Industrial** | **93 bp** (smallest) | 시장이 가장 낙관 가격 → 2024 −17.7% sell-off 일관 |

★ **이게 v1 lens 의 "Reflation → industrial 강세" 단정이 왜 틀렸는지의 mechanism**:
2023 Q2 시점 industrial 의 cap rate spread 가 이미 좁아져 있었다 (93bp = 시장 가격에 이미 낙관 fully
priced). 2024 의 Reflation-like 환경에서도 추가 upside 가 작아 NOI growth 가 multiple
contraction 으로 상쇄됨. **시장 priced expectations 와 미래 fundamentals 의 mismatch**.

NEW 발견 trajectory: "Private appraisal cap rate +15 bp/Q × 7 quarters" — appraisal-based private
valuation 은 sticky-down (transaction 보다 느리게 따라옴) → public-private gap 잔존의 source.

NEW closing-gap 함의: spread 폐기 시 private write-down 필요 폭 industrial/retail 20%+,
apartment/office 30%+ — H2 의 reject signal "deep discount 6Q+ 지속" 의 mechanism (private 가
큰 폭 write-down 못 하면 spread 영구화 가능).

---

## §C. 가격결정 원리 (4 approach 학술/실무 정리)

### C-1. NAV (Net Asset Value)
- 정의: 보유 부동산 시가 (private market cap rate × NOI) − 부채.
- 사용 source: Green Street, Citi, BTIG 등 third-party appraisal.
- 강점: 부동산 실물 가치 anchor. 사모재진입 (사모 PE 매수) 가능성 평가.
- 약점: 시장 마찰 (transaction cost, illiquidity) 무시. private cap rate 가 stale (Q-end 평가).

### C-2. P/FFO (Funds From Operations)
- 정의: FFO = Net Income + D&A − Gain on sale (Nareit 정의 1991).
- 강점: REIT 회계의 D&A 노이즈 제거. 가장 보편적 valuation 배수.
- 약점: maintenance capex 미반영 (capex 큰 sector 는 FFO 가 distributable cash 과대평가).

### C-3. P/AFFO (Adjusted FFO)
- 정의: AFFO = FFO − maintenance capex − straight-line rent adj.
- **AFFO/FFO 비율 sector standard** (실무):
  - triple-net (NNN, Realty Income): 95-100%
  - industrial / multifamily: 85-95%
  - office / retail / lodging: 70-85%
- → 동일 FFO 도 sector 가 다르면 AFFO 가 다름. **AFFO yield transform 시 sector adjust 필수**.
- v2 block2 `affo_yield` 의 transform 은 `own_history_z` 가 아니라 `sector_adjusted_z`로 변경.

### C-4. DCF (Discounted Cash Flow)
- 정의: P = Σ AFFO_t × payout / (1 + r_t)^t.
- 근사 공식: P ≈ AFFO_0 / (r_f + ERP_REIT + ΔCapRate − g_NOI).
- ERP_REIT historical: 3-5% (NAREIT 50y 평균 ~3.8%).
- 약점: terminal value 가정에 강하게 의존.

### C-5. 4 approach 간 cross-check
실무 standard = **NAV anchor + P/AFFO sanity check + DCF stress test**. 3 metric 이 동시 underprice
시 high-conviction 매수. 한 metric 만 underprice 시 sector/temporal anomaly 가능성 우선 검증.

---

## §D. 학설 정리 — REIT rate sensitivity

### D-1. 기본 합의
REIT-rate negative 관계는 광범위 학술 합의:
- Chen-Tzang (1988): 초기 negative 합의
- Allen et al. (2000): cross-sectional sensitivity 증거
- He et al. (2003): regime-dependent variation 시사
- **Giliberto-Shulman (2017)**: rate β 의 modern reference, short + long 양쪽 음

### D-2. ★ 정량은 INCONCLUSIVE
"empirical evidence on REIT-rate relationship varies across countries, econometric techniques,
interest rate proxies (short vs long, level vs change), and sample periods." (Round 2 인용)
→ **v1 의 "β_rate -1.0 ~ -2.0" 정량 단정 금지**. v2 는 부호 가설만 (H1).

### D-3. 시변 — Pre-2022 debt maturity extension
REIT firms 가 2010s 저금리 + flat curve 시기에 debt maturities 를 extend → 2022 rate-shock 시 rate
β 가 완화. **자본구조 (debt maturity profile) 가 시변 모수**. v2 H3 (debt maturity stratify) 가
직접 이 발견을 반영.

### D-4. Cross-sectional specialization value (Pacific Rim 학술)
Researchgate 350174334 ("Varying interest rate sensitivity: Cross-country evidence from REITs"):
sub-sector specialization value 가 cross-country 일관. ★ **paper 본문 access 403 forbidden** —
abstract 만 인용. v2 H1 (long-WALT cross-section) 의 학술 base 는 본 paper + Allen et al. (2000).

### D-5. ★ WALT × rate β 학술 reference: paywall 한계
Shulman UCLA Anderson Letter PDF: binary corrupt, 본문 미추출.
Researchgate 본문: 403 forbidden.
→ v2 H1 의 "long-WALT 가 short-WALT 보다 rate-shock 시 underperform" 가설은 **이론적 mechanism**
(long-duration cash flow asset 의 discount rate 민감도 ↑) + 2023-2024 cross-sectional 실증
(REIT analytics, Nareit T-tracker 시계열) 으로 검증. 학술 paper 정량 reference 직접 인용 X.

---

## §E. 지표 의미·관계도

### E-1. 핵심 지표 5 cluster
1. **valuation**: AFFO yield, P/NAV, implied cap rate spread (vs 10Y)
2. **growth**: same-store NOI growth, occupancy delta, FFO/AFFO growth YoY
3. **risk**: realized vol, debt/EBITDA, fixed-charge coverage, WALT (duration proxy)
4. **macro sensitivity**: rate β, credit β, dollar β (international REIT only)
5. **sector archetype**: 9 sub-sector membership (soft)

### E-2. 핵심 관계도 (v2 partial-corr prior 후보)
- **AFFO yield ↔ implied cap rate spread**: 회계 정의식 (둘 다 NOI 분자 + 가격/EV 분모)
  → 강한 양의 partial-corr (force-include).
- **rate (10Y) ↔ REIT total return**: 직접 음 (discount rate channel + cap rate floor),
  단 conditioning_set = real_gdp + credit_spread (regime separation).
- **HY OAS ↔ REIT**: 직접 음 (refinancing cost), conditioning_set = realized_vol.
- **same-store NOI ↔ occupancy**: 회계 직접 (NOI = rent × occupancy, lagged 1-2Q).
- **leverage (debt/EBITDA) ↔ credit β**: 직접 양, conditioning_set = sector_archetype + WALT.
- **WALT ↔ rate β**: 직접 양 (long-duration 가 rate β 절대값 ↑), conditioning_set = sector_archetype.
- **public-private cap rate spread ↔ 12m forward REIT return**: lagged 양 (mean-reversion, H2).

### E-3. 지표 family 매핑 (study_session.yaml block2 family enum)
- valuation: AFFO_yield, fwd_EP, P/NAV, implied_cap_rate_spread
- quality: leverage_debt_ebitda, fixed_charge_coverage, ROE, margin_trend
- growth/revision: same_store_NOI_growth, occupancy_rate, FFO_growth, eps_revision_breadth
- momentum: mom_12_1
- macro_sensitivity: beta_rate, beta_credit, beta_dollar, beta_oil
- macro_driver: sector_archetype (라벨)
- risk: realized_vol, WALT_years, FFO_payout_ratio

---

## §F. v1 yaml 보완 포인트 (v2 study_session.yaml 작성 시 반영)

### F-1. block1 lens (정성 렌즈)
- **pricing_principle**: §C 의 DCF 근사 공식 그대로 + ERP_REIT 3-5% historical anchor 추가.
- **report_relations**: §E-2 의 관계도 7 항목으로 보강.
- **regime_reading**: ★ 단정 표현 모두 가설형으로 강등 ("Reflation → industrial 강세" → "Reflation
  에선 NOI growth 기대 + 낮은 rate 의 dual tailwind. 단 H4 (window flip) 및 사전 priced
  expectation (cap rate spread) 에 의존").
- **estimation_note**: ★ 2024 실측 정량 명기 (industrial -17.7% / office +21.5%) + Q2 2024 spread
  130bp + 회복 추세.

### F-2. block2 indicators
- `affo_yield` transform: `own_history_z` → `sector_adjusted_z` (AFFO/FFO 비율 sector standard 반영).
- `implied_cap_rate_spread` baseline 산출: H2 검증 시 Nareit T-tracker 시계열로 fresh 갱신.
- `debt_maturity_wam_years` (NEW) 추가: H3 stratifier. EDGAR 10-K 텍스트 (lease + debt schedule).
- `sub_sector_cap_rate_spread` (NEW) 추가: §B 의 sector-level breakdown. private = NCREIF ODCE.

### F-3. block3 relationships
- §E-2 의 7 force-include 후보 (이론·회계 강한 관계) 정수화.
- 단순 "Reflation → industrial" 단정 매핑 카드 모두 제거 (반증됨).

### F-4. block4 weight_rules
- granularity = sector_archetype × ticker (debt_maturity_wam stratifier).
- H4 (window flip) 발견 반영: window 명시된 modulate_by — `[regime, window_length, industry, name_specific]`.

### F-5. block5 confidence_hooks
- H1~H5 모두 confirm/reject signal + e-process 누적 + lens·weight feed-back path 명시.
- ★ H2 의 reject (b) "deep discount 6Q+ 지속" 의 mechanism = §B 의 private write-down 필요 폭
  (industrial/retail 20%+ / apartment/office 30%+).
- ★ H5 의 reject 는 이미 2024 데이터로 trigger 됨 → block1 lens 의 단정 매핑 제거가 그 결과.

### F-6. block6 collector_plan
- ★ NEW: NCREIF ODCE private appraisal cap rate (membership 유료) — H2 의 정수 baseline.
- ★ NEW: Nareit T-Tracker quarterly time-series (FFO/AFFO/NAV/implied cap rate aggregate)
  — 무료 download (Excel/PDF).
- 기존 block6 항목 (EDGAR XBRL 확장, yfinance analyst estimates, GICS sub-industry mapping) 보존.

### F-7. block7 code_change_plan
- 변화 무 (§4 4단계 코드 구조는 v1 분석 유효). 단 `_extract_indicator_z` 의 series_id mapping 에
  `debt_maturity_wam_years` + `sub_sector_cap_rate_spread` 2 항목 추가.

---

## §G. 2-3 단계 진입 준비 (실데이터 시계열 검증)

승인 후 2-3 진입 시 priority 순:

1. **H4 (window flip meta-가설)**: 단순 cross-tabulation — Nareit T-tracker monthly + Yahoo
   VNQ/sector ETF 시계열로 1d/30d/12m/24m ranking flip 산출. → `raw/validation-H4.md`.

2. **H1 (long-WALT cross-section)**: WALT proxy = sector-average (hotel 1y, apartment 1y,
   office 6y, industrial 5y, healthcare 12y, datacenter 8y, storage 1y, retail 7y) 로 1차
   검증. ticker-level WALT 는 후속 EDGAR 텍스트 NLP. → `raw/validation-H1.md`.

3. **H2 (cap rate spread mean-revert)**: ★ Nareit T-Tracker Excel/PDF 직접 download +
   NCREIF private cap rate (free aggregate 또는 차선) cross-merge. spread Z-score 시계열 →
   12m forward Rank-IC. baseline 정수치 fresh 갱신. → `raw/validation-H2.md`.

4. **H3 (debt maturity stratify)**: EDGAR 10-K debt schedule 텍스트 NLP → ticker-level
   debt WAM. 부족 시 sector-average proxy. cross-section Rank-IC. → `raw/validation-H3.md`.

5. **H5 (sub-sector × regime 단순매핑 반증 잔여 확인)**: 이미 2024 데이터로 partial reject.
   2010-2024 historical 시계열로 quantitative reject 확인 마무리. → `raw/validation-H5.md`.

산출: validation-{H1..H5}.md 5건 + **`study_session.yaml` (v2, 7 block)**. v1 yaml 은 raw 참고로
보존 (main 명시).

---

## §H. 미해결 항목 (잔존 caveat)

1. **Shulman UCLA Letter PDF** = binary corrupt, 본문 미추출. 학설 정량 reference 직접 인용 X.
   v2 lens 의 학술 reference 는 secondary (search synthesizer 인용) 한정.
2. **Researchgate cross-country paper** = 403 forbidden. Pacific Rim sub-sector specialization
   value 정량 미확인. abstract 만 잔존.
3. **WALT × rate β 학술 정량** = direct paper access 한계. v2 H1 은 부호 가설만, 정량은 실데이터
   검증으로.
4. **Q4 2024 = 120 bp cap rate spread** = primary 부분 검증 (Q2 2024 130 bp). H2 검증 시 fresh
   산출로 대체.
5. **Stagflation 1970s REIT data** = direction.md R1 빈틈 잔존. 2-3 실데이터 검증 시 NAREIT
   1970s monthly index (가용 시) 또는 시기적 한계로 가설만 잔존.

→ 위 5 caveat 는 모두 2-3 단계 (실데이터 검증) 에서 실측으로 대체. v2 study_session.yaml 작성 시
caveat 명시 후 진행.

---

## §I. raw / archive / memory 누적 file 목록 (2-2 완료 시점)

study-research/reit/:
- direction.md (2-1 종합)
- raw/round-1.md / round-2.md / round-3.md (2-1 라운드)
- raw/theory-notes.md (본 파일, 2-2)
- raw/lens-rationale.md / data-availability-audit.md (v1 참고용 보존)
- study_session.yaml (v1, 폐기 X — v2 작성 시 reference)

~/.claude/docs/archive/research-raw/:
- reit-pricing-theory-native-20260530.txt (R1)
- reit-validation-methodology-native-20260530.txt (R2)
- reit-q1-2025-cross-verify-native-20260530.txt (R2)
- reit-2024-subsector-verified-native-20260530.txt (2-2 환각검증 #1)
- reit-cap-rate-spread-verified-native-20260530.txt (2-2 환각검증 #2)
- reit-sector-cap-spread-q2-2023-native-20260530.txt (2-2 NEW finding)

~/.claude/memory/research/:
- reit-pricing-theory.md (R1 summary)
- reit-validation-methodology.md (R2 summary)
- (theory-notes 단계는 별도 memory file 생성 — 다음 액션)

~/.claude/memory/MEMORY.md: R1 + R2 인덱스 2줄 추가 완료.

---

## §J. main 보고 메시지 초안

```
[reit→main] 2-2 이론 학습 완료. raw/theory-notes.md 산출. ★ 환각 검증 결과:
(1) ✅ 2024 industrial -17.7% Nareit webinar recap primary confirmed.
(2) ✅ 243 bp Q3 2022 peak Nareit market commentary primary confirmed.
    ⚠️ Q4 2024 120 bp 는 Q2 2024 130 bp primary 와 회복추세 일관, ±10bp 잠정.
★ NEW: Q2 2023 sub-sector cap rate spread breakdown 확보 (Office 259 / Apt 194 / Retail 150 /
Industrial 93 bp). v1 의 "Reflation→industrial 강세" 단정 반증의 mechanism = industrial 의
이미 좁은 spread (낙관 priced) + 2024 multiple contraction. NEW: private appraisal +15bp/Q ×
7Q trajectory + closing-gap arithmetic (industrial 20%+ / office 30%+ write-down).
★ 미해결 5 caveat (Shulman PDF binary 깨짐 + Researchgate 403 등) 모두 2-3 실데이터 검증으로 대체 계획.
★ 2-3 진입 priority: H4 → H1 → H2 → H3 → H5. study_session.yaml v2 + validation-{H1..5}.md 산출.
파일: D:/projects/Inv/study-research/reit/raw/theory-notes.md.
```
