---
tags: [handoff, inv, phase1, harness2, autocompact]
date: 2026-05-28
---

# Handoff — Inv Phase 1 두뇌 마이그레이션 (메인 재시작 인계)

> 작성: 2026-05-28, ctx 540k 도달로 메인 앱 재시작 직전. 재시작 후 이 문서 + progress.md ckpt-202605282235 로 재개.

## 1. 현재 상태

- **Phase 0 완료**: SO-1~5 PASS, 43 tests, commit 0eba44c(SO-5)까지. Sufficiency PASS.
- **Phase 1 진행 중**: SO-1 완료(commit **d4ba414** "LLMProvider abstraction + LLMRouter with OAuth-only Claude"). SO-2~6 미착수.
- **팀**: h2wf-Inv-p0 (Phase 0 에서 스폰, Phase 1 이어감). Worker(Phase0 완료모드)→Standby1 승계로 SO-1 마무리.

## 2. 이번 세션 핵심 사건 — teammate ctx limit hard stop

- **증상**: Phase 1 SO-1 작업 중이던 Worker(teammate)가 "Context limit reached · /compact or /clear to continue" 로 멈춤. execution-log 에 Phase1 Worker ev 없어서 처음엔 "완료모드 무응답"으로 **오진** → 사용자가 화면(pytest 2 PASS + Context limit reached) 제시로 정정.
- **근본 원인**: settings.json `"autoCompactEnabled": false`. 이게 전역이라 teammate(sonnet)도 상속 → teammate auto-compact 안 됨 → ctx 초과 시 hard stop. teammate 는 운영 규약상 /compact 금지라 스스로 못 풀고 멈춤.
- **왜 self-relay(turn) 가 못 막았나**: turn≥50 self-relay 는 **commit 경계** 조건. SO-1 이 무거워서(llm_provider 232줄 + test 167줄 16개 + pytest 출력) **첫 commit 전에 ctx limit 도달**. teammate 는 ctx 못 봐서(CTX-INVISIBLE) turn 휴리스틱만 의존하는데 그게 ctx 를 못 앞지름.

## 3. 설계 결정 (사용자 확정)

- **자동압축 = 메인 안전장치(fallback), 휴리스틱(self-relay) = 보조**. 자동압축이 꺼져 있어서 안전장치가 없던 게 문제.
- **(A) autoCompactEnabled: true** (전역). 메인(opus 1M)은 압축 임계가 멀고 ctx-warn hook 이 먼저 수동 관리하니 영향 미미. teammate(sonnet)는 ctx 차기 전 auto-compact 로 살아남음.
- **(B) turn 임계 SOFT30/HARD50** (구 50/75). 무거운 SO 대비 보조 예방.
- **기각 대안**: (B)만(autoCompact 유지 false) — teammate hard stop 재발 위험으로 기각. teammate별 auto-compact 설정 — 불가(claude-code-guide 확인, 전역 필드만).

## 4. 모델/서비스 구성 (Phase 1 확정)

- **quick** = Ollama Qwen(qwen3-coder, localhost:11434, D:\ollama 18G). ollama.exe PATH 미등록, curl localhost:11434/api/tags 로 확인.
- **deep** = Claude Max **OAuth**(~/.claude/.credentials.json claudeAiOauth.accessToken). ⚠️ **anthropic SDK `Anthropic(api_key=token)` 은 x-api-key 헤더로 덮어써서 OAuth 불가 → urllib 직접 HTTP `Authorization: Bearer` 방식**(SO-1 d4ba414 에서 발견·수정, SO-6 llm_worker 재사용 시 동일 적용). Max quota, ⛔API key sk-ant-api 금지.
- **임베딩** = da embed 서비스 재사용(127.0.0.1:8787 /embed, BGE-m3 1024, ONNX-DML GPU, parity 1.0). ⛔신규 ollama BGE 금지(사용자 검토 확정). /rerank(bge-reranker-v2-m3) 보너스.
- ollama Qwen·Claude OAuth·da 8787 = 실호출 검증 가능. Supabase/Gemini = mock(.env 없음).

## 5. 재시작 후 재개 절차 (순서대로)

1. **settings 적용 확인**: autoCompactEnabled=true (재시작으로 로드됨).
2. **기존 팀 정리**: `bash ~/.claude/skills/harness2-wf/lib/teammate-spawn.sh unblock-leader h2wf-Inv-p0` → TeamDelete tool 1회(leader 제약 해소).
3. **팀 재스폰**: TeamCreate h2wf-Inv-p0 → `bash ~/.claude/skills/harness2-wf/lib/teammate-spawn.sh spawn D:/projects/Inv/.harness2 h2wf-Inv-p0` PLAN → Agent 8(VERBATIM). ⛔ build 재실행 시 Worker.prompt SACRED=vaultvoice 잔재 재교체 필요(이미 교체돼 있으면 spawn 만). turn 30/50·autoCompact true 자동 적용.
4. **resume_baseline 갱신**: `h2-log.sh append` 로 remaining=[SO-2,SO-3,SO-4,SO-5,SO-6] phase:1 (SO-1 done 반영).
5. **Verifier SO-1 verdict 확인**: execution-log 에 SO-1(phase1, ts>1779976304263) verdict 있는지. 없으면 Verifier 에 SO-1(d4ba414) 검증 지시.
6. **SO-2 진행**: embedder.py(core/brain/) — da 8787 /embed HTTP 래핑 + Gemini 폴백. taskspec-phase-1.txt SO-2 참조.

## 6. 미해결/주의

- promotion-log K 보강 필요: ① teammate auto-compact off = hard stop 근본원인(settings 전역) ② unblock-leader 함수화(이전 ckpt) ③ turn 임계 30/50.
- harness2 구조 교훈: 무거운 SO 는 granularity invariant(commit-to-commit ~10 tool-call) 위반 → SO 입도 축소 + 중간 체크포인트 커밋 권장.
- 설계 SSOT: IMPLEMENTATION_PROMPT.md §Phase1(L276)·§0.6-A, implementation-keys.md §4·§7, .harness2/taskspec-phase-1.txt, .harness2/harness2.md(Phase1 표).
