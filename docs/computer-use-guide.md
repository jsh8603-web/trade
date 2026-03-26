# Claude Computer Use 완전 가이드

> 작성일: 2026-03-26 | Claude Code 기반 자동매매 시스템용

---

## 1. 개요

Claude Computer Use는 Claude가 데스크톱 환경과 직접 상호작용하는 기능이다.
스크린샷 캡처 → AI 분석 → 마우스/키보드 조작의 에이전트 루프로 작동한다.

**2026년 3월 23-24일** 연구 프리뷰 출시 (macOS 전용).

---

## 2. 두 가지 구현 방식

### A. Claude Desktop (소비자용 — 우리가 사용할 방식)

| 항목 | 내용 |
|------|------|
| **위치** | Claude Desktop 앱 > Code 탭 |
| **요구사항** | macOS, Claude Pro 또는 Max 구독 |
| **활성화** | Settings > Desktop app > General > "Computer use" 토글 ON |
| **macOS 권한** | Accessibility(클릭/타이핑) + Screen Recording(화면 캡처) |
| **Dispatch** | iPhone에서 작업 지시 → Mac에서 실행 |

**앱 권한 등급:**
- 브라우저: 보기 전용 (view-only)
- 터미널/IDE: 클릭만 (click-only)
- 기타 앱: 전체 제어 (full control)

### B. Claude API (개발자용)

| 항목 | 내용 |
|------|------|
| **위치** | Messages API (`api.anthropic.com/v1/messages`) |
| **요구사항** | API 키 + Docker/VM 환경 |
| **실행** | 개발자가 에이전트 루프 직접 구현 |
| **Claude 역할** | tool_use 요청만 전송, 실제 실행은 개발자 코드 |

---

## 3. 모델 호환성 & Beta 헤더

| 모델 | 도구 버전 | Beta 헤더 |
|------|----------|----------|
| **Opus 4.6, Sonnet 4.6, Opus 4.5** | `computer_20251124` | `computer-use-2025-11-24` |
| Sonnet 4.5, Haiku 4.5, Opus 4.1, Sonnet 4, Opus 4, Sonnet 3.7 | `computer_20250124` | `computer-use-2025-01-24` |

⚠️ 구 버전 도구는 신규 모델과 호환되지 않음. 반드시 모델에 맞는 도구 버전 사용.

---

## 4. 도구 정의 (Schema-less)

Computer Use 도구는 **스키마 불필요** — 모델 내장.

```json
{
  "type": "computer_20251124",
  "name": "computer",
  "display_width_px": 1024,
  "display_height_px": 768,
  "display_number": 1,
  "enable_zoom": true
}
```

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| `type` | ✅ | `computer_20251124` / `computer_20250124` / `computer_20241022` |
| `name` | ✅ | 반드시 `"computer"` |
| `display_width_px` | ✅ | 디스플레이 너비 (픽셀) |
| `display_height_px` | ✅ | 디스플레이 높이 (픽셀) |
| `display_number` | ❌ | X11 디스플레이 번호 |
| `enable_zoom` | ❌ | 줌 액션 활성화 (`computer_20251124`만). 기본값: `false` |

---

## 5. 지원 액션 전체 목록

### 기본 액션 (모든 버전)

| 액션 | 설명 | 파라미터 |
|------|------|---------|
| `screenshot` | 현재 화면 캡처 | 없음 |
| `left_click` | 좌클릭 | `coordinate: [x, y]` |
| `right_click` | 우클릭 | `coordinate: [x, y]` |
| `middle_click` | 가운데 클릭 | `coordinate: [x, y]` |
| `double_click` | 더블클릭 | `coordinate: [x, y]` |
| `type` | 텍스트 입력 | `text: "문자열"` |
| `key` | 키/조합 입력 | `text: "ctrl+s"` |
| `mouse_move` | 커서 이동 | `coordinate: [x, y]` |
| `left_click_drag` | 드래그 | `start_coordinate`, `coordinate` |
| `cursor_position` | 커서 위치 조회 | 없음 |

### 확장 액션 (`computer_20250124`+)

| 액션 | 설명 | 파라미터 |
|------|------|---------|
| `scroll` | 스크롤 | `coordinate`, `scroll_direction`, `scroll_amount` |
| `triple_click` | 트리플 클릭 | `coordinate: [x, y]` |
| `left_mouse_down` | 마우스 버튼 누름 | `coordinate: [x, y]` |
| `left_mouse_up` | 마우스 버튼 해제 | `coordinate: [x, y]` |
| `hold_key` | 키 홀드 | `text: "key"`, `duration: seconds` |
| `wait` | 대기 | `duration: seconds` |

### 최신 액션 (`computer_20251124`)

| 액션 | 설명 | 파라미터 |
|------|------|---------|
| `zoom` | 화면 영역 확대 (고해상도) | `region: [x1, y1, x2, y2]` |

---

## 6. 액션 JSON 예시

```json
// 스크린샷
{ "action": "screenshot" }

// 좌표 클릭
{ "action": "left_click", "coordinate": [500, 300] }

// 텍스트 입력
{ "action": "type", "text": "Hello, world!" }

// 스크롤
{
  "action": "scroll",
  "coordinate": [500, 400],
  "scroll_direction": "down",
  "scroll_amount": 3
}

// 화면 영역 줌 (Opus 4.5/4.6만)
{ "action": "zoom", "region": [100, 200, 400, 350] }

// 수정 키 + 클릭 (Shift+클릭)
{ "action": "left_click", "coordinate": [500, 300], "text": "shift" }

// 키 조합
{ "action": "key", "text": "ctrl+c" }

// 드래그
{
  "action": "left_click_drag",
  "start_coordinate": [100, 200],
  "coordinate": [300, 400]
}
```

**수정 키 값:** `shift`, `ctrl`, `alt`, `super` (Cmd/Windows)

---

## 7. API 호출 코드

### Python (anthropic SDK)

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=[
        {
            "type": "computer_20251124",
            "name": "computer",
            "display_width_px": 2560,
            "display_height_px": 1080,
            "display_number": 1,
            "enable_zoom": True,
        },
        {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
        {"type": "bash_20250124", "name": "bash"},
    ],
    messages=[
        {"role": "user", "content": "NordVPN 앱에서 Meshnet을 활성화해줘."}
    ],
    betas=["computer-use-2025-11-24"],
)
```

### HTTP 헤더

```
Content-Type: application/json
X-API-Key: $ANTHROPIC_API_KEY
anthropic-version: 2023-06-01
anthropic-beta: computer-use-2025-11-24
```

---

## 8. 에이전트 루프 패턴

```python
import anthropic
import base64
import subprocess

client = anthropic.Anthropic()
messages = [{"role": "user", "content": "작업 지시"}]

tools = [
    {
        "type": "computer_20251124",
        "name": "computer",
        "display_width_px": 2560,
        "display_height_px": 1080,
    }
]

MAX_ITERATIONS = 30

for i in range(MAX_ITERATIONS):
    response = client.beta.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        tools=tools,
        messages=messages,
        betas=["computer-use-2025-11-24"],
    )

    # 응답을 메시지에 추가
    messages.append({"role": "assistant", "content": response.content})

    # tool_use 블록 처리
    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            result = execute_computer_action(block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    # 도구 호출 없으면 완료
    if not tool_results:
        break

    messages.append({"role": "user", "content": tool_results})


def execute_computer_action(input_data):
    """Claude의 computer use 요청을 실제 실행"""
    action = input_data.get("action")

    if action == "screenshot":
        subprocess.run(["screencapture", "-x", "/tmp/cu_screen.png"])
        with open("/tmp/cu_screen.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        return [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            }
        }]

    elif action == "left_click":
        x, y = input_data["coordinate"]
        subprocess.run(["cliclick", f"c:{x},{y}"])
        return "Click executed"

    elif action == "type":
        text = input_data["text"]
        subprocess.run(["cliclick", f"t:{text}"])
        return "Type executed"

    elif action == "key":
        key = input_data["text"]
        # cliclick key mapping needed
        subprocess.run(["cliclick", f"kp:{key}"])
        return "Key pressed"

    elif action == "scroll":
        # AppleScript or cliclick scroll
        direction = input_data.get("scroll_direction", "down")
        amount = input_data.get("scroll_amount", 3)
        return f"Scrolled {direction} {amount}"

    return f"Unknown action: {action}"
```

---

## 9. 스크린샷 반환 형식

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "<base64-encoded-screenshot>"
          }
        }
      ]
    }
  ]
}
```

**이미지 제약:**
- 최대 5MB
- 최장 변 1568px
- 총 ~1.15 메가픽셀

---

## 10. 좌표 시스템 & 스케일링

좌표는 왼쪽 상단 (0,0) 기준 픽셀 단위 `[x, y]`.

```python
import math

def get_scale_factor(width, height):
    """API 이미지 제약에 맞는 스케일 팩터 계산"""
    long_edge = max(width, height)
    total_pixels = width * height
    long_edge_scale = 1568 / long_edge
    total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
    return min(1.0, long_edge_scale, total_pixels_scale)

# Mac Mini: 2560x1080
scale = get_scale_factor(2560, 1080)  # ≈ 0.613

# 스크린샷 리사이즈: 2560×1080 → 1568×662
# Claude 좌표를 실제 좌표로 변환:
def to_screen(x, y):
    return int(x / scale), int(y / scale)
```

**권장 스케일링 해상도:**

| 이름 | 해상도 | 비율 |
|------|--------|------|
| XGA | 1024×768 | 4:3 |
| WXGA | 1280×800 | 16:10 |
| FWXGA | 1366×768 | ~16:9 |
| Mac Mini 스케일 | 1568×662 | 21:9 |

---

## 11. Claude Desktop에서 활성화하는 방법

### 단계별 설정

1. **Claude Desktop** 앱 실행 (Mac Mini에 이미 설치됨)
2. **Settings** (설정) 열기 — 좌측 하단 기어 아이콘 또는 Cmd+,
3. **Desktop app** → **General** 섹션
4. **"Computer use"** 토글 **ON**
5. macOS 시스템 설정에서 두 가지 권한 부여:
   - **시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용** → Claude 추가
   - **시스템 설정 > 개인정보 보호 및 보안 > 화면 기록** → Claude 추가
6. Claude Desktop 재시작

### Dispatch (iPhone → Mac 원격 실행)

1. iPhone의 Claude 앱에서 작업 지시
2. Mac의 Claude Desktop이 computer use로 실행
3. 결과를 iPhone으로 반환

---

## 12. Claude Code CLI에서의 활용 방법

Claude Code CLI 자체에는 computer use가 내장되어 있지 않다. 하지만 다음 방법으로 우회 가능:

### 방법 1: API 직접 호출 (Python 스크립트)

위 섹션 7-8의 에이전트 루프를 Python 스크립트로 구현.
`cliclick` + `screencapture`로 macOS 데스크톱 조작.

### 방법 2: MCP 서버 활용

| MCP 서버 | 기능 |
|---------|------|
| **Puppeteer** (이미 설치됨) | 브라우저 자동화 (navigate, screenshot, click, fill) |
| **mcp-desktop-automation** | RobotJS 기반 마우스/키보드/스크린샷 |
| **DesktopCommanderMCP** | 터미널 제어, 파일 시스템 |

### 방법 3: Claude Desktop과 파이프라인 연동 (권장)

```
Claude Code CLI (RC/iPhone)
    ↓ 작업 지시 (텍스트)
Claude Desktop (Mac Mini)
    ↓ Computer Use 실행
    ↓ 스크린샷 + 클릭 + 타이핑
결과 반환
    ↓ 텔레그램 알림 또는 파일 저장
```

---

## 13. 파이프라인 설계: Claude Code → Claude Desktop Computer Use

### 아키텍처

```
[사용자 (iPhone RC)]
        ↓ 텍스트 명령
[Claude Code CLI (터미널)]
        ↓ Python 스크립트 실행
[computer_use_agent.py]
        ↓ Anthropic API 호출 (beta: computer-use-2025-11-24)
        ↓ screencapture → base64 → API 전송
        ↓ API 응답 → cliclick/osascript 실행
        ↓ 결과 스크린샷 → API 전송 (반복)
[실제 Mac 데스크톱 조작]
        ↓ 완료
[텔레그램 알림 / 결과 파일 저장]
```

### 핵심 컴포넌트

1. **`scripts/computer_use_agent.py`** — 에이전트 루프 메인
2. **`scripts/cu_executor.py`** — 액션 실행기 (cliclick, screencapture, osascript)
3. **`scripts/cu_pipeline.sh`** — CLI 래퍼 (자연어 명령 → agent 실행)

---

## 14. 동반 도구 (Companion Tools)

Computer Use와 함께 사용하면 효과적인 도구:

| 도구 | 버전 | 용도 |
|------|------|------|
| `bash` | `bash_20250124` / `bash_20250728` | 셸 명령 실행 |
| `text_editor` | `text_editor_20250728` / `text_editor_20250124` | 파일 편집 (str_replace) |
| `computer` | `computer_20251124` | 데스크톱 조작 |

---

## 15. 가격

| 항목 | 비용 |
|------|------|
| 시스템 프롬프트 오버헤드 | 466-499 토큰 |
| 도구 정의 | 735 토큰 (computer use 1개당) |
| 스크린샷 이미지 | Vision 가격 (이미지 크기별) |
| Opus 4.6 토큰 | 입력 $5 / 출력 $25 (MTok당) |
| Sonnet 4.6 토큰 | 입력 $3 / 출력 $15 (MTok당) |
| Haiku 4.5 토큰 | 입력 $1 / 출력 $5 (MTok당) |

⚠️ Beta 기간 중 Zero Data Retention (ZDR) 미지원

---

## 16. 안전 고려사항

1. **전용 VM/컨테이너** 사용 권장 (최소 권한)
2. **민감 데이터 접근 제한** — 계정 비밀번호 노출 주의
3. **인터넷 접근 제한** — 허용 도메인만 화이트리스트
4. **금융 거래 시 인간 확인 필수** — 매매 실행 전 승인
5. **프롬프트 인젝션 방어** — 스크린샷 내 악의적 텍스트 감지
6. **권한 우선 모델** — Claude가 새 앱 접근 시 사용자에게 먼저 질문

---

## 17. 알려진 제한사항

1. **지연 시간** — 사람보다 느림, 백그라운드 작업에 적합
2. **좌표 정확도** — 가끔 좌표 환각 발생
3. **스크롤** — 20250124에서 개선되었지만 완벽하지 않음
4. **스프레드시트** — 세밀한 마우스 제어가 어려움
5. **SNS 계정** — 계정 생성/콘텐츠 생성 제한
6. **macOS 전용** — Windows/Linux 미지원 (Desktop)

---

## 18. 참고 자료

| 자료 | URL |
|------|-----|
| 공식 문서 | https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool |
| Anthropic 블로그 | https://claude.com/blog/dispatch-and-computer-use |
| 레퍼런스 구현 | https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo |
| Claude Desktop 문서 | https://code.claude.com/docs/en/desktop |
| 피드백 양식 | https://forms.gle/H6UFuXaaLywri9hz6 |

---

## 19. 우리 시스템에서의 활용 계획

### 즉시 가능한 활용

1. **NordVPN GUI 조작** — VPN 연결/해제, Meshnet 설정 (오늘 수동으로 한 작업 자동화)
2. **차트 캡처 자동화** — Playwright 대신 실제 Upbit 앱/웹에서 캡처
3. **시스템 설정 자동화** — macOS 설정 변경, 앱 설정 조정
4. **Google Chrome 원격 데스크톱** — 원격 관리 자동화

### 파이프라인 통합

```
cron_run.sh
  ↓
run_agents.sh (매매 결정)
  ↓
computer_use_agent.py (필요 시 GUI 조작)
  ↓
notify_telegram.py (결과 보고)
```
