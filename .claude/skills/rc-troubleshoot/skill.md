---
name: rc-troubleshoot
description: Claude Code Remote Control(RC) 설정, 진단, 복구 스킬. iPhone Claude 앱에서 원격 세션 연결이 안 될 때 사용.
version: 1.0.0
tags:
  - Remote Control
  - RC
  - iPhone
  - 원격 세션
  - 트러블슈팅
---

# rc-troubleshoot 스킬

Claude Code Remote Control을 iPhone Claude 앱에서 사용하기 위한 설정 및 트러블슈팅 가이드.

## RC란?

Claude Code CLI에서 `/remote-control` (또는 `/rc`)을 실행하면 원격 세션이 생성된다. 이 세션을 iPhone/iPad의 Claude 앱에서 열어 원격으로 Claude Code를 사용할 수 있다.

## RC 작동 조건 (3가지 모두 필수)

### 1. OAuth 로그인

RC는 **claude.ai 계정 OAuth 인증**이 필수다. API 키 인증으로는 동작하지 않는다.

```bash
# 셸에서 직접 실행 (Claude Code 세션 밖에서)
unset CLAUDECODE && claude auth login
```

- 브라우저가 열리면 claude.ai 계정으로 로그인/승인
- `Login successful.` 메시지 확인
- 토큰은 이후 자동 유지됨

**확인 방법:**
- `~/.claude/.credentials` 파일 존재 여부 (OAuth 시 생성)
- 또는 macOS 키체인에 `claude-code` 항목 존재 여부

### 2. Claude Code 최신 버전 (v2.1.78+)

구버전(v2.1.69 등)에서는 OAuth 로그인 후에도 세션 ID 불일치로 RC가 실패한다.

```
# 디버그 로그에서 이런 에러가 나오면 버전 문제:
Rejecting foreign session: expected=session_... got=cse_...
```

**버전 확인 및 업데이트:**
```bash
# 현재 버전 확인
claude --version

# PATH에서 어떤 바이너리가 잡히는지 확인
which claude
# ~/.local/bin/claude 가 먼저 잡힐 수 있음

# 설치된 최신 버전 확인
/opt/homebrew/bin/claude --version  # homebrew
npm list -g @anthropic-ai/claude-code  # npm

# ~/.local/bin이 구버전에 고정되어 있으면 심볼릭 링크 업데이트
ln -sf /opt/homebrew/bin/claude ~/.local/bin/claude
```

**PATH 우선순위 주의:**
```
~/.local/bin          ← 여기가 먼저 잡힘 (구버전 고정 가능)
/opt/homebrew/bin     ← npm update로 최신 설치
```

### 3. iPhone Claude 앱 동일 계정

Mac에서 `claude auth login`한 계정과 iPhone Claude 앱의 로그인 계정이 동일해야 한다.

## 진단 흐름

### Step 1: RC 상태 확인

```bash
# tmux에서 RC 화면 캡처
tmux capture-pane -t "blockchain:1" -p -S -5 | grep -i "remote"
# "Remote Control active" 표시 확인
```

### Step 2: 디버그 로그 확인

```bash
# 최신 디버그 파일
LATEST=$(ls -t ~/.claude/debug/*.txt | head -1)

# Transport 문제 확인
grep -i "transport" "$LATEST" | tail -5
```

| 로그 메시지 | 원인 | 해결 |
|------------|------|------|
| `Transport not configured, dropping messages` | OAuth 미로그인 | `claude auth login` |
| `Rejecting foreign session: expected=session_ got=cse_` | 구버전 (v2.1.69) | 버전 업데이트 |
| `Session created: session_...` + `Ready: env=...` | 정상 | — |
| `authentication_error: no OAuth token` | OAuth 토큰 만료 | `claude auth login` 재실행 |

### Step 3: 네트워크 연결 확인

```bash
# Claude Code 프로세스의 외부 연결 확인
PID=$(pgrep -f "claude.*dangerously" | head -1)
lsof -a -i -p $PID | grep ESTABLISHED
# Anthropic 서버 (160.79.x.x 또는 34.149.x.x)로의 연결이 있어야 함
```

## 전체 설정 절차 (처음부터)

```bash
# 1. OAuth 로그인
unset CLAUDECODE && claude auth login

# 2. 버전 확인
claude --version  # 2.1.78+ 필요

# 3. Claude Code 시작
unset CLAUDECODE && claude --dangerously-skip-permissions

# 4. RC 시작 (세션 내에서)
/remote-control
# → "Remote Control connecting..."
# → "/remote-control is active. Code in CLI or at https://claude.ai/code/session_..."

# 5. 세션 URL 저장
# remote_url.txt에 자동 기록 (watchdog 또는 startup.sh)

# 6. iPhone Claude 앱에서 확인
# → 좌측 사이드바에 컴퓨터 아이콘 + 초록 점으로 세션 표시
```

## startup.sh에서 RC 자동 설정

현재 문제: Claude 초기화 15초 대기 → `/rc` → 60초 URL 폴링 → 타임아웃

**개선 포인트:**
- Claude 초기화 대기: 15초 → 30초
- URL 캡처 타임아웃: 60초 → 120초
- URL grep 패턴: `session_[A-Za-z0-9]*` (현재 패턴 유지)

```bash
# startup.sh 핵심 부분 (개선안)
sleep 30  # Claude 초기화 충분히 대기
tmux send-keys -t "$TMUX_SESSION:claude" "/remote-control" Enter
sleep 2
tmux send-keys -t "$TMUX_SESSION:claude" Enter  # 자동완성 메뉴 선택

MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 5
    WAITED=$((WAITED + 5))
    PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_SESSION:claude" -p -S -30 2>/dev/null)
    REMOTE_URL=$(echo "$PANE_OUTPUT" | grep -o 'https://claude.ai/code/session_[A-Za-z0-9]*' | tail -1)
    if [ -n "$REMOTE_URL" ]; then
        echo "$REMOTE_URL" > "$REMOTE_URL_FILE"
        break
    fi
done
```

## watchdog_remote.sh 연동 (v5)

워치독이 문제 감지 시 **이 스킬의 진단 체크리스트를 자동 실행**한다.

### 자동 진단 함수: `run_rc_diagnostics`

문제 발생 시 아래 4가지를 순서대로 검사하고 텔레그램으로 결과 전송:

1. **버전 검증** (`check_claude_version`) — v2.1.78 미만이면 심볼릭 링크 자동 수정
2. **OAuth 검증** (`check_oauth`) — 디버그 로그에서 `Transport not configured` 감지
3. **세션 ID 검증** — `Rejecting foreign session` 감지
4. **URL 유효성** — `remote_url.txt`가 "pending"이면 실패

### 호출 시점

| 상황 | 호출 |
|------|------|
| `fast_restart` 실패 | `run_rc_diagnostics("fast_restart failed")` |
| `full_rebuild` 전 | `run_rc_diagnostics("before full_rebuild")` + `check_claude_version` |
| `no_oauth` 감지 | `run_rc_diagnostics("no_oauth detected")` |

### 자동 수정 가능한 것

- **버전 문제**: `~/.local/bin/claude` → `/opt/homebrew/bin/claude` 심볼릭 링크 자동 업데이트
- **킵얼라이브**: 4분 간격 Space+BSpace 전송

### 수동 개입 필요한 것

- **OAuth 만료**: 브라우저 인증 필요 → 텔레그램 알림 전송
  ```
  ⚠️ RC Transport 미연결
  Mac에서 수동 실행 필요:
  unset CLAUDECODE && claude auth login
  ```

## 트러블슈팅 체크리스트

- [ ] `claude auth login` 완료 (`Login successful.`)
- [ ] `claude --version` → v2.1.78 이상
- [ ] `~/.local/bin/claude` → `/opt/homebrew/bin/claude` 심볼릭 링크
- [ ] iPhone Claude 앱 동일 계정 로그인
- [ ] 디버그 로그에 `Transport not configured` 없음
- [ ] 디버그 로그에 `Rejecting foreign session` 없음
- [ ] 디버그 로그에 `Session created` + `Ready` 있음

## RC "reconnecting" 무한 루프 문제

RC가 한번 끊기면 "Remote Control reconnecting" 상태가 **몇 시간째 지속**되며 자동 복구 안 됨.

**원인**: Claude Code의 RC 자동 재연결은 성공률이 낮음 (WebSocket 세션 만료).
**해결**: reconnecting이 감지되면 **세션 종료 → 새 세션 시작 → /remote-control**이 유일한 방법.

워치독 v5에서 "reconnecting" 감지 → `fast_restart` 자동 실행.

## 워치독 윈도우 감시 문제 (v5 해결)

**문제**: tmux에 여러 claude 세션이 있을 때, 워치독이 **잘못된 윈도우**를 감시할 수 있음.
- 윈도우 0: OAuth 세션 (reconnecting 상태) ← 이걸 봐야 함
- 윈도우 1: 구버전 세션 (active 표시, Transport 없음) ← 이걸 보고 "healthy" 판정

**해결 (v5)**: `find_rc_window()` — 윈도우 이름 대신 **모든 윈도우를 순회**하여 RC 상태가 있는 윈도우를 동적 탐색. "active" 우선, "reconnecting" 차선.

## 장애 이력

| 날짜 | 증상 | 원인 | 해결 |
|------|------|------|------|
| ~2026-03-19 | RC "active" 표시되나 iPhone 앱에 세션 안 뜸 | OAuth 미로그인 + 구버전 v2.1.69 | `claude auth login` + 심볼릭 링크 v2.1.78 |
| 2026-03-20 | 6시간 방치 후 "reconnecting" 무한 루프 | RC 자동 재연결 실패 + 워치독이 잘못된 윈도우 감시 | 세션 재시작 + watchdog v5 동적 윈도우 감지 |
| 지속 | startup.sh에서 URL 캡처 항상 실패 | 초기화 대기 15초 부족 | 30초로 증가 완료 |
