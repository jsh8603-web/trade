---
tags: [type/consult-prompt, domain/commodity, phase/study-system, round/2]
date: 2026-05-30
note: R2 자문 — R1 (Gemini Pro) 결론 누적 + 7개 구현 디테일 질문. claude-web/gemini-web 공통.
---

# R2 자문 — commodity 검증 구현 디테일 정량화

## §0. 이전 자문 맥락 (R1 결론 누적 — 매 자문 = fresh session 이라 자동 전달 안 됨)

R1 (Gemini Pro 응답 8441자) 핵심 결론:

**이론 학파 보강** (사용자가 R0 에 놓친 시각):
- Tang & Xiong (2012, RFS) "Index Investment and the Financialization of Commodities" — 2004년 이후 commodity index 자금 유입으로 sub-sector 간 교차 상관 비정상 상승 (=반사성/financialization)
- Bakshi, Gao, Rossi (2019, Mgmt Sci) "A Better Measure of Commodity Risk Premia" — basis-momentum 시그널 (basis + relative-basis 결합) 이 carry/momentum 단일보다 우수
- Hamilton (1996 JME, 2003 J Econometrics) — Net Oil Price Increase (NOI) 비선형. 유가 1년 최고치 경신폭만 침체 예측, 하락은 비대칭
- Erb & Harvey (2013 FAJ) "The Golden Dilemma" + Baur & Lucey (2010 FR) gold safe-haven 실증
- Hicks-Keynes Normal Backwardation, Kaldor 1939 / Working 1949 / Brennan 1958 convenience yield, Erb-Harvey 2006 spot/roll/collateral 분해

**검증 통계 추가**:
- Westerlund-Hosseinkouchack (2016) panel cointegration (재고-가격 장기균형 검증)
- FIGARCH (Fractionally Integrated GARCH, Baillie-Bollerslev-Mikkelsen 1996) — commodity vol long-memory
- Bai-Perron (1998 Econometrica) multiple structural breaks — 셰일/COVID 전후 β shift 탐지
- Hamilton (1996) NOI 비선형 변수 + Threshold regression 결합
- Fama-MacBeth cross-section + Rolling Portfolio Sharpe/MDD

**가설 8개 yaml** (id / statement / sub_sleeve / falsification_criterion / data_required / lag / prior_strength):
1. `gold_real_rate_nexus` (precious, 0.9) — 36m partial-corr(Au, DFII10 | DXY) > −0.1 6개월 → 반증
2. `theory_of_storage_backwardation` (energy/industrial, 0.85) — inv_z<−1.5 인데 (F1−F2)/F1>0 4주 → 반증
3. `roll_cost_drag_collapse` (all, 0.95) — contango>6m 인데 index>spot+2% → 반증
4. `china_demand_bellwether` (industrial, 0.75) — Caixin>52 3m 인데 Cu return<0 → 반증
5. `financialization_reflexivity` (all, 0.8) **신규** — VIX>30 인데 mean cross-corr(energy/agri/metal)<0.2 → 반증
6. `usda_surprise_jump` (agri, 0.85) **신규** — WASDE_z<−2 인데 F1 daily return<0 → 반증
7. `oil_macro_nonlinear_shock` (energy, 0.7) **신규** — WTI 1yr NOI>30% 이고 12m 후 CFNAI>0 유지 → 반증
8. `cot_momentum_amplification` (all, 0.65) — COT_rank>95% 후 3m 가격 지속 상승 → 반증

R1 응답 끝부분에 Gemini 가 R2 후속 질문 제안: 데이터 가용성 우선순위 + e-CUSUM 임계 설정 기준.

## §1. 시스템 컨텍스트 재요약 (자기완결, R1 동일)

Quant 가정 검증 시스템 R15. commodity 자산군 (4 sub-sleeve: energy/industrial/precious/agri).

**우리 가용 데이터**: FRED 17 시리즈 (DFII10·NAPM·DCOILWTICO·POILBREUSDM 4개 추가 예정, 1줄 수정 가능), FxStore PIT (DXY/USDKRW, main 선구축), 신규 collector 필요 (EIA crude/petroleum stocks free API, USDA WASDE stock-to-use free, CME 지연 EOD futures term structure, CFTC COT public, LME 1차 stub 보수 band). 이미 보유: `core/structure/commodity_assumptions.py` 의 carry_forward_slope (prequential sign_flip), seasonal_f_test, variance_ratio (Lo-MacKinlay), threshold_regression (Hansen), oversupply_decoupling. `config/archetypes/commodity_carry.yaml` (primary=roll_yield).

**파이프라인**: regime-conditional graphical lasso (nonparanormal + EBIC + EB shrink, n0=10, lam_floor=0.05) → belief-mixed Ω_eff → Grinold w∝Ω·IC + 1/N(blend=0.3) + cap(0.4) → S_L1 = clamp_floor(Σwz, floor=0.25) → Judge LLM down-only attenuation. flag emit/accumulate → e-value/Beta posterior → derive_weights 재적합 (route_lifecycle SECONDARY).

**규모**: regime 당 obs N ≈ 30~50 (monthly 2년~4년). cglasso 표본 부족 — EBIC + EB shrinkage 보강.

## §2. R2 질문 (7개) — 구현 정량 + Python 단편

각 질문에 (a) 정확한 수식 또는 알고리즘 (b) Python 구현 단편 또는 패키지 추천 (c) 우리 데이터 매핑 / lag / vintage 명시.

### Q1. Bakshi-Gao-Rossi (2019) basis-momentum 정확한 계산식

"R1 에서 SOTA 로 추천된 Bakshi-Gao-Rossi 2019 의 basis-momentum signal 정의식을 정확히 적어달라:
- basis_t, relative_basis_t, basis_momentum_t 계산식 (CME EOD F1·F2·F3 만으로)
- 일별 또는 월별 frequency 권장
- 신호 부호 (양=long / 음=short)
- 우리 시스템에서 indicator id 명명 (예: `bgr_basis_momentum_12m`)"

### Q2. FIGARCH 우리 표본 정밀도

"FIGARCH(1,d,1) 추정에 필요한 최소 obs 수. 우리 regime 당 N=30~50 monthly 이 부족하면:
- weekly resample (4x obs) 로 보강 가능?
- 또는 GARCH(1,1) + Granger-Joyeux long-memory test 로 다운그레이드?
- Python `arch` (Sheppard) package 코드 단편: `am = arch_model(returns, vol='FIGARCH', p=1, q=1); res = am.fit()`
- d (long memory) 추정 SE, p-value (H0: d=0=short memory) 우리 표본 검정력"

### Q3. Bai-Perron Python 패키지 + 우리 표본 검정력

"Bai-Perron 1998 multiple structural breaks 검정 Python:
- `ruptures` (PELT/BinSeg) vs 직접 구현 vs `statsmodels.tsa.regime_switching`
- 25년 monthly = 300 obs / regime 분리 후 30~50 obs 검정력
- 최대 break 수 권장 (3? 5?)
- 셰일 혁명 (2010 전후), COVID (2020-03), 우크라이나 (2022-02) 사전 후보 윈도우 — auto 탐지 vs 지정?
- 코드 단편 (m breaks regression with structural change in slope of `commodity_return ~ macro_factors`)"

### Q4. Rank-IC e-CUSUM K boundary sub-sleeve 별

"우리 weight_falsification.score_ic_breakdown_eprocess 의 e-CUSUM 단측 K boundary (stock 기본 추정). commodity sub-sleeve 별 variance 차이:
- energy realized vol ≈ 30-50%, precious ≈ 15-25%, industrial ≈ 20-35%, agri ≈ 20-30%
- K boundary 를 stock 의 (a) 동일 (b) 1.5x (c) 2x (d) sub-sleeve adaptive — 각 옵션의 false alarm rate (Type I) 와 detection delay (Type II)?
- e-CUSUM 의 standard practice (Page 1954, Lorden 1971) 적용. n_eff (autocorr 보정, AR1 ρ) 우리 시계열에 0.3~0.5 가정 — K 조정 공식?"

### Q5. financialization 측정 — Tang-Xiong measure 재현

"Tang-Xiong (2012) 의 financialization measure 구체:
- CFTC Disaggregated COT (DCOT) report — "Money Manager" + "Index Trader" 카테고리 net long position 직접 사용?
- 또는 commodity index AUM / total open interest 비율?
- 가공 단계 (raw → log-z → cross-section avg)
- 매핑: CFTC public API (https://publicreporting.cftc.gov/) — 주간 발표, lag 3일
- Python `requests + pandas` 단편 (DCOT extract)
- 신호 임계 (재고 z>1.5 = high financialization regime?)"

### Q6. sub-sleeve 별 B matrix (n_assets × n_macro) 권장 구조

"cglasso 의 conditional model: asset_core | macro ~ N(B·macro, Ω_asset). sub-sleeve 별 B prior 구조 제안:
- **Energy** (WTI/Brent/NG): B columns = [BAA10Y, CFNAI, DXY, EIA_crude_inv_z, OPEC_quota_z]
- **Industrial metals** (Cu/Al/Ni/Zn): B columns = [Caixin_PMI, DXY, LME_stocks_z, China_credit_impulse]
- **Precious metals** (Au/Ag/Pt): B columns = [DFII10, DXY, NFCI, VIX, central_bank_net_buying_z]
- **Agricultural** (corn/wheat/soy): B columns = [DXY, NOAA_ENSO_index, USDA_stock_to_use, planted_area_yoy]

이 분리가 cglasso 분담에 적절한가? 사용자 놓친 macro driver / sub-sleeve 별 추가/제거 권고?
prior_strength: B coefficient 별 권장 calibration (예: gold→DFII10 = 0.85, gold→DXY = 0.7).
그리고 sub-sleeve 간 cross-influence (예: energy → industrial via input cost) 를 cglasso 의 어디서 흡수?"

### Q7. ENSO index 시리즈 권장

"agri sub-sleeve 의 ENSO 기상 risk indicator:
- NOAA MEI v2 (Multivariate ENSO Index) 또는 Niño 3.4 SST anomaly 또는 ONI (Oceanic Niño Index)
- 가용성: FRED 미보유 → 신규 collector 필수. NOAA https://www.cpc.ncep.noaa.gov/ 무료
- monthly 발표, 가공 (3개월 rolling 평균 = ONI 정의)
- agri 가격 영향 lag (3-12 months 보고됨), sub-asset (corn vs wheat vs soy) 별 차이?
- Python download 단편 (NOAA CSV → pandas)"

## §3. 형식 요청

- Q1~Q7 **모두** 답변 (skip 금지). 각 Q 별로 (a) 정확한 수식/알고리즘 (b) Python 단편 5-15줄 (c) 데이터 매핑 + lag + vintage
- 인용 (저자년) + 핵심 발견 1줄
- 우리 시스템 코드 (`commodity_assumptions.py`, `weight_falsification.py`, `weight_panel.py`) 와 통합 시 구체 함수명 제안
- ⛔ 추상 단정 금지 — 모든 통계 게이트는 정량 수치

## §4. 다음 단계 (R3 또는 수렴)

R2 응답 후 본 작업방이 두 모델 응답 비교 → 의견 차이/공통/빈틈 → R3 (필요 시) 또는 direction.md 수렴 (이론 수집방향·이론 검증방향·핵심 가설 초안 3 섹션 완성) → main 승인 게이트.

답변 길이 제한 없음 — **완전성·정확성 우선**.
