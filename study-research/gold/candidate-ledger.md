---
tags: [type/candidate-ledger, domain/inv, study/gold, phase/2-3]
date: 2026-05-31
study_id: gold
note: 자문(R1+R2)+이론+M3+v1+main 추가 지시에서 등장한 모든 지표 후보 enumeration + 채택/이연/미채택 + 사유. direction.md/collector_plan/audit 흩어진 사항 1파일 집약 — "뭐가 왜 빠졌나" 한눈에.
---

# gold 지표 후보 ledger (study v2)

> 예시 = `study-research/commodity/candidate-ledger.md`. 후보 출처 = 자문 R1·R2 (gemini-web + claude-web) + theory-notes (학술 + WGC GRAM) + M3 macro-linkage + v1 산출 + main 추가 지시.
> 분류 enum: **[채택-force]** = force_include 4 / **[채택-indicator]** = 블록2 / **[채택-basis-pin]** = 항등식 basis 외부 가드 / **[채택-monitor]** = computed 지표 (다른 검증 산출) / **[이연-collector]** = collector_plan 신규 fetch / **[이연-proxy]** = 임시 proxy 대체 / **[미채택-tautology]** = Fisher 항등식 / common-cause 분해 / **[미채택-OOS]** = 검증력 부족 OOS 보류 / **[미채택-skip-explicit]** = 명시 skip.

---

## §A 1차 가격 driver (R2 합의 핵심 — 모두 force_include 4 또는 basis pin)

| # | id | 출처·시리즈 | 분류 | 사유 |
|---|---|---|---|---|
| A1 | real_rate_10y | FRED DFII10 | **[채택-force]** | force_include 1번째. Barsky-Summers level 母船. H1·H4·M3 검증. opportunity cost 채널. |
| A2 | dollar_index (broad) | FRED DTWEXBGS | **[채택-force]** | force_include 2번째. M3 corr -0.378 (DXY -0.348 보다 강). de-dollar 서사 정합. |
| A3 | gpr_daily | Caldara-Iacoviello GPR (matteoiacoviello.com xls, 1985-) | **[채택-force]** | force_include 4번째. H7 OLS t=2.19 유의 + q90/OLS=5.91× tail amplified. safe-haven 평균+꼬리 채널. |
| A4 | cb_demand_proxy | WGC quarterly GDT (annual 박제 + Kalman 분기 보간 production) | **[채택-force]** | force_include 3번째. H3 corr +0.784 (annual n=15). H2 level intercept 운반. |
| A5 | breakeven_10y | FRED T10YIE | **[채택-basis-pin]** | ★force_include 외 항등식 basis 외부 가드 (옵션 a, main 판정). H6 partial=-0.054 < 0.20 (common_cause 매개). VIF<5 게이트. |

## §B Numeraire ablation (Q4 합의)

| # | id | 출처 | 분류 | 사유 |
|---|---|---|---|---|
| B1 | gold_USD | Yahoo v8 GLD ETF | **[채택-indicator]** | 기본 numeraire. H1~H7 검증 사용. |
| B2 | gold_SDR | FRED FX 4 + IMF 2022 weights 합성 (43.38% USD + 29.31% EUR + 12.28% CNY + 7.59% JPY + 7.44% GBP) | **[채택-indicator]** | numeraire trap 보정 1차. H4 dollar β 감쇠 +66.8% 실증. |
| B3 | gold_USD-excluded basket (EUR/JPY/CNY/GBP) | 합성 | **[이연-collector]** | robustness ablation, production wiring 시. |
| B4 | gold_LBMA_PM (직접 fix) | FRED GOLDPMGBD228NLBM (직접 fetch 실패, HTML 반환) | **[이연-collector]** | GLD ≈ LBMA/10 비례 대체. 수준 회귀 절대값 해석 시 환산 필요. |
| B5 | gold_CFTC_OI (front-month futures) | CFTC | **[이연-collector]** | 변화율은 GLD 대체, OI 자체는 별도. |

## §C 항등식 친척 (Fisher real=nominal-BE)

| # | id | 출처·시리즈 | 분류 | 사유 |
|---|---|---|---|---|
| C1 | nominal_10y | FRED DGS10 | **[미채택-tautology]** | Fisher 항등식 (real+BE) → glasso/partial-corr 동시 포함 시 VIF 1만배 발산 (H6 실증 1.04 → 12996). basis 게이트 검증용으로만 사용. |
| C2 | breakeven_5y | FRED T5YIE (fred_adapter 보유) | **[미채택-skip-explicit]** | direction.md basis = 10Y 단일. 5Y 는 curve term-structure 별도 분석 시. |
| C3 | real_rate_5y | FRED DFII5 | **[이연-collector]** | robustness. DFII10 1차. |

## §D Safe-haven 채널 (H5 conditioning)

| # | id | 출처·시리즈 | 분류 | 사유 |
|---|---|---|---|---|
| D1 | credit_HY_OAS | FRED BAMLH0A0HYM2 | **[이연-collector]** | ★fredgraph.csv 가 3년치만 반환 (cosd 무시). 위기 (2008/2020) 미포함 → H5 검증 부분적. ALFRED API key 발급 시 full history 확보 가능. |
| D2 | credit_BAA10Y | FRED BAA10Y (4279 obs 보유) | **[채택-indicator]** | H5 검증 1차 (Moody's BAA−10Y, long history). HY OAS 부분 대체. |
| D3 | credit_IG_OAS | FRED BAMLC0A0CM | **[이연-collector]** | robustness. HY OAS 와 동반 fetch. |
| D4 | vix | FRED VIXCLS (4280 obs 보유) | **[채택-indicator]** | risk regime proxy. H5 보조. |
| D5 | move_index (채권 vol) | ICE MOVE | **[이연-collector]** | R2 Claude 추가 (별도 regime 변수). 분리 sourcing 필요. |

## §E Positioning 지표 (main 추가 지시 1)

| # | id | 출처·시리즈 | 분류 | 사유 |
|---|---|---|---|---|
| E1 | cftc_mm_net_long_gold | CFTC COT Disaggregated Futures, gold 088691 managed-money net long (cftc.gov 공개 weekly) | **[채택-indicator]** | ★main 추가 지시 — 투기 포지션 과열/디레버 신호. lens·블록5 confidence_hook 신규. raw/cftc_{2022,2023,2024}.zip fetch 완료, 다음 turn 추출. R1 Claude 변수정의표 부수 위치 → 본 ledger 로 정정. |
| E2 | cftc_etf_holdings (GLD/IAU) | WGC ETF flows + 거래소 공개 | **[이연-collector]** | gold ETF 보유 변화 = retail/institutional 흐름. WGC GDT 분기 ETF 부분과 통합. |
| E3 | shanghai_gold_premium | SGE 공개 | **[이연-collector]** | 중국 onshore-offshore 프리미엄 = physical demand 신호. 별도 fetch 필요. |

## §F Decoupling 모니터 (main 추가 지시 2)

| # | id | 출처·정의 | 분류 | 사유 |
|---|---|---|---|---|
| F1 | real_rate_decoupling_monitor | computed = H2 unexplained ln_gold (pre-2022 OLS residual) + H7 rolling 504d EG ADF stat | **[채택-monitor]** | ★main 추가 지시 — 금-실질금리 음의상관 깨지는 국면 = CB demand/GPR 우위. 별도 fetch 불요 (H2+H7 computed). 정의: (a) unexplained ln_gold trend %/year (b) rolling EG ADF stat (c) 252d rolling Pearson real-gold. 셋 conjunction. |
| F2 | level_R2_breakdown_monitor | computed = H2 rolling 252d level R² | **[채택-monitor]** | RBC 시계열 84%→3%→7% 재현 (실측 70%→52%→44%). H2 산출 직접 reuse. |

## §G 추가 거시 driver (M3 + 자문)

| # | id | 출처·시리즈 | 분류 | 사유 |
|---|---|---|---|---|
| G1 | wti_oil | FRED DCOILWTICO (1214 obs 보유) | **[채택-indicator]** | M3 E1 epoch +0.41 loading (러-우 충격). M3 force 아님, indicator (regime 의존 effect). family=macro_driver. |
| G2 | gold_mom_12_1 | computed (GLD price) | **[채택-indicator]** | WGC GRAM momentum 4범주 1. family=momentum. own_history_z. |
| G3 | gold_realized_vol | computed (GLD 20d rolling) | **[채택-indicator]** | family=risk. own_history_z. |
| G4 | eco_expansion_proxy (manufacturing PMI 또는 글로벌 cyclical) | ISM·OECD CLI | **[이연-collector]** | WGC GRAM 4범주 economic expansion. 일별 시리즈 부재 → 월별·분기별. force_include 외. |
| G5 | leasing_rate (GOFO) | LBMA 공개 (deprecated post-2015) | **[미채택-skip-explicit]** | O'Connor 2015 survey 언급. 시장 deprecated 후 의미 약화. |

## §H 미실현 / 검증 보류

| # | id | 분류 | 사유 |
|---|---|---|---|
| H1 | Bayesian SVAR sign restriction (monetary vs haven shock 분리) | **[미채택-OOS]** | R2 합의 statistical 기법. 본 study local 미실시. production wiring 시. |
| H2 | TVP-VAR continuous time-varying β·γ | **[미채택-OOS]** | R2 합의 robustness. H1 rolling β + H7 rolling EG ADF 가 부분 대체. |
| H3 | VECM 정식 (Johansen rank ≥ 1 전제) | **[미채택-OOS]** | ★Johansen rank=0 (H2 실측) → 정식 VECM 적용 불가. EG rolling ADF stat 로 γ proxy 사용 (H7). |
| H4 | Bayesian State-Space α(t) random walk latent (online monitor) | **[미채택-OOS]** | R2 Q1 합의 online monitor. 본 study 미구현, production wiring 시. |
| H5 | Kalman smoother cb_demand 보간 (분기→일별) | **[이연-collector]** | R2 Q5 합의. annual 분석으로 baseline (H3) — 분기 데이터 + Kalman 은 production. |
| H6 | Quantile Regression q90·q10 (gold tail) | **[채택-monitor]** | H7 부분 구현 (GPR q90 vs OLS). 다른 driver q-Reg 도 다음 차수 가능. |
| H7 | 차원 스케일링 전처리 파이프라인 (glasso → partial/marginal → 표준화 → e-process) | **[이연-collector]** | R2 Q7 합의. yaml 블록7 code_change_plan 박제. 본 study 직접 검증 외. |
| H8 | Gregory-Hansen regime-shift cointegration | **[채택-indicator]** | H2 sup-ADF -2.50 (cv5% -4.92 미달, 검정력 부족) + break date 2023-12-05 (window 정합). 보강 검정 다음 차수. |
| H9 | sys_priors gold loading 재보정 | **[이연-collector]** | ★main G6 게이트 사안. H4 압도 기각 + numeraire trap +66.8% 감쇠 → production wiring 시 main G6 처리. yaml lens estimation_note 박제. |

## §I Lens narrative (학술 anchor 분리)

| # | source | 분류 | 사유 |
|---|---|---|---|
| I1 | Barsky-Summers 1988 (level relation) | **[채택-anchor]** | H2 학술 母船. 모든 lens block 1차 anchor. |
| I2 | Erb-Harvey 2013 (golden constant) | **[채택-anchor]** | 보조 anchor. horizon 의존성. |
| I3 | WGC GRAM 4-driver | **[채택-anchor]** | 결정론 baseline. force_include 4 의 GRAM 1:1 span 정합. |
| I4 | Reboredo 2013 + Pukthuanthong-Roll 2011 (numeraire trap) | **[채택-anchor]** | Q4 / B2-B4 직접 출처. |
| I5 | Baur-Lucey 2010 / Baur-McDermott 2010 (hedge vs haven 분리) | **[채택-anchor]** | H5 학술 출처. |
| I6 | Arslanalp 2023 (stealth dollar erosion) | **[채택-anchor]** | H3 / cb_demand 학술 토대. |
| I7 | Caldara-Iacoviello 2022 (GPR Index) | **[채택-anchor]** | A3 / H7 학술 출처. |
| I8 | O'Connor 2015 survey | **[채택-anchor]** | 후속 인용망 허브. |
| I9 | Bridgewater/Dalio Paradigm Shifts / Changing World Order | **[미채택-skip-explicit]** | ★Claude R2 보수 판정 수용. peer-reviewed 아닌 narrative 색채만, confirmatory/causal 인용 금지. H2 의 동기 narrative 로만. |

---

## §J 종합 (다음 세션 한눈에)

**force_include 4 (옵션 a 채택)** = A1 real_rate_10y + A2 dollar_broad + A3 gpr_daily + A4 cb_demand_proxy
**Basis pin (항등식 외부 가드)** = A5 breakeven_10y (VIF<5)
**indicator (force 외 채택)** = B1 gold_USD + B2 gold_SDR + D2 credit_BAA10Y + D4 vix + G1 wti_oil + G2 gold_mom_12_1 + G3 gold_realized_vol + H8 GH break date + E1 cftc_mm_net_long
**Computed monitor (다른 검증 산출 reuse)** = F1 real_rate_decoupling_monitor + F2 level_R2_breakdown_monitor
**Collector 이연** = B3·B4·B5·D1·D3·D5·E2·E3·G4·H5·H7·H9 (12건)
**미채택 사유 명시** = C1 (Fisher 항등식) + C2 (basis 단일) + G5 (deprecated) + H1·H2·H3·H4 (OOS / 검정력) + I9 (narrative 색채만)

★ yaml v2 작성 시 본 ledger §A-G 의 [채택] 항목을 블록2 indicators 에 enumerate, [이연-collector] 를 블록6 collector_plan 에 매핑, [미채택-tautology/skip-explicit] 는 lens estimation_note 박제, [채택-monitor] 는 블록5 confidence_hooks 의 affects_indicator 로.
