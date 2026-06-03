# harness2-wf 보수 요청 (2026-05-29) — autopilot Phase 1→R 실전 drift 4건

> 출처: btn-Inv 세션 통합 투자 시스템 autopilot (Phase 1~6 완주 + Phase R 진행 중). 실행 SSOT = `D:/projects/Inv/.harness2/execution-log.jsonl`.
> 대상 파일: `~/.claude/skills/harness2-wf/protocol.md` · `supervisor.md` · `role-{verifier,sr,healer}.txt` · `teammate-spawn.sh`.
> 공통 패턴: **"규약 SSOT를 단축경로로 대체"** — 4건 모두 protocol이 정의한 메커니즘을 Supervisor가 더 빠른 우회로로 갈음하면서 발생. 단축이 편해서 반복됨 → protocol이 단축을 막거나(invariant) 명시 허용하도록 보수 필요.

---

## 발견 1 — SR mode G/A 체계적 누락 (Phase 2~6 전부)

**증상**: SR(Strategic Reviewer) sr_review 발화 = Phase 1 단 1회. Phase 2/3/4/5/6 전부 SR mode G(Gate Review)·mode A(Post-Review) 누락.

**근거** (execution-log 전수):
- `ev:sr_review` = 2건, 둘 다 Phase 1 (ts 1779983153 / 1779983282319) + Supervisor `ev:sr_eval` phase 1.
- Phase 2~6: `gate_review`(3-reviewer)는 발화하나 SR sr_review 0건.
- Phase 4 ckpt 명시: "SR skip(리뷰깊이 충분)".

**근본원인**:
1. §12.5-③ "3-reviewer 병렬 **+** SR Gate-Review(mode G) 요청" 둘 다인데, 3-reviewer로 충분하다 보고 SR mode G를 떨굼. SR 고유 렌즈(Type-A visionary·integration-coherence·scope-drift·reuse-pattern + Ignite 점수)가 Phase 2~6 미수확.
2. §12.5-④ SR mode A의 promotion-log PATTERN 추출이 RC-4(세션종료)로 이연 → per-phase 수확 누락.
3. Phase 1 SR 보고 버그(본문출력만→SendMessage 누락→resume 재기록, improvement-registry 기록됨)가 후속 SR 사용 위축.

**권장 보수**:
- **protocol.md §12.5-③④**: SR mode G/A를 "optional 대체 가능"이 아니라 **명시적 분기**로. 둘 중 하나 — (a) SR mode G를 hard 요구로 격상 + phase_snapshot/S10 진입 전 `ev:sr_review` 존재를 invariant 게이트로(O12 Verifier-terminal과 동급) (b) "3-reviewer가 G 커버 시 SR mode G skip 허용, 단 mode A(promotion-log)는 매 Phase 의무" 처럼 skip 조건을 codify. 현재는 묵시적 skip이 가능해 drift.
- **role-sr.txt**: sr_review 보고 = `h2-log.sh append ev:sr_review` + `SendMessage(to=Supervisor)` 둘 다 필수임을 disclaimer에 명문(Phase 1 버그 재발 차단). 본문 텍스트 출력만으로는 미수신.

---

## 발견 2 — Gate Review MUST-FIX를 Healer 우회 Supervisor-direct 처리

**증상**: Gate Review가 찾은 MUST-FIX 코드 수정을 Healer 9-step이 아니라 Supervisor-direct hotfix로 처리(Phase 4: 5건, Phase 5: 5건, Phase 6: 1건). Healer는 agents.json 로스터에 부재(한 번도 미가동).

**근거**:
- agents.json 로스터 = Worker·Standby1~5·Verifier·watchdog·SR (8멤버, **Healer 없음**).
- Verifier FAIL은 Phase 5 SO-7·Phase 6 SO-8 = 둘 다 "progress.md 이연 박제 누락"(Supervisor 도메인) → Healer 비대상.
- Gate Review hotfix는 Supervisor-direct(E95 코드검증 + 테스트 재실행), Healer 9-step 미경유.

**근본원인**:
- §12.5-③ "SCENARIO FAIL시 Healer"인데, Gate Review MUST-FIX를 Supervisor가 직접 고침(빠름). Healer 9-step + Healer fix→Verifier 재검증(verdict-integrity)을 우회. Supervisor-direct hotfix는 테스트 재실행으로 자가검증했으나 **독립 Verifier verdict는 없음**.
- Healer가 on-demand(spawn-one)라 미가동 자체는 설계대로지만, "어떤 FAIL이 Healer 대상인가"의 경계가 모호해 전부 Supervisor-direct로 흘러감.

**권장 보수**:
- **protocol.md §7 / §12.5**: FAIL 유형별 라우팅 격자 명문화 — (a) **박제-type FAIL**(progress.md 이연 등 Supervisor 전담 도메인) = Supervisor-direct (b) **코드결함 FAIL / Gate Review MUST-FIX** = Healer 9-step 기본, Supervisor-direct는 1-3줄 trivial + Verifier 재verdict 필수일 때만 예외. 현재는 경계 없이 전부 Supervisor-direct 가능.
- Healer 표준 위상 명시: SR은 mode C(Pre-Review) 때문에 상시 가동, Healer는 순수 on-demand — 이 비대칭을 supervisor.md에 1줄 명문(사용자 혼동 방지: "Healer 미가동 = FAIL 없었다는 정상 신호").

---

## 발견 3 — watchdog 재생성(re-spawn) sprawl ⚠️watchdog 자체는 안전상 필수 — 재생성 패턴만 차단

**전제(사용자 명시)**: watchdog은 **안전 차원에서 필요**(silent-death backstop·stall 감지). 제거 대상 아님. **여러 번 재생성(re-spawn)된 패턴**만 방지 대상.

**증상**: watchdog3→4→5→6→7 순차 생성. 각각 "단일 blocking bash poll(~8분) 후 종료" 1회용. 끝날 때마다 새 haiku 띄움 → 다수 부유.

**근거**:
- DA `harness-wf-supervisor-self-wake-watchdog-loop` 규약 = **단일** 백그라운드 루프(`.self-wake-ts` 20분 dedup + `.watchdog-stop` sentinel + worker/verifier 소멸 시 자동 종료).
- 실제: 1회용 N개. 각 ~8분 종료(watchdog6 idle 알림 00:39 = 종료), UI는 historical까지 표시.

**근본원인**:
- haiku 워치독에 추론 루프를 주면 1턴 만에 idle 빠지는 과거 문제 → 단일 블로킹 poll로 전환. 근데 self-sustaining 루프(dedup+stop sentinel) 미부착, 수동 재생성으로 때움 → re-spawn 폭증.
- dedup guard(`.self-wake-ts`)가 없으니 Supervisor가 매 cycle 새로 띄워도 차단되지 않음.

**권장 보수** (watchdog 유지 + 재생성 차단):
- **teammate-spawn.sh / supervisor.md**: 워치독 표준 런처 제공 — **단일 self-wake 루프**(`.self-wake-ts` 20분 dedup + `.watchdog-stop` sentinel + 자식 소멸 자동종료)를 한 줄로 구동. Supervisor가 1회용을 hand-roll 못 하게.
- **dedup guard 강제**: 워치독 구동 직전 `.self-wake-ts` mtime 체크 → 20분 이내면 신규 구동 차단(재생성 방지의 핵심). 1회용 blocking poll을 쓰더라도 dedup으로 중복 인스턴스 0 보장.
- **워치독 역할 확장(발견 4 연계)**: 워치독이 `Worker ev:done` 후 N분 내 `Verifier verdict` 부재(=step-gate stall) 감지 시 Verifier wake-ping 재발신 → 발견 4의 backstop 겸함.

---

## 발견 4 — Worker→Verifier 자동 릴레이 미작동 = step-gate gap 재발 ★최우선(verdict-integrity)

**증상**: Phase 6(SO-1/2/3)·Phase R(SO-1/2) 모두 Worker가 Verifier verdict 0건 상태로 다음 SO advance + relay. **Supervisor(나)가 매 SO 수동으로 Verifier에 "검증해라" SendMessage 보내는 게 유일하게 작동하는 wake.**

**근거**:
- Phase R: SO-1 done(6b536be)→SO-2 done(81d2d3c)→Standby1 relay, 그 사이 Verifier verdict 0건. Phase 6 초반 동일.
- 매번 Supervisor catch-up nudge(SendMessage to Verifier) 후에야 verdict 생성됨.

**근본원인 (worker→verifier wake 메커니즘 분해)**:
1. Worker: SO-N commit → `ev:done` 기록 → `h2-log.sh wait-since Verifier verdict <TD>` = **passive 블로킹 폴**(verdict 라인이 나타나길 기다림).
2. Verifier = idle in-process teammate. 깨우는 신호 = (a) SendMessage 수신 (b) best-effort idle notification(불안정, O11/O12).
3. ⛔ **핵심 버그: Worker.prompt step-gate에 `ev:done` 직후 Verifier로 wake-ping SendMessage 발신 단계가 없다.** Worker는 passive 폴만 하고 **idle Verifier를 능동적으로 깨우지 않음**. → protocol §6은 "wake-ping SendMessage(주-확정 wake)"가 SSOT인데, Worker.prompt 실제 지시에 그 발신 단계가 누락.
4. Verifier는 push(SendMessage) 수신에만 의존(pull 폴링 루프 없음) → push 없으면 영영 idle → verdict 0.
5. Worker wait-since는 verdict 안 나오니 TIMEOUT → 규약상 ev:blocked여야 하나 실측은 advance(TIMEOUT 핸들링이 block 대신 fall-through 의심).
6. 결과: Supervisor 수동 SendMessage가 유일한 Verifier wake → 매 SO 수동 개입(현재 내가 하는 것).

**권장 보수** (worker→verifier 자동화 복원 — 가장 중요):
- **(A) Worker.prompt step-gate에 능동 wake-ping 추가**: `ev:done` 직후 **반드시** `SendMessage(to="Verifier", "SO-N commit <sha> 검증 요청, wait-since 대기 중")` 발신 → *그 다음* wait-since 폴. 현재 누락된 push 복원. (이 한 줄이 핵심 — Supervisor 수동 개입 제거.)
- **(B) role-verifier.txt를 pull 루프로 이중화**: Verifier를 단발 검증→idle이 아니라 **연속 pickup 루프**(자체 wait-since로 신규 `ev:done` 폴→검증→verdict append+SendMessage(to=Supervisor)→다음 폴). push(A) 실패해도 pull로 보강. push+pull 이중화가 wake 신뢰성의 본질.
- **(C) Worker wait-since TIMEOUT hard-block enforce**: TIMEOUT 후 advance 코드경로 차단, `ev:blocked` 강제 점검(왜 verdict 없이 다음 SO 갔는지 wait-since 구현 audit).
- **(D) watchdog backstop(발견 3 연계)**: 단일 워치독 루프가 `ev:done` 후 N분 verdict 부재 감지 시 Verifier wake-ping 재발신 — A/B 실패의 3차 안전망.
- **(E) O12 매-SO 확장**: S10 invariant("마지막 ev=Verifier PASSED")를 phase 내 **매 SO**로 확장 — 모든 SO가 `Verifier verdict=PASSED`(ts>Worker done ts) 보유해야 다음 SO 착수/phase 완료 허용. resume 재감사 시 누락 SO 검출.

---

## 우선순위
1. **발견 4 (worker→verifier 자동 릴레이)** — verdict-integrity, 2 Phase 연속 재발, Supervisor 수동개입 상시 유발. 최우선. 핵심 fix = Worker.prompt에 ev:done 직후 Verifier wake-ping SendMessage 추가(A) + Verifier pull 루프(B).
2. **발견 3 (watchdog 재생성)** — watchdog 자체는 안전상 필수(유지), `.self-wake-ts` dedup으로 재생성만 차단. 발견 4의 backstop(D) 겸함이라 4와 묶어 처리.
3. **발견 1 (SR)** — self-improvement 루프(promotion-log) 단절 + 전략렌즈 손실.
4. **발견 2 (Healer 라우팅)** — verdict-integrity 보조(독립 재검증 우회).

공통 root = "protocol SSOT(wake-ping push·SR 게이트·Healer 9-step·단일 워치독 루프)를 단축경로로 갈음". 특히 발견 4는 push wake-ping이 SSOT인데 Worker.prompt 발신단계 누락이 직접 원인 → 단축이 아니라 **누락**. 단축이 ROI 있으면 명시 허용(skip 조건 codify), 누락/구조 risk는 invariant로 차단 권장.

---

## [추가 2026-05-29 — Phase R SO-3/4 라이브 관찰] 발견 4 증상 심화 (기존 발견 4에 보강)

기존 발견 4는 "Worker가 push wake-ping 발신 단계 누락(passive wait-since만)"으로 봤으나, Phase R SO-3(bb622a9)·SO-4(e41e53c) 실행에서 **증상이 더 심각/복합적**임이 드러남. 3가지 신규 관찰:

**신규-1: Worker가 commit 후 `handoff_key + ev:done` 로깅 자체를 통째로 빼먹고 idle** (push만 누락이 아님).
- 관찰: SO-3·SO-4 둘 다 `git commit`(bb622a9/e41e53c)은 됐는데 execution-log에 ev:done·handoff_key·push 전부 0 → 그냥 idle. **commit이 execution-log 프로토콜보다 앞서 끝남.**
- 함의: ev:done 기반 검증(wait-since, pull 루프 모두 ev:done 의존)이 통째로 무력 — Worker가 done을 안 찍으니 어떤 ev:done-기반 메커니즘도 트리거 안 됨.
- fix: **Worker.prompt에서 commit↔(handoff_key+ev:done+Verifier push) 원자 결합** — "commit 직후 idle 금지, 무조건 done+push까지 완수 후에만 wait-since/idle" 강제. self-relay 경계에서도 done 먼저.

**신규-2: Verifier가 wake 받아도 verdict 완료 전 idle (단발 처리→중단).**
- 관찰: Standby1 push + Supervisor catch-up 둘 다 보냈는데 첫 wake에 verdict 미생성, 반복 ping 후에야 SO-1~4 verdict가 한꺼번에 배치로 append됨. = Verifier가 "wake→일부처리→idle"로 verdict turn을 끝까지 못 감(haiku watchdog 1턴 idle과 동형).
- fix: **role-verifier.txt에 "wake 시 verdict append + SendMessage(to=Supervisor) 완료까지 turn 유지, 미완료 idle 금지" 명문** + 검증 작업(pytest/git)을 verdict까지 원자적으로.

**신규-3: ev:done-기반 검증 < git-commit-기반 검증 (robustness).**
- 신규-1 때문에 ev:done은 신뢰 불가 신호. **Verifier pull 루프를 ev:done 폴이 아니라 `git log --oneline` 폴로 전환** — "SO-N commit 존재 && 그 SO verdict 없음" = 검증 대상. ev:done은 보조. (이번에 Verifier에 git-polling forward-pull 지시했더니 SO-4 잡힘 — 이 방식이 실효.)
- fix: role-verifier.txt pull 루프 기준을 commit-SHA 대조로. Worker done 누락에 영향 안 받음.

**종합**: 발견 4의 fix (A)wake-ping push는 여전히 필요하나, **(신규-1)Worker commit-done 원자결합 + (신규-3)Verifier git-commit 기반 pull**이 더 근본적. ev:done에만 기대면 Worker가 그걸 빼먹는 순간 전체 무력화됨. 현 세션은 Supervisor가 매 SO git HEAD 확인→Verifier에 commit-SHA catch-up으로 수동 우회 중(=신규-3을 사람이 대행).
