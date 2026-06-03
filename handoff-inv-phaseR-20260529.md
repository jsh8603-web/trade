# 인계 — Phase R 진행 + harness2-wf drift 보수 (2026-05-29, btn-Inv)

## 진행 상태 (compact 직전)
- **Phase 6 COMPLETE**(git 339a710): SO-1~8 PASS + Gate Review 1 hotfix(faa4b29) + 이연 3건(N-P6-90D/CONSENSUS-LLM/FULL-INTEGRATION) 박제 + N3/rpm 소진. 129 p6 passed.
- **Phase R 진행 중**(autopilot 마지막): taskspec-phase-R.txt + harness2.md Phase R + resume_baseline(phase R) + phase-state S1/R + Worker.prompt repoint(SACRED Phase R) 전부 작성됨. 백업 harness2.phase6.done.md.
  - **SO-1(6b536be)·SO-2(81d2d3c)·SO-3(bb622a9)·SO-4(e41e53c) 전부 Verifier PASSED**. git HEAD=e41e53c.
  - **SO-5(집행 상태머신 coin 변형) 미착수/진행 중** — git HEAD에 SO-5 commit 없음(2026-05-29 01:23 기준). SO-6(consensus 코인렌즈)·SO-7(§2.9 PhaseR 게이트)·SO-8(GOLDEN RULE) 잔여.
  - SO-1~4 검증 결과: 래핑 전후 decision 동치·coin_track 본체 미변경·Upbit fee·RSI 동치(N-P5-COIN-METRICS 소진)·Riskfolio tail HRP·crypto decay 4h·SACRED execute_trade/run_cycle diff=0 전부 PASS.

## ⚠️ 핵심 미해결 — worker→verifier 자동 릴레이 stall (매 SO 수동 브리지 중)
- **증상**: Standby1(active Worker)이 SO commit 후 **handoff_key+ev:done 로깅 통째 누락하고 idle**(push만 누락이 아님). Verifier는 wake 받아도 verdict 완료 전 idle. → 매 SO Supervisor가 수동 catch-up(Verifier에 commit-SHA 검증 지시)으로 봉합.
- **현 우회책**: Verifier에 **git-poll forward-pull** 지시(`git log --oneline` 대조로 verdict 없는 SO 커밋 자동 검증, ev:done 의존 안 함) + Standby1에 commit 후 push 강제. SO-3/4는 이 방식으로 PASS.
- **재개 시**: git HEAD 확인 → SO-5 commit 있는데 verdict 없으면 Verifier에 commit-SHA catch-up. SO-5는 **SACRED 최민감**(execute_trade 실주문/run_cycle/nonce diff=0 반드시 확인). SO-8 도달 시 audit-goldenrule-pR.md §3 이연 → progress.md `## 이연 항목` 박제=Supervisor 전담 → Verifier 재검증.

## btn-button 보수 요청 (전달 완료)
- 파일: `D:/projects/Inv/harness2wf-maintenance-request-20260529.md` (drift 4건 + Phase R 라이브 보강 신규-1/2/3).
- btn-button(psmux) 세션에 2회 전달(원본 + 보강). 핵심: **(신규-1)Worker commit↔done+push 원자결합 (신규-3)Verifier git-commit 기반 pull(ev:done 의존 탈피)**이 근본 fix. + 발견1(SR mode G/A Phase2~6 누락)·발견2(Healer 9-step 우회)·발견3(워치독 재생성 차단, 단일 self-wake 루프+`.self-wake-ts` dedup, watchdog 자체는 안전상 유지).

## RC-4 promotion-log K (세션 종료 시, task #8)
- drift 공통 패턴 "protocol SSOT를 단축경로로 갈음/누락" — SR→3-reviewer 대체·Healer 우회 Supervisor-direct·워치독 N개 1회용·worker→verifier ev:done 의존 stall. Phase 4/5/6/R 재현.
- 기존 Phase 4 K(harness2-gate-review-catches-concurrency-bugs) 강화.

## 운영 환경
- long-mode 압축 시 자동 원복 → 재개 후 필요 시 `bash ~/.claude/scripts/ctx-warn-long-mode.sh on`.
- 워치독 추가 생성 중단(재생성 sprawl 방지). wake 경로=팀원 idle 알림 + 비서 nudge + Verifier git-poll.
- 팀 h2wf-Inv-p0 in-process 생존(SendMessage 재활성). Phase R 완료=autopilot 종착(실거래 flip+90일=사용자 go-live, 범위 밖).
