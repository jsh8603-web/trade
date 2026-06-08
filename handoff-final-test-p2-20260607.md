---
next-action: harness2.md B2 "병합층 태깅" 반영 마무리 → Worker/Verifier/watchdog spawn(teammate-spawn.sh spawn) → P2A 코드 배선 착수
session: btn-Inv (opus)
date: 2026-06-07
---

# handoff — 최종 테스트 진입: P0/P1 완료 + P2 harness2 진입(SR Pre-Review 완료)

## §1 현재 상태 · 첫 행동
- **완료**: P0(현황 진단) + P1(문서 체계 재편 + 루트 정리) + P2 명세(harness2.md) + P2 SR Pre-Review(mode C).
- **첫 행동(재개)**: (1) `.harness2/harness2.md` B2 SO에 SR directive "자산축은 호출자 병합층 태깅" 한 줄 반영 마무리(A2/A3는 반영 완료) → (2) `bash ~/.claude/skills/harness2-wf/lib/teammate-spawn.sh spawn .harness2 h2-Inv-p2` PLAN대로 Worker/Standby5/Verifier/watchdog dispatch(팀 h2-Inv-p2 이미 생성됨, SR은 on-trigger 잔존) → (3) P2A 코드 배선 착수. harness2 protocol = `~/.claude/skills/harness2-wf/protocol.md`.
- harness2 상태: `.harness2/execution-log.jsonl`(ev:sr_review C 기록됨), `.harness2/harness2.md`(P2 명세), 팀=h2-Inv-p2.

## §2 진행맵 (plan-final-test-20260607.md / progress-final-test-20260607.md)
- P0 ✅ 현황(연결성맵·판정표·진단조사·스모크) / P1 ✅ 문서(README 사용자용 교체·CODEMAP 신설·CLAUDE 운영기준·루트 gitignore+archive)
- P2 ▶ 진행중: 명세+SR Pre-Review 완료, Worker dispatch 직전. P2A(entry 배선 6 SO)+P2B(진단 5삽입)
- P3 테스트1(10년 in-sample + 1~2년 OOS) / P4 모의 라이브 / P5a·b 자기진화. 실행순 P0→P1→P2→P5a→P3→P4→P5b

## §3 사용자 박제 (대화 고유 결정)
- **자율 flag ON** (`agent/.secretary/.autopilot-btn-Inv.flag`). 끝까지 자율. 원칙: 사용자 의도(구현된 대로 테스트 완주) 보존 + 기존 코드 의도 확인 후 왜곡 금지(버그 판정 시 수정 OK).
- **teammate 동시 ≤5** (사용자 상향). 코드 작업=harness2(장수명), 1회성 수집·문서=subagent.
- **한투 모의계좌 = 실거래 연결 승인** (e2e 실매매 자유, KIS paper=True).
- **LLM 3층**(P3-1): 10년=전부 off 결정론 / 1~2년=on·off A/B(golden hash diff) / 카드·하이쿠=샘플 동작검증. 10년 전체 LLM 실호출 금지(비용·replay 불변식).
- **per-asset attribution**(사용자 핵심): 자산별(코인 개별·**주식 섹터/sleeve eq_us·eq_kr 7산업까지**·자산군) passive 대비 excess. 장기 음수 자산=신호 결함(전체 평균에 안 묻힘). self-ref base 금지(∑excess≡0).
- **문제 시그널 3차 게이트**: 발견(4층 미달)→확정(p·Newey-West·block-bootstrap·walk-forward 부호일관)→귀속(L0~L3 시그널표). 단일측정 단정 금지.
- **레이어 5+1단계**: L0배선/L1이론·yaml/L2a코드/L2b데이터·PIT/L2c상수/L3a LLM계약/L3b LLM판단. (사용자 3단계 세분화)
- **진단 로깅 top-down**: bar×asset×stage×layer 최대분해 깔되, 자산별 집계 먼저→문제 자산 drill-down→레이어 귀속.

## §4 파일 inventory (절대경로 D:/projects/Inv/)
- 산출: `plan-final-test-20260607.md`(SSOT plan), `progress-final-test-20260607.md`, `CODEMAP.md`(코드색인·디버깅 진입), `README.md`(사용자용 교체), `CLAUDE.md`(운영기준 재작성), `docs/legacy-coinbot.md`(레거시 보존)
- harness2: `.harness2/harness2.md`(P2 명세), `.harness2/execution-log.jsonl`, `.harness2/harness2-eqstudy-bak.md`(이전 백업)
- 진단 근거: `.p0-connectivity-map.md`(배선·L0 10건), `.p2b-diag-infra-survey.md`(진단 삽입점 5), `.p2-smoke-readiness.md`(replay 즉시가능·DRY_RUN 안전), `.p0-root-cleanup-plan.md`(정리 판정표)
- git status 깔끔(10개 변경, 신규 CODEMAP/legacy + 수정 README/CLAUDE/.gitignore). **커밋 보류**(사용자 명시 요청 시, push 금지).

## §5 미해결 · 실패 (삽질 방지)
- **harness2.md B2** "병합층 태깅" 한 줄 미반영(A2/A3 SR directive는 반영 완료).
- **harness2 Worker 미spawn** — SR Pre-Review C까지만. spawn은 teammate-spawn.sh spawn PLAN 경유(raw Agent 금지).
- **tracked .consult-kr-*(11)·.consult-r15-*(6)·.py 2개** = 루트정리 중 복구함(git 자산). archive 이동은 P2~P4 후 최종 커밋 때 사용자 확인.
- **teams/ 에 이전 잔재 다수**(inv-wire·kr-equity 등) — leader 교착 시 protocol O13 unblock-leader.
- KIS 주식 키 `.env.example`에 없음 — P2A SO-5 모의 왕복 시 추가 필요.

## §6 자문 종합 (SR Pre-Review mode C, ev:sr_review 기록)
SR이 thin wiring 치명 결함 3개 코드라인까지 적발(ignite=true, A2:5 A3:5):
1. **stock 무음 hold**: `stock_track.generate_candidate`=dict(line165) vs engine `getattr(decision,action)`(line439) → stock 항상 hold. → A2 track-어댑터(dict→Decision, action!=hold 단언) **ACCEPT**.
2. **멀티에셋 게이트 미발동**: engine `avg_correlation=0.0`/`sector_weight=current_weight` 하드코딩(line489,493) → corr_cap/max_weight_sector 영구 미발동. → A3 corr/sector 게이트를 A1 호출자 합산층에서 risk_gate.check 재호출(engine 단일루프 0.0은 per-asset 격리) **ACCEPT**.
3. **drill-down 위치**: B2 자산축 태깅은 engine(단일 asset) 아닌 호출자 병합층 **ACCEPT**(반영 마무리 필요).
- Type A(비전) "attribution-bus-first"(자산×단계×레이어 단일 이벤트버스 먼저, entry는 첫 소비자) = **DEFER**(B2 병합층 태깅으로 부분 흡수, 전면 도입은 P2 범위확대라 보류).
