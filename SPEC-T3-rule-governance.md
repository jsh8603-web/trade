---
tags: [type/spec, domain/inv, phase/II, track/T3]
date: 2026-05-29
split_index: ./SPLIT-INDEX-phase2.md
findings: ./FINDINGS-phase2-sector-rule-framework.md
impl_outline: ./IMPL-OUTLINE-phase2.md
raw: ./research-raw-phase2/
track: T3 rule·승격·거버넌스·관측 (의존: T2 cheapness_z·archetype)
---

# SPEC-T3 — rule·승격·거버넌스·관측 층

> 다른 main agent 위임. 공통맥락=split_index·findings·impl_outline. T2 산출은 mock으로 개발. ⛔ 실자산 거래 — 안전 최우선. 기존 valuation.py·execute_trade·emergency_stop 폐기금지 증분.

## 목적
T2의 cheap 신호를 rule로 조립·승격·적용·관측·통제. **L1 결정론=불가침 floor, rule=soft 의견만**.

## WP
- **T3-1 signal·resolver**: bitemporal versioned signal `signals/{id}/{ver}.yaml` + `policy/{sector}.yaml`(archetype dispatch) + `rule_resolver(sector,decision_date,as_of)→EffectiveRule`. weak-rule 앙상블(∑≥4). ⚠️ 타임스탬프 2개 effective_from≠knowable_from, 백테스트=knowable_from≤as_of. ⚠️ canonical as_of resolver 선행(R7).
- **T3-2 주입 L1 veto**: L1 결정론=hard veto floor / rule=L1 허용공간 내 soft만 / resolver 부호충돌→abstain. 우선순위 하드리스크>L1 veto>rule>default. RuleProvider로 execute_trade 주입(valuation.py를 Provider 뒤). value_trap_guard veto > 앙상블(veto 우선, R8). ⚠️ 죽은 sector_ev_ebitda hook 부활/삭제 명시결정.
- **T3-3 승격 G0~G6**: G0 사전등록→G1 effect+BH FDR→G2 국면안정→G3 purged+embargo WF→G3.5 비용/유동성/슬리피지→G4 PBO≤0.2→G5 shadow→G6 사람. ⚠️ multiplicity 전역(LLM 제안 전체 FDR 분모)→Alpha Spending(R7~8). EvidenceCard→rule_evidence.jsonl. anchoring=LLM 변수·방향만+임계 적합 P/R, Pydantic strict schema(환각 방어 R8).
- **T3-4 변경 트리거·consensus**: 잔차 drift(PSI+0근방질량)→재검토큐(자동변경X). ⚠️ regime 먼저 판별→동일레짐 내 drift만(무한루프 방지 R7). 토너먼트 가지치기. Proposer-Challenger-Arbiter.
- **T3-5 기존데이터 2-ledger**: decision(불변)/analysis(소급), version_basis 꼬리표. rule_performance(version×regime×sector×regime_model_version) append-only, dormant 부활.
- **T3-6 관측·거버넌스(실자산)**: RuleObserver 5지표(★divergence shadow↔live=1차방어선). rule attribution(deciding_rule_id, opportunity cost별도). Rule-level Stop(OOS MDD-5%→Mute). Grandfather(강제청산X)+좀비포지션 Time-stop(R8). bitemporal soft-delete rollback(row append). Token Bucket kill-switch(rule⊂emergency_stop). 비대칭 거버넌스(퇴출자동·진입수동). 모듈 4분리(관측≠제어).

## 충족 축
C(주입)·D(변경)·E 일부·F(관측)·G(거버넌스). 불변식 4 전부.

## 리서치 포인터
findings §5.5(C/D/E)·§5.6(F/G)·§5.7~5.8(구현디테일). raw: gemini/claude R5·R6·R7·R8.

## ★ wire 판정 교정 (subagent)
- 경로: `core/valuation.py` 없음 → `stock/valuation.py`(value_stock:244, sector_ev_ebitda:247). consensus=`core/consensus.py`(primitive), PBO/WF=`backtest/{pbo,walk_forward}.py`(tests-only).
- **브리지 이미 존재**: `run_agents.py:869` INV_CORE_GATE 패턴(RiskGate/MemoryLayer/RegimeClassifier 라이브 호출, 코인). T3 주입은 이 패턴 따름.
- Token Bucket = WIRE-READY(execute_trade.py:346-480 MAX_* 블록 + core/risk_gate 라이브).
- ⚠️ blocker: StockTrack 라이브 미인스턴스화(주식 경로 죽음) → 주식 rule production 전 StockTrack 라이브화 선행. shadow-only부터.
- 차용: skfolio `_combinatorial.py`(CPCV/PBO, mlfinlab stub 대체 BSD) → G3/G4. statsmodels fdr_bh → G1. PSR/DSR rubenbriones(~40줄) → G4. ai-hedge-fund/valuation(MIT) → L1 floor. (ref-borrow-20260529.txt)
- ⚠️ mlfinlab refs=전부 stub(`pass`)+독점 라이선스, 복사 금지.

## 산출물
`core/rules/`(resolver·signal·promotion_gate·consensus), `config/sector_rules/*.yaml`, `core/observability/`, bitemporal rule store, kill-switch. 기존 stock/valuation·execute_trade·core/risk_gate 증분(INV_CORE_GATE 패턴).
