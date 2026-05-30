---
tags: [type/direction, study_id/reit, phase/2-1-completed, phase/v2-mirror-phase35-completed]
date: 2026-05-31
study_id: reit
asset_scope: [reit]
note: STUDY-KIT §2 v2 2-1 산출 (R1+R2+R3, §1-§7) + eq_kr v2 7-Phase 미러 Phase 3.5 산출 (§8 v2-mirror R1+R2+R3 supplement). main 승인 게이트.
status: phase35_v2_mirror_awaiting_main_approval
rounds_2_1: [round-1.md (이론수집), round-2.md (검증방향), round-3.md (가설+반증조건)]
rounds_v2_mirror_phase3: [consult-round-1.md (sub-cluster + driver + real rate), consult-round-2.md (β_rate cross-verify + paradox), consult-round-3.md (H1/H3 + 5게이트 + H6-H10)]
---

# REIT 자산군 — direction.md (2-1 자문 다회 종합)

> 본 문서는 STUDY-KIT §2 v2 의 2-1단계 (방향성 자문 다회) **종합 산출**이다.
> 라운드별 원문 = `raw/round-{1,2,3}.md` 누적. 본 문서는 ①이론 수집방향 ②검증방향 ③가설 초안 (반증조건) 세 축으로 정리.
>
> ⛔ **main(btn-Codlearn) 승인 전 2-2 (이론 학습) 진입 금지** (STUDY-KIT 명시).
> 승인되면 2-2 → 2-3 진행.

---

## 0. 자문 사이클 메타 (수렴 기록)

| Round | Focus | 도구 | 핵심 산출 |
|:-:|---|---|---|
| R1 | 이론 수집방향 | WebSearch ×2 (native, gemini-web/claude-web 9세션 경합 회피) | NAV/FFO/AFFO/DCF 4 approach + 2024 industrial -17.7% 반증 |
| R2 | 이론 검증방향 | WebSearch + WebFetch (Nareit blog cross-verify) | 학술 inconclusive + 시변 자본구조 + window flip 발견 |
| R3 | 가설 초안 (반증조건) | 합성 (새 검색 X) | 5 가설 (H1~H5) + 반증조건 + 우선순위 |

**수렴 판정**: 3R 만에 critical gap 해소. 잔존 미해소 = (a) Stagflation 1970s data 정독 (b) 환각 검증
243bp/120bp + 2024 industrial -17.7% — 모두 2-2 (이론 학습) 단계에서 처리 가능. 5R~7R 까지 갈 필요 없음.

---

## 1. ①이론 수집방향 — 무엇을 학습해야 하나

### 1-A. 가격결정 framework 4 approach (실무 standard)
- **NAV (Net Asset Value)**: 부동산 시가 − 부채. private appraisal cap rate × NOI.
- **P/FFO**: accounting earnings (D&A 정화) 배수.
- **P/AFFO**: distributable cash 근접 배수 = FFO − maintenance capex − straight-line rent.
- **DCF**: future cash flow discount.

### 1-B. 핵심 spread 관계 (mean-reverting anchor 후보)
- Implied cap rate (public REIT, NOI/EV) − Private appraisal cap rate.
- ★ Round 1 인용: Q3 2022 peak 243 bp → Q4 2024 = 120 bp. ⚠️ **primary 미검증** (2-2 cross-verify 의무).

### 1-C. AFFO/FFO 비율 sector 별 standard
- triple-net: 95-100% / industrial-multifamily: 85-95% / office-retail-lodging: 70-85%.
- → AFFO yield transform 시 **sector adjust** 필요 (단순 own_history_z 부족).

### 1-D. 학술 reference (2-2 정독 priority)
1. ★ Shulman (UCLA Anderson Ziman 2015 Letter) — 실무 readable.
2. ★ Researchgate 350174334 (Cross-country evidence, sector specialization value) — H1 base.
3. Giliberto-Shulman (2017) — REIT-rate negative 기준 합의.
4. Researchgate 317830157 (20Y daily data) — H2 시계열 base.
5. Neuberger Berman "Returning to REITs" — post-2022 outlook practitioner.
6. Green Street NAV-based Pricing Model (Nareit hosted PDF) — H2 anchor 정량.
7. CFA Level 2 REIT chapter (analystprep) — 4 approach 학술 정리.

### 1-E. 데이터 source 두 축
- **거시 (이미 가용)**: FRED (DGS10, BAMLH0A0HYM2 HY OAS, BAA10Y, CPILFESL, T5YIE).
- **REIT 종목 (가용 부분 + 부족 부분)**:
  - 가용: 가격 시계열 (yfinance/FinanceDataReader), GAAP 일부 (EDGAR _GAAP_MAP).
  - 부족: FFO/AFFO/NOI/NAV/InterestExpense/DividendsPaid (EDGAR XBRL 확장), GICS sub-industry,
    WALT (10-K 텍스트 파싱), occupancy/same-store NOI (supplemental table NLP).

---

## 2. ②이론 검증방향 — 어떻게 데이터로 시계열 검증하나

### 2-A. ★ 학술 합의 = INCONCLUSIVE → 단정 가설 금지
> "empirical evidence on REIT-rate relationship varies across countries, econometric techniques,
> interest rate proxies, and sample periods" (Round 2)

→ **v1 yaml 의 "β_rate -1.0 ~ -2.0" 정량 단정은 학술적 근거 약함**. v2 는 *반증가능 가설* 형식.

### 2-B. 시변 (time-varying) 자본구조 변수
- Pre-2022 저금리 시기에 REIT 가 debt maturities extend → rate β 완화.
- → rolling β 만으로 부족. **debt maturity profile stratify** 필요 (H3).

### 2-C. ★ Window-conditional sector return flip (2025 Dec 실증)
- 2025 YTD: Healthcare #1 (+28.5%) — Dec 단일월: Healthcare WORST (-8.4%) — 10Y +16bp 동행.
- → 같은 sector 가 window 길이에 따라 top↔bottom flip.
- → **regime → sector 단순 매핑 무효**. window 명시 필수 (H4).

### 2-D. 검증 방법론 표준 (3축)
1. **Cross-section Rank-IC** (sector level + ticker level) — 매 window 별 산출.
2. **Time-series rolling β** (24m, debt-maturity stratified) — H3.
3. **Anytime-valid e-process** (Ville 단측) — confirm/reject 임계 통계 (이미 시스템 보유 — 
   `weight_falsification.score_ic_breakdown_eprocess`).

### 2-E. PIT 보장 (lookahead 차단)
- FRED ALFRED vintage + EDGAR accession 단위 → 모든 fundamentals point_in_time.
- 반사성 게이트 (`weight_panel._REFLEXIVE_WORDS`) word-boundary 통과 확인.
- 시스템 보유 `core/data/weight_panel.build_indicator_matrix` 그대로 사용 가능.

### 2-F. Window 표준 4종 (H4 meta-가설 결정)
| Window | 용도 |
|---|---|
| 1d | rate-shock 즉시 reaction (10Y 1d Δ > +20bp 라벨) |
| 30d | rate-shock cumulative (10Y 4w Δ > +50bp 라벨) |
| 90d | cross-section Rank-IC 표준 (forward return) |
| 12m | mean-reversion (H2 cap rate spread) |
| 24m | rolling β (rate β stratify base) |

→ 모든 가설은 이 4-5 window 중 하나 명시 의무.

---

## 3. ③핵심 가설 초안 (반증조건 명시) — 5종 + 우선순위

### H4. ★ Window flip meta-가설 (★★★ 우선, 다른 가설들의 prerequisite)
- **명제**: REIT sub-sector ranking 은 evaluation window 길이에 따라 flip.
- **window**: 1d vs 30d vs 12m vs 24m 동시.
- **confirm**: mean swap rate (sector ranking 1+ tier flip 비율) > 30%.
- **reject**: window 무관 sector ranking 일관 (Kendall τ > 0.7).
- **v1 차이**: regime → sector 단순 매핑 (v1) → window-conditional 매핑 (v2).

### H1. Long-WALT REIT rate-shock cross-section underperformance (★★★ 우선)
- **명제**: rate-shock window 후 90d, long-WALT (top tertile) < short-WALT (bottom tertile)
  cross-sectional total return.
- **window**: 60-90d cumulative + rate-shock conditional.
- **confirm**: cross-section Rank-IC (WALT_rank vs fwd_60d_return) < -0.05 평균.
- **reject**: e-CUSUM 단측 (baseline -0.05 위로) e-value ≥ 20 (Ville α 0.05).
- **v1 차이**: v1 정량 단정 (-1.0~-2.0) → v2 부호 단정만, 정량은 데이터.

### H2. Implied-private cap rate spread mean-revert (★★ 우선)
- **명제**: spread Z < -1.5 (압축) → 12m forward REIT total return Rank-IC > +0.15.
- **window**: 12m forward, Q-end 시그모이드 가중.
- **confirm**: Rank-IC 양 + e-value ≥ 20 누적.
- **reject**: (a) e-CUSUM 단측 붕괴, 또는 (b) deep discount (Z<-2) 6Q+ 지속 미회복 = regime change.
- **v1 차이**: v1 mean-revert 단정 → v2 regime-change 가능성 명시.
- **⚠️ 환각 의존**: 243bp/120bp primary 미검증. 2-2 단계 cross-verify 후 baseline 확정.

### H3. Debt maturity profile stratification (★★ 우선)
- **명제**: debt WAM > 5y REIT 가 rate-shock 시 < 3y REIT 보다 *덜* 떨어진다.
- **window**: rate-shock window 30-90d cumulative.
- **confirm**: cross-section debt_WAM_rank vs rate-shock 60d return Rank-IC > +0.05.
- **reject**: 2022~2024 cross-section 정반대 부호 (e-value ≥ 20).
- **v1 차이**: v1 = leverage *량* 만 (debt/EBITDA). v2 = *term structure* 도 stratifier.

### H5. Sub-sector × regime 단순 매핑 반증 (★ 우선, 잔여 확인)
- **명제**: v1 의 "Reflation → industrial 강세" 매핑은 2024 데이터로 반증.
- **window**: regime 라벨 × calendar year (12m).
- **confirm**: regime × sub-sector 9 종 historical Rank-IC > 0.1.
- **reject**: ★ 이미 2024 데이터로 reject (industrial -17.7% in Reflation/Recovery-like 환경).
- **v1 차이**: v1 의 sub-sector regime 매핑 = 반증된 가설. v2 lens regime_reading 은 단정 → 
  "초기 prior, H4-conditional" 로 강등.

---

## 4. v1 (이전 산출) 의 결함 진단 (재작업 사유)

main 의 v2 재작업 지시 = "자문을 그대로 코드화하고 끝낸 것". v1 의 3 근본 결함:

1. **이론 단정**: "β_rate -1.0 ~ -2.0" 같은 정량 단정 — Round 2 학술 inconclusive 와 충돌.
2. **시변 무시**: pre-2022 debt maturity extension 으로 β 변동, 자본구조 term structure 누락.
3. **window 단일**: regime → sub-sector 매핑이 단일 frame. 2025 Dec healthcare flip 으로 직접 반증.

→ v2 = **반증가능 가설 + window 명시 + 시변 stratifier** 3 축으로 reframe. lens 는 단정 X, 가설 초안.

---

## 5. 다음 단계 (main 승인 후)

### 2-2 [이론 학습] — 승인된 ①②③ 정독
- Shulman + Researchgate 350174334 + Green Street + CFA L2 + Giliberto-Shulman 정독.
- ★ 환각 검증: 243bp/120bp + 2024 industrial -17.7% primary cross-verify.
- 산출: `raw/theory-notes.md` (가격결정 원리, 지표 의미·관계도, 학설 정리, 환각 검증 결과).

### 2-3 [실데이터 시계열 검증 → 코드화]
- H4 먼저 (단순 cross-tabulation) → H1 (cross-section Rank-IC) → H2/H3 → H5 순서.
- 무거운 분석 = Bash python 직접 실행 (RegimeGlasso 전체 적합 대신 상관행렬·partial-corr 만 먼저).
- 산출: `raw/validation-H1.md` ... `raw/validation-H5.md` (시계열 검증 근거 + 도표)
  + `study_session.yaml` (§3 7 블록, v1 yaml 폐기 X → raw 참고 → v2 갱신).

---

## 6. main 에 보고할 메시지 (다음 액션)

```
[reit→main] 2-1 자문 다회 (3R 수렴) 완료. direction.md + raw/round-{1,2,3}.md 누적.
핵심: v1 의 3 결함 (이론단정 / 시변무시 / window단일) 직접 식별. v2 = 반증가능 5 가설 (H1~H5,
H4 meta) + window 명시 + 시변 stratifier. 환각 미검증 2건 (243bp/120bp + 2024 industrial -17.7%)
은 2-2 정독 시 cross-verify 예정. ★ 승인 또는 보완요청 부탁.
파일: D:/projects/Inv/study-research/reit/{direction.md, raw/round-{1,2,3}.md,
~/.claude/memory/research/reit-pricing-theory.md, reit-validation-methodology.md}.
```

---

## 7. raw 누적 file 목록

- `raw/round-1.md` — 이론 수집방향 + 2024 sub-sector 반증 (WebSearch ×2)
- `raw/round-2.md` — 이론 검증방향 + 학술 inconclusive + window flip (WebSearch + WebFetch)
- `raw/round-3.md` — 가설 초안 + 반증조건 정련 (합성)
- `~/.claude/docs/archive/research-raw/reit-pricing-theory-native-20260530.txt` — R1 raw
- `~/.claude/docs/archive/research-raw/reit-validation-methodology-native-20260530.txt` — R2 raw
- `~/.claude/docs/archive/research-raw/reit-q1-2025-cross-verify-native-20260530.txt` — R2 WebFetch raw
- `~/.claude/memory/research/reit-pricing-theory.md` — R1 memory summary
- `~/.claude/memory/research/reit-validation-methodology.md` — R2 memory summary

이전 v1 산출 (`study_session.yaml`, `summary.md`, `raw/lens-rationale.md`, `raw/data-availability-audit.md`)
은 폐기 X — raw 참고용 보존 (main 지시).

---

## 8. ★ v2-mirror Phase 3 자문 R1+R2+R3 보강 (2026-05-30~31, eq_kr v2 7-Phase 미러)

> 본 §8 = STUDY-KIT §2 v2 2-1 산출 위에 eq_kr v2 7-Phase 절차 (사용자 검증 완료) 미러로 추가 자문 3R 수렴 결과. 기존 §1-§7 = 5 가설 (H1-H5) + 환각 cross-verify + 학설 정리 (영구 유효).
> §8 supplement = REIT sub-cluster 분할 보강 + 거시 driver 확장 + 신규 가설 H6-H10 + estimand 변경 (panel-level pooling) + shrinkage 의무 + R4 carry.

### 8-1. ① 이론 수집방향 — sub-cluster 분할 + 거시 driver 확장

#### 8-1-A. Sub-cluster 분할 (R1+R2+R3 합의)
6 cluster → **7 cluster (C6 분리) + 1 별도 cluster (C8 mREIT)** = total 8 cluster:
- C1 Residential (AVB)
- C2 Commercial-Retail (BXP, SPG) — Office+Retail 병합 논쟁 carry (R4 분리 검토)
- C3 Industrial-Logistics (PLD)
- C4 Datacenter-Infra (EQIX, AMT) — Tower-Datacenter 결합 vs 분리 검토
- C5 Healthcare (WELL) — 단독 cluster 채택 (Medicare policy proxy 차등)
- **C6a Lodging (HST)** — short-lease, GDP/consumption proxy (Hotel +1.79 paradox)
- **C6b Storage (PSA)** — recession-resilient, 통상 negative β
- **C8 mREIT (NLY/AGNC/MFA 별도)** — equity REIT 와 duration profile 근본 다름. driver = yield curve slope + convexity + MBS OAS + book value MTM. R3 가설 트랙 분리 (R4 carry).

★ R4 carry: Gaming (VICI/GLPI), SFR (INVH/AMH), Timberland (WY/RYN), Farmland, Diversified — universe 확장 검토.

#### 8-1-B. 거시 driver 확장 (R1+R2 합의)
기존 4 driver → **6 driver**:
- D1 Real rate (FRED DFII10, 2003-01~ daily continuous, M3 sample fully available)
- D2 Cap-rate spread (Nareit T-Tracker, Q3 2022 peak 243bp / Q4 2023 = 123bp)
- D3 Dollar (DXY, FRED DTWEXBGS)
- D4 Sector supply (Census Construction Put in Place 월별 + CMBS Delinquency leading, CBRE/CoStar appraisal lag 회피)
- D5 (신규) **HY OAS (BAMLH0A0HYM2 FRED)** — REIT 고leverage refinancing channel, cap-rate spread 와 부분 collinear 만 별도 정보
- D6 (신규) **Inflation Breakeven (T10YIE)** — lease escalator 가치, real rate 분해 의무

#### 8-1-C. Fisher 항등식 collinearity invariant ★
- "nominal + real + breakeven 동시 투입 금지, **real + breakeven 만**" (R1 claude critique 정착)
- M3 nominal β_rate=−3.82 decompose expect: real β ≈ −4~−6 / breakeven β ≈ 0~소폭 양수 (sample-dependent, 실측 ground truth)

#### 8-1-D. 학설 ref 박제 (R2+R3 R supervisor 채택)
- **자산-부채 듀레이션 비대칭**: Boudry et al. 2012 JREFE (WALT positive escalator option) / Harrison-Panjian-Seiler 2011 JREFE (WAM negative refinancing risk) / Allen-Madura-Springer 2000 JREFE 21(2) (specialization·leverage β_rate modulate) / He-Xiong 2012 Journal of Finance 67(2) (Rollover Risk — long WAM 이론적 protective).
- **REIT-rate inconclusive primary citation**: Liu-Mei 1992 JREFE 5(2) (predictability/market timing 주제, ★정량 β range 인용 금지) / Mueller-Pauley 1995 JRER 10(3) (저상관 + 횡보국면 의존, 정성적 인용 mid-high) / Giliberto-Shulman 2017 (bond-like + equity 시변) / Yobaccio 1995 RealEstFin 11(1) (빈약한 인플레 헤지) / Chen-Tzang 1988.
- **REIT-inflation 부호 inconclusive**: Glascock-Lu-So 2002 (REIT-inflation 음의 관계 = 통화정책 발현 spurious) / Beracha-Feng-Hardin 2019 RealEstateEconomics (hedging + illusion 공존, illusion dominant). [★ Beracha-Krautz 2022 = 환각 catch, ref 교체]
- **Hotel short-lease pass-through**: Holland-Ott-Riddiough 2000 / Hoesli-Lizieri-MacGregor (short-lease 양 breakeven loading) — **단 +1.79 = cyclical demand proxy, orthogonalize 시 0 수렴 expect**.
- **2-stage Ling-Naranjo decomposition**: Ling-Naranjo 1999 RealEstateEconomics 27(3) "The Integration of CRE Markets and Stock Markets" + Ling-Naranjo 1997 JREFE 14(3) "Economic Risk Factors and CRE Returns" [★ Ling-Naranjo 2014/2015 = phantom catch, 1997/1999 대체].
- **Shrinkage**: Ledoit-Wolf 2003/2004 / Jorion 1986 JFQA Bayes-Stein / Ridge L2 / Gelman hierarchical Bayes.
- **Tower lease escalator pass-through**: 학술 약함 → mechanism 자기완결 (5-10y term + renewal option + 고정 ~3% escalator → CPI>3% real revenue erosion). [★ Green Street = proprietary, 학술 citation 부적합 catch].
- **Generic flow predictability** (H10 anchor): Coval-Stafford 2007 JFE 86(2) / Ben-Rephael-Kandel-Wermers 2012 JFE 104(2) / Ben-David-Franzoni-Moussawi 2018 JF 73(6). REIT-specific 약함 confidence mid.

### 8-2. ② 검증방향 — estimand 변경 + shrinkage + event-study

#### 8-2-A. 5게이트 estimand 변경 (★ R3 claude critique 우위)
- **★ threshold 완화 (0.05→0.03) 금지** — Type I error 폭증 (cell n=60 SE 0.13, 임계 0.05 도 noise 매몰).
- **★ per-cell 검정 폐기 → panel-level (sector fixed/random effect) effective n 확보**
- **또는 pooled cross-sectional rank-IC + Newey-West t-stat** (REIT cross-section 신호 표준)
- 임계 0.05 유지, 적용 단위를 cell 아닌 panel/pooled 로 이동

#### 8-2-B. Shrinkage / Hierarchical Bayes 의무 (R2+R3 합의)
- 9 sub-sector × 6 driver × epoch small-N → OLS 불안정, **Ridge L2 + Ledoit-Wolf 2003/2004 + Jorion 1986 Bayes-Stein 의무**
- Robustness gate = **posterior shrinkage 생존 (95% CrI 0 제외) + prior-sensitivity gate (λ grid 부호·유의성 robust) + posterior predictive check + Bayes Factor >3**
- λ point estimate 단정 금지, λ 분포 sweep

#### 8-2-C. Event-study (H9 Medicare policy)
- CMS final-rule (SNF PPS / IPPS / physician fee schedule) 발표일 CAR + cross-section (gov-pay 노출 높은 SNF-heavy [OHI/SBRA] vs senior-housing operating [WELL/VTR] CAR 차이)
- 단순 contemporaneous monthly ρ>0.3 = dilution 부적합

#### 8-2-D. 2-stage Ling-Naranjo within-sleeve decomposition
- 1차: sub-sector return ~ VNQ + market 회귀 (broad REIT + equity broad factor 제거)
- 2차: 잔차 ρ = 진짜 sub-sector unique comovement
- 0.547 mean ρ = pure equity beta ≈0.6 + CRE systemic mix (claude/gemini 합의)

### 8-3. ③ 신규 가설 H6-H10 (반증조건 정량성)

#### H6. Cap-rate spread > 200bp 진입 시 +12m mean-revert
- **anchor**: Plazzi-Torous-Valkanov 2010 RFS 23(9) "Expected Returns and Expected Growth in CRE" (High) + Ghysels-Plazzi-Torous-Valkanov 2013 Handbook (mid-high)
- **반증조건** (★ claude critique 우위): episode 사전정의 (threshold cross + 최소 dwell 명시) + overlapping 12m Hansen-Hodrick/Newey-West 보정 + reject = OOS episode forward 12m 중앙값 ≤ 0 (one-sided) OR hit-rate binomial CI 하한 < base rate. "75% confidence" point 주장 금지 → CI 박제.

#### H7. Datacenter capex 사이클 EQIX lead 6-9m
- **anchor 약함** (low) — academic primary 부재 (too recent). AI capex proxy = Nvidia revenue / hyperscaler (MSFT/GOOGL) capex disclosure
- **반증조건**: lead-lag CCF peak [6,9]m 밖 reject + Granger (capex proxy → EQIX FFO/leasing fundamental, 가격 아님; broad equity 통제) 비유의 reject + 역인과 (EQIX leasing→capex) sub-sample 비정상성 점검. 표본 짧음 power 경고 박제. seasonal X-13ARIMA-SEATS 선행.

#### H8. Tower long-duration discount = lease escalator pass-through 약함 (CPI>3%)
- **anchor**: 학술 약함, mechanism 자기완결 (5-10y term + 고정 ~3% escalator + renewal option)
- **반증조건** (★ claude critique 분할):
  - **H8a (fundamental)**: tower organic revenue growth (또는 AFFO/share) ~ realized CPI 회귀, 계수 < 1 (incomplete pass-through). reject = 계수 ≥ 1 또는 <1 비유의.
  - **H8b (price/duration)**: 가격 검정 유지하되 **rate 통제 후**. mechanism (H8a) + price (H8b) 분리해야 confound 제거.

#### H9. Healthcare β_rate 약함 = Medicare 정책 dominant
- **anchor**: Allen-Madura-Springer 2000 JREFE 21(2) "specialization β_rate modulate" (mid). Medicare 직접 primary 약함. Roig-Luchtenberg 2014 JREPM (mid).
- **반증조건** (★ claude event-study): CMS final-rule 발표일 CAR + cross-section (SNF-heavy [OHI/SBRA] vs senior-housing [WELL/VTR] CAR 차이). reject = event CAR 비유의 AND β_rate 가 net-lease β 와 CI 구분 불가.

#### H10. REIT broad ETF flow vs sub-sector divergence regime 신호
- **anchor** (generic flow predictability): Coval-Stafford 2007 JFE 86(2) (High) + Ben-Rephael-Kandel-Wermers 2012 JFE 104(2) (mid-high) + Ben-David-Franzoni-Moussawi 2018 JF 73(6) (mid-high). REIT-specific 약함, confidence mid.
- **반증조건**: orthogonalized flow innovation (reverse-causality 제거, Ben-Rephael 류) 이 forward sub-sector dispersion / forward broad return 에 대해 5게이트 (panel-level, Newey-West) 미충족 → reject.

#### H1 재정식화 (R3 권고)
- H1 원전 ("long-WALT underperform" = duration textbook 추론, 특정 primary 약함) **reject 유지**
- **재정식화**: "long-WALT + escalator option = conditional outperform (rate-shock + 동반 인플레 condition 한정)" — M3 +0.240 직접 반영

#### H3 sign reversal 처리 (R3 ★ confounding 의심)
- He-Xiong 2012 JF Rollover Risk 이론은 long WAM = protective (positive) 여야 함
- M3 long-WAM underperform = ★ **mechanism 아니라 confounding 의심**
- R4 carry: long-WAM 표본의 sector/leverage orthogonalize 후 재검 의무

### 8-4. ★ R4 carry 3건 (Phase 5 dispatch + 별도 트랙)

1. **c2/c3/c6 원문 검증** — Beracha-Feng-Hardin 2019 정확 ref / AMT 10-K 2023 손상차손 수치 (VIL $3.22B 가설) / CCI-AMT churn schedule disclosure. Phase 5 sub-cluster dispatch 시 collector_plan 의무.
2. **H3 sign reversal orthogonalize 재검** — long-WAM 표본의 sector/leverage 와 H3 Rank-IC partial out. Phase 5 실측에서 처리.
3. **C8 mREIT 전용 가설 신설** — empirical duration gap × curve slope (NLY/AGNC asset-liability mismatch 본질). 별도 가설 트랙 (R3 = equity REIT 9 한정).

### 8-5. 산출 cross-ref

- methodology-brief.md (Phase 2, 165 lines)
- raw/consult-round-1.md (Q1-Q3 sub-cluster + driver + real rate, R1)
- raw/consult-round-2.md (Q4-Q7 β_rate cross-verify + paradox, R2)
- raw/consult-round-3.md (Q8-Q10 H1/H3 + 5게이트 + H6-H10, R3)
- archive: `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r{1,2,3}-{gemini,claude}-2026053{0,1}.txt`
- 기존 input 재사용: raw/m3-macro-linkage.md + raw/validation-{H1..H5}.md + raw/theory-notes.md + raw/round-{1,2,3}.md + study_session.yaml (v2 = structural prior)

### 8-6. ★ main 승인 게이트

본 §8 산출 (v2-mirror Phase 3 자문 R1+R2+R3 supplement) = direction.md (Phase 3.5 산출) 완료. ⛔ **main 승인 전 Phase 4 (plan.md) + Phase 5 (sub-cluster dispatch) 진입 금지**.

main 승인 요청 메시지 = 별도 psmux_send_message btn-Codlearn 송신.
