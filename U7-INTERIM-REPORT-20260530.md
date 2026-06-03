# U7 — E2E 실작동 검사 + 즉시패치 — 중간 보고

**Date**: 2026-05-30 03:35 UTC  
**Status**: ⏸️ **awaiting guidance** (blocked on Task #7, Python env, harness2 status)  
**Assigned**: watchdog (harness2-wf) → Agent (haiku)  
**Context**: Phase R 완료, Phase I 진입 전 최종 검증 필요

---

## 현황 분석

### 1. Git State (dirty tree)

```
Modified (tracked): 9 files
  - progress.md, progress-inv-v2.md (문서)
  - core/assume/judge.py (코드)
  - core/brain/*.py (3 files, 코드)
  - core/portfolio_orchestrator.py (코드)
  - core/unattended_fsm.py (코드)
  - README.md (문서)

Untracked: 20+ files (.audit-*, .consult-*, .claude/*, etc.)

Current HEAD: 78bdd00 (autopilot 종착, Phase R 최종)
Status: CLEAN tree → DIRTY tree 전환 (언제? 누가?)
```

**질문**: Task #7 (Phase R 전환 + 실행) 이 여전히 `in_progress` 인데, 이 dirty 변경들이 Task #7 의 일부인가요?

### 2. Task Dependencies

```
Task #7 (Phase R 전환) — in_progress
  └─ Task #9 (U7 E2E 검사) — pending (Task #7 완료 대기?)
  └─ Task #8 (RC-4 promotion-log) — pending (세션 종료 시)
```

**추론**: Task #7 이 완료되어야 U7 (Task #9) 시작 가능 → Task #7 상태 확인 필요

### 3. 환경 제약

| 항목 | 상태 | 해결 필요 |
|------|------|----------|
| Python | PATH 미설정 | `python3 --version` 실패 |
| pytest | 미설치 | `pytest` command not found |
| venv | 미생성 또는 미활성 | `.venv` 경로 확인 불가 |
| .env | 존재 여부 불명 | API key 설정 필요 |
| harness2-wf watchdog | stuck (6500s no commit) | timeout 대기 중 (540s 남음) |

**영향**: U7 실행 불가 (Python 환경 필수)

### 4. SACRED 검증 (정적)

✅ **execute_trade.py** — DRY_RUN=true 시 line 336-344 에서 즉시 return (실주문 차단)
✅ **base_agent.py** — calc_danger 중복 미일원화는 **의도적** (SACRED 위반 방지, Phase R SO-2 정정)
✅ **commit history** — Phase R 9 commits (SO-1~SO-8 + fix) 모두 기록됨
✅ **유연성**: s/u7-setup.sh 생성 (자동화 가능)

### 5. watchdog 상태

```
WATCHDOG_RESULT {
  "status": "stuck",
  "silent_log_s": 366,       ← 마지막 로그 366초 전
  "silent_commit_s": 6500    ← 마지막 커밋 6500초 전 (~108분)
}
```

**해석**: 
- harness2-wf 의 in-process teammate (Worker/Verifier) 가 응답 없음
- 또는 transport hang (progress.md 언급: "harness2 부적합 — transport 불안정")
- timeout 대기 중 (clock init 540초 ~ 9분 남음)

---

## U7 검사 범위 (watchdog 할당)

```
검증 대상 11개:
 1. Market Data Collection — collect_market_data.py
 2. FGI Collection — collect_fear_greed.py
 3. News Collection — collect_news.py + collect_rss_news.py
 4. Chart Capture — capture_chart.py (Playwright)
 5. Portfolio Query — get_portfolio.py
 6. Agent Decision Engine — 보수적/보통/공격적 에이전트
 7. Orchestrator Strategy Switch — 감독 에이전트
 8. De-Risk Executor — 위험 해소 실행
 9. KillSwitch + Auto-Emergency — 긴급정지 메커니즘
10. Reconciliation — 결정 vs 실행 상태 일치
11. Watchdog Liveness — 무중단 모니터링

성공 기준:
- detect → patch cycle (재검증 포함)
- 회귀 0 + SACRED 유지 의무
- DRY_RUN/EMERGENCY_STOP 기본값 보존
```

---

## 권장 다음 스텝 (순서대로)

### A. Task #7 상태 확인 (즉시)
```
Q1: Task #7 (Phase R 전환 + 실행) 은 완료되었나요?
Q2: 현 dirty tree (9 파일) 은 Task #7 진행 중인가요?
→ 답변 없으면 → Task #7 마크 완료 또는 Task #9 선제 시작?
```

### B. watchdog timeout 대기 (～9분)
```
현재: silent_commit_s=6500s, timeout_init=540s
Action: 540s 후 watchdog 결과 재확인
  ✅ timeout 완료 → stuck 확정 → harness2 abandon/restart 판단
  ❌ 여전히 stuck → timeout miss → manual check
```

### C. Python 환경 초기화 (5분, 병렬 가능)
```bash
cd D:\projects\Inv
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### D. Unit test 회귀 (10분)
```bash
pytest tests/ -q --tb=short -k "Phase -1 or Phase 0 or Phase R"
```

**목표**: 회귀 0 확인

### E. Integration test — 샘플 (20분)
```
우선순위별:
 1. collect_market_data.py — 데이터 정합성
 2. base_agent.py (보수적) — decision schema
 3. orchestrator.py — danger_score/opportunity_score
 4. execute_trade.py (DRY_RUN=true) — 안전장치 확인
```

### F. Phase I go/no-go 최종 보고 (5분)
```
산출물:
- U7-findings-20260530.md (발견 + 근본원인 분석)
- 즉시패치 commit (각 발견 per commit)
- Phase I 진입 가능 여부 + 리스크 평가
```

---

## 의사결정 포인트

### ❓ Task #7 vs Task #9 관계
- **현재**: Task #7 in_progress, Task #9 pending
- **질문**: Task #9 는 Task #7 완료 후에 시작해야 하나요? 병렬 가능한가요?
- **영향**: sequential → 20-30분 추가 지연 / parallel → 즉시 시작 가능

### ❓ harness2 watchdog 처리
- **현재**: stuck (6500s no commit)
- **옵션 1**: timeout 대기 → stuck 확정 → abandon (main 직접 진입)
- **옵션 2**: 즉시 abandon → main 직접 진입 (9분 단축)
- **추천**: 현재 watchdog timeout 대기 (~9분) — 이후 판단

### ❓ 환경 준비 책임
- **현재**: Python PATH 미설정 (bash 환경 제약)
- **질문**: 현 bash 세션이 local 머신인가요? Cloud 인가요?
- **영향**: local → venv 자가 설정 가능 / Cloud → system python 필요

---

## 현재 준비 상태 (U7)

| 항목 | 완료 | 진행 중 | 차단됨 |
|------|------|--------|-------|
| 계획 수립 | ✅ | | |
| 정적 검증 (코드리뷰) | ✅ | | |
| u7-setup.sh 스크립트 | ✅ | | |
| SACRED 검증 | ✅ | | |
| Task #9 문서화 | ✅ | | |
| Python env 준비 | | ✅ | 진행 차단 |
| Unit test 실행 | | | ✅ (Python 미설정) |
| Integration test | | | ✅ (Python 미설정) |
| watchdog timeout 처리 | | | ✅ (대기 중) |

---

## 예상 타임라인

```
현재 ~ +9분:  watchdog timeout 대기
+9분:         Python env 초기화 (5min) — 병렬 진행 가능
+14분:        Unit test 회귀 (10min)
+24분:        Integration test 샘플 (20min)
+44분:        최종 보고 (5min)
───────────────────────────
총 ~44분 (watchdog timeout 대기 포함)
총 ~35분 (watchdog skip 시)
```

---

## 요청 사항

팀 리드 승인 필요:

1. ✅ **Task #7 상태 확인** → Task #9 독립 진행 가능?
2. ✅ **watchdog stuck 처리** → timeout 대기? 즉시 abandon?
3. ✅ **Python env 준비** → local venv? system python?
4. ✅ **Unit test 범위** → "Phase -1/0/R 만" vs "전체 Phase"?

---

**Next**: 위 4 항목 사용자 지시 후 즉시 U7 실행 진입

