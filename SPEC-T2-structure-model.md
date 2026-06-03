---
tags: [type/spec, domain/inv, phase/II, track/T2]
date: 2026-05-29
split_index: ./SPLIT-INDEX-phase2.md
findings: ./FINDINGS-phase2-sector-rule-framework.md
impl_outline: ./IMPL-OUTLINE-phase2.md
raw: ./research-raw-phase2/
track: T2 구조모델·archetype·regime (의존: T1 패널 schema)
---

# SPEC-T2 — 구조모델·archetype·regime 층

> 다른 main agent 위임. 공통맥락=split_index·findings·impl_outline. T1 패널은 fixture parquet으로 mock 개발 가능. ⛔ 바닥부터 최후(jumpmodels/bnpy/ruptures 차용 — ref repo agent 결과 참조).

## 목적
"싸다"의 정의를 만든다. **★게임체인저: cheap=raw 분위 아니라 구조모델 잔차**. 밸류트랩=잔차≈0이 dual로 자동도출.

## 산출 인터페이스 (T3 소비 — 먼저 고정)
- `StructureModel.cheapness_z(firm, sector, date, as_of) -> float` (음수 클수록 저평가)
- `ArchetypeCard(archetype, primary_metric, companion_signals[], value_trap_guards[])` discriminated union

## WP
- **T2-1 structure model**: `cheapness_z=(E[multiple|drivers,sector,regime]−actual)/σ_resid`. ⚠️(R7~8) purged/expanding OOS 적합(in-sample 누수→전부"안싸") + Robust(Huber) or regime별 σ분리(패닉장 정상학습 방지, 단순 OLS 100% 깨짐). 표본부족(섹터당 30~100종목×분기40)→계층베이즈 부분풀링 검토(ref repo agent 결과).
- **T2-2 estimand 분리**: 구조모델(descriptive 멀티플수준) vs 오분류(prescriptive forward return) 한 회귀에 안 섞음.
- **T2-3 드라이버 식별**: SHAP 그대로X(공선성→grouped, regime-stratified, lead/lag 역인과). 서사×통계 2×2→driver_card. cheapness_z=패널레벨(firm 순수함수 아님).
- **T2-4 archetype 5종**: cyclical/event_driven/spread_driven/asset_stable/compounder discriminated union(pydantic). ⚠️ archetype도 시변(엔비디아 과거 게임카드→반도체)→valid_from. percentile은 cyclical 과적합.
- **T2-5 regime**: PIT 가능 경제지표(수익률곡선·PMI)로 정의+regime_model_version. D1 비모수 후순위(bnpy sticky HDP-HMM·ruptures, 고정-K jumpmodels baseline 잔차에 BOCPD 부착).
- **T2-6 D4 Book**: ruptures 분절→regime join→aggregate(PIT)→narrative+HITL→provenance.
- **★ T2-7 검증(필수)**: 반도체(cyclical) 라벨 에피소드(2016-17·2020-21)로 잔차의 밸류트랩 vs 진짜저평가 precision/recall 실증. **안 갈리면 잔차 reframe 자체 재검토**(전체 전제).

## 충족 축
A(학습대상)·B 일부(cheap 정의). 

## 리서치 포인터
findings §2 D1/D4·§5(R4 cheap=잔차)·§5.7(시변 archetype). raw: claude R4(사용자제공)·R8, gemini R4·R8.

## ★ wire 판정 + R8 보강
- cheapness_z=**GREENFIELD ★게이팅**(producer 자체 없음, multiple_band=raw분위). 차용: jumpmodels(Apache, regime)·ai-hedge-fund/valuation(MIT, actual multiple)·ruptures(기간분절). cheapness_z 본체=바닥부터.
- structure model=**계층베이즈 부분풀링**(claude R8: GBM=진단기로만, 패널OLS=불안정, 표본부족 대응). cold-start=최근접 archetype informative prior.
- ★ R8 바닥 2(필수 선결): ①종속변수 비정상성(multiple 정의·GAAP/non-GAAP 40분기 drift)→정의버전 고정·재기술 ②생존편향(상장유지 적합→정상multiple 생존조건부, value_trap_guard가 그 사후패치=추정기·veto 미정합)→delisted/M&A/파산 포함 적합. **이 둘이 최하층, 안 풀면 cheapness_z 허상.**

## 산출물
`core/structure/structure_model.py`·`archetype.py`, `config/archetypes/*.yaml`, `core/regime/`, D4 Book + T2-7 precision/recall 리포트.
