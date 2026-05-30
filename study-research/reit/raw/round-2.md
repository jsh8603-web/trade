---
tags: [type/raw-round, study_id/reit, round/2, source/websearch-native]
date: 2026-05-30
round_focus: ②이론 검증방향 — 학술 검증 방법론 + Round 1 정량 cross-verify
note: STUDY-KIT §2 v2 의 2-1단계 자문 라운드 2. Round 1 환각 검증 시도 + 검증방법론 식별.
---

# Round 2 — 이론 검증방향 (학술 방법론 + Round 1 cross-verify)

## A. 라운드 질문 설계 (Round 1 → 2 자가 점검 반영)

Round 1 끝의 빈틈 식별 5개 중 본 라운드 우선 2개:
1. **WALT × rate β 정량 관계 학술 reference** (Round 1 "검색 부재" 빈틈)
2. **Round 1 정량 환각 검증** — implied-private cap rate spread 243bp/120bp + 2024 industrial -17.7%

남은 3개 (Stagflation REIT, sub-sector regime 실증, 검증 방법론 세부) → Round 3 또는 2-2 이론 학습.

## B. 사용 도구

- WebSearch (학술 reference 검색) — 6 source 확보
- WebFetch (Nareit primary source PDF) — ★ FAIL (10MB content limit)
- WebFetch (Nareit blog HTML 작은 페이지) — 성공, 2025 데이터 cross-verify
- raw 저장: `~/.claude/docs/archive/research-raw/reit-validation-methodology-native-20260530.txt` + `reit-q1-2025-cross-verify-native-20260530.txt`

## C. 핵심 발견 (Query 결과)

### C-1. 학술 reference — REIT rate sensitivity

**가용 reference 6 source**:
1. **UCLA Anderson Ziman (Shulman) Economic Letter** — 2015 실무 정리 ★ readable
2. **Researchgate "On Interest Rate Sensitivity of REITs: 20 Years Daily Data"** — academic
3. **Researchgate "Interest Rate Sensitivities of REIT Returns"** — academic
4. **Researchgate "REIT characteristics and the sensitivity of REIT returns"** — academic
5. **Researchgate "Varying interest rate sensitivity: Cross-country evidence from REITs"** — ★ cross-sectional 핵심
6. **Neuberger Berman "Returning to REITs"** — practitioner post-2022 outlook

**핵심 학설 (search synthesizer 정리)**:
- REIT-rate 관계: negative (short + long 양쪽)
- 인용 학자: **Giliberto & Shulman (2017)** + Chen-Tzang (1988) + Allen et al. (2000) + He et al. (2003)
- Cross-sectional sensitivity: property sector 별로 다름 (Pacific Rim 연구에서 "specialization value" 증거)

### C-2. ★ 핵심 통찰 — 학술 결론의 *inconclusive* 상태

"empirical evidence on REIT-rate relationship is INCONCLUSIVE — varies across countries,
econometric techniques, interest rate proxies (short vs long, level vs change), and sample periods."

→ **v1 yaml 의 "β_rate ≈ -1.0 ~ -2.0" 단정은 근거 약함**. 학술계 자체가 결론 불일치.

### C-3. ★ Pre-2022 debt maturity extension = rate sensitivity 시변

> "Real estate companies used the long period of low rates and flat yield curves before 2022 to
> extend their debt maturities and thereby mitigate their sensitivity to higher rates."

→ rate β 는 **시변 (time-varying)**. 정량값이 sample period 에 강하게 의존. rolling β 만으로
충분하지 않음 — 자본구조 (debt maturity profile) 도 변수.

## D. Round 1 정량 환각 검증

### D-1. 243bp / 120bp implied-private cap rate spread
- **목표**: Nareit T-tracker Q1 2025 PDF 직접 확인
- **결과**: WebFetch FAIL (PDF 10MB 한계). primary source 직접 검증 *미완*.
- **차선**: Nareit blog (HTML 작은 페이지) cross-check → ★ blog 에 cap rate spread 언급 없음.
- **잠정 결론**: Round 1 의 243bp/120bp 수치는 search synthesizer 가 어딘가에서 종합한 것이라 환각
  가능성 잔존. 2-2 이론 학습 단계에서 Green Street 또는 Nareit 다른 source 로 cross-verify 필수.

### D-2. 2024 industrial -17.7% / office +21.5%
- **목표**: Nareit subsector index 직접 확인
- **결과**: Round 1 search 결과 자체가 Nareit 인용. blog HTML 에는 2024 breakdown 없음 (2025 만).
- **부분 cross-verify**: 2025 YTD Industrial +17.0% (회복), Healthcare YTD +28.5% (지속 강세).
  Industrial 의 2024→2025 swing (-17.7% → +17.0%) = sector return 의 high temporal volatility 증거.
- **잠정 결론**: Industrial 의 시변 사례 패턴 (2024 worst → 2025 top 5)은 cross-verify 의 *간접* 증거.

### D-3. ★ NEW cross-verify 발견 — 2025 데이터

**2025 YTD**:
- Health care: **+28.5%** (#1)
- Industrial: +17.0%
- Diversified: +15.5%

**December 2025 단일월**:
- LEADERS: Timberland +4.5%, Lodging +0.8%, Gaming +0.7%
- LAGGARDS: **Health care -8.4%** (YTD 1위가 월단위로 worst), Office -6.4%, Self-storage -3.1%

**Rate 환경**: 10Y Treasury Dec 2025 +16bp → year-end 4.18%.

★ Healthcare 가 YTD 1위 (+28.5%) 인데 Dec 한달 -8.4% 로 worst.
→ rate-shock window (Dec 10Y +16bp) 와 healthcare β_rate 음 가설 *일관*.
→ 하지만 같은 healthcare 가 YTD 평균은 1위 (rate cut 기대 누적) → **window-conditional sector return**.

## E. ★ 의미 — v1 yaml 의 근본 결함

Round 1 + 2 합쳐 v1 yaml 의 3가지 약점:

1. **이론 단정**: "β_rate -1.0 ~ -2.0" 정량 = 학술계 inconclusive 데도 단정.
2. **시변 무시**: pre-2022 debt maturity extension 으로 β 변동, 자본구조 변수 누락.
3. **window 단일**: regime → sub-sector 매핑이 단일 window (예: "Reflation → industrial 강세").
   실제는 window 길이 (일/월/연/multi-year) 에 따라 ranking flip.

→ **v2 의 lens 는 단정 대신 *window-conditional 반증가능 가설* 로 reframe** 필요.

## F. Round 2 → Round 3 자가 점검

Round 3 (이번 자문 사이클 마무리) 의 focus = **③ 가설 초안 + 반증조건 종합**:
- C-2 의 inconclusive 학술 합의 → 우리 가설은 *반증가능* 으로 짜야 (단정 금지).
- C-3 의 시변 자본구조 → 가설에 "자본구조 stratify" 차원 포함.
- D-3 의 window flip → 가설 각각에 "evaluation window 명시" 필수.

Round 3 가설 후보 (반증조건 포함, 초안):
- H1 (rate β cross-section): rate-shock window 내 long-WALT REIT < short-WALT 90d cumulative.
  반증: rolling 24m cross-section Rank-IC e-CUSUM 단측 붕괴.
- H2 (cap rate spread mean-revert): spread Z<-1.5 → 12m forward total return Rank-IC > 0.15.
  반증: 6Q 지속 deep discount + Rank-IC < 0.
- H3 (debt maturity stratification): debt maturity > 5y REIT 가 rate-shock 시 < 3y REIT 보다
  *덜* 빠짐 (Round 2 C-3). 반증: 2022~2024 cross-section 에서 정반대.
- H4 (window-conditional sector flip): YTD 누적 1위 sector 가 단일월 worst 가능 (D-3). 반증조건:
  YTD 누적과 단일월 ranking 상관 > 0.5.
- H5 (sub-sector × regime 단정 약함): "Reflation → industrial 강세" 단순 매핑 무. 반증 = 2024
  데이터 (industrial -17.7% in Reflation-like rate-cut anchor).

Round 3 = 위 5 가설 + 반증조건 정련 + direction.md 종합.

## G. 출처

- [Shulman UCLA Anderson Letter 2015 (PDF)](https://www.anderson.ucla.edu/documents/areas/ctr/ziman/UCLA_Economic_Letter_Shulman_01-16-15x.pdf)
- [On Interest Rate Sensitivity of REITs (20Y Daily, Researchgate)](https://www.researchgate.net/publication/317830157_On_the_Interest_Rate_Sensitivity_of_REITs_Evidence_from_Twenty_Years_of_Daily_Data)
- [Interest Rate Sensitivities of REIT Returns (Researchgate)](https://www.researchgate.net/publication/5129600_Interest_Rate_Sensitivities_of_REIT_Returns)
- [REIT characteristics and sensitivity (Researchgate)](https://www.researchgate.net/publication/5151598_REIT_characteristics_and_the_sensitivity_of_REIT_returns)
- [Cross-country evidence REITs (Researchgate)](https://www.researchgate.net/publication/350174334_Varying_interest_rate_sensitivity_of_different_property_sectors_Cross-country_evidence_from_REITs)
- [Returning to REITs (Neuberger Berman)](https://www.nb.com/handlers/documents.ashx?id=54b17896-bb5e-4b1d-82b7-87a233128c19)
- [REITs Post Narrow Gains in 2025 (Nareit blog, primary 정량)](https://www.reit.com/news/blog/market-commentary/reits-post-narrow-gains-2025)

★ 환각 검증 status (Round 2 종료 시점):
- ❌ 243bp/120bp implied-private spread: primary 미검증 (PDF FAIL). 2-2 단계에서 Green Street 또는
  다른 Nareit page 로 cross-verify 필수.
- ⚠️ 2024 industrial -17.7%: blog 에 부재 (2025 만). search synthesizer Nareit 인용 신뢰 의존.
  2-2 단계에서 Nareit subsector historical performance 페이지 직접 fetch.
- ✅ 2025 YTD healthcare 28.5% / industrial 17.0% / Dec 10Y +16bp: 직접 cross-verified.
- ✅ Giliberto-Shulman (2017) 외 학설: ResearchGate 다중 출처 일관.
