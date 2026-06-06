---
name: handoff-fhc-live-wire-20260606
description: 거시 FHC LLM 파이프라인 shadow 완결(13커밋, audit 2회 PASS). 남은=실거래(실주문)만 빼고 production LIVE wire(발권→bonus→weight DRY_RUN 시뮬 + 종목 e2e). 토큰 한계로 명세 인계.
next-action: "실거래(execute_trade·DRY_RUN=false)만 제외하고 FHC 파이프라인을 production LIVE 연결. 순서 = (B)발권 wire: core/coin_track_macro.py:83 macro_view 생성 후 → loop_factory.build_active_loop(use_claude=True).run_cycle(macro_view) opt-in(env ACTIVE_LOOP_SHADOW) → shadow sink, off=byte-identical / (C)bonus→weight: 발권 카드 → fhc.transition으로 5-state 전이 + bonus_channel.size_with_bonus(l1_weights, card_states, ceilings) → allocate weight 조정(env FHC_BONUS, DRY_RUN=true 시뮬, 천장C·INV-11 off=byte-identical, ★결정론 코어 변경 신중·회귀 엄수) / (D)종목 e2e: security_news_loop + in_universe_fn=button stock/ 스크린 통과분 주입 + 뉴스 소스(scripts/collect_news 또는 리포트). ⛔(E)실주문(KIS/upbit execute_trade·DRY_RUN=false)=사람 게이트 유지. OAuth=메인과 동일 키(한도 OK, 발권 LIVE 검증됨)."
type: project
tags: [domain/macro, type/handoff, topic/fhc-live-wire]
date: 2026-06-06
---

# FHC LLM 파이프라인 production LIVE wire 핸드오프 (2026-06-06)

> 인계: judge 재설계 = `plan-judge-report-arch.md` / progress = `progress-judge-report-arch.md` (Working Notes ckpt 전체) / 계약 = `.coord-fhc-contract-20260603.md`.

## §1. 현재 상태 + 첫 행동
- **상태**: ★**production LIVE wire (B)(C)(D) 전부 완료**(2026-06-06, ckpt-202606062130). 5커밋(04d963a B / ffb5c24 C / e2288a5 D / 5fea15a README + version). tests/assume 132 passed + 도메인 646 passed 0회귀. env opt-in(`ACTIVE_LOOP_SHADOW`/`FHC_BONUS`) off=byte-identical.
  - (B) `coin_track_macro._run_fhc_shadow` 발권 wire(probationary 자본0) / (C) `allocate(fhc_card_states)` bonus→weight tilt(INV-5 confirmed-only, 천장 clip) / (D) `stock_admission_universe_fn` **stock.admission 실연결**(더미 회피 제거, 사용자 지적 반영).
- **LIVE 검증됨**: 하이쿠 요약·BGE 임베딩·대형 LLM 발권 코드/인증/요청 완성. temperature deprecated 픽스 + 429 backoff retry.
- **★남은 것(사람 게이트만)**: ⛔(E) 실주문(execute_trade·DRY_RUN=false)·git push. + 발권 LIVE 카드 **출력** 확인 = 메인 세션 멈추고 `.p2-fhc-live-mint.py` 단독 실행(메인과 동일 OAuth 키 동시점유 시 429, idle 시 통과).

## §2. 진행 맵 (shadow 완료 / LIVE wire 남음)
| 구분 | 모듈 | shadow | LIVE wire |
|---|---|---|---|
| 전제 구독 | macro_mediator | ✅ | (C에서 카드 mediator 평가 소비) |
| 판정 게이트 | spanning_gate · info_delta_gate | ✅ | (B/D에서 호출) |
| 능동 발권 | active_loop + loop_factory(use_claude) | ✅ LIVE 검증 | **B: coin_track_macro opt-in** |
| 리서치 | research_ingest + build_research_ingest(haiku/bge) | ✅ LIVE | (D 뉴스 소스 연결) |
| 종목 소식 | security_news_loop | ✅ 골격 | **D: in_universe_fn + 뉴스 소스** |
| bonus→weight | bonus_channel.size_with_bonus | ✅ self-test | **C: allocate wire(DRY_RUN 시뮬)** |
| 실주문 | execute_trade | — | ⛔ E: 사람 게이트(제외) |

## §3. 사용자 박제
- "남은거 **실 거래 연결빼고** 다 되게 만들어" (2026-06-06). 실거래 = execute_trade·DRY_RUN=false·실주문(KIS/upbit). 그 외(발권·채점·bonus→weight DRY_RUN 시뮬·종목 e2e)는 전부 LIVE.
- "OAuth 한도 문제 없다 — 메인 돌리는 것과 같은 OAuth 키" → 발권 LIVE 동시 호출 OK(rate 경합 무시 가능).
- 기존 게이트(autopilot-run-scope): 실자금 flip(DRY_RUN=false)·90일 검증·push = 사람 게이트 유지. 안전장치(DRY_RUN/EMERGENCY_STOP) 유지.

## §4. 파일 inventory (D:/projects/Inv/)
- **신규(이번 세션, 전부 dormant)**: core/assume/{macro_mediator, spanning_gate, info_delta_gate, active_loop, research_ingest, loop_factory, security_news_loop}.py + tests/assume/test_*.py (7모듈). 기존 fhc/bonus_channel/fhc_fdr(S1/S3/INV-12).
- **수정(transport)**: core/brain/llm_provider.py(ClaudeProvider temperature 4.x deprecated 픽스, commit f443527).
- **wire 대상(C 신중)**: core/coin_track_macro.py:53 collect_market_state(:83 macro_view 생성) / core/portfolio_orchestrator.py(allocate, bonus 반영 지점).
- **LLM/임베딩**: ClaudeProvider(OAuth ~/.claude/.credentials.json, model=claude-opus-4-7 발권/claude-haiku-4-5-20251001 요약) · DaServiceEmbedder(127.0.0.1:8787 BGE-m3).
- **python**: /c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe, PYTHONPATH=.

## §5. 미해결·실패 (삽질 위험)
1. **(C) bonus→weight = 결정론 코어(allocate) 변경**: portfolio_orchestrator/coin_track_macro에 size_with_bonus 끼우면 weight 변경 → INV-11 off=byte-identical 깨질 위험. env gated(FHC_BONUS off=미반영) + 회귀(coin/포트 테스트) 엄수. ★button construction과 계약(§6'' b2: construction.build_sleeve_decisions가 소비)이라 거시 allocate ↔ button construction 소비 지점 정합 확인.
2. **(D) 종목 universe = button stock/ 의존**: in_universe_fn = button 스크린 통과분(stock/ admission/screen). 거시 세션 단독은 더미 universe로만 검증 가능. 실 universe = button 합류.
3. **뉴스 소스**: scripts/collect_news.py(Tavily)·collect_rss_news.py 존재. research_ingest에 ingest_batch로 연결. 증권 리포트 PIT 소스 = 별도(rag_pit/ReportStore).
4. **OAuth rate**: 직전 429는 메인 동시 호출 경합(사용자 "한도 OK"). 발권 LIVE는 메인 idle 시 또는 한도 충분 시 통과.

## §6. 자문 종합
- audit subagent 2회(질문+agent답변↔코드 / plan progress↔코드+LIVE) 둘 다 PASS. 약속-구현 정합, 왜곡·위반·은폐 0, 124 passed. 누락분 전부 button/go-live 선결 정직 분류.
- button 계약(.coord §6''): core/assume FHC=btn-Inv 단일소유 / construction이 size_with_bonus 소비 / 종목 universe=button / RegimeGlasso 공급측=button.
