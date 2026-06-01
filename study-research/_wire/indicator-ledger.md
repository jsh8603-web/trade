# 지표 통합 Ledger — 자산별 후보/채택/기각 (재탐구 조회용)

> 자동생성(`core/study/indicator_ledger.build_indicator_ledger`). 산발된 8자산 study_session.yaml 통합.
> status: **adopted**=weight_rules base_weight>0 / **candidate**=indicators만(미채택) / **rejected**=audit(P2) verdict 후 주입.
> ★reject 사유 산발분(validation-*.md / direction.md)은 P2 audit verdict 주입 시 채워짐. 현재=채택/후보 가시화 1차.

**전체 합계: adopted 71 / candidate 54 / rejected 0** (자산 8개)


## commodity — adopted 10 / candidate 12 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| real_rate_dfii10 | macro_driver | **adopted** | 0.1 | Theory of Storage: r↑ → F-S spread ↑ → bac | - |
| dxy_index | macro_driver | **adopted** | 0.05 | USD 표시 commodity: DXY↑ → 가격↓ → spot 약세 → b | - |
| indpro_yoy | macro_driver | **adopted** | 0.15 | 관찰된 통계 (raw, latest vintage): INDPRO YoY ↔ | O |
| china_credit_impulse_z | macro_sensitivity | **candidate** | 0.0 | Biggs 2009 credit impulse → industrial met | - |
| cfnai | macro_driver | **candidate** | 0.0 | Hamilton 1996 NOI. ★실측: 30% threshold 단 1건 | O |
| credit_spread_hy_oas | macro_driver | **candidate** | 0.0 | risk-off regime (C) 매개. partial-corr 으로 분해 | O |
| vix_level | risk | **candidate** | 0.0 | ★Tang-Xiong 2012 검증된 명제: VIX 급등 → delevera | - |
| roll_yield | valuation | **adopted** | 0.2 | Theory of Storage: r↑ → F-S spread ↑ → bac | - |
| bgr_basis_momentum_12m | valuation | **adopted** | 0.15 | Bakshi-Gao-Rossi 2019: Basis_t · sign(RelB | - |
| convenience_yield_z | valuation | **adopted** | 0.1 | Working 1949: 재고 타이트 (days_of_supply ↓) →  | - |
| days_of_supply | macro_sensitivity | **adopted** | 0.1 | Working 1949: 재고 타이트 (days_of_supply ↓) →  | - |
| stock_to_use_ratio | macro_sensitivity | **candidate** | 0.0 | Roberts-Schlenker 2013: ENSO → corn/soy yi | - |
| lme_metal_stocks_z | macro_sensitivity | **candidate** | 0.0 |  | - |
| momentum_12_1 | momentum | **adopted** | 0.05 | 관찰된 통계 (raw, latest vintage): INDPRO YoY ↔ | - |
| realized_vol_60d | risk | **adopted** | 0.05 | risk-off regime (C) 매개. partial-corr 으로 분해 | - |
| wti_noi_1yr | macro_sensitivity | **candidate** | 0.0 | Hamilton 1996 NOI. ★실측: 30% threshold 단 1건 | - |
| mm_net_long_oi_z | macro_sensitivity | **candidate** | 0.0 | Hong-Yogo 2012: OI 변화 macro 예측. MM net lon | - |
| cross_sector_mean_corr_60d | macro_sensitivity | **adopted** | 0.05 | ★Tang-Xiong 2012 검증된 명제: VIX 급등 → delevera | - |
| cit_long_position_z | macro_sensitivity | **candidate** | 0.0 | Tang-Xiong 2012: CIT index 자금 유입 → common  | - |
| noaa_oni_3m_ma | macro_sensitivity | **candidate** | 0.0 | Roberts-Schlenker 2013: ENSO → corn/soy yi | - |
| cushing_utilization_pct | risk | **candidate** | 0.0 | Deaton-Laroque competitive storage: 저장 한계  | - |
| ted_or_fra_ois_spread | risk | **candidate** | 0.0 |  | - |

## crypto — adopted 6 / candidate 2 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| mvrv_btc | macro_sensitivity | **adopted** | 0.55 | 실측: marginal Spearman(MVRV,fwd_30d)=-0.071 | O |
| fgi | risk | **adopted** | 0.1 | FGI 단독 → BTC 효과는 MVRV 와 강 공통원인 매개 (둘 다 sen | O |
| funding_rate | risk | **adopted** | 0.15 | ★[자문 REJECT] cascade 가설 부호 정반대 실측. extreme | O |
| btc_price | momentum | **candidate** | 0.0 | 실측: marginal Spearman(MVRV,fwd_30d)=-0.071 | O |
| stablecoin_total_supply | macro_driver | **adopted** | 0.2 | Granger supply->BTC p<0.005 (lag 7d) 유의 =  | - |
| btc_dominance | macro_driver | **candidate** | 0.0 |  | - |
| etf_net_flow_usd | macro_driver | **adopted** | 0.05 | post-2024 only n=613. 5d cum flow >0 후 fwd | - |
| halving_phase | macro_driver | **adopted** | 0.1 | regime label only. MVRV→fwd_30d IC 가 phase | - |

## eq_intl — adopted 8 / candidate 7 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| fwd_ep_country | valuation | **adopted** | 0.15 | value(싼 국가)와 momentum(오른 국가)은 횡단면에서 음의 동시상 | - |
| roe_country | quality | **candidate** | 0.0 |  | - |
| eps_revision_breadth_country | revision | **adopted** | 0.13 |  | - |
| mom_12_1_country | momentum | **adopted** | 0.12 | 강달러 추세가 EM모멘텀을 꺾음(모멘텀=환추세 동반). 위험/금리 고정 후에 | - |
| dollar_beta_country | macro_sensitivity | **adopted** | 0.22 | US real yield↑가 달러강세와 EM자본유출을 동시 유발 — real | - |
| rate_beta_country | macro_sensitivity | **candidate** | 0.0 | US real yield↑가 달러강세와 EM자본유출을 동시 유발 — real | O |
| oil_beta_country | macro_sensitivity | **adopted** | 0.08 | China 신용자극↔원자재수요↔유가·원자재수출국 동반(동시 정성 맥락). ★ | - |
| credit_beta_country | macro_sensitivity | **adopted** | 0.1 | risk-off(HY OAS 확대) 시 EM 변동성 동반 급등 — 글로벌 위 | O |
| realized_vol_country | risk | **adopted** | 0.06 | risk-off(HY OAS 확대) 시 EM 변동성 동반 급등 — 글로벌 위 | - |
| fx_carry_momentum | macro_sensitivity | **adopted** | 0.04 | 환carry/모멘텀과 달러베타는 같은 환 채널(동시 노출) — 금리차 고정  | - |
| real_exchange_rate_valuation | valuation | **candidate** | 0.0 |  | - |
| china_credit_impulse | macro_driver | **candidate** | 0.0 | China 신용자극↔원자재수요↔유가·원자재수출국 동반(동시 정성 맥락). ★ | - |
| foreign_equity_flow | macro_driver | **candidate** | 0.0 |  | - |
| terms_of_trade | macro_driver | **candidate** | 0.0 | 원자재수출국은 유가↑가 교역조건·지수 동반 개선 — archetype(수출국 | - |
| sovereign_cds_spread | risk | **candidate** | 0.0 |  | - |

## eq_us_cyclical — adopted 11 / candidate 6 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| fwd_ep_normalized | valuation | **adopted** | 0.3 | ★실검증 H5 sign 분리 미입증 (모든 섹터 β>0). 종목 단위 EDG | - |
| roe_margin_trend | quality | **adopted** | 0.1 |  | - |
| earnings_revision_breadth | revision | **candidate** | 0.0 |  | - |
| fwd_eps_momentum | revision | **candidate** | 0.0 | ★실검증 cyclical-defensive excess 선행성 미입증(IC< | - |
| price_mom_12_1 | momentum | **adopted** | 0.06 |  | O |
| rate_beta | macro_sensitivity | **adopted** | 0.04 | ★실검증 H5 sign 분리 미입증 (모든 섹터 β>0). 종목 단위 EDG | O |
| dollar_beta | macro_sensitivity | **candidate** | 0.0 |  | O |
| oil_beta | macro_sensitivity | **candidate** | 0.0 |  | O |
| credit_beta | macro_sensitivity | **adopted** | 0.08 | ★실검증 IC d_VIX vs d_IG_spread: 둘 다 risk sho | O |
| realized_vol | risk | **adopted** | 0.08 | VIX 상승 = 실현변동성 동시 상승, risk-off 채널 | O |
| vix_beta | macro_sensitivity | **adopted** | 0.18 | ★실검증 IC d_VIX vs d_IG_spread: 둘 다 risk sho | O |
| ebp_residual | macro_driver | **candidate** | 0.0 | ★실검증 빈자 EBP lead 부재(k≥1 IC<0.05). GZ 정공법 적 | - |
| yield_curve_10y_2y | macro_driver | **candidate** | 0.0 |  | O |
| asset_growth_yoy | quality | **adopted** | 0.08 | Cooper-Gulen-Schill 2008 JF Asset Growth A | - |
| capex_to_rev | quality | **adopted** | 0.04 | Chancellor Capital Cycle: capex 과열 → 6-12M | - |
| operating_leverage_nm | quality | **adopted** | 0.04 | ★합성 검증(proxy=gross_margin) IC +0.084 약함, b | - |
| ism_pmi_proxy | macro_driver | **adopted** | 0.04 | ★실검증 cyclical-defensive excess 선행성 미입증(IC< | O |

## eq_us_defensive — adopted 9 / candidate 9 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| fwd_ep | valuation | **adopted** | 0.1 |  | O |
| roe_margin_trend | quality | **adopted** | 0.1 |  | O |
| earnings_revision_breadth | revision | **candidate** | 0.0 |  | - |
| fwd_eps_momentum | revision | **candidate** | 0.0 |  | O |
| price_mom_12_1 | momentum | **adopted** | 0.04 |  | O |
| rate_beta | macro_sensitivity | **adopted** | 0.08 |  | O |
| dollar_beta | macro_sensitivity | **adopted** | 0.06 |  | - |
| oil_beta | macro_sensitivity | **candidate** | 0.0 |  | O |
| credit_beta | macro_sensitivity | **adopted** | 0.07 |  | O |
| realized_vol | risk | **adopted** | 0.06 |  | O |
| vix_term_structure | risk | **candidate** | 0.0 |  | - |
| dividend_yield | valuation | **candidate** | 0.0 |  | - |
| dividend_safety | quality | **candidate** | 0.0 |  | - |
| fcf_yield | valuation | **candidate** | 0.0 |  | - |
| earnings_stability | quality | **candidate** | 0.0 |  | - |
| nim_trend | quality | **candidate** | 0.0 |  | - |
| yield_curve_slope_beta | macro_sensitivity | **adopted** | 0.08 |  | O |
| pb_ratio | valuation | **adopted** | 0.06 |  | O |

## gold — adopted 0 / candidate 11 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| real_rate_10y | macro_driver | **candidate** | 0.0 | Barsky-Summers 1988 + Erb-Harvey 2013 = 무수 | - |
| dollar_index_broad_TWI | macro_driver | **candidate** | 0.0 | Pukthuanthong-Roll 2011 = numeraire endoge | - |
| cb_demand_proxy | macro_driver | **candidate** | 0.0 | Arslanalp 2023 + WGC GDT = EM CB de-dollar | - |
| gpr_daily | macro_driver | **candidate** | 0.0 | Caldara-Iacoviello 2022 AER = geopolitical | - |
| breakeven_10y | macro_driver | **candidate** | 0.0 | Erb-Harvey 2013 = 명목금리 = real + breakeven  | - |
| cftc_mm_net_long_gold | positioning | **candidate** | 0.0 | speculative crowding indicator — 과열 시 정점 r | - |
| real_rate_decoupling_monitor | macro_driver | **candidate** | 0.0 | H2 STRONGLY SUPPORTED + H7 SUPPORTED + H8  | - |
| credit_spread_hy_oas | macro_driver | **candidate** | 0.0 | Baur-Lucey 2010 J Fin Res = 평시 hedge / 위기  | O |
| vix_proxy | risk | **candidate** | 0.0 |  | O |
| gold_realized_vol | risk | **candidate** | 0.0 |  | - |
| gold_mom_12_1 | momentum | **candidate** | 0.0 | Barsky-Summers 1988 + Erb-Harvey 2013 = 무수 | - |

## macro — adopted 6 / candidate 6 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| real_rate_10y | macro_driver | **adopted** | 0.22 | 달러=글로벌 펀딩금리, real rate↑→달러강세. ★2-3 부트스트랩 C | - |
| yield_10y_2y | macro_driver | **adopted** | 0.18 | 리스크오프 시 HY 확대 + 커브 베어플래트닝 동반(침체확률·활동 통제 후  | O |
| credit_spread_hy_oas | macro_driver | **adopted** | 0.25 | 리스크오프 시 HY 확대 + 커브 베어플래트닝 동반(침체확률·활동 통제 후  | O |
| credit_spread_baa | macro_driver | **candidate** | 0.0 |  | O |
| breakeven_5y | macro_driver | **adopted** | 0.15 | 명목금리 = real + breakeven 회계항등. 둘은 성장/Fed 기대 | O |
| dollar_dxy | macro_driver | **adopted** | 0.12 | 달러=글로벌 펀딩금리, real rate↑→달러강세. ★2-3 부트스트랩 C | - |
| usdkrw | macro_driver | **candidate** | 0.0 |  | - |
| nfci | risk | **adopted** | 0.08 | HY OAS 는 NFCI 금융상황 구성요소 — 동일 risk-premium  | O |
| fred_recession_prob | macro_driver | **candidate** | 0.0 | 침체확률·HY 둘 다 성장둔화 공통원인. 직접인과 아님(분해) | O |
| cfnai | macro_driver | **candidate** | 0.0 |  | O |
| jgb_10y | macro_driver | **candidate** | 0.0 | 미-일 금리차(real_rate - jgb) 통제 시 JGB↑→엔강세→달러약 | - |
| m2_yoy | macro_driver | **candidate** | 0.0 | 통화량→인플레는 lag 길고 국면 의존(Overheat 만 성립). 약 pr | - |

## reit — adopted 21 / candidate 1 / rejected 0

| id | family | status | weight | reason(theory) | in_system |
|---|---|---|---|---|---|
| fwd_ep_ratio | valuation | **adopted** | 0.1 | REIT 에서 EP ≈ AFFO yield × (1 − D/A adj). 회 | - |
| roe | quality | **adopted** | 0.03 |  | O |
| margin_trend | quality | **adopted** | 0.03 |  | O |
| earnings_revision_breadth | revision | **adopted** | 0.04 | 둘 다 information arrival 의 reflection. 공통원인 | - |
| fwd_eps_momentum | revision | **adopted** | 0.03 |  | - |
| mom_12_1 | momentum | **adopted** | 0.05 | 둘 다 information arrival 의 reflection. 공통원인 | O |
| beta_rate | macro_sensitivity | **adopted** | 0.1 | rate-shock 이 REIT vol 자극 (long-duration di | O |
| beta_dollar | macro_sensitivity | **adopted** | 0.02 |  | O |
| beta_oil | macro_sensitivity | **adopted** | 0.02 |  | O |
| beta_credit | macro_sensitivity | **adopted** | 0.07 | rate β 와 credit β 의 공통원인 = risk-off regime | O |
| realized_vol | risk | **adopted** | 0.04 | rate-shock 이 REIT vol 자극 (long-duration di | O |
| affo_yield | valuation | **adopted** | 0.18 | 정의식: AFFO yield ≈ NOI yield ≈ implied cap  | - |
| implied_cap_rate_spread | macro_sensitivity | **adopted** | 0.08 | 정의식: AFFO yield ≈ NOI yield ≈ implied cap  | - |
| price_to_nav | valuation | **adopted** | 0.05 |  | - |
| same_store_noi_growth | revision | **adopted** | 0.08 | NOI = rent × occupancy. 회계 직접 (occupancy 가 | - |
| occupancy_rate | quality | **adopted** | 0.04 | NOI = rent × occupancy. 회계 직접 (occupancy 가 | - |
| walt_years | risk | **adopted** | 0.04 | ★ H1 실측 (mean Rank-IC +0.240, z+3.18, n=23 | - |
| debt_maturity_wam_years | risk | **adopted** | 0.02 | ★ H3 실측 (mean Rank-IC -0.117, z-2.09, n=23 | - |
| leverage_debt_ebitda | quality | **adopted** | 0.1 | 고레버리지 → credit 충격 전달 큼. archetype baseline | O |
| fixed_charge_coverage | quality | **adopted** | 0.05 |  | - |
| ffo_payout_ratio | risk | **adopted** | 0.03 | payout 100% 초과 = 배당 cut 위험 = vol spike. le | - |
| sector_archetype | macro_driver | **candidate** | 0.0 |  | - |
