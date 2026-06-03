---
tags: [type/plan, domain/inv, phase/II, track/T1, topic/assumption-lifecycle-v2, session/btn-Inv]
date: 2026-05-29
session: btn-Inv
design: ./DESIGN-inv-v2.md
progress: ./progress-inv-v2.md
contract: [./DESIGN-button-v2.md (§10.6), ./CONSULT-DECISIONS-button-v2-20260529.md]
note: btn-Inv(T1) 데이터·PIT·실거래 안전 v2 구현 plan. Walking Skeleton 순서. event-ledger 본체 + PIT substrate. 설계 상세=DESIGN-inv-v2.md.
---

# plan-inv-v2 — 구현 plan (Walking Skeleton)

> 설계 SSOT = `DESIGN-inv-v2.md`. event ledger 계약 = `DESIGN-button-v2.md §10.6` (확정, 재논의 X). 각 모듈 self-test = `PYTHONIOENCODING=utf-8 PY -m core.data.X` (PY=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`).

## 핵심 원칙
- **로직+인프라 동시 테스트 금지**. ledger reducer 를 dummy-event 로 먼저 증명 → 통계 플러그인 → 최소 backtest.
- 신규 의존 = pandera(설치됨)만. 기존 코드 재사용(online_fdr LORD++, ledger, as_of, panel_schema, kill_switch, corp_action).
- ⛔ 빌드 전 btn-Codlearn 3자 schema 합의 (DESIGN-inv-v2 §4 interface 회신). 단 substrate 모듈(identity/calendar/fx 등)은 ledger 계약 비침범이라 병행 착수 가능.

## 모듈 → 축/GATE 매핑
| 모듈 | 축/요청 | 레이어 |
|---|---|---|
| event_ledger.py | IA-1·IA-3·R5 | L1 (본체) |
| data_contract.py | IA-2·R11 | L2 |
| lineage.py | IA-3·R11 | L2 |
| online_fdr (ledger 내장 reduce) | IA-3·R11 | L1 |
| pit_query.py 확장 | IA-3 | L2 |
| identity.py | IA-4 (PSID) | L2 |
| corporate_action.py | IA-4·R4데이터 | L2 |
| instrument_source.py | IA-4·R4데이터 | L2 |
| fx.py | IA-4·IA-6 | L2 |
| calendar.py | IA-6 | L2 |
| universe_membership.py | IA-4 | L2 |
| panel_schema.py 확장 | IA-4·R4데이터 | L2 |
| promotion_gate_live.py | IA-5·R12 | L2 |
| d4_book.py wire | R8 | L2 |

## 단계 (Walking Skeleton)
- **P0** 3자 schema 합의 회신 (btn-Codlearn) + DESIGN/plan/progress·raw 포인터 전달.
- **P1** event_ledger reducer 골격: 11 event dataclass + 공통필드 + `state=reduce(pure_apply, sorted)` + dummy-event 랜덤순서 TDD (decision_time state 100% 복원, FDR_DECISION decision_time 불변). 인프라만.
- **P2** data_contract.py(Pandera, DATA_CONTRACT_VIOLATION emit + HOLD_SUSPENDED) + calendar.py + identity.py(PSID) substrate stub→실.
- **P3** instrument_source.py(crypto MVRV 최소, CoinMetrics) + fx.py + outcome resolver → 최소 backtest closed-loop(crypto MVRV 7d, PREDICTION_MADE→OUTCOME_OBSERVED→FDR_DECISION).
- **P4** universe_membership.py + corporate_action.py + vintage open-sequence + panel_schema 확장 + pit_query 확장 + lineage.py.
- **P5** promotion_gate_live.py(shadow→live 사람게이트) + d4_book 실데이터 wire.
- **P6** self-test 전수 + IA-1~6 GATE 증거 + btn-Codlearn 최종 보고.

## 분기 옵션 (plan-branch-min-2)
- substrate 정정(CA/vintage) 표현: (A) substrate bitemporal 테이블 + ledger 가 data_vintage 로 참조 [채택] vs (B) 정정도 이벤트화. → (A): ledger=의사결정/outcome/lifecycle, substrate=PIT 시장데이터 분리가 reducer 순수성 보존(자문 수렴).
- FX/terminal/universe: (A) OUTCOME payload + substrate 참조 [채택] vs (B) 공통필드 승격. → (A): 공통필드 최소 유지(btn-button 계약 비침범), 3자 합의 확인.
