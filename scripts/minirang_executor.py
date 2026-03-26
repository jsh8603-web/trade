#!/usr/bin/env python3
"""
미니랑(MiniRang) Executor — Computer Use 액션을 macOS 명령으로 변환

cliclick + screencapture + osascript로 Mac Mini 데스크톱을 조작한다.
"""

import base64
import math
import os
import subprocess
import time
from pathlib import Path


class MiniRangExecutor:
    """Claude Computer Use API 액션을 macOS에서 실행"""

    def __init__(
        self,
        display_width: int = 2560,
        display_height: int = 1080,
        screenshot_dir: str = None,
    ):
        self.display_width = display_width
        self.display_height = display_height
        self.screenshot_dir = Path(
            screenshot_dir or os.path.join(os.path.dirname(__file__), "..", "data", "minirang_screenshots")
        )
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.iteration = 0

        # API 이미지 제약: 최장 변 1568px, 총 1.15M 픽셀
        long_edge = max(display_width, display_height)
        total_pixels = display_width * display_height
        long_edge_scale = 1568 / long_edge
        total_pixels_scale = math.sqrt(1_150_000 / total_pixels)
        self.scale = min(1.0, long_edge_scale, total_pixels_scale)

        self.scaled_width = int(display_width * self.scale)
        self.scaled_height = int(display_height * self.scale)

    def get_display_dimensions(self):
        """API 도구 정의에 사용할 스케일된 해상도 반환"""
        return self.scaled_width, self.scaled_height

    def _to_screen(self, x, y):
        """API 좌표 → 실제 화면 좌표"""
        return int(x / self.scale), int(y / self.scale)

    def _run(self, cmd, timeout=10):
        """셸 명령 실행"""
        try:
            result = subprocess.run(
                cmd, shell=isinstance(cmd, str), capture_output=True,
                text=True, timeout=timeout
            )
            return result.stdout.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "Command timed out", 1
        except Exception as e:
            return str(e), 1

    def execute(self, action_input: dict):
        """
        Claude API의 computer tool_use 입력을 실행하고 결과 반환.
        Returns: tool_result content (list or string)
        """
        self.iteration += 1
        action = action_input.get("action", "")

        try:
            if action == "screenshot":
                return self._screenshot()
            elif action == "left_click":
                return self._click(action_input, "c")
            elif action == "right_click":
                return self._click(action_input, "rc")
            elif action == "double_click":
                return self._click(action_input, "dc")
            elif action == "triple_click":
                return self._click(action_input, "tc")
            elif action == "middle_click":
                return self._middle_click(action_input)
            elif action == "type":
                return self._type_text(action_input)
            elif action == "key":
                return self._press_key(action_input)
            elif action == "mouse_move":
                return self._mouse_move(action_input)
            elif action == "left_click_drag":
                return self._drag(action_input)
            elif action == "scroll":
                return self._scroll(action_input)
            elif action == "cursor_position":
                return self._cursor_position()
            elif action == "zoom":
                return self._zoom(action_input)
            elif action == "wait":
                duration = min(action_input.get("duration", 1), 5)
                time.sleep(duration)
                return f"Waited {duration}s"
            elif action == "left_mouse_down":
                x, y = self._to_screen(*action_input["coordinate"])
                self._run(f"cliclick dd:{x},{y}")
                return f"Mouse down at ({x},{y})"
            elif action == "left_mouse_up":
                x, y = self._to_screen(*action_input["coordinate"])
                self._run(f"cliclick du:{x},{y}")
                return f"Mouse up at ({x},{y})"
            elif action == "hold_key":
                return self._hold_key(action_input)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error executing {action}: {e}"

    def _screenshot(self):
        """화면 캡처 → 리사이즈 → base64"""
        raw_path = "/tmp/minirang_raw.png"
        resized_path = f"/tmp/minirang_scaled.png"

        # 화면 깨우기
        self._run("caffeinate -u -t 2")
        time.sleep(0.5)

        # 캡처
        self._run(f"screencapture -x {raw_path}")

        # 리사이즈
        self._run(
            f"sips --resampleWidth {self.scaled_width} {raw_path} --out {resized_path}",
            timeout=10
        )

        if not os.path.exists(resized_path):
            return "Error: Screenshot failed"

        # base64 인코딩
        with open(resized_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # 로그용 복사본 저장
        log_path = self.screenshot_dir / f"iter_{self.iteration:03d}.png"
        try:
            subprocess.run(["cp", resized_path, str(log_path)], check=False)
        except Exception:
            pass

        return [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            }
        }]

    def _click(self, action_input, click_type):
        """클릭 계열 액션 (left/right/double/triple)"""
        coord = action_input.get("coordinate", [0, 0])
        sx, sy = self._to_screen(coord[0], coord[1])
        modifier = action_input.get("text", "")

        cmd_parts = []
        if modifier:
            cmd_parts.append(f"kd:{self._map_modifier(modifier)}")
        cmd_parts.append(f"{click_type}:{sx},{sy}")
        if modifier:
            cmd_parts.append(f"ku:{self._map_modifier(modifier)}")

        cmd = "cliclick " + " ".join(cmd_parts)
        out, rc = self._run(cmd)
        if rc != 0:
            return f"Error: {out}"
        return f"Clicked ({sx},{sy}) [{click_type}]"

    def _middle_click(self, action_input):
        """가운데 클릭 (cliclick에 없으므로 osascript 사용)"""
        coord = action_input.get("coordinate", [0, 0])
        sx, sy = self._to_screen(coord[0], coord[1])
        # Ctrl+Click as fallback
        self._run(f"cliclick kd:ctrl c:{sx},{sy} ku:ctrl")
        return f"Middle-clicked ({sx},{sy})"

    def _type_text(self, action_input):
        """텍스트 입력 — 한글은 클립보드 붙여넣기"""
        text = action_input.get("text", "")
        if not text:
            return "No text to type"

        # ASCII만 있으면 cliclick 직접 입력
        if all(ord(c) < 128 for c in text):
            self._run(f"cliclick t:'{text}'")
        else:
            # 한글/유니코드: 클립보드 → Cmd+V
            proc = subprocess.run(
                ["pbcopy"], input=text.encode("utf-8"), check=False
            )
            time.sleep(0.1)
            self._run("cliclick kd:cmd t:v ku:cmd")

        return f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"

    def _press_key(self, action_input):
        """키/키 조합 입력"""
        key_text = action_input.get("text", "")
        if not key_text:
            return "No key specified"

        keys = key_text.lower().split("+")
        if len(keys) == 1:
            mapped = self._map_key(keys[0].strip())
            self._run(f"cliclick kp:{mapped}")
        else:
            # 조합키: 수정키 홀드 → 키 입력 → 수정키 해제
            modifiers = keys[:-1]
            main_key = keys[-1].strip()
            parts = []
            for m in modifiers:
                parts.append(f"kd:{self._map_modifier(m.strip())}")
            parts.append(f"kp:{self._map_key(main_key)}")
            for m in reversed(modifiers):
                parts.append(f"ku:{self._map_modifier(m.strip())}")
            self._run("cliclick " + " ".join(parts))

        return f"Key pressed: {key_text}"

    def _mouse_move(self, action_input):
        """마우스 이동"""
        coord = action_input.get("coordinate", [0, 0])
        sx, sy = self._to_screen(coord[0], coord[1])
        self._run(f"cliclick m:{sx},{sy}")
        return f"Mouse moved to ({sx},{sy})"

    def _drag(self, action_input):
        """드래그"""
        start = action_input.get("start_coordinate", action_input.get("coordinate", [0, 0]))
        end = action_input.get("coordinate", [0, 0])
        sx1, sy1 = self._to_screen(start[0], start[1])
        sx2, sy2 = self._to_screen(end[0], end[1])
        self._run(f"cliclick dd:{sx1},{sy1} du:{sx2},{sy2}")
        return f"Dragged ({sx1},{sy1}) → ({sx2},{sy2})"

    def _scroll(self, action_input):
        """스크롤"""
        coord = action_input.get("coordinate", [self.display_width // 2, self.display_height // 2])
        sx, sy = self._to_screen(coord[0], coord[1])
        direction = action_input.get("scroll_direction", "down")
        amount = min(action_input.get("scroll_amount", 3), 15)

        # 먼저 마우스를 위치로 이동
        self._run(f"cliclick m:{sx},{sy}")
        time.sleep(0.1)

        # osascript로 스크롤 이벤트 전송
        scroll_y = amount if direction == "up" else -amount if direction == "down" else 0
        scroll_x = amount if direction == "right" else -amount if direction == "left" else 0

        apple_script = f'''
        tell application "System Events"
            set curX to {sx}
            set curY to {sy}
        end tell
        do shell script "cliclick m:{sx},{sy}"
        '''
        # cliclick 스크롤 (화살키 기반)
        arrow = {
            "up": "arrow-up", "down": "arrow-down",
            "left": "arrow-left", "right": "arrow-right"
        }.get(direction, "arrow-down")

        for _ in range(amount):
            self._run(f"cliclick kp:{arrow}")
            time.sleep(0.05)

        return f"Scrolled {direction} x{amount} at ({sx},{sy})"

    def _cursor_position(self):
        """현재 커서 위치"""
        out, _ = self._run("cliclick p:")
        return f"Cursor position: {out}"

    def _zoom(self, action_input):
        """화면 영역 확대 캡처"""
        region = action_input.get("region", [0, 0, 500, 500])
        x1, y1, x2, y2 = region
        # API 좌표 → 실제 좌표
        sx1, sy1 = self._to_screen(x1, y1)
        sx2, sy2 = self._to_screen(x2, y2)
        w = sx2 - sx1
        h = sy2 - sy1

        raw_path = "/tmp/minirang_raw.png"
        zoom_path = "/tmp/minirang_zoom.png"

        self._run(f"screencapture -x -R {sx1},{sy1},{w},{h} {zoom_path}")

        if not os.path.exists(zoom_path):
            return "Error: Zoom capture failed"

        with open(zoom_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        return [{
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64,
            }
        }]

    def _hold_key(self, action_input):
        """키 홀드"""
        key = self._map_key(action_input.get("text", ""))
        duration = min(action_input.get("duration", 1), 5)
        self._run(f"cliclick kd:{key}")
        time.sleep(duration)
        self._run(f"cliclick ku:{key}")
        return f"Held {key} for {duration}s"

    def _map_key(self, key):
        """Claude 키 이름 → cliclick 키 이름"""
        mapping = {
            "return": "return", "enter": "return",
            "tab": "tab", "escape": "esc", "esc": "esc",
            "backspace": "delete", "delete": "fwd-delete",
            "space": "space", "up": "arrow-up", "down": "arrow-down",
            "left": "arrow-left", "right": "arrow-right",
            "home": "home", "end": "end",
            "pageup": "page-up", "pagedown": "page-down",
            "page_up": "page-up", "page_down": "page-down",
        }
        k = key.strip().lower()
        return mapping.get(k, k)

    def _map_modifier(self, mod):
        """수정 키 매핑"""
        mapping = {
            "ctrl": "ctrl", "control": "ctrl",
            "alt": "alt", "option": "alt",
            "shift": "shift",
            "super": "cmd", "command": "cmd", "cmd": "cmd", "meta": "cmd",
        }
        return mapping.get(mod.strip().lower(), mod.strip().lower())

    def cleanup(self, keep_last=True):
        """스크린샷 캐시 정리"""
        screenshots = sorted(self.screenshot_dir.glob("iter_*.png"))
        if keep_last and screenshots:
            for f in screenshots[:-1]:
                f.unlink(missing_ok=True)
        elif not keep_last:
            for f in screenshots:
                f.unlink(missing_ok=True)
