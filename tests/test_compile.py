"""
Compilation smoke tests.

These tests verify that the C++ emitted by the transpiler actually
compiles with g++. They are slower than the string-comparison tests
in test_transpiler.py, so they live in their own file.

Skip these tests with:
    pytest tests/test_transpiler.py

Run everything with:
    pytest tests/
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from kofty.transpiler import transpile


# Where raylib is installed on this machine. Adjust via env vars
# if you move raylib elsewhere.
RAYLIB_INCLUDE = os.environ.get("RAYLIB_INCLUDE", "C:/raylib/include")
RAYLIB_LIB = os.environ.get("RAYLIB_LIB", "C:/raylib/lib")

GPP = "g++"


def compile_to_object(source: str) -> subprocess.CompletedProcess:
    """
    Transpile the given InterScript source, write it to a temp .cpp file,
    and run g++ -c (compile only, no linking). Returns the CompletedProcess
    so the caller can inspect returncode, stdout, stderr.
    """
    cpp_code = transpile(source)

    with tempfile.TemporaryDirectory() as tmpdir:
        cpp_path = Path(tmpdir) / "test.cpp"
        cpp_path.write_text(cpp_code, encoding="utf-8")

        cmd = [
            GPP,
            "-c",                        # compile only, no link
            str(cpp_path),
            "-o", str(Path(tmpdir) / "test.o"),
            f"-I{RAYLIB_INCLUDE}",
            "-std=c++17",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        return result

def test_minimal_program_compiles():
    """The smallest possible InterScript program should compile."""
    source = "import raylib\nwindow(400, 300, \"Hi\")"
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_variables_and_loop_compile():
    """Variables, reassignment, while loop, and drawing calls should compile."""
    source = (
        "import raylib\n"
        "window(400, 300, \"Loop\")\n"
        "x = 0\n"
        "while running():\n"
        "    x = x + 1\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(x), 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_user_functions_compile():
    """A user-defined function should compile to valid C++."""
    source = (
        "import raylib\n"
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "x = add(2, 3)\n"
        "window(400, 300, \"Funcs\")\n"
        "while running():\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(x), 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_boolean_and_collision_compile():
    """and / or / not / rects_overlap should emit compiling C++."""
    source = (
        "import raylib\n"
        "window(400, 300, \"Bools\")\n"
        "x = 10\n"
        "y = 20\n"
        "while running():\n"
        "    if x > 0 and y < 100:\n"
        "        x = x + 1\n"
        "    if x == 5 or y == 5:\n"
        "        y = y - 1\n"
        "    if not (x == 0):\n"
        "        y = y + 1\n"
        "    if rects_overlap(x, y, 10, 10, 20, 20, 10, 10):\n"
        "        x = 0\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(x), 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_print_and_str_compile():
    """print() and str() in expressions should emit compiling C++."""
    source = (
        "import raylib\n"
        "print(\"starting\")\n"
        "score = 42\n"
        "msg = \"Score: \" + str(score)\n"
        "print(msg)\n"
        "window(400, 300, \"Print\")\n"
        "while running():\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(msg, 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_class_compile():
    """Classes with methods and instances should compile."""
    source = (
        "import raylib\n"
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "\n"
        "    def move(self, dx, dy):\n"
        "        self.x = self.x + dx\n"
        "        self.y = self.y + dy\n"
        "\n"
        "window(400, 300, \"Class test\")\n"
        "p = Point(10, 20)\n"
        "p.move(5, 5)\n"
        "while running():\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(p.x), 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )


def test_elif_compile():
    """if/elif/else chains should emit valid C++."""
    source = (
        "import raylib\n"
        "window(400, 300, \"elif\")\n"
        "x = 5\n"
        "while running():\n"
        "    if x == 1:\n"
        "        print(\"one\")\n"
        "    elif x == 2:\n"
        "        print(\"two\")\n"
        "    elif x == 3:\n"
        "        print(\"three\")\n"
        "    else:\n"
        "        print(\"other\")\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_mouse_constants_compile():
    """MOUSE_BUTTON_* constants should compile when passed to
    is_mouse_down()."""
    source = (
        "import raylib\n"
        "window(400, 300, \"mouse\")\n"
        "while running():\n"
        "    if is_mouse_down(MOUSE_BUTTON_LEFT):\n"
        "        print(\"left\")\n"
        "    if is_mouse_down(MOUSE_BUTTON_RIGHT):\n"
        "        print(\"right\")\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_break_continue_compile():
    """break and continue inside loops should emit valid C++."""
    source = (
        "import raylib\n"
        "window(400, 300, \"break\")\n"
        "i = 0\n"
        "while running():\n"
        "    i = i + 1\n"
        "    if i > 100:\n"
        "        break\n"
        "    if i == 50:\n"
        "        continue\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(i), 10, 10, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_method_return_compile():
    """Methods that return values should emit valid C++."""
    source = (
        "import raylib\n"
        "window(400, 300, \"methods\")\n"
        "class Counter:\n"
        "    def __init__(self, start):\n"
        "        self.value = start\n"
        "    def get_value(self):\n"
        "        return self.value\n"
        "    def twice(self):\n"
        "        return self.value + self.value\n"
        "c = Counter(5)\n"
        "while running():\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(c.get_value()), 10, 10, 20, 255, 255, 255)\n"
        "    draw_text(str(c.twice()), 10, 40, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_tuple_compile():
    """Tuples as std::pair should emit valid C++."""
    source = (
        "import raylib\n"
        "window(400, 300, \"tuples\")\n"
        "t = (1, 2)\n"
        "x = t[0]\n"
        "y = t[1]\n"
        "a, b = t\n"
        "while running():\n"
        "    begin_draw()\n"
        "    clear(0, 0, 0)\n"
        "    draw_text(str(x), 10, 10, 20, 255, 255, 255)\n"
        "    draw_text(str(y), 10, 40, 20, 255, 255, 255)\n"
        "    draw_text(str(a), 10, 70, 20, 255, 255, 255)\n"
        "    draw_text(str(b), 10, 100, 20, 255, 255, 255)\n"
        "    end_draw()\n"
    )
    result = compile_to_object(source)
    assert result.returncode == 0, (
        f"g++ failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
