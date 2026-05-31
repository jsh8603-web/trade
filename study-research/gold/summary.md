---
tags: [type/summary, domain/inv, study/gold]
date: 2026-05-30
note: gold 스터디 작업방 산출 요약 + 다음 세션 재개 핸드오프. study_session.yaml(7블록) 동행.
---

# gold 스터디 요약 (study_id=gold)

> 산출 계약: `study_session.yaml`(7블록 완성) + 본 요약. main(btn-Codlearn)이 G1~G6 골격으로 production wiring.

## 1. 일반론·리포트 핵심 (lens 근거)
- **금 = 현금흐름 없는 자산** → 내재가치 평가 불가. 가격 = 보유 기회비용 + 대체화폐 수요.
- **핵심 방정식**: ΔlnGold ≈ -β_r·Δ(실질금리) - β_$·Δ(달러) + β_c·(리스크오프) + β_i·Δ(기대인플레, 명목금리분 상쇄) + structural(중앙은행·탈달러).
- **단일 최강 driver = 실질금리(10Y TIPS=DFII10)**. "anti-real-rate bond". real rate 하락=금 강세.
- 우리 시스템 `core/study/system_priors.py` gold factor loading `[-0.5 rate, -0.8 dollar, 0.0 oil, -0.2 credit]` = 이 노출구조의 실증 추정치(데이터 대조 1차 증거: rate·dollar 음, oil 무관, credit 음=safe-haven).
- regime 방향(`regime_to_weights.REGIME_DIRECTION`): Reflation/Overheat/Stagflation=up, Recovery=down. 이미 시스템에 코드화됨.

## 2. ★핵심 발견 (결정·기각 사유)
1. **real rate(DFII10)·10Y breakeven(T10YIE)·dollar 가 fred_adapter.FRED_SERIES 에 없음** — 금 최강 driver 누락. 블록7 learn 1순위 변경점. credit_spread_hy_oas(BAMLH0A0HYM2)·breakeven_5y(T5YIE)·yield_10y_2y 만 보유.
2. **gold 은 종목 단위 세분화 부적합** — 단일 자산. 주식의 industry/ticker pooling(부록 B) 대신 **macro driver 단위**(real_rate/dollar/credit/breakeven/cb_demand)로 가중. granularity=sleeve 고정. `regime_to_weights` 에 이미 gold sleeve 존재(BASE 0.08, Bloc.USD).
3. **2022-2024 decoupling 가설** — real rate 상승에도 금 신고가 = 전통 모델 이탈. 중앙은행 순매수(cb_demand_proxy)가 새 driver. ★이걸 lens(estimation_note)+블록5 flag(cb_demand_regime)로 가변 처리: real_rate beta 붕괴는 **kill 아닌 SECONDARY refit**(real_rate→cb_demand 질량이전). 금 특유 — driver 교체지 가정 폐기 아님.
4. 주식 통일 하드룰(§6) **면제** — gold 은 equity.* 아님(study_loader.is_equity()=False). 코어셋 6 family 강제 안 받음.

## 3. lens↔flag↔weight 루프 (블록5 핵심)
- 3 flag: `real_rate_beta_holds`(→real_rate_10y), `cb_demand_regime`(→cb_demand_proxy), `safe_haven_holds`(→credit_spread_hy_oas).
- 경로: 거래 outcome → `flag_router.FlagRouter.emit_from_ic`/`on_trade` → e-value 누적(eprocess_backbone.e_cusum) + Beta posterior → `tilt_weights` → `study_register._build_card` 재적합 → derive_weights. affects_indicator 로 G6 tilt 연결 명시됨.

## 4. §2 2단계 실데이터 대조 — 완료(2026-05-30 압축 후 재개)

**입력**: FRED DFII10(10Y real rate)·T10YIE(10Y breakeven)·DTWEXBGS(broad dollar) 공개 CSV + Yahoo v8 chart GLD ETF. 병합 daily n=4279, 2010-01-04~2026-05-29. 산출 `raw/{fred_*.csv, try_yahoo_v8.json, analyze.py, analysis_summary.json, correlation_matrix.csv, rolling_corr.csv}`.

**실측 핵심 결과** (Δreal_rate bp · Δbreakeven bp · log return dollar/gold 기준):

| period | n | real-gold | dollar-gold | brk-gold | IC real-gold | gold vol(ann) |
|---|---:|---:|---:|---:|---:|---:|
| all 2010-2026 | 4279 | **-0.318** | **-0.331** | +0.039 | -0.311 | 0.163 |
| pre-2020 | 2606 | -0.310 | -0.310 | +0.015 | -0.285 | 0.153 |
| covid 2020-21 | 523 | -0.406 | -0.316 | +0.206 | -0.444 | 0.166 |
| **decoup 2022-26** | 1150 | **-0.304** | **-0.377** | -0.005 | -0.316 | 0.183 |

Rolling 252d real-gold Pearson: median **-0.349** / max **-0.009** (★positive 부호반전 **0회**, 16y), |corr|<0.10 약화일 135일(3.1%, 2013-05~2026-03 산발).

**★ 4가지 결정**:
1. **변화율 단위 "decoupling" 가설 기각.** real-gold β 가 16y 안정(pre2020 vs 2022-26 차이 0.006). 시장 통설의 "2024-26 사상최고 랠리"는 *level intercept shift* (real rate 상승에도 금 신고가)이지 베타 약화가 아니다. yaml estimation_note·regime_reading·블록1 마지막 report_relation 항목 재정의 완료.
2. **블록5 real_rate_beta_holds reject_signal 임계 강화** — "음전환/소멸" 추상에서 **rolling 252d Pearson 부호반전(≥0) 또는 |corr|<0.10 비율 베이스라인 3.1% × 3 초과** 정량 임계로 박음. 실측 historic 0회·median -0.349 base.
3. **블록5 cb_demand_regime confirm_signal 재정의** — "잔차-cb 상관" → **레벨 회귀 ln_gold ~ a + b·real_rate + c·ln_dollar 의 잔차 추세성분 vs cb_demand_proxy 누적순매수 양 지속**. 변화율 단위가 아니라 *수준* 잔차에서만 작동함을 명시.
4. **dollar↔gold β 는 오히려 강화** (pre2020 -0.310 → 2022-26 -0.377). 블록4 dollar_index base_weight 0.18 유지(상향 여지 있으나 force_include 보호 충분).

**★ sys_priors 검증 사안 (★main 인지)**: `core/study/system_priors.py` gold factor loading `[-0.5 rate, -0.8 dollar, 0.0 oil, -0.2 credit]` 절댓값이 실측 일별 Pearson 대비 약 **2배**(real -0.5 vs -0.32, dollar -0.8 vs -0.33). 단순 corr ≠ factor β 이므로 즉시 정정은 아니나, factor-model derivation 출처 확인 필요 — production wiring 시 dimensional consistency 게이트.

**미완(자문/오프라인)**: `/gemini-web`+`/claude-web` 으로 "2024-26 gold rally의 level shift 메커니즘(EM CB 매수 규모·지정학 프리미엄 분해)" 자문은 본 세션에서 미실행(9세션 경합 가능 + 실측만으로 lens 정합 충분 — main 판단에 위임).

**yaml 무결**: load_study_session+validate_study_session 통과 (errors=0, warnings=0, 7블록 전부, force_include=2≤4).
