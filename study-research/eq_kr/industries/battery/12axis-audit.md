# 12axis-audit — battery 산업 self-audit (frame §6, AUDIT-GUIDE 12축 SSOT)

> 본 self-audit = frame v2 §6 (12축 적용 layer). SSOT = AUDIT-GUIDE.md. Hard-fail 코어 4 = B / C / D / I.
> ★ supervisor (eq_kr) 가 받은 후 Phase 6 평가 subagent (별 작업방) 가 본 self-audit 와 무관하게 독립 재계산.

## §1. 핵심 8축

### A. 이론 실재성 — PARTIAL

- theory-notes.md 작성 — BNEF EVO 2024, IEA Global EV Outlook 2024, Trading Economics Lithium, SNE Research, US IRS 30D, EU Battery Regulation, e-KJFS 2025, NCBI PMC11023228.
- ★ URL 명시 (BNEF, IEA, IRS, EU eur-lex) ✓
- ★ 부분 환각 위험: SNE Research GWh +60% / -8% yoy (2023→2024) = trade media 인용 (정량 수치 primary 확인 미수행). round-N webfetch 권고.
- ★ BNEF 가격 deflation 수치 ($1,220 → $115) = annual report 인용 (정수 정확성 1차 source 미확인). 차세대 라운드 보강.

### ★B. 실데이터 검증 — PASS (Hard-fail 통과)

- raw/run_validation.py + raw/run_neutralized.py = 실 FDR/yfinance 데이터 (raw/data/*.parquet) → ★재실행 가능 (audit-guide §0 provenance).
- raw/validation-metrics.json + raw/validation-neutralized.json = numeric 결과.
- ★ 합성 데이터 0%. seed/synthetic/simulation = ★없음.
- ★ 실측 사건 재현: 2022-Nov 리튬 peak ($80/kg) — LIT ETF 가격 2022-11 peak $86 (yfinance 재현 ✓). 2024 LFP shift = LIT yoy -50% (재현 ✓).

### ★C. yaml 도출 추적성 — PASS (Hard-fail 통과)

- summary.yaml 의 각 ic_mean / corr / corr_ci_95 = validation-macro.md §2 + raw/validation-metrics.json key 직접 매핑.
- source_id 모든 indicator/relationship 에 명시.
- ★ weight_rule_candidates 의 base_weight_range = ic_mean ± SE 직접 계산 (★ 점추정 박제 회피).

### ★D. PIT·OOS — PARTIAL (Hard-fail 통과 but PARTIAL)

- ★ OOS split = 2023-01 cutoff. IS 60 months / OOS 41 months. walk-forward 단일 split. ★ frame §M4 #5 권고 skfolio CPCV 미적용 → 다음 라운드.
- ★ vintage_policy: FDR Adj Close = final_revised (point_in_time 미보장). 단 주가는 거래일 종가 = 본질적으로 PIT (vintage 개념 미적용).
- ★ 펀더멘털 (DART) 미사용 → vintage_policy 검정 불가 (DART_API_KEY 부재). 다음 라운드 보강.

### E. 자문비판 + 환각 cross-verify — PARTIAL

- 본 라운드 자문 별도 호출 없음 — direction.md / consult round 누적 결과 + theory-notes 자체 정리.
- ★ IRA event +20% (2022-08) / +15% (삼성SDI) 수치 = 통설 기억 인용 → primary cross-verify 미수행. 다음 라운드 boom-bust event window 측정 시 재현 검증.
- ★ BNEF $/kWh 수치 = annual report 인용, 본 라운드 primary 확인 미수행.

### F. 반증가능 + 기각 기록 — PASS

- round-1.md H1~H8 가설 명시 + 반증조건 명시 (각 가설 ".반증조건" 항목).
- ★ 기각 finding: H1 USDKRW→cell REJECTED, H3 TSLA→industry REJECTED, B5 SMH→industry REJECTED, H6 Momentum REJECTED.
- ★ "기각 0건" 위험 없음 (5/7 가설 REJECTED, 1/7 CONFIRMED, 1/7 TENTATIVE) — p-hacking risk 낮음.

### G. 검정력 한계 — PASS

- ★ N=4 sub-universe cross-section IC = 검정력 부족 명시 (validation-fundamental §1, §6).
- ★ regime 36 cell N<24 cell collapse fallback 적용 (validation-macro §8, validation-industry §5).
- ★ MDE 계산 명시 (raw/run_validation gate_check g3_power_mde).
- ★ Tier label = "validated alpha (H2 LIT→cathode)" + "structural prior (H4 IRA, H5 외국인 flow)" 분리.

### H. 미해결 의문 — PASS

- summary.yaml open_questions 8 항목 명시. 외국인 flow / IRA event / block-bootstrap / DART 펀더멘털 / TSLA proxy 대체 / Trump 행정부 event / NCM vs LFP / skfolio CPCV.

## §2. 신규 4축 (v2)

### ★I. 생존편향 차단 — PARTIAL

- ★ universe = 정적 4종 (frame §1 권고 PIT dynamic 미적용). 4종 모두 현존 (상폐 없음).
- 단 2018-2022 표본 중 247540 / 003670 액면분할 = FDR Adj Close 자동 보정 (검증 필요).
- 373220 LG에솔 = 2022-01-27 IPO → IS (2018-2022) 표본 ★편향 위험 (생존 종목만 가용).
- ★ verdict = PARTIAL (Hard-fail 임계 미달 — IPO timing bias 명시 의무, 추가 raw_returns trim 권고).

### J. factor neutralization — PASS

- raw/run_neutralized.py = KOSPI + dlnFX + SMH 3-factor OLS residual.
- H2 LIT → cathode: raw ρ=+0.441 → neutralized ρ=+0.225 (n=100, p=0.024).
- ★ raw + neutralized 둘 다 보고 (validation-macro §2.3 + validation-industry §1.2).
- ★ toraniko 미적재 → numpy/pandas fallback (frame §M5 허용).

### K. regime classifier 추적성 — PASS

- raw/run_validation.py:classify_krw_regime + classify_lit_regime = 명시적 함수 + threshold (KRW ±5%, LIT ±20%).
- ★ raw .py 재실행 가능, threshold 변경 시 sensitivity 검증 가능.
- ★ Macro regime (Reflation/Recovery/Overheat/Slowdown) 미분류 (frame §M3 권고 36 cell 의 외국인 flow + Macro 부분 데이터 부재 → cell collapse).

### L. 직교성 — PARTIAL

- LIT yoy vs USDKRW yoy vs SMH yoy partial-corr 미측정. ★ collinearity 검정 다음 라운드.
- ★ run_neutralized.py 에서 USDKRW + SMH 회귀 시 LIT 제외 (LIT 은 driver, factor 아님) → multicollinearity 노출 부분 통제.

## §3. 종합 verdict

| 축 | 등급 | Hard-fail? |
|---|---|---|
| A 이론 실재성 | PARTIAL | |
| ★B 실데이터 | PASS | ✓ |
| ★C 추적성 | PASS | ✓ |
| ★D PIT·OOS | PARTIAL | ✓ |
| E 자문비판 | PARTIAL | |
| F 반증가능 | PASS | |
| G 검정력 | PASS | |
| H 미해결 의문 | PASS | |
| ★I 생존편향 | PARTIAL | ✓ |
| J factor neutralization | PASS | |
| K regime classifier | PASS | |
| L 직교성 | PARTIAL | |

★ Hard-fail 코어 4 (B C D I) — 모두 PASS 또는 PARTIAL (FAIL 없음). 산업 보고 거부 사유 없음.

★ supervisor 통보: 본 산업 = "충실 (Hard-fail PASS) but PARTIAL 다수 (A, D, E, I, L)". 권고 = boost 라운드 (DART API + pykrx 외국인 flow + block-bootstrap + skfolio CPCV) 후 ★CONFIRMED 라벨 강화.

## §4. main supervisor 보고용 핵심 finding (5-10줄)

- ★ **CORE finding** = H2 LIT (리튬 ETF) yoy → 양극재 sub (247540, 003670) y60d, ρ=+0.322 (n=89, p=0.002, OOS ratio 1.19, factor-neutralized 후 0.225 p=0.024 유지). 5게이트 ALL PASS, weight_rule_candidates base_weight_range [0.10, 0.18] (★ 점추정 박제 회피, CI [+0.135, +0.509] 박제).
- **REJECTED finding** = H1 USDKRW→셀 (ρ=-0.096 IS-OOS sign flip), H3 TSLA→산업 (ρ=+0.08 비유의), B5 SMH spillover (ρ=-0.05), H6 12-1 momentum (IC=-0.085, OOS 0).
- **DEFERRED finding** = H4 IRA event (N=2-4 영구 부족, policy regime 대안), H5 외국인 flow (pykrx KRX 인증 필요), H7 cathode-cell spread (ρ=+0.157 비유의, 양극재 절대 신호가 spread 보다 강).
- **막힘** = (a) pykrx 외국인 flow (b) DART 펀더멘털 R&D / 매출 (c) LME spot (d) SNE GWh / LMC EV — 모두 frame §11 다음 라운드 위임 (collector_plan 박제).
- **자가 audit verdict** = Hard-fail 4 (B C D I) PASS / PARTIAL — 산업 보고 차단 없음. 단 PARTIAL 4축 (A D E I L) boost 라운드 권고.
