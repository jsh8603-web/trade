---
tags: [type/direction, domain/inv, asset/bond, asset/cash, phase/study-2-1]
date: 2026-05-30
study_id: bond_cash
note: STUDY-KIT v2 §2-1 산출 — 방향성 종합. 자문 5R 수렴. 2-2(이론학습) 진입 전 main 승인 게이트.
source-rounds: raw/round-1.md ~ raw/round-5.md (각 라운드별 누적)
fallback: WebSearch native (자문채널 경합 회피, main 폴백 허용)
---

# bond_cash 방향성 종합 (2-1 산출 · 5R 수렴 결과)

> 본 문서는 STUDY-KIT v2 §2 의 **2-1 단계 산출** 이다.
> ⛔ 2-2 (이론학습 → theory-notes.md) 는 **main 승인 후** 착수한다. 본 직전 단계.

---

## ① 이론 수집 방향 (무엇을 정독·정리할까)

> "이 종목을 이해하려면 무슨 이론·교과서·리포트를 봐야 하나" — 5R 누적.

### A. 가격결정 1차 원리 (필수)
- **Carry / Duration / Convexity 3-항 분해** — Fabozzi *Fixed Income Analysis* (CFA Level 1 fixed-income 단원 기준) + AnalystPrep 자료 + Vinod Kothari 정리본
- **Modified duration**, **convexity adjustment**, **roll-down carry**, **option-adjusted spread (OAS)** 개념 명확화
- 원전 후보:
  - Carr, P. *Decomposing long bond returns: A decentralized modeling approach* (NYU)
  - CFA L1 Fixed Income 단원

### B. 자산배분 프레임 (필수)
- **Investment Clock** — Trevor Greetham 원전 (KS3 attached PDF) + Merrill Lynch 2004 original + Richard L Medium 해설 + Royal London/RLAM 공식 자료
  - 4국면 × 자산우위 표 (Reflation=Bond / Recovery=Stock / Overheat=Commodity / Stagflation=Cash)
  - **TIPS 분리 채널**: Overheat·Stagflation 에서 TIPS > 명목채 (Round 2·5 일관)

### C. Credit Cycle (필수)
- **HY OAS (BAMLH0A0HYM2)** = 침체 가장 신뢰 가능한 선행 지표 — Money365 분석 + Janus Henderson 시장 시각 + LongtermTrends 시계열
- **600 bps threshold** = 12~18개월 침체 ~85% (1996~2024)
- "peak HY 매수 → 15-25% / yr 2-3년" (contrarian carry 우위)

### D. Curve 역전 → 침체 lead time (필수)
- 평균 lead time = 48주 ≈ 11개월, IQR 6-18개월
- **bull steepening event** (역전 해소) = long-Tsy ETF (TLT/TLH) buy 시점 — 2007-2009 사례
- 원전: arXiv *Forecasting the Leading Indicator of a Recession: 10Y-3M* (2009.05507), Quantified Strategies, YCharts

### E. Cash sleeve 의 정량 가치 (필수)
- **Rate-cut optionality** (VGSH 사례) — 단기 T-Bill ETF 가 단순 carry 가 아닌 *옵션 자산*
- **Duffee** (JHU): 5년 이하 Tsy 의 월 Sharpe 가 주식시장 Sharpe 를 *살짝 초과* (REGIME_DIRECTION[Overheat][cash]="down" 재검토 트리거)
- T-Bill 공급량 → curve flattening 모니터 (Ainvest)

### F. 한국 KTB / Fed spillover (KR sleeve 확장 시)
- 3 driver: Fed rate cut + BoK rate + WGBI inclusion (ING THINK)
- BIS WP 1145: 달러 유동성 ↔ KTB 유동성 직접 연결
- arXiv 2402.07266: Fed 인상 + EPU 동반 → 신흥국 spillover *증폭*
- 5월 BoK 금리동결 + 인플레 전망 2.7% 상향 (CNBC 2026-05-28)

### G. 보조 (시간 허용 시)
- Distorted probability operator / Shortfall probability 최소화 (arXiv) — 위험 측도 robust 화
- Systemic global inflation 과 portfolio 함의 (arXiv 2111.11022) — 인플레의 systematic risk

---

## ② 이론 검증 방향 (어떻게 데이터로 검증할까)

> "그 이론을 우리 수집기 데이터로 시계열상 어떻게 검증하나"

### 1) 패널 구성 (PIT 강제)
- **거시 driver** (in_our_system 6 + 추가 6):
  - 보유: T10Y2Y / BAMLH0A0HYM2 / BAA10Y / T5YIE / NFCI / RECPROUSM156N / CFNAI
  - 추가 (collector_plan): DGS10 / DGS2 / DGS3MO / DFII10 / FEDFUNDS / MORTGAGE30US / VIXCLS / USEPUINDXD
- **자산 ETF** (collector_plan):
  - Long: TLT / TLH (10-20Y) / EDV (25Y+)
  - Mid: IEF (7-10Y)
  - Short: SHY (1-3Y) / VGSH (1-3Y)
  - Cash: BIL (1-3M) / SHV (≤1Y)
  - Credit: LQD (IG) / HYG / JNK (HY)
  - TIPS: TIP / VTIP / STIP
- **vintage_policy = point_in_time** 강제 (학습 입력은 release_date 기준)

### 2) 1차 검증 (회계항등 + 듀레이션 베타)
- **Fisher 분해 검증**: nominal_y = real_y + breakeven (이미 v1 raw 에서 Pearson=0.9999 확인)
- **Duration regression**: ΔP/P 회귀 = α + β·Δy + γ·(Δy)² + ε
  - 기대: β̂ ≈ -D (음수), γ̂ ≈ +0.5·C (양수)
  - R² 임계: long > 0.7, mid > 0.5
- **Carry-to-total decomposition**: 60일 cumulative return 분해 = carry + duration + convexity + residual

### 3) Regime 분해 (Investment Clock 4국면)
- **국면 라벨링** (CFNAI growth × T5YIE inflation 의 2축, NBER 침체일자로 가이드):
  - growth_axis: CFNAI 60일 sign / rolling z
  - inflation_axis: T5YIE 60일 변화 sign / rolling z
- **국면별 forward return panel**: TLT/IEF/SHY/BIL/HYG/TIP 의 60일 평균 + Sharpe
- **regime-conditional partial-corr** (RegimeGlasso): 가설 H2-A ~ H2-D 직접 검증

### 4) HY OAS · Curve 신호 검증
- **600 bps event study**: BAMLH0A0HYM2 ≥ 600 → 12~18개월 forward bond/cash sleeve return panel
- **Curve flip event study**: T10Y2Y 부호 flip 전후 ±18개월 forward TLT/IEF/SHY return
- **3-signal warning** (HY+curve+VIX) vs 단일 HY OAS: lead time IQR 비교

### 5) Falsification (반증 게이트)
- **anytime-valid e-process**: `weight_falsification.score_ic_breakdown_eprocess`
  - baseline_ic: regime별 사전등록 (Reflation→long=+0.05, Stagflation→cash=+0.04 등)
  - alpha=0.05, Ville 부등식
- **Omega drift**: `weight_falsification.omega_drift`
  - 듀레이션 bucket × regime 의 partial-corr 구조 변화 = TRANSITION 트리거
- **calibration**: belief b(t) ECE 검증 (regime 분류기 과신 차단)

### 6) Cash optionality 정량
- **Sharpe head-to-head**: SHY/BIL/SHV 의 36개월 rolling Sharpe vs SPY 동일 윈도 (Duffee 사실 재현)
- **Rate-cut event return**: FOMC 인하 발표 후 5/10/20일 SHV forward return 분포 (양수 분리 t-test)
- **Shock event CVaR**: 1987/1998/2008/2020 shock 이벤트에서 cash floor 효과

### 7) KR 분기 (KR sleeve 확장 시)
- KOSEF 국고채 ETF + DXY + FEDFUNDS + EPU + WGBI 편입 dummy → multi-factor regression
- 외국인 KTB 순매수 (한국거래소) + DXY Z → Rank-IC

### 8) 무거운 분석은 Bash python 으로 직접 실행 (main 지침 반영)
- 분석 스크립트는 `raw/validation-{지표}.py` + 결과 `raw/validation-{지표}.md`
- 출력 파일은 archive 사본 동반

---

## ③ 핵심 가설 초안 (반증조건 포함) — 5R 누적 16개 → 통합 12개

> 모든 가설은 **반증조건** + **데이터 출처** + **검증 코드 위치** 동반. R1~R5 의 H1-A ~ H5-E 정리 후 중복 통합.

| # | hypothesis_id | 본 가설 (1줄) | 반증 조건 | 검증 코드 위치 |
|:-:|---|---|---|---|
| 1 | `bond_return_decomposition` | 일별 ETF return = -D·Δy + 0.5·C·(Δy)² + carry/252 + idiosyncratic (R1) | TLT regress (Δy, Δy²) R² < 0.7 OR D̂ 부호 양수 | `core/data/weight_panel.py` + 신규 `etf_track.py` (R6 별도 검토) |
| 2 | `convexity_premium_positive` | TLT 의 일평균 convexity gain > 0 (R1) | t-test 양수 미유의 (p>0.10) | `weight_falsification.score_ic_breakdown_eprocess` |
| 3 | `regime_long_dur_reflation` | Reflation 국면 60일 forward TLT return > 전체 평균 + 유의 (R2) | regime-conditional t-test 기각 못 함 | `RegimeGlasso.fit` + regime 분류기 |
| 4 | `tips_overheat_stagflation_outperform` | Overheat·Stagflation 에서 TIP - TLT cumulative return > 0 (R2/R5) | spread 누적 ≤ 0 OR 미유의 | regime-conditional return panel |
| 5 | `cash_sharpe_competitive` | 1976-2024 SHY+BIL 월 Sharpe > SP500 월 Sharpe (R5, Duffee) | cash Sharpe ≤ stock Sharpe → REGIME_DIRECTION[Overheat][cash] 재검토 | `weight_falsification.rank_ic` + Sharpe 계산 |
| 6 | `hy_oas_600bps_recession` | HY OAS ≥ 600 후 12~18M forward bond - cash spread < 0 (R3) | spread ≥ 0 | event study panel (BAMLH0A0HYM2 1996~) |
| 7 | `hy_oas_widening_hyg_underperform` | HY OAS Z 6주 변화율 ↑ × HYG 4주 forward return 의 partial Rank-IC < 0 (R3) | Rank-IC ≥ 0 OR e-CUSUM 단측 붕괴 | `score_ic_breakdown_eprocess` |
| 8 | `flight_to_quality_tlt` | HY OAS Z 급등 시 TLT 1주 forward Rank-IC > 0 (R3) | Rank-IC ≤ 0 in shock window | shock window subset Rank-IC |
| 9 | `curve_flip_recession_lead` | 10Y-2Y flip event 후 forward 12M sleeve return 의 Rank-IC > 0 (R4) | baseline_ic 미달 OR sign reversal | curve flip event panel |
| 10 | `bull_steepening_tlt_lead` | 역전 해소 시점 후 6M TLT Rank-IC > IEF Rank-IC (R4) | TLT Rank-IC ≤ IEF | duration-arch panel |
| 11 | `rate_cut_optionality` | FOMC 인하 발표 후 5/10/20일 SHV forward return 양수 분리 (R5) | t-test 미유의 | FOMC event study |
| 12 | `fed_epu_compound_amplification` | Fed 인상 + EPU 동반 상승 시 KTB sleeve return < Fed 단독 인상 시 (R5, KR 확장) | compound shock 효과 미관측 | KOSEF + EPU multi-factor |

### Trade-off / 미확정 점
- **TIPS 분리 archetype 신설** 여부 (R2/R5) — main 의사결정 대상 (블록2 신규 indicator + 블록4 weight_rules `inflation_regime` modulate)
- **3-signal warning** (HY+curve+VIX) 합성 vs 단일 HY OAS — VIX (FRED VIXCLS) collector_plan 추가 의사결정
- **EPU index** (FRED USEPUINDXD) collector_plan 추가 의사결정 — KR sleeve 확장 시점 결정
- **etf_track 신설 vs stock_track 분기** — 본 방의 sleeve-내부 ticker 가중 inject 경로 (이전 v1 yaml 의 미확정 사항 그대로 유지)

---

## Trace — 라운드별 누적 출처

| 라운드 | raw 파일 | 주제 | URL 수 |
|:-:|---|---|:-:|
| 1 | `raw/round-1.md` | 가격결정 (Duration·Convexity·Carry) | 7 |
| 2 | `raw/round-2.md` | Investment Clock 4국면 | 10 |
| 3 | `raw/round-3.md` | HY OAS credit cycle | 7 |
| 4 | `raw/round-4.md` | Curve 역전 lead time | 9 |
| 5 | `raw/round-5.md` | Cash optionality + KTB/Fed spillover | 13 |
| **합계** | | | **46 URL** |

archive 사본: `~/.claude/docs/archive/research-raw/bond-cash-round{1..5}-native-20260530.txt` (5건 모두 보존).

---

## 2-2 진입 전 main 승인 요청 사항

1. **5R 수렴 충분 여부** — 본 ①②③ 로 2-2 (theory-notes.md) 진행 OK 판정 필요
2. **TIPS / VIX / EPU collector_plan 추가** 사전 결정 — 2-2 정독 깊이 확정용
3. **etf_track 신설 vs stock_track 분기** — 2-3 검증 단계 inject 경로 영향
4. **자문(gemini-web/claude-web) 추가 라운드** 요구 여부 — 본 5R 은 WebSearch native 폴백 (사용자 메시지의 채널 경합 회피 지침 + R5 마무리 명시 반영)

⛔ main 승인 전 2-2 (이론학습) 진입 금지. 본 멈춤은 idle 아님 (승인 대기 = STUDY-KIT v2 §2-1 명시 게이트).
