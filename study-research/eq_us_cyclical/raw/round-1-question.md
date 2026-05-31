---
tags: [type/consult-question, study/eq_us_cyclical, round/1]
date: 2026-05-30
---
# Round 1 자문 질문 (gemini-web + claude-web 동시 송신)

## 1. 컨텍스트 (자기완결)
저는 **미국 경기민감주(US cyclical equity)** 자산군의 종목 단위 평가 시스템을 설계하는 담당 애널리스트입니다.

- **자산 정의**: GICS 11섹터 중 Consumer Discretionary(XLY) · Industrials(XLI) · Materials(XLB) · Energy(XLE) · Financials(XLF) + IT 일부(반도체 SOX = early-cycle 대표). Defensive(Staples/Utilities/HealthCare) 와 대비.
- **시스템 목적**: 평가 지표의 가중치를 거시 국면·산업 사이클·종목 특성에 따라 **동적으로** 바꾸는 R15 동적 가중 메타레이어. 학습→규칙화→주입→해제 4단계 파이프(regime-conditional glasso + Grinold IC + e-process falsification).
- **현재 진행상황(이전 v1 산출)**:
  - 합성 반도체 패널(40firm×36Q, 2014-2023) 분석으로 (a) valuation(val_gap) Rank-IC=**+0.658** 압도, multiple IC=-0.427 (b) momentum/rev_growth IC=+0.054 약함 (c) **peak_trap**(peak regime val_gap≈0 + 유망비율 0%) (d) inventory_qoq·capex 과열 IC=-0.31 역신호 (e) val_gap→Δmultiple(t+1) IC=+0.385 mean-reversion 메커니즘 확인.
  - 거시지표(ISM/HY OAS/DXY/WTI) 부재로 ism/credit/dollar/oil/rate 관계는 미검증. 라이브 환경 EDGAR + FRED + ETF holdings 적재 후 재검증 예정.

## 2. 의뢰 질문 — 세 가지를 자세히

### ① 이론 수집 방향 (필수 자료 우선순위)
미국 경기민감주를 **전문 애널리스트 수준**으로 이해하려면 어떤 교과서·리포트·프레임워크를 봐야 하나? 다음 후보를 평가하고 빠진 핵심을 추가해 주세요:
- Damodaran (Valuation, "Aswath Damodaran on Valuation" — 사이클 종목 적정 P/E·EV/EBITDA 결정)
- Fama-French 3/5-factor + Carhart momentum
- Merrill Lynch Investment Clock (Trevor Greetham 2004) — 4국면 자산매핑
- Ken French data library (industry portfolios, FF factors)
- NBER recession dating + ISM PMI 해석 (manufacturing/services)
- Sector rotation 모델 (Fidelity, S&P 사이클별 섹터 weighting)
- Operating/Financial leverage 분석 (DOL/DFL/DCL — Brealey-Myers Corporate Finance)
- Late-cycle/peak detection (Ned Davis Research, yield curve inversion)
- Behavioral cycle / sentiment indicators (AAII, BoA Bull&Bear)
- Sell-side industry reports (Goldman cyclical playbook, Morgan Stanley sector primer)

**필수 5-10개를 우선순위 + 그 이유**로 답해 주세요. 한국어 답변.

### ② 이론 검증 방향 (시계열 통계 검증법)
위 이론을 시계열 데이터로 **falsifiable**하게 검증하려면 어떤 통계 기법을 어느 가설에 적용해야 하나?
- regime-conditional **partial correlation** (glasso EBIC)
- **lead-lag Rank-IC** (선행지표 → t+k 수익)
- **anytime-valid e-process** (Ville inequality — type-I 통제하면서 optional-stopping robust)
- structural break test (Bai-Perron, CUSUM)
- Bayesian model averaging (regime mixture)
- block-bootstrap autocorr 보정 IC
- **MDE + effective-n 사전등록** (소표본 검정력 게이트)

각 기법이 어느 종류 가설(상관·인과·예측력·국면전환)에 적합한지, **잘못 쓰면 어떤 함정**이 있는지 짚어 주세요.

### ③ 핵심 가설 초안 (반증조건 명시 — 데이터 통계량 기준)
경기민감주 알파의 핵심 가설 **6-10개**를 제시하고, 각 가설에 **명시적 반증조건**(어떤 통계량이 어떤 임계 아래로 갈 때 거부)을 적어 주세요. 예시 양식:

> H1: "Forward E/P z-score가 trough regime에서 forward 12M return의 가장 강한 단일 예측자다."
> 반증: "OOS Rank-IC < momentum OOS Rank-IC 가 연속 3개 regime 윈도에서 성립" 또는 "anytime-valid e-process 단측 붕괴(reject = baseline 0.1 아래)".

특히 다음 영역을 다뤄 주세요:
- valuation vs momentum 우위 (cycle phase별)
- ISM PMI · yield curve · HY OAS · DXY · oil 의 **선행성/공통원인**
- rate_beta의 name_specific(고멀티플 vs value 경기민감) 분리
- peak_trap (정점 신규진입 차단의 조건)
- operating_leverage의 EPS 증폭 (proxy=gross_margin 한계 인정하면서)
- regime 전환점에서 **revision breadth** 의 turning-point alpha

## 3. 응답 기대 양식
- 한국어 답변, 섹션별 (①②③) 명확 구분.
- 가능하면 출처(저자/연도/책·논문)를 함께.
- **반론·맹점·간과** 환영합니다. 제 v1 분석의 함정·왜곡도 지적해 주세요.
- 길이: 2000-4000자 권장. 너무 압축하지 말 것.
