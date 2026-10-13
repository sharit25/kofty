"""
Type stubs for InterScript built-ins.

This file exists ONLY so Pylance / VS Code stops reporting
"undefined variable" on InterScript calls. It is never imported
at runtime and never transpiled. The real definitions live in
kofty/transpiler.py's BUILTINS table.

If you add a built-in to BUILTINS, add a matching stub here.
"""

from typing import Any

# --- Window / lifecycle ---
def window(width: int, height: int, title: str) -> None: ...
def set_fps(fps: int) -> None: ...
def close_window() -> None: ...

# --- Drawing ---
def begin_draw() -> None: ...
def end_draw() -> None: ...
def clear(r: int, g: int, b: int) -> None: ...
def draw_text(text: str, x: int, y: int, size: int, r: int, g: int, b: int) -> None: ...
def draw_rectangle(x: int, y: int, w: int, h: int, r: int, g: int, b: int) -> None: ...
def draw_circle(cx: int, cy: int, radius: int, r: int, g: int, b: int) -> None: ...

# --- Input ---
def running() -> bool: ...
def is_key_down(key: int) -> bool: ...
def is_key_pressed(key: int) -> bool: ...
def get_mouse_x() -> int: ...
def get_mouse_y() -> int: ...
def is_mouse_down(button: int) -> bool: ...
def is_mouse_pressed(button: int) -> bool: ...

# --- Conversion ---
def str(value: Any) -> str: ...
def print(value: Any) -> None: ...

# --- Raylib keyboard constants (subset commonly used) ---
KEY_A: int
KEY_D: int
KEY_W: int
KEY_S: int
KEY_SPACE: int
KEY_LEFT: int
KEY_RIGHT: int
KEY_UP: int
KEY_DOWN: int
KEY_ESCAPE: int
KEY_ENTER: int

# --- Raylib mouse buttons ---
MOUSE_BUTTON_LEFT: int
MOUSE_BUTTON_RIGHT: int
MOUSE_BUTTON_MIDDLE: int

# --- Raylib mouse buttons ---
MOUSE_BUTTON_LEFT: int
MOUSE_BUTTON_RIGHT: int
MOUSE_BUTTON_MIDDLE: int
