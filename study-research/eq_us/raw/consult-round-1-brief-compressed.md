## 자문 요청 — 미국 주식 (eq_us) 평가 시스템 설계 (GICS 11 sector Tier 차등 × regime 동적 가중)

### 배경 (자기완결)

한국 주식 (eq_kr) baseline v2 7-Phase 방법론으로 사용자 검증 완료. 미국 주식 동등 적용 중. 평가 시스템 = 종목 buy 시 score = Σ wᵢ × zᵢ(indicator) (정형 합성 + LLM down-only). wᵢ 가 regime·산업·종목특성에 따라 동적 변화 = 본 study 산출물.

본 R1 = 자문 첫 라운드. R2-R3 수렴 후 direction.md (이론수집 + 검증방향 + 핵심가설 N) → Phase 4+.

### 외부 모델 5 금지

1. 점추정 prior 박제 금지 (IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트)
2. 합성·시뮬 데이터 금지 (실제 수집기 PIT만)
3. 자문 그대로 코드화 금지 (supervisor 비판 후 채택)
4. Single-source 단정 금지 (학술 + 실무 + 1차 데이터 3중)
5. Small-N 단정 금지 (cell N<24 유의 주장 X)

### 이미 있는 입력 (재사용 baseline)

eq_kr 12 가설 미러링 후보: 외국인 net buy → 대형 KOSPI t+5~20d return 양 / 밸류업 Index 편입 → re-rating / USDKRW × export_share 교호 / 반도체 cycle → fwd EPS lag / 모멘텀 약효 / 외국인 flow regime × Tier 교호 등.

eq_us_cyclical M3 검증 (n=756 daily 2021-12 ~ 2024-12):
- ★ β_dxy 가 β_us10y 보다 1자리 차이 (전 cyclical sector β_dxy in -0.58 ~ -1.62, β_us10y 약 0). rate 가 거의 dollar 채널 경유.
- ★ epoch 별 dollar 강도 가변 (E1 긴축 R2=0.21 / E2 전환 R2=0.29 / E3 재상승 R2=0.13 / E4 완화 R2=0.07).
- ★ SOXX = 고듀레이션 amplifier (epoch swing -50% → +89%). XLE = anti-cyclical hedge (oil rank-IC +0.602).
- ★ within-cyclical sleeve mean corr 0.617 → Kish eff_N=1.47.

eq_us_defensive ⚠️ 합성 의심 (synthetic 240m, seed 20260530). 5 archetype 권고 = staples / utility / healthcare / bank / insurance. real rate 상승 시 utility 음 / bank 양 (부호 반대 sub-sleeve).

### 자문 질문 Q1-Q10

Q1. GICS 11 sector Tier 차등 분류 적합성. 제안 = T1 (IT XLK + Communication Services XLC, 시총 50% 이상), T2 (Financials + Health Care + Consumer Disc + Industrials + Energy, 각 5-12%), T3 (Staples + Materials + Utilities + Real Estate, 각 2-5%). 대안 = (a) factor 기반 5 sleeve (growth/value/quality/low-vol/cyclical) (b) macro 민감도 4 sleeve (rate-sensitive bond proxy / dollar-sensitive multinational / credit-sensitive levered / pure equity factor) (c) Mag7 단독 sleeve + 나머지 10 GICS. 미국 실측 시총 분포 + factor 노출 구조 정합?

Q2. 미국 1-3 순위 alpha driver. 한국 1순위 = 외국인 net buy. 미국 후보 5 = (a) Fed funds path expectation (FOMC dot plot vs OIS) (b) AI capex concentration (Mag7 capex yoy) (c) total shareholder yield (buyback + dividend) (d) HY OAS regime 4분류 (e) earnings revision breadth. 학술 + 실무 종합 1-3 순위는? 각 driver 의 measurable signal source + IC magnitude + regime stability?

Q3. cyclical M3 finding vs defensive 통합 reconcile. cyclical = β_dxy 우위, defensive = real rate 직접 (bank 양 / utility 음). (a) cyclical dollar 채널 우위 = 표본 한정 (2022-2024 강달러)? (b) defensive rate 직접 = sub-sleeve 효과 (bank NIM)? (c) GICS 11 sector 통합 sleeve 정의 시 default channel?

Q4. 5 archetype (defensive) GICS 11 sector 매핑. staples → XLP / utility → XLU / healthcare → XLV (sub: pharma/biotech/MD/HMO 분기) / bank → XLF (sub: 은행/asset manager/payments/insurance 분리) / insurance → XLF 안 또는 별도. 미국 GICS + Damodaran sector valuation 정합 sub-sleeve 분류? T1 안 sub-cluster (AI semis / hyperscaler / software platform) 학술 baseline?

Q5. Mag7 / AI capex 집중 → reflexive loop 위험. S&P 500 30% 이상 Mag7. AI capex thesis 강화 → Mag7 weight 상승 → 시장 corr 상승 → AI thesis 더 강해 보임 → cascade 위험 (2024-08 mini-crash). 반영 방법 = (a) Mag7 단독 sleeve 격리 (b) toraniko factor-neutralized IC (c) ticker shrinkage cap 0.2 (d) regime-conditional (AI capex yoy 30% 이상 regime = Mag7 weight 상승).

Q6. Real Estate (XLRE) reit study 중복 경계. Inv 시스템에 별도 reit study (H1 REJECT 이력) 존재. XLRE 처리 = (a) eq_us 안 포함 (Tier 3) + reit partial-corr 통합 (중복 우려) (b) 분리 (eq_us = GICS 10) (c) reit study 산출 input 수용?

Q7. PIT/lookahead 미국 검증 인프라. EDGAR 10-Q 45d / 10-K 90d (정확)? ALFRED vintage 가용 (yes). survivorship-bias-free universe OSS 대안 = Sharadar / Norgate / yfinance + 자체 historical / FinanceDatabase + EDGAR XBRL. OSS only 로 PIT universe 가능?

Q8. validate 인프라 OSS. skfolio CombinatorialPurgedKFoldSplit + toraniko factor model + Newey-West HAC SE + block bootstrap 미국 적용? 추가 OSS = Ken French 5-factor, QMJ (Asness-Frazzini-Pedersen), BAB (Frazzini-Pedersen), alphalens, pyportfolioopt 어느 것 권고?

Q9. 핵심 가설 5-10 초안 (반증조건 포함). Q1-Q8 답에 기반 본 eq_us study 핵심 가설 5-10. 예 = AI capex x Mag7 fwd EPS lag 1-2Q / HY OAS regime x sector rotation / total shareholder yield vs 10Y Treasury → value alpha / Fed funds path surprise event study / earnings revision breadth → fwd 3M return.

Q10. 미해결 confound bias. 미국 시장 study confound + selection bias + 데이터 한계 우려 5 이상.

### 출력 양식 (강제)

각 Q1-Q10 에 5 필드 응답:
- 답변 (1-3 paragraph, 결론 먼저)
- 근거 (학술 [저자 연도 DOI/URL] + 실무 [리포트/정책 발행자 연도] + 1차 데이터 [FRED ID / SEC form / OSS lib])
- 정량 magnitude (IC mean +- SE / R2 / lag / regime stability — range/CI 포함, 점추정 단독 X)
- 반증조건 (Q9 가설 답변 시 필수 — e-value, CI bound, regime transition signal)
- confound confidence (교란 변수, 표본 한계, 미국 특화 의문, low/medium/high)

각 Q 200-500 단어 (총 3000-5000 단어). 환각 reference 금지 (실제 DOI/URL/SEC form/FRED ID).
