---
tags: [type/handoff, domain/inv, study/eq_us_cyclical]
date: 2026-05-30
---
# Handoff — eq_us_cyclical 스터디 (btn-common-task)

## 산출물
- `study-research/eq_us_cyclical/study_session.yaml` — 7블록. 블록1~6 완성, 블록7 일부 TODO. 하단 `status:` 가 done/todo SSOT.

## 완료
- STUDY-KIT.md 정독. 작업순서 1단계(lens) 완성: 미국 경기민감주 = 멀티플 M × 사이클이익 E, operating/financial leverage 증폭, regime별 리더십 로테이션(early 반도체→mid Industrials→late Energy/Materials).
- 코드 Read 완료(블록7 learn/card/falsify 일부): weight_panel.py(build_indicator_matrix+반사성게이트), weight_card.py(WeightAssumptionCard/composed_weights/derive_weights/synthesize_l1/천장불변식), conditional_correlation.py(RegimeGlasso.fit/effective_precision/EBIC glasso), weight_cycle.py(GlassoWeightLearner/build_weight_card/run_weight_cycle/route_lifecycle), weight_falsification.py(rank_ic/score_ic_breakdown_eprocess/omega_drift/evaluate_weight_card), train_weights.py(train_weight_cards 배치).

## 재개 포인트 (다음 세션)
1. ★코드 Read: core/stock_track.py(_extract_indicator_z/_apply_r15_sizing/_resolve_weight_card), core/assume/judge.py(synthesize_l1 호출부/assert_ceiling_invariant), core/assume/registry.py(register/get), core/assume/update_controller.py(retract_now/step), core/brain/regime_to_weights.py → yaml 블록7 inject/falsify "★미Read" current 칸 정밀화.
2. ★데이터 실분석(작업순서 2단계): EDGAR(edgar_provider.py)+FRED(fred_adapter.py 86시리즈+HY OAS)+Yahoo(collect_macro) 가용성 확인 → 경기민감 유니버스(XLY/XLI/XLB/XLE/XLF 구성종목) forward return 으로 블록2 indicators IC 측정, lens 가설 regime별 분해 대조. 자문 막히면 WebSearch 폴백.
3. summary.md 작성 → main(btn-Codlearn) 방향성 보고: `bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "[eq_us_cyclical→main] ..."`

## 설계 의도/기각
- 종목단위 가중 = 독립학습 아님(obs 부족). composed_weights(pi) 계층 풀링: w_global+δ_regime+δ_arch(early/mid/late cycle archetype)+ticker shrinkage(부록B).
- 거시는 Block Matrix 금지(§8). credit/real_rate/dollar/oil 4 named driver 만, 나머지 regime 조건키.
