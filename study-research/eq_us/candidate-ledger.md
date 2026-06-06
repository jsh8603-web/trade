---
tags: [type/candidate-ledger, study/eq_us, purpose/easy-review]
date: 2026-05-31
study_id: eq_us
phase_snapshot: Phase 3 (R1+R2 자문 수렴 완료, direction.md 미작성) → Phase 3.5 진입 직전
purpose: |
  Phase 3 자문 (Claude R1/R2 + Gemini R1/R2) + eq_us_cyclical/defensive input + eq_kr baseline +
  M3 findings 에 나온 지표·이론·가설 후보 전체 + [채택/이연/미채택/환각회피] + 사유.
  ★특히 "논의·검증됐으나 yaml/코드 미투입" 항목 (direction.md 미작성 상태라 거의 전부) 정직 박제.
note: |
  MAIN-DISPATCH.md (Tier 차등 분할 명령) / progress.md (Phase 추적 + 사용자 박제 2건) /
  raw/consult-round-{1,2}-{claude,gemini}.md (4 raw) / eq_us_cyclical (17 indicators + M3) /
  eq_us_defensive (실측 H1~H4 + 5 archetype) / eq_kr baseline (v2 7-Phase 미러링) — 6+ 출처에
  흩어진 후보를 1파일로 집약. ★현 상태 = direction.md 미작성 → 거의 모든 채택 후보가 "pending injection".
basis_raw:
  - raw/consult-round-1-claude.md (Q1~Q10, Opus 4.8 fresh, 5 필드)
  - raw/consult-round-1-gemini.md (Q1~Q10, Gemini 2.5 Pro, 5 필드)
  - raw/consult-round-2-claude.md (QR2-1~6, 절충 + 환각 cross-verify)
  - raw/consult-round-2-gemini.md (QR2-1~6, 입장 수정 + 환각 self-verify)
  - study-research/eq_us_cyclical/{study_session.yaml, candidate-ledger.md, m3-findings.md}
  - study-research/eq_us_defensive/{study_session.yaml, summary.md, direction.md} (★합성 의심 P0 재검증 대상)
  - study-research/eq_kr/methodology-final-for-main-dispatch.md (v2 7-Phase baseline)
---

# eq_us 지표·이론·가설 후보 원장 (candidate ledger)

> **현 phase = Phase 3 R1+R2 자문 수렴 완료, direction.md 미작성** (Phase 3.5 진입 직전).
> ★대부분의 "채택 후보" = R1+R2 양 채널 수렴 의견 + cyclical/defensive 검증 결과 ★but 아직 yaml/코드 X.
> 다음 세션이 direction.md 작성 시 이 ledger 를 ① 채택 후보 → direction.md ②③ 매핑 ② 이연 → collector_plan 등록 ③ 미채택 → Q&A 박제로 활용.

---

## ✅ 채택 후보 (Phase 3 자문 수렴, direction.md 작성 시 ② alpha driver / ③ 핵심 가설로 진입 예정)

### ✅-A. R1+R2 양 채널 (Claude + Gemini) 합의 항목 = 강 prior

| 후보 | family | 합의 근거 | direction.md 매핑 (예상) |
|---|---|---|---|
| **earnings_revision_breadth** (ERB) | revision | Claude R1 Q2 1순위 + Gemini R1 Q2 1순위 = **양 채널 1순위 합의**. monthly IC 0.03-0.06 (Claude tentative), SE ±0.015 (Gemini). I/B/E/S 가장 안정적 cross-sectional alpha | direction.md ② 1순위 alpha driver, ③ H1 (반증=IC CI 하한 ≤0 OR FF5+Mom intercept t<2) |
| **total_shareholder_yield** (buyback + dividend) | valuation/quality 하이브리드 | Claude R1 Q2 2순위 + Gemini R1 Q2 2순위 = **양 채널 합의**. L/S spread 역사 2-4%/yr, post-2010 t-stat 약화 (decay). Boudoukh-Michaely-Richardson-Roberts 2007 JF anchor | direction.md ② 2순위 alpha driver, ③ H2 |
| **HY_OAS_regime** (BAMLH0A0HYM2) | macro_driver | Claude R1 Q2 3순위 + Gemini R1 H3 = **regime conditioner 합의**. Credit cycle → cyclical-defensive rotation. OAS +X bps/Q transition signal | direction.md ② 3순위 regime conditioner, ③ H3 |
| **real_rate (DFII10) — sub-sleeve 부호 분기** | macro_sensitivity | Claude R1 Q3 (sub-sleeve mechanical) + Gemini R1 Q3 (구조적) + eq_us_defensive H1 실측 XLU −0.167 / XLF +0.129 n=5844 = **3중 합의**. utility/REIT/long-duration NEG, bank POS | direction.md ② regime conditioner, ③ H4 (Q9 H5 = bank +/utility − 부호 안정성) |
| **PCA macro-sleeve (3-5 PC) > Tier 11 GICS 독립** | structural | Claude R1 Q1 + Claude R2 QR2-3 + Gemini R2 QR2-3 = **양 채널 합의**. 80% 분산 4-6 PC. cyclical 내 mean corr 0.617 eff_N 1.47 (사용자 실측) anchor | direction.md ① framework 결정 (Tier 시총 분할 기각 → macro-sleeve) |
| **Mag7 GICS 3 sector 파편화** (XLK+XLC+XLY) | factual | Claude R1 Q1 (Mag7 cross-sector finding) + Claude R2 QR2-5 (S&P 2018-09-28 effective) + Gemini R2 QR2-5 = **양 채널 confirm**. T1=XLK+XLC=시총50% 가설 깨짐 (AMZN/TSLA XLY 누락) | direction.md ① Tier 재정의 (Mag7 custom basket 격리) |
| **Reflexivity Monitor (intra-Mag7 corr + breadth)** | risk | Claude R1 Q5 (cap-down) + Claude R2 QR2-2 spec (corr>0.70~0.75 AND EW-CW spread<−3~−5%p **동시**) + Gemini R2 (방어형 대안 1, corr>0.65 AND breadth 하위 10%) = **양 채널 합의 (단 Gemini 는 cap-up Sharpe 인지 의무 명시)** | direction.md ③ H5/H6 (반증=monitor flag 발효 후 3-6m Mag7 drawdown 비-flag 대비 유의 차 없음 → monitor 무효) |
| **dollar 채널 = ρ-conditional regime switch** | macro_sensitivity | Claude R2 QR2-1 절충 (3 메커니즘: 다국적 translation 구조 + commodity 구조 + global risk artifact) + Gemini R2 QR2-1 입장 수정 (구조 + 표본 혼재) = **양 채널 절충 합의** | direction.md ③ H7 (반증=2015-2019 ρ<0.3 구간 β_dxy |β|<0.2 → artifact 설 확정 / |β|≥0.3 + 유의 → 구조설) |
| **factor decay (McLean-Pontiff 58% post-pub)** | meta | Claude R2 QR2-4 + Gemini R2 QR2-4 = **양 채널 동수치 인용**. shareholder yield (fundamental) > revision breadth (info) > pure statistical 순 resilience | direction.md ④ 미해결 confound, weight rules haircut 적용 |
| **EDGAR filing timestamp PIT (filer-grade 차등)** | infrastructure | Claude R1 Q7 정정 (Large=60d/40d, Non-acc=90d/45d, 사용자 45/90=Non-acc case) + Gemini R1 Q7 부분 동의 (Sharadar 도입 권장 별개) = **Claude 정확 사실 추가** | direction.md ④ PIT infrastructure, collector_plan EDGAR submissions API |
| **survivorship-bias-free 가격 = 무료 OSS 불충분** | infrastructure | Claude R1 Q7 + Gemini R1 Q7 = **양 채널 합의** (Sharadar $50/월 또는 Norgate $1000+/yr 권장). yfinance 단독 = delisted 누락 backtest 1.5-3.0%/yr 과대 (Gemini 정량) | direction.md ④ 의사결정 사항 (예산 대 alpha 결정), 사용자 framing 사항 |
| **FF5+Mom+QMJ+BAB residual intercept 의무** | methodology | Claude R1 Q8 + Gemini R1 Q8 = **양 채널 합의**. 모든 sleeve alpha = factor regression intercept (NW-HAC SE, CPCV) | direction.md ④ validation infrastructure, plan.md 명시 |
| **Deflated Sharpe + BH multiple testing 보정** | methodology | Claude R1 Q8 + Gemini Q8/Q10 (multiple testing bias 경고) = **양 채널 합의** | direction.md ④ statistics infrastructure |
| **2018 GICS 재편 사실** (Comm Services 신설) | factual | Claude R2 QR2-5 정밀 (S&P 2018-09-28 vs MSCI 2018-11-30 시점 불일치) + Gemini R2 QR2-5 = 합의 (단 Gemini 시점 차이 미언급) | direction.md ① 배경 사실 박제 |

### ✅-B. eq_us_cyclical input 재사용 (M3 실측 + cyclical 17 indicators)

| 후보 | 출처 | 합의 |
|---|---|---|
| **dollar_beta (β_dxy −0.58~−1.62 cyclical sector)** | M3 epoch R²=0.21 (E1) 강 | Claude R2 QR2-1 절충 인정 (다국적 + commodity + risk-mixed). Gemini R2 입장 수정. ★재사용 |
| **oil_beta (XLE rank-IC +0.602)** | cyclical 실측 | Gemini R1 미언급. cyclical-specific. ★XLE 분리 트랙 |
| **vix_beta (동시 IC −0.378)** | cyclical H4 검증 | Claude R1 Q10 risk-off 채널 합치. ★재사용 |
| **yield_curve_10y_2y (Estrella-Mishkin 12-18M 침체 선행)** | cyclical v2 신규 | Gemini R1 Q9 H3 인접. ★재사용 |
| **realized_vol_60d** | cyclical core | Claude R1 Q10 + cyclical AMP 2013 학술. ★재사용 |
| **ism_pmi_proxy** | cyclical (H3 REJECT 종속 재정의 대기) | Gemini R1 Q9 H1 인접. ★재사용 단 종속 재정의 |
| **price_mom_12_1** | cyclical (base 0.06 약화) | Claude R1 Q2 base driver 아님 (regime conditioner). ★재사용 단 base 강등 |
| **fwd_ep_normalized (Damodaran)** | cyclical H1 backbone (EDGAR 적재 대기) | direction.md ② 매핑 강 후보. ★재사용 |
| **operating_leverage_nm (Novy-Marx 2011 fixed_costs/book_assets)** | cyclical | Claude R1 Q9 H1 인접. ★재사용 |
| **asset_growth_yoy (Cooper-Gulen-Schill 2008 CMA)** | cyclical | Gemini R1 미언급. cyclical theoretical. ★재사용 |

### ✅-C. eq_us_defensive input 재사용 (P0 재검증 의무 — 합성 의심)

| 후보 | 출처 | 합의 / caveat |
|---|---|---|
| **rate_beta sub-sleeve sign-split (XLU −0.167 / XLF +0.129)** | defensive H1 실측 n=5844 | Claude R1 Q3 sub-sleeve mechanical + Q9 H5 = 합의. ★단 ★MAIN-DISPATCH §1 = "합성 의심 P0 재검증 대상" — 실측 재실행 의무 |
| **yield_curve_slope_beta (XLF contemporaneous IC +0.171)** | defensive H2 실측 n=317 월 | Stigum 3-6M lag 미관측 (시장 효율성). Gemini R1 H3 인접. ★재검증 후 재사용 |
| **HY_OAS REVERSED (Credit Stress -1.5%/월 sleeve excess)** | defensive H3 실측 n=9 월 | ★★n=9 month → small-N 단정 금지 (사용자 박제 5금지 #5). Frazzini-Pedersen BAB modern QE 시대 본 sleeve 에 X = **잠정 directional 신호 한정**. P0 재검증 시 LOO + Block Bootstrap autocorr 보정 의무 |
| **dollar β rate-regime 부호 반전** (E3 +0.21~+0.66 / E4 −0.01~−0.18) | defensive M3 실측 | Claude R2 QR2-1 절충 합치. ★재검증 후 재사용 |
| **5 archetype (staples/utility/healthcare/bank/insurance)** | defensive sleeve 구조 결정 | Claude R1 Q4 + Gemini R1 Q4 = sub-sleeve 분해 합의. XLF 분할 (banks vs asset mgr vs payments) 권장. ★재사용 |
| **dividend_safety + earnings_stability + fcf_yield + nim_trend + pb_ratio** | defensive 특화 (is_core:false) | Claude R1 Q2 2순위 (shareholder yield) 부분 정합. ★재검증 후 재사용 |

### ✅-D. cross-cyclical-defensive 관계 (M3 본질)

| 발견 | 출처 | 합의 |
|---|---|---|
| **cross_sector_mean_corr_60d ↑ + breadth 협소화 = cascade flag** | Claude R2 QR2-2 spec (corr>0.70~0.75 AND EW-CW spread<−3~−5%p) | Gemini R2 (방어형 대안 1) 합의. ★Reflexivity Monitor 핵심 trigger |
| **within-sleeve corr (cyclical 0.617 / defensive 0.556) vs cross-cyclical-defensive corr ~0.3-0.5 → 진짜 2축 분리** | Claude R2 QR2-3 + cyclical/defensive 실측 | Gemini R2 PCA 합치. ★ 2-4 sleeve 구조 > 11 tier |

---

## ⏳ 이연 — 자문·이론 합의됐으나 yaml/코드 미투입 (direction.md 작성 + collector_plan 등록 의무)

### ⏳-1. 데이터 수집기 미구축 (collector 인프라 의존)

| 후보 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|
| **EDGAR 분기 펀더 (10-Q ROE/buyback/cash flow)** | sec.gov EDGAR API 미적재. shareholder yield = SEC 10-Q cash flow statement (Boudoukh-Michaely-Richardson-Roberts 2007 정확 정의). cyclical edgar_provider.py 코드만 존재 | EDGAR submissions API + XBRL financial statement datasets + accel filer 등급 매핑 |
| **EDGAR filing acceptance timestamp** | Claude R1 Q7 정확 PIT rule = filing timestamp 사용 (가정 불필요). 현 시스템 = 45/90 flat 가정 (Non-acc case 만 정확) | EDGAR full-text/submissions API filing date 컬럼 적재 |
| **I/B/E/S revision (Refinitiv)** | 유료. FINNHUB 무료티어 estimate 대체 시도 가능 (cyclical 권고) | FINNHUB_API_KEY (무료) 발급 + estimate consensus 컬럼 |
| **Sharadar (Core US) 또는 Norgate survivorship-free 가격** | 유료. ★Claude R1 + Gemini R1 = 양 채널 권장. yfinance 단독 = delisted 누락 backtest 1.5-3.0%/yr 과대. ★예산 의사결정 필요 | 사용자 framing (예산 vs alpha 결정), 또는 OSS PIT 우회 (대형주만 + bias 명시) — Gemini R1 후속 질의 |
| **ALFRED vintage DB** (FRED PIT) | look-ahead bias 잔존 (cyclical 박제). CFNAI 등 깊은 revision 시리즈 risk. Gemini R3 cyclical 경고: 2019년 말 지표가 2021년에 크게 바뀜 | FRED ALFRED endpoint + vintage 컬럼 |
| **Ken French data library** (FF5+Mom+QMJ+BAB) | factor neutralization residual intercept 검증 위해 필수. Claude R1 + Gemini R1 합의 | pandas-datareader 또는 French 사이트 직접 다운로드 (무료) |
| **FOMC dot plot vs OIS surprise** (H7 Fed funds path surprise) | Claude R1 Q9 H7. duration-sorted event-study CAR. ★OIS market quote 적재 | FRED OIS futures (또는 CME group) + FOMC 메타데이터 |
| **EDGAR 은행 특화 파싱 (NIM/NPL/CET1/Y-9C)** | defensive sub-sleeve 신호 활성화 prerequisite (block6 #5~#8) | SECEdgar + 10-K 텍스트 regex + 은행 Y-9C XBRL |
| **CMS/Medicare drug 가격 이벤트 캘린더** | defensive XLV pharma sub-sleeve. IRA 협상 = pharma multiple 디레이팅 핵심 이벤트 | CMS.gov 정책 캘린더 + 수동 등록 |
| **GICS sub-industry + ETF holdings** (XLY/XLI/XLB/XLE/XLF/XLP/XLU/XLV/XLC/XLK/XLRE) | FinanceDatabase(MIT) 적재 미수행. Mag7 GICS 3 sector 파편화 정확 분류 + custom basket 정의 prerequisite | FinanceDatabase scraper + SPDR holdings (월간 CSV) |
| **0DTE options volume (CBOE)** | Gemini R1 Q10 신규 confound (장중 ±1.5% 왜곡 빈도 급증). 펀더멘털 시그널 압도 risk | CBOE Market Insights 데이터 (월간 CSV 또는 구독) |
| **Non-GAAP ↔ GAAP reconciliation (SBC 등)** | Gemini R1 Q10. 10-K reconciliation 표 파싱 | EDGAR 10-K 별도 파싱 모듈 |

### ⏳-2. 코드 모듈 미작성 (자문 합의됐으나 실 코드 X)

| 후보 | 위치 (예상) | 사유 | unblock 조건 |
|---|---|---|---|
| **2-cell regime (low-ρ / high-ρ rolling 252d corr 분위)** for dollar channel | falsify · 신규 모듈 | Claude R2 QR2-1 spec 합치 + Gemini R2 대안 1. continuous shrinkage w_dxy × (1−ρ²) 보다 small-N 안전 | rolling corr 모듈 + 분위 cell 생성 |
| **직교화 dollar (residual after rate regression)** | falsify · 신규 모듈 | Gemini R2 대안 2 + Claude R2 high-ρ cell 권고. dollar = rate orthogonalize 후 잔차만 sleeve 입력 | 회귀 잔차 추출 모듈 |
| **Mag7-EW − S&P493-EW spread (concentration factor)** | learn · 신규 모듈 | Claude R2 (regime indicator 활용 권고, priced factor 아님) + Gemini R2 (priced factor 대안 2, toraniko characteristic). ★role 차이 reconcile 필요 | EW 포트폴리오 구성 + spread 계산 + Z-score |
| **intra-Mag7 60d mean pairwise corr** | falsify · monitor 모듈 | Claude R2 QR2-2 spec (>0.70~0.75) + Gemini R2 (>0.65) | rolling corr 매트릭스 mean 모듈 |
| **S&P500 EW-CW return spread** | falsify · monitor 모듈 | Claude R2 (3m return spread<−3~−5%p) + Gemini R2 (하위 10%) | EW/CW 포트폴리오 차이 + Z-score |
| **%>200dma breadth** | falsify · breadth 모듈 | Claude R2 QR2-2 (<40% trigger 후보) | 200d MA crossing 카운터 |
| **PCA market-residual eigenvalue table** | learn · 신규 진단 | Claude R2 QR2-3 + Gemini R2 QR2-3 = 양 채널 사용자 직접 실측 권고 (raw + residual 양쪽). H8 결정자 | sklearn PCA + market-residualize 전처리 |
| **CombinatorialPurgedKFold (skfolio)** | falsify · validation pipeline | Claude R1 + Gemini R1 합의. cyclical block7 명시. 코드 미작성 | skfolio 라이브러리 + embargo 1-5% sample |
| **Newey-West HAC SE (q ≥ 3, 4Q overlap)** | falsify · 신규 함수 | overlapping window SE 미보정 (lead-lag IC t-stat 부풀 위험). Claude R1 Q8 명시. cyclical block7 동일 | statsmodels NW + Andrews 1991 data-dependent bandwidth |
| **Block bootstrap (Politis-Romano stationary)** | falsify · 신규 함수 | Claude R1 Q8 + cyclical block7. autocorr 시계열에 IID bootstrap 적용 금지 | block length = T^(1/3) + Politis-White 2004 자동 |
| **Benjamini-Hochberg FDR + Deflated Sharpe (Bailey-López de Prado)** | falsify · 신규 함수 | Claude R1 Q8 multiple-testing 표준. cyclical block7 박제만 | scipy.stats + BLP 2014 공식 |
| **E-value (VanderWeele-Ding 2017)** | falsify · 신규 함수 | Claude R1 Q9 (e-value 목표 >1.5 반증조건). 미측정 confounder 강도 측정 | VanderWeele-Ding 공식 코드화 |
| **alphalens IC tearsheet (decile spread + IC decay + turnover)** | report · 신규 | Claude R1 Q8 권고. cyclical 미작성 | alphalens 라이브러리 + 일별 IC 시계열 |
| **PIT revision IC 재추정 (look-ahead artifact 측정)** | falsify · 신규 | Claude R2 QR2-4 반증 spec: PIT (unrestated) vs backfilled IC 차이 >30% → look-ahead artifact 확인. ★Phase 5 실측 권고 #3 | I/B/E/S unrestated 데이터 적재 + 재계산 |
| **2015-2019 β_dxy sub-sample 회귀** | falsify · 신규 | Claude R1 Q3 + Gemini R2 Q3 + Claude R2 QR2-1 = 양 채널 ★사용자측 실측 권고 #1. dollar 채널 구조성 판정자 | FRED DXY + sector ETF + statsmodels 회귀 |
| **11-ETF PCA (raw + market-residual)** | falsify · 신규 | Claude R2 QR2-3 + Gemini R2 QR2-3 = 양 채널 ★사용자측 실측 권고 #2. eff_N 실측 | yfinance 11-ETF + sklearn PCA |
| **factor decay haircut 적용 (50% 일괄 또는 Dynamic Decay)** | card · weight_rules | Gemini R2 QR2-4 대안 1+2. 백테스트 alpha 일괄 50% 또는 short interest + turnover penalty | weight_rules base 항목별 haircut multiplier 추가 |
| **EDGAR bottom-up beta (산업 무차입 → D/E relever)** | card · 신규 | cyclical block7 박제, 미작성. Damodaran > 회귀 베타 | EDGAR D/E + 산업 분류 후 unlever-relever |
| **Damodaran implied ERP (월별 vintage)** | card · ERP source | NYU Stern 적재 미수행. cyclical block6 P1 동일 | NYU Stern 월간 CSV scraper |
| **GZ EBP 정공법** (TRACE + Merton DD) | learn · 신규 | cyclical 빈자판 BAA10Y-AAA10Y 대체. defensive 미언급. ★cyclical 한정? | TRACE_API_KEY 또는 Favara FEDS Notes 부록 |
| **regime predicted prob (filtered → predicted)** | inject · regime_classifier.py | cyclical 박제, 미작성. b(t) predictable 보존. smoothed prob 사용 금지 | regime_classifier.py predicted prob 모드 |
| **룰베이스 BMA + filtered HMM + BOCD overlay 계층** | inject · regime_classifier.py | cyclical 박제, 미작성 | 계층 prob 모듈 신규 |
| **judge lens_prompt 조립** (defensive 5 archetype lens 정성필드) | inject · judge.py · `_call_qwen_with_lens` | defensive summary §3.5 = "lens_prompt 조립 경로 신규". 시그니처 검사 기구현, 조립 함수 X | lens_prompt 빌더 함수 |
| **weight_card.delta_arch_by_type** (5 archetype 등록) | card · weight_card.py | defensive 박제, 미작성. staples/utility/healthcare/bank/insurance + cyclical early/mid/late 총 8 archetype | dict 등록 + composed_weights(pi) 보간 활용 |

### ⏳-3. Phase 5 산업 subagent 작업 대상 (Tier 차등 dispatch 시 산출 예정)

| 후보 | 산출 예정 위치 | 상태 |
|---|---|---|
| **T0 custom Mag7+AI basket sleeve** | industries/mag7/{summary.yaml, theory-notes.md, validation-*.md} | Mag7+AVGO/ORCL/AMD ± ASML US ADR (Claude R2 QR2-5 권고). ASML 네덜란드 = universe 정의 명시 |
| **T1 macro-sleeve 3-4축** (cyclical/defensive/rate-sensitive/commodity) | industries/{cyclical,defensive,rate_sensitive,commodity}/... | PCA 실측 (Phase 5 권고 #2) 결과로 최종 결정 |
| **T2 sub-archetype 8** (early/mid/late cycle + staples/utility/healthcare/bank/insurance) | industries/{sub}/... | cyclical 3 archetype + defensive 5 archetype 통합 |
| **5게이트 (G1~G5) eq_us 자체 정의** | plan.md §3 | cyclical 가 SSOT 부재로 자체 정의 — eq_us 동일 패턴 |
| **검증관 3-tier (Tier1 측정 / Tier2 James-Stein / Tier3 도메인)** | plan.md dispatch | cyclical 패턴 미러링 |
| **regime cell N gate 의무 (36 cell)** | 8 evaluation axes | eq_kr 미러링. N<24 = small-N 5게이트 |

### ⏳-4. Phase 6 평가 subagent (★supervisor 직접 평가 금지 — 사용자 박제)

| 후보 | 사유 | unblock 조건 |
|---|---|---|
| **별 평가 subagent (opus 1m) dispatch** | MAIN-DISPATCH §5 박제. main pass-bias 회피 미러 | Phase 5 산업 subagent 산출 후 |

---

## ⏳ 이연 — 가설 보류 / 우선순위 후순위

### ⏳-H. eq_us 핵심 가설 후보 (R1 Claude 7 + Gemini 5, R2 절충 결과)

| H | 출처 | 명제 | 보류 사유 |
|---|---|---|---|
| **H1** ERB → fwd 1-3M cross-sec | Claude R1 Q9 H1 | revision breadth → fwd return (+) | ★direction.md ③ 진입 예정 (채택), 단 PIT 검증 필수 |
| **H2** shareholder yield | Claude R1 Q9 H2 | yield → value alpha, real-rate regime 조건부 | ★direction.md ③ 진입 예정 (채택), 단 EDGAR 적재 의존 |
| **H3** HY OAS regime | Claude R1 Q9 H3 / Gemini Q9 H3 | OAS → cyclical↔defensive rotation | ★direction.md ③ 진입 예정 (채택), defensive 실측 REVERSED (n=9 small-N) 재검증 |
| **H4** dollar 채널 = 긴축-regime 조건부 | Claude R1 Q9 H4 | 2015-19 sub-sample 부호 안정 → 기각 (구조), |β|<0.2 → 채택 (artifact) | ★direction.md ③ 진입 예정 (절충), 실측 #1 의존 |
| **H5** bank(+) vs utility/REIT(−) rate-beta 부호 안정 | Claude R1 Q9 H5 | sub-sleeve mechanical 정합성 | defensive H1 실측 합치, P0 재검증 후 채택 |
| **H6** AI-capex → Mag7 fwd EPS lag 1-2Q | Claude R1 Q9 H6 / Gemini Q9 H5 | reflexivity monitor 동반 | ★direction.md ③ 진입 예정, Mag7 capex 10-Q 적재 의존 |
| **H7** Fed funds path surprise → duration-sorted CAR | Claude R1 Q9 H7 | FOMC event-study | ★OIS 적재 의존, Phase 4 후 진입 |
| **H8** sector eff_N ≤5 (PCA 80% 분산 >7 PC 시 기각) | Claude R1 Q9 H8 | macro-sleeve vs Tier 11 판정자 | ★실측 #2 의존, Phase 4 전 결정 필요 |
| **H9** Macro-Value Rotation (Real rate → Value IC) | Gemini R1 Q9 H2 | real rate 상승 → Value IC 견인 | Claude 미언급. Gemini-only, 후순위 |
| **H10** TSY > Dividend Yield IC 항상 | Gemini R1 Q9 H4 | shareholder yield 구성요소 분리 | Claude H2 일부 (TSY 통합). Gemini-only sub-test, 후순위 |
| **H11** 0DTE → 장중 ±1.5% 왜곡 | Gemini R1 Q10 | 펀더멘털 시그널 압도 | 신규 confound, Phase 4 plan 단계 결정. CBOE 데이터 의존 |
| **H12** Non-GAAP SBC 과대계상 | Gemini R1 Q10 | True-EPS 팩터 IC < Non-GAAP IC | 신규 confound, EDGAR 10-K reconciliation 파싱 의존 |
| **H13** Capital Cycle (asset_growth_yoy CMA) | cyclical 재사용 | Cooper-Gulen-Schill 2008 음부호 | cyclical multi-sector OOS 대기 |
| **H14** Mag7 격리 sleeve | Claude R1 Q5 + Gemini R1 Q1 | 나머지 493 cross-sectional IC 오염 방지 | ★Tier 재정의 필수 |
| **H15** XLRE 분리 (eq_us = GICS 10) | Claude R1 Q6 + Gemini R1 Q6 | REIT study exogenous prior 만 수용 | ★MAIN-DISPATCH §2 합치, direction.md ① 박제 예정 |

---

## ❌ 미채택 / proxy 대체 / 자문 충돌 → 한쪽 선택

| 후보 | 사유 |
|---|---|
| **시총 기준 T1/T2/T3 분류 (Mag7 시총 50% 가설)** | ★Claude R1 Q1 + Claude R2 QR2-5 + Gemini R1 Q1 + Gemini R2 QR2-5 = **양 채널 합의 기각**. Mag7 GICS 3 sector 파편화 (AAPL/MSFT/NVDA=XLK / GOOGL/META=XLC / AMZN/TSLA=XLY) → 시총 50% 격리 불가. **MAIN-DISPATCH §2 의 "T1=IT+CommServices=시총 집중 50%+" 가설 폐기** |
| **Tier 11 GICS 독립 가설 (각 sector 독립 bet)** | Claude R1 Q1 (eff_N 1.47, mean corr 0.617) + Claude R2 QR2-3 (PCA 80% 4-6 PC) + Gemini R2 QR2-3 (4-6 PC) = **양 채널 합의 기각**. macro-sleeve 3-4축 우세 |
| **capex YoY > 30% regime → Mag7 weight 상승 ((d) Claude R1 Q5)** | Claude R1 Q5 명시 기각 (reflexive trap). Claude R2 QR2-2 ★ "2023-24 backtest cap-up 압도 = 정확히 recency trap". Gemini R2 cap-up Sharpe 1.2-1.5 인지 의무지만 모니터 결합 권고 → ★cap-down + monitor 채택 |
| **외국인 net buy 직접 매핑 (eq_kr 가설)** | Claude R1 + 자체 (미국은 기축통화 자국시장). 대안 = (a) Fed path (b) Mag7/AI capex (c) buyback yield (d) HY OAS regime |
| **PBR 단독 governance proxy (eq_kr)** | 미국 = buyback yield + governance score (Russell 1000 검증 다수, 반대). 자체 finding |
| **yfinance 단독 PIT universe** | Claude R1 Q7 + Gemini R1 Q7 = 양 채널 기각 (survivorship-biased delisted 누락). bias 1.5-3.0%/yr 과대 (Gemini) |
| **단순 K-fold CV (CPCV 없이)** | Claude R1 Q8 + Gemini R1 Q8 = Sharpe 30~50% overfitting. CPCV 채택 |
| **Bruno & Shin (2015) 직접 메커니즘 (US sector cross-section)** | Claude R2 QR2-1 ★메커니즘 오적용 의심 (EM/sovereign 수준 → US sector 비직접). Gemini R2 자인. 인용 약화 |
| **R5 cyclical operating_leverage gross_margin proxy** | cyclical 박제 (IC +0.084 약함). Novy-Marx 2011 정밀 proxy (fixed_costs/book_assets) 로 대체 (collector 대기) |
| **회귀 베타 (top-down)** | cyclical 박제: Damodaran bottom-up beta (산업 무차입 → D/E relever) > 회귀 베타 |
| **historical ERP 5% (고정)** | cyclical 박제: Damodaran implied ERP (월별 vintage) > historical |
| **smoothed HMM full-sample 라벨** | cyclical 박제: 라이브 거래 불가 (미래정보) → predicted (1 lag) 만 |
| **Bai-Perron / CUSUM 사후 탐지 break** | cyclical 박제: "탐지" ≠ "예측" → 라이브 거래 불가 |
| **Sector rotation (Fidelity/Stovall 1996), Ned Davis** | cyclical 박제: 후순위 휴리스틱 (검증 대상이지 전제 X) |
| **Damodaran NIM proxy = DGS10-DGS2 lagged 3-6M** | defensive H2 실측 REJECT (Stigum 의 lag X, contemporaneous 만 유의 IC +0.171). 실측 합치 만 채택 |
| **HY OAS 확대 시 방어 sleeve outperform (Frazzini-Pedersen BAB)** | ★defensive H3 실측 REVERSED (Credit regime sleeve -1.5%/월, n=9 small-N). 양 채널 자문 prior 와 정 반대. ★재검증 의무 |
| **Tier 시총 1순위 가중 (사용자 직관)** | ★MAIN-DISPATCH §2 의 Tier 차등 분류는 R1+R2 양 채널 기각 → Mag7 custom basket + macro-sleeve 재편으로 진로 변경 |
| **Mag7 격리 없는 priced concentration factor** | Claude R2 QR2-2: "최근 momentum/growth/quality 와 고-collinear → priced factor 보다 regime indicator 활용 권고". Gemini R2 (priced factor 대안 2) 와 충돌 → Claude 채택 |
| **smoothed Markov-switching prob** | cyclical 박제 (look-ahead 누설). predicted prob 만 |
| **full-sample PCA** | cyclical 박제 (look-ahead 100%). expanding-window 강제 |
| **reference-period timestamp** | cyclical 박제 (look-ahead). release-date 기준 PIT 강제 |
| **CFNAI × HMM 입력 (이중 평활)** | cyclical 박제 (CFNAI = 이미 필터링). 원천 직접 HMM |
| **Greetham-Hartnett Investment Clock = ground truth** | cyclical 박제 (단일 휴리스틱, 가설 생성기로만) |
| **scipy.stats.spearmanr 단순 p-value** | cyclical 박제 (자기상관 미보정). NW q≥3 강제 |

---

## 🚫 환각 회피 / 함정 박제 (R2 cross-verify 결과)

### 🚫-1. 양 채널 cross-verify 확정 정정 4건

| Original (R1) | (a) 실재 | (b) ★정정 | 출처 |
|---|---|---|---|
| Gemini #1 Asness et al. (2000) "Value and Momentum Everywhere" | O | ★**Asness, Moskowitz, Pedersen (2013), Journal of Finance vol 68** | Claude R2 + Gemini R2 자체 정정 |
| Gemini #2 Ben-David et al. (2021) "Do ETFs Increase Volatility?" | O | ★**Ben-David, Franzoni, Moussawi (2018), JF vol 73** | Claude R2 + Gemini R2 자체 정정 |
| Claude #5 Gormsen-Lazarus "equity yield" | O | ★**"Duration-Driven Returns" JF 2023** (Gormsen & Lazarus, 단일 paper 제목) | Claude R2 자체 정정 |
| Claude #6 Asness-Frazzini-Pedersen (2019) QMJ | O | ★저널 정정: **Review of Accounting Studies (RAS) vol 24**, NOT RFS/JoF | Claude R2 자체 정정 |

### 🚫-2. R2 verify 권고 4건 (tentative — direction.md 인용 전 1차 verify)

| Reference | verify 사유 |
|---|---|
| Gemini #6 Ling-Naranjo (1999 vs 1997) | Claude R2: 인접 후보 = "Ling-Naranjo (1997) Economic Risk Factors and Commercial Real Estate Returns JREFE". Gemini R2 = 1999 REE 주장. 사용자 verify 권고 |
| Gemini #9 Brogaard 0DTE (2023) | Claude R2: 0DTE market-quality WP군 존재하나 정확 저자/제목 매칭 불확실 |
| Claude #4 Weber (2018) JFE | Weber, JFE 2018 vol 128 추정 [moderate confidence]. vol verify 권고 |
| Claude #9 Stickel (1991) | "Common Stock Returns Surrounding Earnings Forecast Revisions: More Puzzling Evidence" The Accounting Review vol 66 [moderate, 부제 verify 권고] |

### 🚫-3. 함정 박제 (자문/실측 정직 명시)

| 위험 | 회피 방식 |
|---|---|
| **R5 cyclical "구조 vs 표본 한정" disagree** | Claude R1 (표본 한정) vs Gemini R1 (구조) → Claude R2 절충 (3 메커니즘) + Gemini R2 입장 수정 (혼재). ★사용자측 2015-2019 실측 (#1) 의무 |
| **R5 Mag7 cap 방향 disagree** | Claude R1/R2 (cap-down + monitor) vs Gemini R1/R2 (cap-up Sharpe 우월 + monitor 결합). Claude R2 "2023-24 backtest cap-up 압도 = recency trap" 인지 의무 |
| **defensive H3 small-N 단정 (n=9 month)** | ★사용자 박제 5금지 #5 "Small-N 단정 금지". Credit regime n=9 → "잠정 directional 신호" 격하. LOO + Block Bootstrap autocorr 보정 의무 |
| **defensive synthetic data 의심 (MAIN-DISPATCH §1)** | "합성 의심 P0 재검증 대상". H1~H4 validation 재실행 의무. v2 study_session.yaml 그대로 채택 금지 |
| **점추정 covariance prior 박제 금지** | ~/.claude/rules/small-n-statistical-rigor.md §1(e). 모든 β/IC 점추정 → CI + p + n 박제 + hedge 어휘 |
| **PIT revision IC vs backfilled IC drift** | Claude R2 QR2-4: "PIT (unrestated) revision IC backfilled 대비 >30% 하락 → look-ahead artifact". Refinitiv/FactSet retroactive 수정 = 실재 confound |
| **factor crowding/decay (McLean-Pontiff 58%)** | ★shareholder yield (fundamental) > revision breadth (info) > pure statistical 순 resilience. 단 PIT 위반 시 IC 인위 부풀림 |
| **2021-2024 collinear regime (긴축 × 강달러 × AI capex 삼중)** | Claude R1 Q10 최대 confound. dollar/rate/capex/concentration 효과 분리 불가. pre-2021 sub-sample 재검 강력 권고 (but AI/Mag7 대표성 상실 — irreducible tension) |
| **단정 어휘 약함 (Gemini)** | Gemini R1 "구조적/강력 권장" 사용. ★small-n-statistical-rigor §2 단정 금지 list 위반 → hedge 어휘 ("방향성 약 prior", "tentative", "CI 넓음") 로 정정 의무 |
| **점추정 magnitude 일부만 CI (Gemini)** | Gemini R1 ERB IC SE ±0.015 OK, Mag7 corr 0.4→0.85 = 점추정 (Claude range 명시 우월). direction.md citation 시 Claude range 우선 |

---

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

### 🔬-1. 사용자측 실측 권고 3건 (Claude R2 + Gemini R2 양 채널 합의)

| 실측 | 판정 기준 | 우선순위 |
|---|---|---|
| **#1 2015-2019 β_dxy sub-sample 회귀** | ρ<0.3 구간 β_dxy 절댓값 ≥0.3 + 유의 → Gemini 구조설 채택 / |β|<0.2 또는 부호 불안정 → Claude artifact 설 채택 | Phase 5 industry subagent dispatch 시 의무 |
| **#2 11-ETF PCA (raw + market-residual)** | residual PCA 80% 분산에 ≥7 PC 필요 → Tier 11 독립 인정 (Claude H8 confirm) / ≤5 PC → macro-sleeve 우월 (★예상) | direction.md 작성 전 결정자 |
| **#3 PIT revision IC vs backfilled IC** | PIT IC < backfilled IC × 0.7 → look-ahead artifact 확정 → IC haircut 적용 | EDGAR + I/B/E/S 적재 후 |

### 🔬-2. monitor 후속 검증 (채택 후 운영)

| 후보 | 현 상태 | 재검증 trigger |
|---|---|---|
| **Reflexivity Monitor (corr + breadth)** | spec 합의 (Claude R2 QR2-2) | monitor flag 발효 후 3-6m Mag7 drawdown 비-flag 대비 유의 차 없음 → monitor 무효 → cap-up 재검토 |
| **dollar 채널 부호** | ρ-conditional regime switch | ρ→0 구간 dollar OOS R² → 0 수렴 → 구조 채널 가설 기각 |
| **HY OAS regime** | Claude H3 + defensive H3 REVERSED 실측 | OAS→sector Granger 실패 OR regime-conditional 수익차 CI 0 포함 → H3 기각 |
| **bank vs utility/REIT rate-beta 부호 안정성** | defensive H1 실측 + Claude H5 | N≥24 epoch 부호 flip OR CI 양방향 0 cross → H5 기각 |
| **AI capex → Mag7 fwd EPS 1-2Q lag (H6)** | Claude R1 Q9 H6 | lagged-capex IC capex-peak 후 regime 포함 전 regime CI 하한 >0 → durable factor (H6 기각 but 위험) |
| **shareholder yield post-publication decay** | Claude R2 QR2-4 | shareholder yield 가 일반 anomaly 동일 ~58% decay → fundamental-resilience 가설 기각 |
| **defensive synthetic 의심 재검증** | MAIN-DISPATCH §1 P0 | H1~H4 실데이터 재실행 후 v2 yaml 안정성 확인. n=9 small-N case (H3) 는 Block Bootstrap + LOO 의무 |

### 🔬-3. cyclical 재사용 후보의 falsifier (cyclical candidate-ledger 합치)

| 지표 | 현 상태 | 재검증 trigger |
|---|---|---|
| **vix_beta** | base 0.18 (cyclical) | regime contemp IC e-CUSUM 단측 붕괴 → base 하향 |
| **ism_pmi_proxy** | base 0.04 cap (H3 REJECT) | 종속 재정의 (sector 단독 XLI / revision breadth) 후 IC ≥0.15 → 회복 |
| **fwd_ep_normalized** | base 0.30 collector 대기 | EDGAR 적재 후 trough Rank-IC ≥+0.10 (FM+DK SE) → 활성 |
| **peak_trap_no_entry** | mechanism 정의 | peak Win-Rate <30% → floor 상향 / ≥50% → 완화 |
| **capital_cycle_overcapex** | 신규 hook | 반도체 밖 multi-sector long-short CMA spread IC e-process |
| **rate_beta** | H5 REJECT base 0.04 (cyclical) vs defensive H1 sub-sleeve 분기 | 종목 EDGAR + Fed surprise 분리 후 sign 분산 재측정. eq_us 통합 시 industry granularity 차등 |

---

## 📊 출처 cross-ref (어느 후보가 어느 파일에서 왔나)

| 후보 출처 | 파일 | 비고 |
|---|---|---|
| 자문 R1 (양 채널) | raw/consult-round-1-claude.md, raw/consult-round-1-gemini.md | Q1~Q10 × 5 필드. Claude epistemic discipline 우위 (hedge + tentative + R2 권고 자체 제시) |
| 자문 R2 (절충 + cross-verify) | raw/consult-round-2-claude.md, raw/consult-round-2-gemini.md | QR2-1~6. 환각 정정 4 확정 + verify 권고 4 + 사용자 실측 3 |
| eq_us_cyclical 17 indicators + 9 relationships | study-research/eq_us_cyclical/{study_session.yaml, candidate-ledger.md, summary.md} | M3 실측 (β_dxy −0.58~−1.62 dominant) + Tier1 산업 분할 + δ_regime/δ_arch 정의 |
| eq_us_defensive 실측 (★P0 재검증 의무) | study-research/eq_us_defensive/{study_session.yaml, summary.md, direction.md} | H1 sign-split + H4a sub-sleeve + M3 dollar rate-regime 부호 반전 + 5 archetype |
| eq_kr v2 7-Phase baseline | study-research/eq_kr/methodology-final-for-main-dispatch.md | 한국→미국 study_id·universe 교체. 12 가설 미러링 (단 미국 특화 = ERB/TSY/HY OAS/Mag7) |
| Phase 3 사용자 박제 (MAIN-DISPATCH § + progress.md) | study-research/eq_us/{MAIN-DISPATCH.md, progress.md} | 5 금지 + supervisor 직접 평가 금지 + analyst-lens 다운그레이드 금지 + reflexive loop 차단 + tier 정직성 + 산업별 산출 양식 박제 + agent 5분 self-wake 박제 |
| 미국 특화 신규 confound (R1 Gemini Q10) | raw/consult-round-1-gemini.md | 0DTE / Non-GAAP SBC / passive ETF flow crowding. eq_kr 12 가설에 없는 미국 특화 |

---

## TL;DR — 다음 세션 한 줄 인계 (direction.md 작성 시)

- **채택 후보 (Phase 3 R1+R2 자문 수렴, ★but yaml/코드 미투입)**:
  ① alpha driver 3 = **ERB / TSY / HY OAS** (Claude+Gemini 양 채널 1-3순위 합의)
  ② regime conditioner = **real_rate (sub-sleeve sign-split)** + **dollar (ρ-conditional)** + **Fed funds path**
  ③ 구조 = **macro-sleeve 3-4축** (Tier 11 GICS 독립 기각) + **Mag7 custom basket** (시총 50% Tier 가설 기각) + **Reflexivity Monitor** (cap-down + corr/breadth)
  ④ infrastructure = **EDGAR filing timestamp PIT** + **Sharadar (예산 결정)** + **FF5+QMJ+BAB residual** + **CPCV + NW HAC + Block Bootstrap + Deflated Sharpe**

- **이연 (코드/데이터 미투입, direction.md ④ 또는 collector_plan 등록 의무)**:
  데이터 12 (EDGAR/Sharadar/I/B/E/S/ALFRED/FF5/OIS/Y-9C/CMS/GICS/0DTE/Non-GAAP) +
  코드 22 (2-cell regime / 직교화 dollar / concentration factor / PCA / CPCV / NW / Block Boot / FDR / E-value / alphalens / PIT IC 재추정 / 사용자측 실측 #1#2#3 / haircut / Damodaran / EBP / regime predicted prob / lens_prompt / archetype 등록 등) +
  가설 15 (H1~H15 중 7~10 채택, 나머지 후순위/data 의존)

- **미채택 (자문 합의 기각)**: 시총 Tier 11 / capex YoY 30% cap-up (d) / yfinance 단독 PIT / 단순 K-fold / Bruno-Shin US sector 직접 / Frazzini-Pedersen BAB defensive sleeve (modern QE 실측 REVERSED) 외 15+

- **환각 정정 4 확정 + verify 4 + 함정 박제 11** (R2 cross-verify 결과)

- **사용자측 실측 3 필수** (Phase 5 산업 subagent 작업): ①2015-2019 β_dxy ②11-ETF PCA ③PIT revision IC

- **defensive v2 yaml = ★P0 재검증 대상** (합성 의심) — 그대로 채택 금지, H1~H4 실측 재실행 의무

<state intent="eq_us candidate-ledger 작성 (자문/이론/M3 후보 + 채택/이연/미채택 + 사유 1파일 집약)" risk="direction.md 미작성 상태 = 거의 모든 채택 후보 'pending injection' 정직 박제" uncertainty="low">

---

## ★다변량 조건부 가설 11종 전수 검증 결과 (2026-06-04, BW8)

> SSOT: [REWORK-prereg-11hypotheses-20260604.md](./REWORK-prereg-11hypotheses-20260604.md) §검증 결과. 단일 FDR family `us_equity_2way_v1` BY q=0.10. one-sided pre-commit(wrong-sign=부호탈락). 실행=team-lead 직접(teammate echo-stall). json: cyclical `_b2_cyclical_interactions_results.json` / defensive `_b2_defensive_interactions_results.json`.

| id | spec | decision | 사유 |
|---|---|---|---|
| **DEF-2** | dividend_yield(고)×op_prof(고) | ★**CONFIRM** | incr+0.065 wild p0.0005, fixed-b+size-valid, BY r1 생존. yield-trap 분리 입증(고DY×고quality=sustainable). ★factor×factor>단일 실증 |
| **DEF-1** | net_issuance×ep_yield | ★**TENTATIVE** | incr−0.076 wild p0.0055 유의·incremental BY r2 생존, but ★PW방향(AMP prior+ 반대=발행페널티 cheap 집중). two_sided_review→manual. flip-sign 신규 pre-reg+OOS 필요 |
| CYC-3 | op_prof(고)×asset_growth(저) | REJECT(wrong-sign) | incr−0.039 p0.013 유의이나 pred+ 역부호. 경제적=사이클정점 reversal. 추격금지(HARKing). flip 후보 |
| CYC-4 | ep_yield×residual_mom | REJECT(wrong-sign) | incr−0.048 p0.038 유의 역부호. cheap+mom=정점 reversal. 동상 |
| DEF-3 | earnings_cv(저)×vol_60(저) | NOT_INCREMENTAL | raw+0.048 p0.006 유의이나 incr 소멸(p0.11)=stability proxy 중복(near-dup 예측 적중) |
| CYC-5 | ep_yield×idio_vol(저) | NULL | incr−0.026 p0.17 |
| DEF-5 | ep_yield×gross_prof | NULL | incr−0.014 p0.59, anti-value quality-decomp 무 |
| CYC-1 | ev_ebitda(저)×gross_prof(고) | NULL | incr+0.019 p0.68, Novy-Marx 방향 맞으나 비유의 |
| CYC-6 | [capex×ep_yield]~Δbaa Tier2 | NULL | slope t−0.51 p0.65 (capex EDGAR fetch 성공) |
| DEF-4 | ep_yield~Δreal_rate Tier2 | NULL | slope t0.27 p0.79, anti-value의 rate-state 의존 없음 |
| CYC-2 | PER-cheap divergence | NULL | raw−0.035 p0.15, incr 소멸 p0.88 |

**종합**: 11 中 BY 생존 2(DEF-2 CONFIRM + DEF-1 TENTATIVE). cyclical interaction 6개 = value(pbr/ev #7 CONFIRM) 위 incremental 0(null 4 + wrong-sign-reject 2). 사용자 "지표간 관점" = noise 아님 정직 검증(DEF-2 = factor×factor>단일 실증 / CYC-3·4 = 유의 reversal 신호이나 부호규율로 reject). 잔여 안전장치(e-process OOS/placebo/Harvey-Liu/turnover)=DEF-1/2 한정 G-C 재audit(BW7).

### ★자문 검증 후 정정 (2026-06-04, /gemini-web+/claude-web 수렴 + curvature 결정검정)
- **DEF-2 = CONFIRM 확정 (격상)**: own-curvature(z² basis) + Fama-MacBeth 전체회귀 이중통제에도 incr IC +0.059(p0.007) / FM coef +0.020(t3.54) 전부 생존, VIF 1.3 = collinearity 무. ★11 가설 中 유일 robust 발견.
- **DEF-1 = TENTATIVE → WEAK_RANK_ARTIFACT (격하)**: Spearman rank-IC −0.076(p0.0055) 유의가 ★Fama-MacBeth 선형 교호계수서 비유의(−0.0095 t−1.66 / +곡률 t−0.87). 자문 경고 "FWL 선형직교화+rank 불일치" 실증 = PW-reversal 이 rank척도/꼬리 주도 artifact. net_issuance **단독** PARTIAL_CONFIRMED 는 유지, ep_yield 교호는 미입증.
- 방법론 codify(차기): interaction primary=FM 계수(rank 병기) + 직교화 z²곡률 의무 + n_eff floor=gradient + right-sign-null 동일엄격 + spec-modulation=SCA/multiverse|이론고정+pristine OOS only.

### ★독립검증 후 재정정 (2026-06-04, 사용자 "자문 적용 타당성 별도 검증" 지적)
- **DEF-2 = CONFIRM → TENTATIVE 재격하**: 독립 방법(2×2 double-sort DiD t1.65 p0.11 / hand-built FM raw곱 t1.82 p0.083) 전부 marginal. ★내 구현 `cs_z(z1*z2)` 교호항 sector-neutral 재-z 가 유의도 인플레(표준 FM raw 곱은 비유의). 방향은 4방법 전부 +(yield-trap 분리 방향성 신뢰), 유의도 spec 의존. nonlinear 가능성 잔존(rank 강·linear marginal).
- **DEF-1 = WEAK 확정**: 표준 FM/double-sort 전부 비유의(t−1.5~−1.9).
- ★**11 가설 中 robust CONFIRM = 0개**. DEF-2 최강이나 marginal. (단일 신호 value pbr/ev #7 + net_issuance PARTIAL 은 재-z 무관, 유지.) ⚠️**SUPERSEDED → §over-kill 정정: DEF-2 = CONFIRM 복원 (rank-FM 척도 통일), robust CONFIRM 1개**.
- codify: interaction 교호항 재-z 금지(raw 곱) + primary=double-sort DiD+hand-built FM + 자문 차용 후 구현 독립검증(assumption-light) 의무.

---

## ★11 시나리오 검증 과정 전수 기록 (2026-06-04, 사용자 "시나리오별 과정 남겨")

> 본 미국 사이클에서 11 다변량 조건부 가설(CYC-1~6 + DEF-1~5)이 거친 검증 단계 + 단계별 수치·verdict 변화 전수. ★결론보다 "과정"이 핵심 — 매 층이 verdict 를 깎음.

### 적용한 검증 층 (순서 = 강도 누적)
1. **pre-reg** (데이터 접촉 전 one-sided 부호·neff_floor·incremental_req 박제)
2. **unconditional interaction** (rank-IC + FWL incremental) — ★결함: 교호항 `cs_z(z1*z2)` 재-z (후술)
3. **단일 FDR family** BY q0.10 m=11 보수적
4. **split-sample OOS** (≤2021 vs 2022~, 유의분만)
5. **외부 자문 2채널** (/gemini-web + /claude-web 수렴 → curvature confound 결함 지목)
6. **curvature 통제** (직교화 basis 에 z² 추가)
7. **★독립 double-sort DiD + hand-built FM(raw 곱)** = 구현 무관 재검 (사용자 "자문 이론≠적용 타당성")
8. **regime 조건부** (연속 slope size-valid + split 진단)
9. **★재-z 결함 발견** (양방향: DEF-2/CYC-4 인플레 ↔ CYC-1 억압)

### 시나리오별 과정 (단계별 수치 → 최종)
| id | spec | unconditional rank-IC | FDR | split-OOS | curvature | 독립 double-sort/FM(raw) | regime | ★최종 disposition |
|---|---|---|---|---|---|---|---|---|
| **DEF-2** | div_yield(고)×op_prof(고) | +0.065 p0.0005 ✅ | ★생존 r1 | 양분 fixed-b sig | 생존 | ★**DS t1.65 p0.11 / FM t1.82 p0.083 marginal** (재-z 인플레 들통) | ★dollar slope t2.22 p0.044(Bonf 후 탈락) | **TENTATIVE** = dollar-conditional suggestive. ★pristine-OOS 후보 |
| **DEF-1** | net_iss×ep_yield | −0.076 p0.0055 ✅ | ★생존 r2 | 양분 음 robust | rank만 생존 | ★**FM t−1.56 p0.148 비유의** | dollar t−2.48 | **WEAK** (rank-artifact, FM 비유의). net_iss 단독 PARTIAL 은 별개 유지 |
| **CYC-1** | ev_ebitda(저)×gross_prof(고) | +0.019 **p0.68 null** | 미생존 | — | — | ★**DS t1.63 p0.13 / FM t1.75 p0.11 정방향**(재-z 가 억압했던 것!) | rate10y t3.44 p0.014 | ★**THEORY-PINNED 후보**(Novy-Marx+method 안정 marginal). pristine-OOS 최우선 |
| **CYC-3** | op_prof(고)×asset_gr(저) | −0.039 p0.013 ✅ wrong-sign | 부호탈락 | 양분 −0.04 안정 | — | ★DS t−0.98 p0.34 null / FM t−2.39 p0.028 = **불일치 UNSTABLE** | vix t−3.84 p0.0009 | **REJECT**(wrong-sign+method 불안정). flip 우선순위 최하 |
| **CYC-4** | ep_yield×residual_mom | −0.048 p0.038 ✅ wrong-sign | 부호탈락 | in약 OOS주도 | — | ★DS t−4.03 p0.0003 / FM t−0.33 p0.77 = **불일치(nonlinear/꼬리)** | dollar t−3.16 | **REJECT/UNSTABLE** |
| **CYC-5** | ep_yield×idio_vol(저) | −0.026 p0.17 | 미생존 | — | — | ★DS −0.04 / FM +0.009 = **부호 flip** | vix t−4.98 p0.0018 | **NULL**(부호 불안정) |
| **DEF-3** | earnings_cv(저)×vol_60(저) | raw+0.048 p0.006 / incr+0.029 p0.11 | 미생존 | — | — | — | — | **NOT_INCREMENTAL**(raw 유의=stability 존재하나 incr 소멸=main 각각 포착) |
| **CYC-6** | [capex×ep]~Δbaa Tier2 | slope t−0.51 p0.65 | 미생존 | — | — | — | — | **NULL**(capex EDGAR fetch 성공) |
| **DEF-4** | ep_yield~Δreal_rate Tier2 | slope t0.27 p0.79 | 미생존 | — | — | — | — | **NULL**(anti-value의 rate-state 의존 무) |
| **DEF-5** | ep_yield×gross_prof | incr−0.014 p0.59 | 미생존 | — | — | — | — | **NULL**(anti-value quality-decomp 무) |
| **CYC-2** | PER-cheap divergence | raw−0.035 p0.15 / incr p0.88 | 미생존 | — | — | — | — | **NULL**(incr 소멸) |
| mega | (n≈8) | — cross-section 불가 | — | — | — | — | — | exposure overlay 확정 |

### ★과정에서 얻은 메타 교훈
> ⚠️ **1~5 = over-kill 정정 전 기록 (SUPERSEDED)**. ★최종 = 아래 §over-kill 정정 (rank-FM 척도 통일 → DEF-2 CONFIRM 복원). 1~5 의 "재-z artifact 격하 / robust 0" 은 discovery·kill 척도 불일치(forking-paths) 산물.
1. **재-z 결함 = 양방향 오염**: 교호항 `cs_z(z1*z2)` 재-z 가 DEF-2/CYC-4 유의도 인플레 ↔ CYC-1 억압. → 원래 `_b2_*_interactions_results.json`(재-z 기반) = 오염, 깨끗한 double-sort/FM(raw)·regime 재검이 대체. ★codify: 교호항 raw 곱 사용, primary=double-sort+hand-FM.
2. **방법 불일치 = robust 아님**: double-sort↔linear-FM 갈리면(CYC-3/4/5) nonlinear/꼬리/artifact. 한 방법 유의로 주장 금지.
3. **자문 이론 ≠ 적용 타당성**: 자문(curvature/FM) 차용을 코드화한 게 또 구현 artifact(재-z FM t3.23 vs raw FM t1.82) → 구현 독립검증(assumption-light) 의무.
4. **regime = forking-paths**: 4 regime 검색 post-hoc, Bonferroni 후 다 탈락. size-valid slope 도 사전등록 X면 후보일 뿐.
5. **최종**: unconditional robust 교호 = 0. pristine-OOS 후보 2(CYC-1 theory-pinned / DEF-2 dollar-cond). 단일 value(pbr/ev)·net_issuance(PARTIAL) 유지. ⏳독립 G-C audit 진행 중(결과 반영 예정).

### ★over-kill 정정 (2채널 자문 수렴 + rank-FM 결정 중재, 2026-06-04)
> 사용자 "다 죽었다 자문하고 잘못한 거 없나 다시 봐". Gemini Pro + Claude Opus 4.8 병렬 + ★Rank-based Fama-MacBeth(discovery·kill 척도 통일). json `_b2_def_rankfm_results.json`/`_b2_cyc_rankfm_results.json`. SSOT = REWORK-prereg §over-kill 최종 정정.

| 가설 | rank-FM full | fixed-b | wild p | n_eff | OOS | ★정정 verdict |
|---|---|---|---|---|---|---|
| **DEF-2** div_yield×op_prof | coef+0.193 t2.68 | **sig** | **0.0105** | 57.9 | t3.13(n_eff14.1 UP) | ★**CONFIRM 복원** (이전 TENTATIVE 격하 = over-kill) |
| **DEF-1** net_iss×ep | coef−0.207 t−2.15 | sig | 0.049 | 50.8 | t−2.39 | **TENTATIVE PW** (WEAK_RANK_ARTIFACT 격하 정정 — 척도 통일서도 wrong-sign 지속 = PW 진짜 신호) |
| **CYC-1** ev(저)×gross_prof | coef+0.416 t2.28 | **미통과** | 0.046 | 31.3 | t5.1 | **TENTATIVE theory-pinned** (over-kill 아님, full fixed-b 미통과 정직 marginal) |
| CYC-3/4/5 | wrong-sign 또는 n.s. | 미통과 | — | — | — | REJECT/NULL 유지 (CYC-4 = "stably wrong-signed" 라벨 교정) |

**핵심 오류 (양채널 정합)**: ★발견은 재-z rank-IC 로, 사살은 raw 곱 FM 으로 = **discovery/kill 척도 불일치 = garden-of-forking-paths**. 더 보수적 구성이 매번 이기게 설계 → robust 0 = false-negative. 재-z 는 **균일 inflator 아님**(DEF-2 강화 ↔ CYC-1 억압, 신호마다 반대) = "raw 정답" 전제 자기-반증. audit: 재-z 는 FM-t 만 인플레(SE~1.70× 축소), **rank-IC 는 monotone-rescale-invariant 라 무관** → DEF-2 격하 근거 붕괴.

**★최종 (over-kill 정정 후)**: robust **CONFIRM = 1 (DEF-2)** + TENTATIVE 2 (CYC-1 theory-pinned / DEF-1 PW) + 단일 value(pbr/ev #7)·net_issuance(PARTIAL) 유지. ★"robust 0" = 점추정 prior 박제 금지 위반(underpowered≠null). codify⑥ 정정 = rank-FM primary / median double-sort 보조. ⏳G-C 재audit(BW7).

---

## ★Phase W — 약신호 보강 (value 외 독립 alpha 탐색, 2026-06-04)

> 사용자 "약한 부분 추가탐구 + 사망판정 다른각도 재검". /gemini-web+/claude-web 수렴(quality 1순위/기존데이터>>신규/exploratory family 분리/등가중 stacking) → ★실측이 자문 prior 반증(advisory-protocol: 본인 시뮬 verification). exploratory FDR family `us_equity_exploratory_v1`. json `_b2_quality_single_results.json`/`_b2_w2_accruals_results.json`/`_b2_w4_lowvol_results.json`. SSOT=REWORK §Phase W.

| 후보 축 | cyclical | defensive | 판정 |
|---|---|---|---|
| **W1 quality**(gross/op_prof) 단일 | IC−0.054 t−1.71 음·비유의 | IC−0.012 t−0.59 null | ★**reject** (alpha 부재 양 sleeve) |
| **W1 value+quality stacking** | IR 4.16→1.475 희석 ❌ | IR 3.514→4.128 +17%(IC 0.082→0.070 하락) | cyclical 무익 / defensive 약 분산효과(alpha 신규 아님) |
| **W1 value↔quality 직교성** | cross-corr −0.023 ≈0 | net_iss↔quality −0.042 ≈0 | ★자문 "QMJ 강음상관" 미실현 |
| **W2 accruals**(Sloan) 3~24M | — | 전부 fb 미통과 wild p>0.25, 24M 부호flip | ★**null** (완전성 마감) |
| **W4 low-vol/BAB** 3~24M | IC 음(역방향) 비유의 12/24M UP | — | ★**null** (within-demean이 BAB 죽임 + cyclical risk-on) |

**★Phase W 종합**: value 외 독립 alpha 축(quality/accruals/low-vol) = 미국 cyclical/defensive 전부 robust 부재. ★**value 1축 편중 = 측정 누락 아닌 데이터 본질** 실측 확인. ⛔ quality/low-vol/accruals 점추정 prior 박제 금지(전부 null). exploratory family 생존 0. **보류**: SUE/PEAD(고회전 별 sleeve) / mega forward(무료 PIT 불가). mega 표현 = "alpha=0" → "N=11 검출불능+무료 PIT불가 탐색종료"(REWORK 반영, sleeve yaml 잔여).

---

## ★매매 파이프라인 연결 (3-subagent 검토, 2026-06-04)

> 사용자 "이대로 매매 불가, 그냥 못 넘어간다 — 우리 코드/reference repo/중복개발 subagent 검토". 3 subagent 종합. SSOT=architecture.md + stock/value_trigger.py + stock/data/{french_factors,sector_multiples}.py + consult-brief-r2-execution-layer-20260603.md.

- **★매매 로직 이미 구현 (중복개발 무)**: reference=`jsh8603-web/coin`(BTC 자동매매 v1.29.0) 일반화(architecture.md:90 "새로 만들지 말 것") + `_refs/` 22 repo. 타이밍=점수제+5단계 레짐적응형(buy_score≥70 / sell 레짐차등 bull85↑·bear40↓ / 트레일링 -15%~-1.5% / 이중손절 / Kelly). 주식=`value_trigger.py` 2단게이트(가격급락 AND 내재가치갭→Claude value-trap veto). 전 체인 signal→FHCard→value_trigger→sizing→risk_gate(우회불가)→kis_client.order(NAS/NYS).
- **★value 연구의 진짜 역할**: `french_factors.py`(FF5 PIT vintage) + `sector_multiples.py`(★French49 49산업 peer 상대저평가)=value_trigger "내재가치갭" valuation 타이밍 입력. ★우리 value(PBR/EV cross-sectional IC robust 입증)=value_trigger 게이트 sector-relative valuation 신호 ★정당화/캘리브레이션. = "value 1축이라 매매불가"는 ★구조 오해(타이밍은 French49 sector-relative+레짐적응형 이미 설계, factor 다양성=sizing tilt 별 레이어). ★indicator-ledger `sector_relative_multiple` candidate(line 127)와 직결.
- **★"매매 불가" 실체 = 실행 wire 3갭**: ①cross-sectional selection 레이어 부재(universe 횡단면 spread→종목픽 변환부, own-history 시계열분위만) ②`sector_multiples.py` French49 라이브 fetch 이연(N-T1-SECTORMULT) ③`GatedOrderRouter`→`KisClient` 조립부 미배선(verdict만 반환). = factor 부족 아닌 wire 미완.
- **다음(사용자 1-3 전부 지시)**: wire 3갭 메우기. go-live 경계(README-unattended-safety D1~D5 사람게이트). ★레저 박제 우선 완료 후 진입.
