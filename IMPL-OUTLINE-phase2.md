---
tags: [type/impl-outline, domain/inv, phase/II]
date: 2026-05-29
findings: ./FINDINGS-phase2-sector-rule-framework.md
raw: ./research-raw-phase2/
note: 구현 청사진(개략). 리서치=findings, 이건 "무엇을 코드로 짓나" 골격. wire 판정·3분할 기준.
---

# IMPL-OUTLINE — Inv Phase2 업종 rule 프레임워크 구현 개략

## 0. 한 줄
"싸다=raw 멀티플 분위"를 "싸다=구조모델 잔차(cheapness_z)"로 바꾸고, rule=YAML 상수를 bitemporal 버전관리, L1 결정론 게이트=불가침 floor에 rule은 soft 의견만, 변경은 OOS 게이트+사람 비준, 안전은 kill-switch+grandfather.

## 1. 3층 런타임 (결정 시)
입력(firm,sector,date,as_of) → L3 BGE(유사 과거사례 retrieval, 근거용 판정X) → L1 결정론(cheapness_z=(E[multiple|drivers,sector,regime]−actual)/σ_resid, 불가침) → L2 Qwen(국면별 맥락+임계 가중 soft) → resolver(weak-rule 앙상블 ∑≥4 + value_trap veto) → EffectiveRule verdict → [기존] valuation floor/ceiling > risk 한도 > execute_trade.
우선순위: **하드 리스크 한도 > L1 veto floor > rule signal > default**. rule은 사이징·리스크 못 건드림.

## 2. 모듈 (신규/증분)
⚠️ **경로 교정(wire 판정)**: `core/valuation.py` **없음**. 실제 = `stock/valuation.py`(value_stock:244, multiple_band:202=raw분위, sector_ev_ebitda hook:247 real·미주입), `stock/value_trigger.py`(Gate1Thresholds:55), `stock/data/macro_vintage.py`(FRED ALFRED, backtest/ 아님), `core/brain/regime_classifier.py`(JumpModel), `backtest/{pbo,walk_forward}.py`, `core/consensus.py`.

| 모듈 | seam | verdict |
|---|---|---|
| `core/data/pit_panel.py` | macro_vintage.py(vintage real)+walk_forward(filter_pit_fundamentals) | NEEDS-REFACTOR |
| `core/structure/structure_model.py` cheapness_z | 없음(multiple_band=raw분위) | **GREENFIELD ★게이팅** |
| `core/structure/archetype.py` | 없음 | GREENFIELD |
| `core/regime/` | regime_classifier.py(이미 라이브도달) | NEEDS-REFACTOR(fixed-K) |
| `core/rules/*` | core/consensus.py+backtest/pbo.py(primitive만) | GREENFIELD |
| `stock/valuation.py` RuleProvider | value_stock:244·hook:247 | NEEDS-REFACTOR(additive) |
| `core/observability/*` | 없음 | GREENFIELD |
| Token Bucket | execute_trade.py MAX_*:346-480·core/risk_gate(라이브) | **WIRE-READY** |

## 2.5. ★ 라이브 통합 (prior audit "core 0% 도달" 무효화)
- **브리지 이미 존재**: `run_agents.py:869` `INV_CORE_GATE`(opt-in)가 RiskGate.check·MemoryLayer.store_decision·RegimeClassifier.classify 라이브 호출(코인). 이 패턴 증분.
- **진짜 blocker 2**: ①cheapness_z producer 없음(greenfield 게이팅) ②StockTrack 라이브 미인스턴스화(run_agents=코인전용).
- v1 DAG: as_of resolver→bitemporal store→structure model→residual OOS→L1 veto→2-ledger.

## 3. v1 vs v2 (과설계 회피)
- v1: 단일 structure model + tag attribution + L1 floor + YAML rule + bitemporal store + 수동승격.
- v2 미룸: consensus 다중agent·GraphRAG·Shapley·BGE 다층.
- v1 검증: 반도체(cyclical) 잔차 precision/recall 실증(밸류트랩 분별) — 안 갈리면 전제 재검토.

## 4. 불변식 4
①position=entry version 고정 ②rollback=append만(mutate0) ③rule⊂emergency_stop ④opportunity cost 계상.

## 5. 구현 디테일 체크리스트 (R7~8)
structure model purged OOS+Robust+regime별σ / sys_time≠knowable_from(silent revision) / sector·archetype·regime_model_version 시변 / corp action adjustment / 상폐+backfill bias / cheapness_z 패널레벨 / Pydantic strict schema+Fallback / 비용·슬리피지 게이트 G3.5 / 전역 FDR Alpha Spending / regime 먼저→drift / 좀비포지션 Time-stop / canonical as_of resolver.
+ R8 바닥2(claude): GAAP/non-GAAP multiple정의 40분기 drift→정의버전 고정 / 생존편향→delisted/M&A/파산 포함 적합. structure=계층베이즈 부분풀링(GBM=진단기로만), cold-start=최근접 archetype prior.

## 6. ★ wiring 순서 (thin live slice, wire 판정)
1. execute_trade Token Bucket(INV_CORE_GATE 확장, 불변식③ 먼저).
2. structure_model 오프라인+**반도체 잔차 precision/recall 검증 — 안 갈리면 STOP(전제붕괴)**.
3. RuleProvider가 stock/value_stock 래핑(sector_ev_ebitda+cheapness_z 주입, shadow-only).
4. PIT 패널+bitemporal store→RuleProvider, RegimeClassifier.classify(라이브도달) regime 입력.
5. StockTrack 라이브화(flag)→RuleProvider→L1 floor→RiskGate→execute_trade→RuleObserver divergence.

## 7. 차용 (ref-borrow, mlfinlab=stub 금지)
skfolio _combinatorial(CPCV/PBO,BSD)→T3 G3/G4 · statsmodels fdr_bh→G1 · ai-hedge-fund/valuation(MIT)→L1 floor·T2 actual · jumpmodels(Apache)→regime · pykrx→KR data · ruptures→기간분절. cheapness_z·archetype·T3 거버넌스=바닥부터.
+ R8 바닥 2(claude): GAAP/non-GAAP multiple 정의 40분기 drift→정의버전 고정 / 생존편향→delisted/M&A/파산 포함 적합. structure model=계층베이즈 부분풀링(GBM=진단기로만), cold-start=최근접 archetype prior.

## 6. ★ wiring 순서 (thin live slice)
1. execute_trade Token Bucket(INV_CORE_GATE 확장, 불변식③ 먼저).
2. structure_model 오프라인+**반도체 잔차 precision/recall 검증 — 안 갈리면 STOP(전제붕괴)**.
3. RuleProvider가 value_stock 래핑(sector_ev_ebitda+cheapness_z, shadow-only).
4. PIT 패널+bitemporal store→RuleProvider, RegimeClassifier regime 입력.
5. StockTrack 라이브화(flag)→RuleProvider→L1 floor→RiskGate→execute_trade→RuleObserver.
