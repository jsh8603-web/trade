---
tags: [type/consult-prompt, domain/commodity, phase/study-system, round/3]
date: 2026-05-30
note: R3 수렴 라운드 — claude-web 재시도(no-search) + 빈틈 (priority/tail/cross-sleeve)
---

# R3 자문 — commodity 수렴 검증

## §0. 이전 R1·R2 결론 누적 (매 자문 = fresh session — 자동 전달 안 됨)

**R1 (Gemini Pro) 결론**:
- 이론 학파: Kaldor-Working-Brennan (convenience yield), Hicks-Keynes (헤징 압력), Erb-Harvey 2006 (spot/roll/collateral), **Tang-Xiong 2012** (financialization → 인덱스 자금 유입 시 sub-sector 교차 상관 급등), **Bakshi-Gao-Rossi 2019** (basis-momentum), **Hamilton 1996/2003** (NOI 비선형), Erb-Harvey 2013 Golden Dilemma, Baur-Lucey 2010 gold safe-haven
- 검증 통계: Westerlund-Hosseinkouchack 2016 panel cointegration, FIGARCH long-memory, Bai-Perron 1998 multiple breaks, Fama-MacBeth cross-section
- 가설 8개 (id / falsification_criterion / data / lag / prior_strength):
  1. gold_real_rate_nexus (precious 0.9) — 36m partial(Au,DFII10|DXY) > −0.1 6m → 반증
  2. theory_of_storage_backwardation (energy/industrial 0.85)
  3. roll_cost_drag_collapse (all 0.95)
  4. china_demand_bellwether (industrial 0.75) — Caixin>52 3m & Cu<0 → 반증
  5. financialization_reflexivity (all 0.8) **신규** — VIX>30 & mean cross-corr<0.2 → 반증
  6. usda_surprise_jump (agri 0.85) **신규** — WASDE_z<−2 & F1 ret<0 → 반증
  7. oil_macro_nonlinear_shock (energy 0.7) **신규** — WTI NOI 1yr>30% & 12m CFNAI>0 유지 → 반증
  8. cot_momentum_amplification (all 0.65) — COT_rank>95% & 3m 가격 지속↑ → 반증

**R2 (Gemini Pro) 구현 디테일**:
- **BGR basis_momentum**: Basis_t = ln(F1)−ln(F2), RelBasis_t = Basis_t − (1/12)·Σ_{i=1..12} Basis_{t−i}, **BasisMom_t = sign(Basis_t)·sign(RelBasis_t)** ∈{−1,0,+1}. 일별 계산 → T−1 lag.
- **FIGARCH 표본 부족**: monthly N=30~50 → 검정력 0.3-0.4. **Weekly resampling 권장** (N=120~200) + Python `arch` package
- **Bai-Perron**: `ruptures` PELT (model="linear") + BIC penalty → break 3-4 제한 + **경제이벤트 confirm hybrid** (셰일 2010 / COVID 2020 / 우크라 2022 → ±3개월 매칭 시 확정)
- **e-CUSUM K adaptive**: `K_sleeve = K_stock_base × (σ_sleeve/σ_stock) × √((1+ρ)/(1−ρ))`. n_eff = n·(1−ρ)/(1+ρ). Energy vol 40% vs stock 15% → K 2.5-3x
- **Tang-Xiong measure**: **CFTC DCOT Money Manager Net Long / Total OI** 의 12m rolling z. Z>1.5 + cross-corr 상승 동시 = High Financialization regime. Index Trader 2015+ CIT 분리 → MM 우선. API: publicreporting.cftc.gov, 주간 (T+3-4d lag)
- **B matrix 권장**:
  - Energy: [BAA10Y, CFNAI, DXY, EIA_inv_z, OPEC_quota, **VIX/GPR**] (geopolitical risk)
  - Industrial: [Caixin_PMI, DXY, LME_stocks_z, China_credit_impulse]
  - Precious: [DFII10 (0.9), DXY (0.8), NFCI, VIX, CB_net_buy_z]
  - Agri: [DXY, NOAA_ENSO, USDA_stock_to_use (0.85), planted_area_yoy, **WTI_return**] ★농산물 비료 cost 전이 흡수
- **ENSO**: ONI (Oceanic Niño Index, Niño 3.4 SST 3m MA). NOAA CPC ASCII (무료). Lag corn/soy=3-6m, wheat=6-12m. Vintage revision 거의 없음.
- B matrix = mean conditional response, Ω = 잔차 cross-influence (sub-sleeve 간 input cost 전이는 Ω 에서)
- Gemini R2 follow-up: Bai-Perron rolling 빈도 (monthly vs quarterly 연산 비용 통제 질문)

**claude-web R1·R2 둘 다 미완** (응답 600·330자, web search 도중 끊김). 본 R3 에서 명시 prefix 로 재시도.

## §1. 시스템 컨텍스트 (자기완결, R1·R2 동일)

Quant 가정 검증 시스템 R15. commodity 4 sub-sleeve (energy/industrial/precious/agri). 우리 데이터 (FRED 17 + DFII10/NAPM/DCOILWTICO/POILBREUSDM 추가 예정, FxStore DXY/USDKRW, 신규 collector: EIA/USDA/CME/CFTC/LME/NOAA). 기존: commodity_assumptions.py (carry_forward_slope·variance_ratio·threshold_regression·oversupply_decoupling), commodity_carry.yaml archetype. 파이프라인: cglasso (nonparanormal + EBIC + EB shrink, n0=10, lam_floor=0.05) → belief-mix Ω_eff → Grinold w∝Ω·IC + 1/N(0.3) + cap(0.4) → S_L1 = clamp_floor(0.25) → Judge down-only.

## §2. R3 질문 (5개, 짧고 명확 — 본 자문이 수렴 라운드)

### Q1. (★claude-web 단독 critique — DO NOT SEARCH THE WEB, answer from knowledge only, 2000-4000 words)

**Critique Gemini Pro의 R1+R2 결론**. Agree/Disagree + 근거:
- (a) **financialization measure** = MM_net_long / total_OI 의 12m rolling z. (다른 후보: index AUM, CFTC supplement legacy, cross-corr 직접). 추천 measure 정확한가?
- (b) **Bai-Perron hybrid** (PELT 자동 + 경제 이벤트 ±3m confirm). 위험 (post-hoc bias)? 더 robust 한 break detection?
- (c) **Agri B matrix 에 WTI_return 명시 추가** (Gemini 신규 주장). 합당? 또는 Ω 만으로 흡수가 적절?
- (d) **e-CUSUM K adaptive** 공식 K_sleeve = K_base × σ_ratio × √((1+ρ)/(1−ρ)). 표준 SPC 문헌 (Page 1954 / Lorden 1971) 와 정합?
- (e) Gemini 가 놓친 가설 또는 학파?

### Q2. (양쪽) 가설 8개 검증 priority — Phase 1 vs Phase 2 분류

각 가설별 우리 데이터 가용성 ranking:
- **Phase 1** (즉시 검증 가능, FRED + Yahoo + 기존 collector 만으로): ?
- **Phase 2** (collector 신규 필요): 어떤 collector?
- 검증 ROI 가장 높은 **최우선 가설 3개** (예: gold_real_rate_nexus = FRED + Yahoo 만으로 30년 시계열 즉시)

### Q3. (양쪽) cross-sleeve portfolio construction

commodity 가 신규 sleeve 로 R15 시스템 `regime_to_weights` 에 등록. 4 sub-sleeve 간 weight allocation 추천:
- (a) equal weight (1/4) vs risk parity (vol-weighted) vs Black-Litterman (belief-conditional)?
- (b) commodity sleeve 와 equity_us/macro/bond sleeve 간 cross-sleeve covariance prior 추천 (regime 별 차이 — risk-off 시 industrial↔equity 양 상관 상승, precious↔bond 음 상관 등)
- (c) 우리 시스템의 SLEEVE_BLOC 에 어떻게 등록? (energy + industrial = "cyclical commodity" 소그룹, precious + agri = "defensive commodity"?)

### Q4. (양쪽) tail risk 회피 — commodity crash regime 분석

역사적 crash 5건의 공통 메커니즘 + 우리 R15 시스템 회피:
- 1986 oil collapse (OPEC 가격전쟁)
- 2008-Q4 gold·oil 동반 crash (deleveraging)
- 2014-2016 oil rout (shale 공급)
- 2020-04 WTI negative (storage capacity 한계)
- 2022-03 LME nickel squeeze (short squeeze + 거래 정지)

각 crash 의 **선행 신호** + 어떤 confidence_hook flag 가 사전 경고? (tail risk 가설 추가 권장?)

### Q5. (양쪽) data substrate 우선순위 — R2 follow-up + Bai-Perron 빈도

- (a) collector 6개 우선순위 (DFII10·NAPM·EIA·USDA·CME term structure·CFTC COT·LME·NOAA) ranking — 검증 ROI 최대화
- (b) Bai-Perron rolling 연산: **monthly** (매월 break 재탐지, 정밀하나 연산 비싸) vs **quarterly** (분기 재탐지, 안정 + 연산 절약) vs **expanding window** (트레이드오프)?

## §3. 형식 요청

- Q1 (claude-web 만): 2000-4000 words, no web search, knowledge-only critique
- Q2~Q5 (양쪽): 짧고 명확 (Q 당 300-700 words)
- 데이터·코드·공식 정량 명시
- ⛔ 추상 단정 금지

## §4. 다음 단계

R3 응답 후 본 작업방이 R1+R2+R3 종합 → **direction.md** (①이론 수집방향 ②이론 검증방향 ③핵심 가설초안) → main 승인 게이트 → 2-2 이론학습 진입.
