---
tags: [type/handoff, domain/inv, study_id/eq_us, phase/bootstrap, session/btn-jpdf]
date: 2026-05-30
note: btn-jpdf 세션 commodity 종결 + eq_us 전담 전환 부트스트랩. /clear 직후 새 컨텍스트 진입점.
producer: btn-jpdf (commodity → eq_us 전환 시점)
consumer: btn-jpdf 새 컨텍스트 (post /clear)
main_session: btn-Codlearn
---

# btn-jpdf 세션 전환 — commodity 종결 → eq_us 전담

> **/clear 직후 SessionStart 가 본 handoff 를 inject 한 새 컨텍스트는 즉시 §1 부터 수행.**
> 별도 사용자 확인 불필요 (main 자율 시작 지시).

## 1. 첫 행동 (post /clear)

1. `D:/projects/Inv/study-research/eq_us/MAIN-DISPATCH.md` 끝까지 Read
2. eq_kr v2 7-Phase baseline + 6 SSOT + 5금지 숙지
3. **Phase 3 자문 (/gemini-web + /claude-web 3~7R) 부터 자율 시작**
4. direction.md 산출 후 main 승인 대기
5. 회신은 항상 `bash ~/.claude/scripts/lib/psmux-send.sh message btn-Codlearn "..."`

## 2. 직전 commodity 작업 종결 (참조용, 추가 작업 없음)

| 항목 | 상태 |
|---|---|
| `study-research/commodity/study_session.yaml` (7블록 v2) | ★ 완성 — main 감사 3건 반영 + SLEEVE_BLOC A 박제 + small-n caveat 격하 |
| `study-research/commodity/macro-linkage.md` (M3) | ★ 완료 — 4단계 격하 정정 (단정 어휘 제거, p-value/Bonferroni/CI 부착) |
| `study-research/commodity/raw/` (v2 raw 일체) | 보존 |
| `study-research/commodity/raw/v1/` (v1 산출 archive) | 보존 (사용자 명시 폐기 X) |
| register(require_raw=True) | main 별도 처리 (본 방 큐 X) |

**본 방 추가 commodity 큐 없음** — main 명시 확인.

## 3. 세션 환경

- model: opus (long-mode ON, cap 500k, compact/resume 시 auto 원복)
- working directory: `D:/projects/Inv`
- session: btn-jpdf
- 누적 commodity ckpt: progress-study-system.md Working Notes (commodity 종결)

## 4. 누적 학습 (이번 세션 → next)

| 학습 | 위치 | 활용 |
|---|---|---|
| K-202605301150 claude-web no-search prefix | promotion-log | claude-web 자문 호출 시 prefix 적용 |
| K-202605301155 FRED ≠ EIA mirror | promotion-log | FRED ID 가용성 사전 검증 의무 |
| ERROR-202605302200 small-n 점추정 단정 | promotion-log | (★ 신규 rule 적용 의무) |
| **rule** `~/.claude/rules/small-n-statistical-rigor.md` | rules | ★ n<30 panel 통계 claim 5 게이트 (p-value/Bonferroni/CI/hedge/covariance prior 박제 금지) + cross-session ERROR check |

→ ★ eq_us Phase 3 (자문) / Phase 4 (검증) 진입 시 자동 적용.

## 5. 거절 조건 (참고)

main 메시지 quote: "혹시 commodity 미완 큐(register 외) 있으면 거절하고 상태 회신해라".
**판정**: 큐 비어있음 — 거절 X, 진행.

## 6. 외부 자문 호출 (Phase 3 시작 시)

- 라우팅: `/gemini-web` (참신·다른 모델) + `/claude-web` (fresh Opus 실무) 항상 둘 다 병렬 default
- 자기완결 4섹션 브리핑 작성 후 호출 (gemini-web-consult / claude-web-consult skill 참조)
- 결과 raw 는 `D:/projects/Inv/study-research/eq_us/raw/round-N-{claude,gemini}.md` 저장
