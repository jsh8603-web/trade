---
tags: [type/research-log, domain/equity, sector/us_mega_tech]
date: 2026-06-03
purpose: 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용. ★재작업(basket화) 과정 박제.
---

# us_mega_tech 리서치 로그

## 데이터 소스 탐구
| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 | yfinance 11종 | OK (2867일, 2015-01~2026-05) | ✅ | survivorship-biased(현 basket, 상폐 거의 없으나 PIT 멤버십=편입시점 look-back) |
| valuation | EDGAR XBRL 4 concept(equity/ni/shares/capex) | OK (6630 rows) | ✅ pbr/per/capex | ★us_cyclical=12 concept인데 mega_tech=4만. gross_prof/sales 미수집(concept 확장 이연) |
| ★real_rate | FRED DFII10 (us_defensive/raw/fred 재사용) | OK (6107 rows ~2026-05-28) | ✅ basket-level β | ★별 fetch 불요 — defensive FRED CSV 재사용(measure_cross.py 패턴) |
| VIX/dollar/rate | FRED VIXCLS/DTWEXBGS/DGS10 | OK | ✅ | 동일 재사용 |
| ERB/fwd EPS | IBES/FactSet/Refinitiv | ★유료 = free API 부재 | ❌ 이연 | ★compounder primary 인데 측정 불가 = 최대 gap. EDGAR=actuals only |

## 막힘·해결 로그 (시계열)
- [2026-06-03 18:25] 막힘: S1 리서치 Gemini 2-Phase(search-engine skill) free key 429(rate-limit) → promo fallback 무한 재시도 2.5h hang, 결과 파일 0 byte → 진단: Gemini API quota 소진 → 해결: ★team-lead 지시 = WebSearch 네이티브 직접 대체(`touch ~/.claude/.allow-native-web` 플래그 = 5분 TTL allow). 7주제 전부 커버 + citation 환각검증 통과 + 3계층 저장(raw archive + memory + index) → 교훈: ★Gemini rate-limit 시 WebSearch 폴백 즉시 전환(2.5h 허비 말 것). search-engine skill §폴백 = Phase1 2회 실패 시 native 허용과 정합.
- [2026-06-03] 막힘: python 명령 없음(`command not found`) → 진단: PATH 미등록 → 해결: `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` 풀패스(pandas/numpy/scipy/statsmodels 가용) → 교훈: PY 변수 풀패스 사용.
- [2026-06-03] 콘솔 한글 출력 mojibake(★ 등) but ★validation-metrics-v3.json 파일은 UTF-8 정상(write_text encoding="utf-8"). print stdout 인코딩만 깨짐 = 무해.

## 측정 방법 결정 로그
- **★sector-neutral z 비적용 (us_cyclical pilot 발견과 분기)**: us_cyclical = multi-sector(5 sector) → sector-neutral z 로 BY 0→8 회복. ★us_mega_tech = 단일 archetype(compounder) basket, 11종 모두 mega-tech 그룹 = sub-sector demean 할 peer 구조 없음 → universe-demean = sector-neutral 동치. ⛔ 비적용 = measure.py cs_z universe-demean 유지. 15axis G-A.5 사유 명시. (가져온 것 = family 3분리/M_eff/eff_N/EDGAR PIT/small-n hedge만.)
- **★basket화 (자문 R2 수정4)**: N=11 cross-sectional rank-IC = Grinold IR=IC√breadth 협소(breadth 11×ρ̄ 0.429 보정 시 cross_eff_n 2.08) = 통계력 약. → ★family_1b basket-level time-series factor exposure timing(real_rate/vix/dollar/rate β + forward timing) 신규 추가 = primary. cross-sectional 은 small-basket hedge(breadth-IR ρ̄ 보정 + magnitude haircut 50~70%), 단독 verdict 금지.
- **★real_rate = multivariate 재측정 (team-lead 코멘트1)**: 기존 measure_cross.py 단일회귀 β −0.030 비유의 → ★multivariate(real_rate+vix+dollar+rate) HAC = β −0.210 t−5.14. + 단독 −0.154 t−4.90. ★level vs Δ: level β −0.003 무 vs Δ β −0.154 = duration 메커니즘(할인율 변화)이 신호. sub-basket mag7 −0.148/ai_semi −0.175 둘 다 음 + leave-year all_negative. = Gormsen-Lazarus duration 이론 정합(defensive −0.066 대비 3배 강).
- **per_z expected null 측정 (코멘트2)**: 측정 생략 안 함. 3M −0.001 p0.987 / 12M +0.013 p0.872 = ≈0 = ★expensive_trap "가설 확인"(REJECT 아님). compounder archetype 지지.
- **capex 양방향 판정 (코멘트3)**: prior 박지 않고 pre/post-AI(2023~) split. pre-AI IC +0.009(n96 무) vs post-AI −0.404(n29 강 음) = over-investment penalty(Cooper-Gulen-Schill) 우세, productive growth 아님. ★n=29 small hedge(post-AI 단일 regime).
- **M_eff (Li-Ji)**: raw m=30 → M_eff=19.0(near-dup vol/mom/per/pbr horizon 상관 포착). nondegenerate(24M strip) M_eff=16.0.
- **eff_N 이중보정**: ρ̄=0.429 → cross_eff_n = 11/(1+10×0.429)=2.08(급감) + ts_eff_n=T/h. breadth-IR 에 cross_eff_n 사용(과대 방지).
- **G-B 판정**: basket-level real_rate t−4.90~−5.14 = 명백 유의 → ★G-B(유의 신호 0) 미발동. 정상 진행(약함 단정 아님).
- **★G-A.3 (directional_spillover [] 금지, 게이트 갱신 2026-06-03 반영)**: dispatch-gates A-3 = sleeve DY/supply-chain 선행신호 후보 보고 의무([] FAIL). → `supply_chain_lead_lag` 추가 = hyperscaler(MSFT/AMZN/GOOGL/META)→semi(NVDA/AVGO/AMD/ASML) lead-lag. corr_0m +0.69 동시 강 / lead 1-3m 비유의 = ★동시 동조만, 선행 없음. directional_spillover 후보 박제(조립=supervisor).
- **★G-A.5 (regime interaction = family_1 미생존 살리기, 게이트 갱신 반영)**: dispatch-gates A-5 = family_1 BY 미생존이어도 regime split 부호 갈리면 interaction term 의무. per_z(hi −0.088 vs lo +0.067) / capex(hi −0.197 vs lo −0.033) VIX regime 부호 갈림 → `regime_interaction`(IC~VIX_chg HAC) 추가. ★capex β +0.0083 t+2.34 유의(살아있음) / per_z·vol_60 비유의. = rejected 박제 회피.

### ★B″ 3R STEP 0/5 재분류 (2026-06-04, 자문 3R 후 설계 B″)
- **★STEP 0(⑧) exposure overlay 재분류**: 자문 3R = ★us_mega_tech 유효 cross-section n≈7(valuation 가용 7~8) = cross-sectional factor 추정 통계적 void → 강제 시 spurious factor 제조. → ★verdict 생성 폐기 = sleeve_type=exposure_timing_overlay. measure.py main() family_1 결과 dict에 `role:diagnostic_no_verdict` 태그 + results meta sleeve_type 추가 + summary.yaml verdict_label 제거 → overlay_report 3종(exposure/concentration/regime-beta). cross-sectional vol_60/per/capex = 참고 지표(weight 0). ★효과 = ③ PASS-search 압력 제거(capex×VIX t+2.34 상대 inflate 자동 해소).
- **★F-score/net-issuance 측정 폐기(STEP 0)**: F-score=high-BM 부실주 설계라 mega-cap growth mismatch / net-issuance=n=11 동질 buyback→dispersion 고갈→IC degenerate. ★측정하지 않음(자문 raw §33).
- **★STEP 5(⑨) spillover CF lagged 재측정**: 기존 `supply_chain_lead_lag` corr_0m +0.69 = ★Cohen-Frazzini(2008 RFS) **오용** = contemporaneous = 같은 risk cluster 동조일 뿐 tradeable alpha 아님. CF 정의 = 고객 return_t → 공급사 return_{t+1}(lagged firm-pair). ★AI capex 체인 방향 = hyperscaler(MSFT/AMZN/GOOGL/META)=고객(capex 지출) → semi(NVDA/AVGO/AMD/ASML)=공급사. → CF 정합 = 고객 hyper_t → 공급사 semi_{t+1}. **재측정 결과**: lead 1-3m corr −0.07~−0.09 전부 비유의 + ★UNDERPOWERED(achieved power 0.13~0.19, MDE|ρ|=0.238). = lagged spillover null 단 ★power 부족(증거부재≠부재증거, Fisher-z MDE 산식). 역방향(semi_t→hyper_{t+1}) 무. `_achieved_power_mde`/`_power_at_rho` 함수 추가. semi↔hyperscaler 체인 한정 명문화.
- **★측정 방향 판정(CF)**: dispatch plan §85는 "NVDA/AVGO→MSFT"(역방향) 적었으나, ★Cohen-Frazzini 정의(고객 return_t→공급사 return_{t+1})를 엄격 적용하면 hyperscaler(고객)_t→semi(공급사)_{t+1}. 양방향 다 측정해 데이터 판정(둘 다 비유의·underpowered).

### ★B″ STEP 2(⑦) capex×VIX fixed-b size-valid 재검정 (2026-06-04, 사용자 갭 지적)
- **갭**: capex×VIX family_2b interaction(t+2.34)이 구 asymptotic HAC(maxlags=3) 그대로 = payout(split t−2.86→fixed-b 2.09 사망)과 동일 Kiefer-Vogelsang size-invalid 위험 미검정. 사용자 "특정 국면에서 산다던 지표 frame 바꾸고 살았나" 지적.
- **방법**: `us_defensive/raw-v3/_b2_stats.py`(fixed_b_cv + wild_cluster_boot + effective_n + persistence_block) import. `regime_interaction()` 에 fixed-b CV + wild-cluster 추가. HAC lag = persistence_block(AR1 기반) = 5(기존 고정 3 → 자기상관 반영). ★전체 n=125 + post-AI n=29(2023~ subset_mask) 둘 다 측정.
- **결과**: ★전체 n=125 = t_HAC +2.43 > fixed-b CV 2.19 + wild p 0.044 = SURVIVE(effN 33). ★★post-AI n=29(capex 신호 −0.404 강한 의미 구간) = t_HAC +1.94 < fixed-b CV 2.86(small-block inflation) + wild p 0.234 = ★DIE. = ★payout 동일 NW over-rejection artifact.
- **판정**: ★MIXED → post-AI 사망 = capex×VIX "timing 신호" 자격 미달(신호 강한 구간서 size-valid 미통과). 전체 SURVIVE = pre-AI 무신호 희석 산물. → summary overlay_report 3 + 측정결과 표 + ledger 비교표 = "diagnostic(size-valid 미입증)" 정정.
- **교훈**: ★small-block(n 한자릿수) regime interaction/conditional 류는 asymptotic HAC = size-invalid → fixed-b CV(KV) + wild-cluster 필수. ★전체 표본 SURVIVE 도 신호 강한 부분표본서 죽으면 = 무신호 구간 희석 = 신호 자격 미달. basket real_rate β(n=185 time-series exposure)는 small-block 아님 = 해당 약.

## 미해결 / 다음 세션 우선 작업
1. ★fwd EPS growth / ERB (compounder primary) = IBES 유료 gap. proxy(net_income TTM YoY) = forward-looking 아님, 보조만.
2. gross_profitability = EDGAR concept 확장(GrossProfit/COGS) fetch 시 추가(us_cyclical 12 concept 미러).
3. FF5+Mom+QMJ+BAB neutralize(concentration β 분리, H12) = supervisor 통합 단계.
4. AI capex→Mag7 supply-chain lead-lag = supervisor DY 단계.
5. capex post-AI IC −0.404 = n=29 small + 단일 regime → N 누적 후 재검(observe-only).
