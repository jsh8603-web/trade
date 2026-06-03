---
tags: [type/handoff, domain/inv, phase/II, track/T3]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-phase2-T3.md
progress: ./progress-phase2-T3.md
matching: ./MATCHING-prompt-vs-impl-phase2.md
note: T3 구현 완료 인계 + 검토 agent rubric + T1/T2/T3 보완 분담. compact 후 재개용.
---

# HANDOFF — T3 구현 완료 + 검토 계획 + 분담

## 1. 구현 현황 (S0~S13 전부 self-test PASS, Python312 풀패스)
| Step | 파일 | 핵심 |
|---|---|---|
| S0 | core/pit/as_of.py | canonical as_of resolver(미래거부·tz·resolve, cheapness_z_safe 어댑터) |
| S1 | core/rules/signal.py | Signal+weak앙상블(quorum4)+rule_resolver(archetype dispatch·trap veto·compounder expensive_trap) |
| S2 | core/rules/bitemporal_store.py | event-sourced append-only+AS-OF 복원+soft-delete rollback |
| S3 | core/rules/promotion_gate.py | G0~G4(BH FDR전역·PSR·PBO)+EvidenceCard, G5/6=NEED_HUMAN. DSR=detail만(v2 게이트) |
| S4 | core/rules/ledger.py | 2-ledger(decision freeze/analysis counterfactual)+RulePerformance dormant부활 |
| S5 | core/rules/l1_gate.py | L1 결정론 floor+archetype dispatch(우선순위 trap veto>L1 veto>event특례>cheap>neutral) |
| S6 | core/observability/rule_observer.py | 5지표+divergence 1차방어선+PageHinkley+Rule-Stop(RO) |
| S7 | core/observability/rule_attributor.py | Trade Tagging+opportunity cost(불변식④) |
| S8 | core/observability/kill_switch.py | Token Bucket+emergency latch(불변식③ rule 우회불가) |
| S9 | core/rules/consensus.py | 변경트리거(regime선행 R7)+ChangeQueue+cap+hysteresis+P-C-A+토너먼트 |
| S10 | core/rules/rule_provider.py | RuleProvider shadow(legacy↔rule divergence, additive) |
| S11 | core/rules/seed_builder.py + config/sector_rules/{cyclical,event_driven}.yaml | ★seed 확보(실데이터/큐레이션 앵커+LLM 키워드 hook+SeedRegistry 무한확장) |
| S12 | core/book/d4_book.py | ★D4 Book(MacroPeriod+IndustryCharCard+to_context LLM주입+ruptures, PIT) |
| S13 | config/archetypes/*.yaml(T2) | 5종 검증 통과 |

남음: **INT**(as_of wire `core/data/pit_query.py:28 set_as_of_resolver(resolve_as_of)` + kill_switch→execute_trade + RuleProvider shadow + run_agents.py:873 INV_CORE_GATE 패턴, ⚠️StockTrack 미가동=shadow까지) / **VERIFY**(전모듈 `PYTHONIOENCODING=utf-8` 일괄+회귀) / **REVIEW**(↓).

## 2. ★ 검토 agent rubric (사용자 지시: 평가기준 사전정의)
opus 1M subagent **8기** 스폰(각 1축, 코드레벨, read-only Explore). 공통 산출 4필드:
**(a) 구현 완전성**(축 요구 ↔ 코드 1:1, 누락) **(b) wiring 깨짐**(import·호출·계약 미연결, 죽은 hook) **(c) 미흡/과설계**(self-test 커버 못한 경로, 엣지) **(d) 보완 액션**(파일:라인 + 무엇을).

| agent | 축 | 검토 대상 | 핵심 질문 |
|---|---|---|---|
| R-A | A 무엇학습 | structure_model·archetype·panel_schema | cheapness_z 잔차 producer 완전? driver 식별? archetype 5종 dispatch? |
| R-B | B 규칙화 | signal·promotion_gate·seed_builder | weak앙상블·G0~G6·anchoring 완전? FDR 전역분모? |
| R-C | C 주입 | l1_gate·rule_provider·as_of | L1 floor 불가침? archetype dispatch? as_of wire(T1 주입점)? |
| R-D | D 변경 | consensus·rule_observer | drift→큐(자동변경X)? regime선행? 토너먼트? |
| R-E | E 기존데이터 | ledger·bitemporal_store | 2-ledger freeze? append-only? dormant 부활 regime_model_version? |
| R-F | F 관측 | rule_observer·rule_attributor | divergence 1차방어선? opportunity cost? 관측≠제어? |
| R-G | G 거버넌스 | kill_switch | Token Bucket? rule⊂emergency? grandfather? |
| **R-SEED** | ★seed/D4 집중(사용자 지시2) | seed_builder·d4_book·config/sector_rules·config/archetypes | **다산업·다기간 학습 수용 충분?**(SeedRegistry→consensus→promotion_gate 연결?) seed 실데이터 앵커 wiring? D4 to_context LLM 주입 경로? 사용자 "무한확장" 메모 충족? 학습 시작 가능 상태? |

### ★ R-SEED 학습 충분성 합격 기준 (사용자 명시: 프롬프트 거시/주식/상품 최소 충족)
학습을 "시작 가능"으로 판정하려면 사용자가 프롬프트에서 논의한 아래 기준을 **최소 코드/구조로 수용**해야 한다(MATCHING 문서 대조):
- **거시 D1**: open-ended 레짐 발견(고정-K 탈피, 새 국면 가지치기) — regime 입력이 다국면 확장 수용? (pit_regime + SeedRegistry regime override)
- **거시 D4**: 거시 기간정의(상황 X 언제~언제·참조지표·서사) Book 에 적재·PIT 조회·LLM 주입 가능? (d4_book)
- **주식 D3**: 업종·기간별 valuation 상수(PER/PBR/EV-EBITDA/WACC) 적응 — sector×regime×기간 seed 변형 수용? (seed_builder threshold_anchor + PeriodVariant)
- **주식 산업특성**: 산업별 "반도체 PER 착시" 변형(화학/철강/바이오 등) 카드 수용 + 다산업 무한 추가? (config/sector_rules·archetypes·IndustryCharCard)
- **상품**: 상품(commodity) archetype/seed 경로 존재? — ⚠️ 현재 cyclical 에 화학/철강만, 순수 commodity(원자재 선물·spread_driven) seed 누락 가능 → R-SEED 가 명시 점검.
- 학습루프: seed → consensus(OOS 증명) → promotion_gate(G0~G6) → bitemporal 승격 의 **닫힌 루프**가 코드로 연결됐는가(끊겨 있으면 "학습 시작 불가" 판정).
→ 위 6 기준 중 미충족분 = 학습 시작 전 보완 필수 항목으로 보완계획에 산입.

→ 8기 결과 내가 통합 → 보완계획 plan/progress 추가.

## 3. ★ 보완 분담 초안 (T1/T2/T3, 사용자 지시3)
- **T1(btn-Inv)**: sector_multiples 라이브 fetch(N-T1-SECTORMULT, Damodaran/French cache, go-live) / 패널 실데이터 빌드 / **regime_id producer**(panel 에 regime 채우기 — T2 regime 모델 연결).
- **T2(btn-button)**: **T2-7 실데이터 재검증**(T1 패널 도착 후 fixture→실데이터, STOP gate 재실행) / **pit_regime 비모수 D1**(open-ended 레짐, bnpy/HDP-HMM v2) / driver 식별 SHAP 2×2.
- **T3(나, btn-Codlearn)**: INT wiring 전부 / seed_builder↔consensus↔promotion_gate 학습루프 연결 / D4 Book LLM judge 주입 / REVIEW 결과 보완.

## 4. 재개 포인트 (compact 후 즉시)
1. INT as_of wire: `core/data/pit_query.py` 의 `set_as_of_resolver` 에 `from core.pit.as_of import resolve_as_of` 주입(순환 회피 lazy). self-test.
2. VERIFY 일괄: `PYTHONIOENCODING=utf-8 /c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe -m core.X` 전 모듈.
3. REVIEW: §2 rubric 대로 8기 스폰(Workflow 또는 Agent Explore). 결과 통합→보완계획.
4. 학습 시작: R-SEED 가 "다산업/다기간 수용 충분" 판정 후(사용자 조건) seed→consensus 학습루프 가동.

## 5. 핵심 설계 불변(검토 시 위반 체크)
①position=entry rule_version 고정 ②rollback append만 ③rule⊂emergency_stop ④opportunity cost 계상. 모듈 4분리(관측≠제어). cheap=잔차(raw분위 아님). L1=불가침 floor, rule=soft. 돈flip=shadow+사람.
