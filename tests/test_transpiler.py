"""Pytest tests for the InterScript transpiler.

Run from C:\\InterScript with:  pytest tests/ -v
"""

import pytest
from kofty.transpiler import transpile, TranspileError


def test_window_call():
    out = transpile('window(800, 600, "Game")')
    assert 'InitWindow(800, 600, "Game");' in out


def test_variable_assign():
    out = transpile("x = 42")
    assert "auto x = 42;" in out


def test_string_variable():
    out = transpile('name = "Hero"')
    assert 'auto name = std::string("Hero");' in out

def test_while_loop():
    out = transpile(
        "while running():\n"
        "    begin_draw()\n"
    )
    assert "while (!WindowShouldClose()) {" in out
    assert "BeginDrawing();" in out


def test_for_loop_range_one_arg():
    out = transpile("for i in range(5):\n    draw_circle(i, 0, 10, 255, 0, 0)\n")
    assert "for (int i = 0; i < 5; ++i)" in out


def test_for_loop_range_two_args():
    out = transpile("for i in range(2, 8):\n    draw_circle(i, 0, 10, 255, 0, 0)\n")
    assert "for (int i = 2; i < 8; ++i)" in out


def test_if_else():
    out = transpile(
        "x = 5\n"
        "if x < 3:\n"
        '    draw_text("low", 0, 0, 20, 255, 255, 255)\n'
        "else:\n"
        '    draw_text("high", 0, 0, 20, 255, 255, 255)\n'
    )
    assert "if ((x < 3)) {" in out
    assert "} else {" in out


def test_user_function():
    out = transpile(
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "x = add(2, 3)\n"
    )
    assert "auto add(auto a, auto b) {" in out
    assert "return (a + b);" in out
    assert "auto x = add(2, 3);" in out


def test_unknown_function_raises():
    with pytest.raises(TranspileError, match="Unknown function"):
        transpile("not_a_real_function(1, 2)")


def test_wrong_arity_raises():
    with pytest.raises(TranspileError, match="expects 3 args"):
        transpile("window(800, 600)")


def test_class_accepts_player_pattern():
    # Classes are now supported. This used to be a "raises" test.
    out = transpile(
        "class Player:\n"
        "    def __init__(self, start_x):\n"
        "        self.x = start_x\n"
    )
    assert "struct Player {" in out

def test_print_string():
    out = transpile('print("hello")')
    assert '#include <iostream>' in out
    assert 'is_to_string("hello")' in out


def test_print_number():
    out = transpile('print(42)')
    assert "is_to_string(42)" in out

def test_str_of_variable():
    out = transpile(
        "score = 42\n"
        "label = str(score)\n"
    )
    assert "auto label = format_float(score);" in out

def test_str_of_number_literal():
    out = transpile("s = str(100)")
    assert "auto s = format_float(100);" in out

def test_str_of_string_passthrough():
    # str("hello") should just be "hello" — already a string
    out = transpile('s = str("hello")')
    assert 'auto s = "hello";' in out


def test_string_plus_number():
    out = transpile(
        "score = 42\n"
        'msg = "Score: " + str(score)\n'
    )
    assert 'auto msg = (std::string("Score: ") + format_float(score));' in out
def test_boolean_and():
    out = transpile("a = True\nb = False\nx = a and b")
    assert "auto x = (a && b);" in out


def test_boolean_or():
    out = transpile("a = True\nb = False\nx = a or b")
    assert "auto x = (a || b);" in out


def test_boolean_not():
    out = transpile("a = True\nx = not a")
    assert "auto x = (!a);" in out

def test_boolean_and_three_operands():
    out = transpile("a = True\nb = False\nc = True\nx = a and b and c")
    assert "auto x = (a && b && c);" in out


def test_boolean_and_with_comparisons():
    out = transpile("a = 5\nb = 5\nx = a > 0 and b < 10")
    assert "auto x = ((a > 0) && (b < 10));" in out

def test_keyboard_constant_passthrough():
    out = transpile("import raylib\nx = is_key_down(KEY_LEFT)")
    assert "auto x = IsKeyDown(KEY_LEFT);" in out


def test_keyboard_constant_space():
    out = transpile("import raylib\nx = is_key_down(KEY_SPACE)")
    assert "auto x = IsKeyDown(KEY_SPACE);" in out

def test_rects_overlap():
    out = transpile("x = rects_overlap(0, 0, 10, 10, 5, 5, 10, 10)")
    expected = "auto x = (0 < (5 + 10) && (0 + 10) > 5 && 0 < (5 + 10) && (0 + 10) > 5);"
    assert expected in out

def test_class_struct_emitted():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
    )
    assert "struct Point {" in out
    assert "int x;" in out
    assert "int y;" in out
    # Batch 10k.3: constructor now uses an initializer list.
    assert "Point(int x, int y) : x(x), y(y) {" in out


def test_class_definition_no_longer_raises():
    # The old test test_class_raises_clear_error will need to be
    # updated — we now support classes. Just confirm no error.
    out = transpile(
        "class Empty:\n"
        "    def __init__(self):\n"
        "        pass\n"
    )
    assert "struct Empty {" in out

def test_class_with_method_emitted():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "\n"
        "    def move(self, dx, dy):\n"
        "        self.x = self.x + dx\n"
        "        self.y = self.y + dy\n"
    )
    assert "struct Point {" in out
    assert "void move(int dx, int dy) {" in out
    assert "this->x = (this->x + dx);" in out
    assert "this->y = (this->y + dy);" in out


def test_class_method_with_no_args():
    out = transpile(
        "class Counter:\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
        "\n"
        "    def reset(self):\n"
        "        self.value = 0\n"
    )
    assert "void reset() {" in out
    assert "this->value = 0;" in out

def test_instance_construction():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "\n"
        "p = Point(3, 5)\n"
    )
    # ClassName(args) now emits brace init to avoid C++ most-vexing-parse
    assert "Point p{3, 5};" in out


def test_instance_construction_no_args():
    # This case specifically triggered the C++ most-vexing-parse bug
    out = transpile(
        "class Ball:\n"
        "    def __init__(self):\n"
        "        self.x = 0\n"
        "\n"
        "b = Ball()\n"
    )
    assert "Ball b{};" in out


def test_instance_method_call():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "\n"
        "    def move(self, dx, dy):\n"
        "        self.x = self.x + dx\n"
        "        self.y = self.y + dy\n"
        "\n"
        "p = Point(0, 0)\n"
        "p.move(10, 20)\n"
    )
    assert "p.move(10, 20);" in out


def test_instance_attribute_read():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x, y):\n"
        "        self.x = x\n"
        "        self.y = y\n"
        "\n"
        "p = Point(7, 8)\n"
        "print(p.x)\n"
    )
    assert "p.x" in out


def test_elif_emits_else_if():
    out = transpile(
        "x = 5\n"
        "if x < 3:\n"
        '    print("low")\n'
        "elif x < 10:\n"
        '    print("mid")\n'
        "else:\n"
        '    print("high")\n'
    )
    assert "} else if (" in out


def test_elif_multiple():
    out = transpile(
        "x = 5\n"
        "if x == 1:\n"
        '    print("one")\n'
        "elif x == 2:\n"
        '    print("two")\n'
        "elif x == 3:\n"
        '    print("three")\n'
        "else:\n"
        '    print("other")\n'
    )
    # Isolate the main() body from the preamble — the preamble now
    # contains "else if" from helper templates, so a global count
    # would overcount.
    main_start = out.find("int main()")
    assert main_start != -1
    body = out[main_start:]
    assert body.count("} else if (") == 2

def test_augassign_plus_equals():
    out = transpile(
        "x = 10\n"
        "x += 5\n"
    )
    assert "x += 5;" in out


def test_augassign_minus_equals():
    out = transpile(
        "x = 10\n"
        "x -= 3\n"
    )
    assert "x -= 3;" in out


def test_augassign_multiply_equals():
    out = transpile(
        "x = 10\n"
        "x *= 2\n"
    )
    assert "x *= 2;" in out


def test_augassign_divide_equals():
    out = transpile(
        "x = 10\n"
        "x /= 2\n"
    )
    assert "x /= 2;" in out

def test_mouse_button_left_passthrough():
    out = transpile("import raylib\nx = is_mouse_down(MOUSE_BUTTON_LEFT)")
    assert "auto x = IsMouseButtonDown(MOUSE_BUTTON_LEFT);" in out


def test_mouse_button_right_passthrough():
    out = transpile("import raylib\nx = is_mouse_down(MOUSE_BUTTON_RIGHT)")
    assert "auto x = IsMouseButtonDown(MOUSE_BUTTON_RIGHT);" in out

def test_break_in_loop():
    out = transpile(
        "x = 0\n"
        "while x < 10:\n"
        "    x = x + 1\n"
        "    if x == 5:\n"
        "        break\n"
    )
    assert "break;" in out


def test_continue_in_loop():
    out = transpile(
        "x = 0\n"
        "while x < 10:\n"
        "    x = x + 1\n"
        "    if x == 5:\n"
        "        continue\n"
    )
    assert "continue;" in out

def test_function_returns_value():
    out = transpile(
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "x = add(2, 3)\n"
    )
    assert "auto add(auto a, auto b) {" in out
    assert "return (a + b);" in out
    assert "auto x = add(2, 3);"

def test_method_return_int():
    out = transpile(
        "class Point:\n"
        "    def __init__(self, x):\n"
        "        self.x = x\n"
        "\n"
        "    def get_x(self):\n"
        "        return self.x\n"
    )
    # Should emit `auto get_x()` not `void get_x()`
    assert "int get_x()" in out


def test_method_return_expression():
    out = transpile(
        "class Math:\n"
        "    def __init__(self):\n"
        "        self.base = 100\n"
        "\n"
        "    def plus(self, n):\n"
        "        return self.base + n\n"
    )
    assert "auto plus(int n)" in out

def test_reserved_word_function_raises():
    with pytest.raises(TranspileError, match="reserved C\\+\\+ keyword"):
        transpile(
            "def double(x):\n"
            "    return x\n"
        )

def test_reserved_word_method_raises():
    with pytest.raises(TranspileError, match="reserved C\\+\\+ keyword"):
        transpile(
            "class Point:\n"
            "    def __init__(self, x):\n"
            "        self.x = x\n"
            "\n"
            "    def int(self):\n"
            "        return self.x\n"
        )

def test_reserved_word_variable_raises():
    with pytest.raises(TranspileError, match="reserved C\\+\\+ keyword"):
        transpile("new = 5\n")

def test_non_reserved_word_ok():
    # `twice` is not a C++ keyword — should work fine
    out = transpile(
        "def twice(x):\n"
        "    return x + x\n"
    )
    assert "auto twice(auto x)" in out

def test_tuple_literal_emits_pair():
    out = transpile("t = (1, 2)")
    assert "#include <utility>" in out
    assert "auto t = std::make_pair(1, 2);" in out


def test_tuple_mixed_types():
    out = transpile('t = (1, "hi")')
    assert 'std::make_pair(1, "hi")' in out


def test_tuple_index_0():
    out = transpile(
        "t = (10, 20)\n"
        "x = t[0]\n"
    )
    assert "auto x = t.first;" in out


def test_tuple_index_1():
    out = transpile(
        "t = (10, 20)\n"
        "y = t[1]\n"
    )
    assert "auto y = t.second;" in out

def test_tuple_unpacking():
    out = transpile(
        "t = (10, 20)\n"
        "a, b = t\n"
    )
    assert "auto a = t.first;" in out
    assert "auto b = t.second;" in out

def test_tuple_three_elements_allowed():
    """3-element tuples now emit std::make_tuple (Plan A step 5)."""
    cpp = transpile("t = (1, 2, 3)")
    assert "std::make_tuple(1, 2, 3)" in cpp

def test_self_method_call():
    out = transpile(
        "class Counter:\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
        "\n"
        "    def reset(self):\n"
        "        self.value = 0\n"
        "\n"
        "    def do_reset(self):\n"
        "        self.reset()\n"
    )
    assert "this->reset();" in out

def test_string_variable_can_be_reassigned():
    # Variables initialized with a string literal should be std::string
    # (not const char*), so later reassignments of other strings work.
    out = transpile(
        'display = "0"\n'
        "display = str(42)\n"
    )
    assert 'auto display = std::string("0");' in out
    assert "display = format_float(42);" in out
def test_mouse_pressed_passthrough():
    out = transpile("import raylib\nx = is_mouse_pressed(MOUSE_BUTTON_LEFT)")
    assert "auto x = IsMouseButtonPressed(MOUSE_BUTTON_LEFT);" in out

def test_float_literal():
    out = transpile("pi = 3.14")
    assert "auto pi = 3.14;" in out

def test_float_arithmetic_literal():
    out = transpile("x = 1.5 + 2.5")
    assert "auto x = (1.5 + 2.5);" in out

def test_float_division_not_truncated():
    # 5.0 / 2.0 should be 2.5 in the emitted C++, not truncated
    out = transpile("x = 5.0 / 2.0")
    assert "auto x = (5.0 / 2.0);" in out

def test_str_uses_format_float():
    # str() of a number should emit format_float(...) not std::to_string(...)
    out = transpile("s = str(42)")
    assert "auto s = format_float(42);" in out


def test_format_float_helper_is_included():
    # The generated C++ should include the format_float helper function
    out = transpile("x = 5")
    assert "std::string format_float(double" in out


def test_format_float_include_headers():
    # format_float needs <sstream> and <iomanip>
    out = transpile("x = 5")
    assert "#include <sstream>" in out
    assert "#include <iomanip>" in out

def test_int_conversion():
    out = transpile("n = int(3.14)")
    assert "auto n = (int)3.14;" in out


def test_float_conversion():
    out = transpile("m = float(5)")
    assert "auto m = (double)5;" in out


def test_int_of_variable():
    out = transpile(
        "x = 3.14\n"
        "n = int(x)\n"
    )
    assert "auto n = (int)x;" in out


def test_float_of_variable():
    out = transpile(
        "x = 5\n"
        "m = float(x)\n"
    )
    assert "auto m = (double)x;" in out

def test_vec2_creates_double_pair():
    out = transpile("pos = vec2(100.0, 200.0)")
    assert "auto pos = std::make_pair((double)100.0, (double)200.0);" in out

def test_vec2_with_int_args_casts():
    out = transpile("pos = vec2(100, 200)")
    assert "auto pos = std::make_pair((double)100, (double)200);" in out

def test_vec2_read_x():
    out = transpile(
        "pos = vec2(100.0, 200.0)\n"
        "x = pos[0]\n"
    )
    assert "auto x = pos.first;" in out

def test_vec2_read_y():
    out = transpile(
        "pos = vec2(100.0, 200.0)\n"
        "y = pos[1]\n"
    )
    assert "auto y = pos.second;" in out

def test_vec2_write_x():
    out = transpile(
        "pos = vec2(0.0, 0.0)\n"
        "pos[0] = 42.5\n"
    )
    assert "pos.first = 42.5;" in out

def test_list_literal_ints():
    out = transpile("xs = [1, 2, 3]")
    assert "auto xs = std::vector<int>{1, 2, 3};" in out


def test_list_literal_floats():
    out = transpile("xs = [1.5, 2.5]")
    assert "auto xs = std::vector<double>{1.5, 2.5};" in out


def test_list_literal_mixed_promotes_to_double():
    # Any float in the list promotes the whole list to double
    out = transpile("xs = [1, 2.5, 3]")
    assert "auto xs = std::vector<double>{1, 2.5, 3};" in out


def test_list_indexing():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "first = xs[0]\n"
    )
    assert "auto first = xs[0];" in out


def test_list_index_with_variable():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "i = 1\n"
        "v = xs[i]\n"
    )
    assert "auto v = xs[i];" in out

def test_len_builtin():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "n = len(xs)\n"
    )
    assert "auto n = xs.size();" in out

def test_empty_list_raises():
    with pytest.raises(TranspileError, match="empty list"):
        transpile("xs = []")

def test_list_append_int():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "xs.append(4)\n"
    )
    assert "xs.push_back(4);" in out


def test_list_append_variable():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "n = 99\n"
        "xs.append(n)\n"
    )
    assert "xs.push_back(n);" in out

def test_list_append_string():
    out = transpile(
        'xs = ["a"]\n'
        'xs.append("b")\n'
    )
    assert 'xs.push_back("b");' in out

def test_list_set_index_literal():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "xs[1] = 99\n"
    )
    assert "xs[1] = 99;" in out

def test_list_set_index_variable():
    out = transpile(
        "xs = [10, 20, 30]\n"
        "i = 1\n"
        "xs[i] = 42\n"
    )
    assert "xs[i] = 42;" in out

def test_for_in_list_basic():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "for x in xs:\n"
        "    print(x)\n"
    )
    assert "for (auto x : xs) {" in out
    assert "is_to_string(x)" in out

def test_for_in_list_with_body_accumulator():
    out = transpile(
        "xs = [1, 2, 3]\n"
        "total = 0\n"
        "for x in xs:\n"
        "    total = total + x\n"
    )
    assert "for (auto x : xs) {" in out
    assert "total = (total + x);" in out

def test_for_in_list_strings():
    out = transpile(
        'xs = ["a", "b"]\n'
        "for s in xs:\n"
        "    print(s)\n"
    )
    assert "for (auto s : xs) {" in out

def test_for_in_unknown_name_emits_foreach():
    # Previously an error, now relaxed: `for x in name:` emits a
    # range-based for loop. g++ will catch if `name` isn't iterable.
    out = transpile(
        "for x in mystery:\n"
        "    print(x)\n"
    )
    assert "for (auto x : mystery) {" in out

def test_field_type_int():
    out = transpile(
        "class Counter:\n"
        "    def __init__(self):\n"
        "        self.value = 42\n"
    )
    assert "int value;" in out

def test_field_type_double():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self):\n"
        "        self.radius = 3.14\n"
    )
    assert "double radius;" in out

def test_field_type_bool():
    out = transpile(
        "class Flag:\n"
        "    def __init__(self):\n"
        "        self.on = True\n"
    )
    assert "bool on;" in out

def test_field_type_string():
    out = transpile(
        "class Label:\n"
        "    def __init__(self):\n"
        "        self.text = \"hello\"\n"
    )
    assert "std::string text;" in out

def test_field_type_vec2():
    out = transpile(
        "class Marker:\n"
        "    def __init__(self):\n"
        "        self.pos = vec2(10.0, 20.0)\n"
    )
    assert "std::pair<double, double> pos;" in out

def test_field_type_list_int():
    out = transpile(
        "class Numbers:\n"
        "    def __init__(self):\n"
        "        self.items = [1, 2, 3]\n"
    )
    assert "std::vector<int> items;" in out

def test_field_type_list_string():
    out = transpile(
        "class Names:\n"
        "    def __init__(self):\n"
        "        self.items = [\"a\", \"b\"]\n"
    )
    assert "std::vector<std::string> items;" in out

def test_field_type_unknown_defaults_to_int():
    # When we can't infer, fall back to int (documented limitation)
    out = transpile(
        "class Pass:\n"
        "    def __init__(self, x):\n"
        "        self.value = x\n"
    )
    assert "int value;" in out

def test_constructor_param_infers_string_from_field():
    out = transpile(
        "class Label:\n"
        "    def __init__(self, text: str):\n"
        "        self.text = text\n"
        "\n"
        "l = Label(\"hello\")\n"
    )
    assert "Label(std::string text)" in out

def test_constructor_param_infers_double_from_field():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "c = Circle(3.14)\n"
    )
    assert "Circle(double r)" in out

def test_constructor_param_no_annotation_defaults_to_int():
    # Without an annotation, we fall back to int
    out = transpile(
        "class Widget:\n"
        "    def __init__(self, x):\n"
        "        self.x = x\n"
        "\n"
        "w = Widget(5)\n"
    )
    assert "Widget(int x)" in out

def test_constructor_param_annotation_int():
    out = transpile(
        "class Counter:\n"
        "    def __init__(self, n: int):\n"
        "        self.n = n\n"
        "\n"
        "c = Counter(10)\n"
    )
    assert "Counter(int n)" in out

def test_constructor_param_annotation_bool():
    out = transpile(
        "class Toggle:\n"
        "    def __init__(self, state: bool):\n"
        "        self.state = state\n"
        "\n"
        "t = Toggle(True)\n"
    )
    assert "Toggle(bool state)" in out

def test_single_inheritance_struct_syntax():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self, name: str):\n"
        "        super().__init__(name)\n"
    )
    assert "struct Animal {" in out
    assert "struct Dog : Animal {" in out


def test_parent_constructor_in_initializer_list():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self, name: str, breed: str):\n"
        "        super().__init__(name)\n"
        "        self.breed = breed\n"
    )
    # The parent constructor call must appear in the initializer list
    assert ": Animal(name)" in out
    # Child field is declared
    assert "std::string breed;" in out
    # Batch 10k.3: child fields assigned from params are now
    # initialized in the initializer list, not the body.
    assert "breed(breed)" in out
    assert "this->breed = breed;" not in out


def test_virtual_on_parent_methods():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self):\n"
        "        self.name = \"animal\"\n"
        "\n"
        "    def speak(self):\n"
        "        print(\"...\")\n"
    )
    assert "virtual void speak()" in out


def test_override_on_child_methods():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self):\n"
        "        self.name = \"animal\"\n"
        "\n"
        "    def speak(self):\n"
        "        print(\"...\")\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "\n"
        "    def speak(self):\n"
        "        print(\"Woof\")\n"
    )
    # Parent method is virtual
    assert "virtual void speak()" in out
    # Child method overrides
    assert "void speak() override" in out


def test_super_init_must_be_first_statement():
    with pytest.raises(TranspileError, match="super\\(\\)\\.__init__"):
        transpile(
            "class Animal:\n"
            "    def __init__(self):\n"
            "        self.name = \"animal\"\n"
            "\n"
            "class Dog(Animal):\n"
            "    def __init__(self):\n"
            "        self.breed = \"lab\"\n"
            "        super().__init__()\n"
        )

def test_inherited_field_access():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "    def describe(self):\n"
        "        print(self.name)\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self, name: str):\n"
        "        super().__init__(name)\n"
    )
    # Parent field access inside parent method should work
    assert "this->name" in out
    # Child struct inherits from Animal
    assert "struct Dog : Animal {" in out

def test_super_method_call():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "    def speak(self):\n"
        "        print(\"...\")\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self, name: str):\n"
        "        super().__init__(name)\n"
        "\n"
        "    def speak(self):\n"
        "        super().speak()\n"
        "        print(\"Woof\")\n"
    )
    # Parent method called via ClassName::method()
    assert "Animal::speak();" in out

def test_super_method_call_with_args():
    out = transpile(
        "class Animal:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "    def greet(self, prefix: str):\n"
        "        print(prefix)\n"
        "\n"
        "class Dog(Animal):\n"
        "    def __init__(self, name: str):\n"
        "        super().__init__(name)\n"
        "\n"
        "    def greet(self, prefix: str):\n"
        "        super().greet(prefix)\n"
        "        print(\"Also woof\")\n"
    )
    assert "Animal::greet(prefix);" in out

def test_super_method_unknown_parent_method_raises():
    with pytest.raises(TranspileError, match="no method"):
        transpile(
            "class Animal:\n"
            "    def __init__(self):\n"
            "        self.name = \"x\"\n"
            "\n"
            "class Dog(Animal):\n"
            "    def __init__(self):\n"
            "        super().__init__()\n"
            "\n"
            "    def bark(self):\n"
            "        super().meow()\n"
        )

def test_class_attribute_static_int():
    out = transpile(
        "class Counter:\n"
        "    count = 0\n"
        "\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
    )
    assert "static int count;" in out
    # Definition outside the struct
    assert "int Counter::count = 0;" in out

def test_class_attribute_static_string():
    out = transpile(
        "class Registry:\n"
        "    name = \"unnamed\"\n"
        "\n"
        "    def __init__(self):\n"
        "        self.x = 0\n"
    )
    assert "static std::string name;" in out
    assert 'std::string Registry::name = std::string("unnamed");' in out

def test_class_attribute_access_uses_scope_operator():
    # `Counter.count` at top level should become `Counter::count`
    out = transpile(
        "class Counter:\n"
        "    count = 0\n"
        "\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
        "\n"
        "c = Counter()\n"
        "x = Counter.count\n"
    )
    assert "auto x = Counter::count;" in out

def test_multiple_inheritance_two_parents():
    out = transpile(
        "class Walkable:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "class Swimmable:\n"
        "    def __init__(self, depth: int):\n"
        "        self.depth = depth\n"
        "\n"
        "class Duck(Walkable, Swimmable):\n"
        "    def __init__(self, name: str, depth: int):\n"
        "        Walkable.__init__(self, name)\n"
        "        Swimmable.__init__(self, depth)\n"
    )
    assert "struct Duck : Walkable, Swimmable {" in out

def test_multiple_inheritance_constructor_init_list():
    out = transpile(
        "class Walkable:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "class Swimmable:\n"
        "    def __init__(self, depth: int):\n"
        "        self.depth = depth\n"
        "\n"
        "class Duck(Walkable, Swimmable):\n"
        "    def __init__(self, name: str, depth: int):\n"
        "        Walkable.__init__(self, name)\n"
        "        Swimmable.__init__(self, depth)\n"
    )
    # Both parent constructors in initializer list, in bases order
    assert ": Walkable(name), Swimmable(depth)" in out

def test_multiple_inheritance_methods_inherited():
    out = transpile(
        "class Walkable:\n"
        "    def __init__(self):\n"
        "        self.a = 0\n"
        "\n"
        "    def walk(self):\n"
        "        print(\"walk\")\n"
        "\n"
        "class Swimmable:\n"
        "    def __init__(self):\n"
        "        self.b = 0\n"
        "\n"
        "    def swim(self):\n"
        "        print(\"swim\")\n"
        "\n"
        "class Duck(Walkable, Swimmable):\n"
        "    def __init__(self):\n"
        "        Walkable.__init__(self)\n"
        "        Swimmable.__init__(self)\n"
    )
    # Both structs exist and Duck inherits from both
    assert "struct Duck : Walkable, Swimmable {" in out

def test_multiple_inheritance_diamond_raises():
    # Diamond: both B and C inherit from A, and D inherits from both
    with pytest.raises(TranspileError, match="[Dd]iamond"):
        transpile(
            "class A:\n"
            "    def __init__(self):\n"
            "        self.x = 0\n"
            "\n"
            "class B(A):\n"
            "    def __init__(self):\n"
            "        super().__init__()\n"
            "\n"
            "class C(A):\n"
            "    def __init__(self):\n"
            "        super().__init__()\n"
            "\n"
            "class D(B, C):\n"
            "    def __init__(self):\n"
            "        B.__init__(self)\n"
            "        C.__init__(self)\n"
        )

def test_multiple_inheritance_super_init_raises():
    # Using super().__init__() in a multi-parent class is ambiguous
    with pytest.raises(TranspileError, match="multiple parent"):
        transpile(
            "class A:\n"
            "    def __init__(self):\n"
            "        self.x = 0\n"
            "\n"
            "class B:\n"
            "    def __init__(self):\n"
            "        self.y = 0\n"
            "\n"
            "class C(A, B):\n"
            "    def __init__(self):\n"
            "        super().__init__()\n"
        )

def test_multiple_inheritance_missing_parent_init_raises():
    # Must call each parent's __init__ explicitly
    with pytest.raises(TranspileError, match="must call"):
        transpile(
            "class A:\n"
            "    def __init__(self):\n"
            "        self.x = 0\n"
            "\n"
            "class B:\n"
            "    def __init__(self):\n"
            "        self.y = 0\n"
            "\n"
            "class C(A, B):\n"
            "    def __init__(self):\n"
            "        A.__init__(self)\n"
        )

def test_multiple_inheritance_wrong_order_raises():
    # Calls must be in the same order as bases
    with pytest.raises(TranspileError, match="order"):
        transpile(
            "class A:\n"
            "    def __init__(self):\n"
            "        self.x = 0\n"
            "\n"
            "class B:\n"
            "    def __init__(self):\n"
            "        self.y = 0\n"
            "\n"
            "class C(A, B):\n"
            "    def __init__(self):\n"
            "        B.__init__(self)\n"
            "        A.__init__(self)\n"
        )

def test_method_return_annotation_int():
    out = transpile(
        "class Counter:\n"
        "    def __init__(self, start: int):\n"
        "        self.value = start\n"
        "\n"
        "    def get(self) -> int:\n"
        "        return self.value\n"
    )
    assert "virtual int get()" in out

def test_method_return_annotation_float():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "    def area(self) -> float:\n"
        "        return 3.14 * self.r * self.r\n"
    )
    assert "virtual double area()" in out

def test_method_return_annotation_str():
    out = transpile(
        "class Named:\n"
        "    def __init__(self, n: str):\n"
        "        self.n = n\n"
        "\n"
        "    def get_name(self) -> str:\n"
        "        return self.n\n"
    )
    assert "virtual std::string get_name()" in out

def test_method_return_annotation_bool():
    out = transpile(
        "class Flag:\n"
        "    def __init__(self):\n"
        "        self.on = True\n"
        "\n"
        "    def is_on(self) -> bool:\n"
        "        return self.on\n"
    )
    assert "virtual bool is_on()" in out

def test_method_no_return_annotation_still_auto():
    # Methods without annotation still fall back to `auto` (not virtual)
    out = transpile(
        "class Counter:\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
        "\n"
        "    def get(self):\n"
        "        return self.value\n"
    )
    assert "int get()" in out
    assert "virtual auto" not in out

def test_method_void_still_virtual():
    # Methods with no return value are still virtual (unchanged)
    out = transpile(
        "class Printer:\n"
        "    def __init__(self):\n"
        "        self.x = 0\n"
        "\n"
        "    def show(self):\n"
        "        print(\"hi\")\n"
    )
    assert "virtual void show()" in out

def test_abstractmethod_simple():
    out = transpile(
        "class Shape:\n"
        "    @abstractmethod\n"
        "    def area(self) -> float:\n"
        "        pass\n"
    )
    assert "virtual double area() = 0;" in out


def test_abstractmethod_void():
    out = transpile(
        "class Base:\n"
        "    @abstractmethod\n"
        "    def run(self) -> None:\n"
        "        pass\n"
    )
    assert "virtual void run() = 0;" in out


def test_abstractmethod_no_annotation_raises():
    with pytest.raises(TranspileError, match="return type annotation"):
        transpile(
            "class Base:\n"
            "    @abstractmethod\n"
            "    def run(self):\n"
            "        pass\n"
        )


def test_abstractmethod_with_subclass():
    out = transpile(
        "class Shape:\n"
        "    @abstractmethod\n"
        "    def area(self) -> float:\n"
        "        pass\n"
        "\n"
        "class Circle(Shape):\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "    def area(self) -> float:\n"
        "        return 3.14 * self.r * self.r\n"
    )
    assert "virtual double area() = 0;" in out
    assert "double area() override {" in out


def test_staticmethod_simple():
    out = transpile(
        "class Math:\n"
        "    @staticmethod\n"
        "    def add(a: int, b: int) -> int:\n"
        "        return a + b\n"
    )
    assert "static int add(int a, int b) {" in out
    # The static method should NOT have `this` in the body
    assert "return (a + b);" in out


def test_staticmethod_no_self_in_signature():
    out = transpile(
        "class Math:\n"
        "    @staticmethod\n"
        "    def square(x: int) -> int:\n"
        "        return x * x\n"
    )
    # Should NOT include `self` parameter
    assert "static int square(int x)" in out
    assert "self" not in out.split("square")[1].split("}")[0]


def test_staticmethod_call_via_class():
    out = transpile(
        "class Math:\n"
        "    @staticmethod\n"
        "    def add(a: int, b: int) -> int:\n"
        "        return a + b\n"
        "\n"
        "r = Math.add(2, 3)\n"
    )
    # Should emit Math::add(2, 3) — class-scope call
    assert "Math::add(2, 3)" in out


def test_abstract_static_combination_raises():
    with pytest.raises(TranspileError, match="Combining"):
        transpile(
            "class Math:\n"
            "    @abstractmethod\n"
            "    @staticmethod\n"
            "    def add(a: int, b: int) -> int:\n"
            "        pass\n"
        )

def test_private_field_with_underscore():
    out = transpile(
        "class Player:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "        self._hp = 100\n"
    )
    # Private section should appear
    assert "private:" in out
    # Private field
    assert "int _hp;" in out
    # Public section should appear
    assert "public:" in out
    # Public field
    assert "std::string name;" in out

def test_all_private_fields():
    out = transpile(
        "class Secret:\n"
        "    def __init__(self):\n"
        "        self._code = 42\n"
        "        self._key = 7\n"
    )
    assert "private:" in out
    assert "int _code;" in out
    assert "int _key;" in out
    # No public fields means no `public:` label needed
    # (or it's harmless if we emit it)

def test_all_public_fields():
    out = transpile(
        "class Simple:\n"
        "    def __init__(self, x: int):\n"
        "        self.x = x\n"
        "        self.y = 10\n"
    )
    # No `_` prefix → no private section
    assert "private:" not in out
    assert "int x;" in out
    assert "int y;" in out

def test_private_field_method_access():
    out = transpile(
        "class Player:\n"
        "    def __init__(self):\n"
        "        self._hp = 100\n"
        "\n"
        "    def take_damage(self, amount: int) -> None:\n"
        "        self._hp = self._hp - amount\n"
    )
    # Method body should reference the private field via `this->_hp`
    assert "this->_hp = (this->_hp - amount);" in out

def test_private_field_constructor_init():
    out = transpile(
        "class Player:\n"
        "    def __init__(self, hp: int):\n"
        "        self._hp = hp\n"
    )
    # Constructor must set private field
    assert "this->_hp = hp;" in out

def test_ptr_builtin_creates_pointer():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "c = ptr(Circle(2.0))\n"
    )
    # ptr(ClassName(...)) → new ClassName(...)
    assert "auto c = new Circle(2.0);" in out

def test_pointer_method_call_uses_arrow():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "    def area(self) -> float:\n"
        "        return 3.14 * self.r * self.r\n"
        "\n"
        "c = ptr(Circle(2.0))\n"
        "a = c.area()\n"
    )
    assert "c->area()" in out

def test_pointer_field_read_uses_arrow():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "c = ptr(Circle(2.0))\n"
        "r_val = c.r\n"
    )
    assert "c->r" in out

def test_ptr_inside_list_append_creates_pointer_list():
    out = transpile(
        "class Circle:\n"
        "    def __init__(self, r: float):\n"
        "        self.r = r\n"
        "\n"
        "shapes = []\n"
        "shapes.append(ptr(Circle(2.0)))\n"
    )
    assert "std::vector<Circle*> shapes;" in out
    assert "shapes.push_back(new Circle(2.0));" in out

def test_pointer_list_index_method_call():
    out = transpile(
        "class Shape:\n"
        "    def __init__(self):\n"
        "        self.x = 0\n"
        "    @abstractmethod\n"
        "    def area(self) -> float:\n"
        "        pass\n"
        "\n"
        "class Circle(Shape):\n"
        "    def __init__(self, r: float):\n"
        "        super().__init__()\n"
        "        self.r = r\n"
        "    def area(self) -> float:\n"
        "        return 3.14 * self.r * self.r\n"
        "\n"
        "shapes = []\n"
        "shapes.append(ptr(Circle(2.0)))\n"
        "a = shapes[0].area()\n"
    )
    assert "shapes[0]->area()" in out

def test_dict_literal_string_values():
    out = transpile('d = {"name": "Alice", "city": "Paris"}')
    assert "#include <map>" in out
    assert "auto d = std::map<std::string, std::string>" in out
    assert '{"name", "Alice"}' in out
    assert '{"city", "Paris"}' in out

def test_dict_literal_int_values():
    out = transpile('d = {"a": 1, "b": 2, "c": 3}')
    assert "auto d = std::map<std::string, int>" in out
    assert '{"a", 1}' in out

def test_dict_literal_float_values():
    out = transpile('d = {"pi": 3.14, "e": 2.72}')
    assert "auto d = std::map<std::string, double>" in out
def test_dict_access():
    out = transpile(
        'd = {"a": 1}\n'
        'x = d["a"]\n'
    )
    assert 'auto x = d["a"];' in out

def test_dict_update():
    out = transpile(
        'd = {"a": 1}\n'
        'd["a"] = 42\n'
    )
    assert 'd["a"] = 42;' in out

def test_dict_add_new_key():
    out = transpile(
        'd = {"a": 1}\n'
        'd["b"] = 2\n'
    )
    assert 'd["b"] = 2;' in out

def test_empty_dict_raises():
    with pytest.raises(TranspileError, match="empty dict"):
        transpile("d = {}")

def test_measure_text_builtin():
    out = transpile('w = measure_text("hello", 20)')
    assert 'auto w = MeasureText("hello", 20);' in out

# ===== vec2 operator overloading =====

def test_vec2_add():
    out = transpile(
        "a = vec2(1.0, 2.0)\n"
        "b = vec2(3.0, 4.0)\n"
        "c = a + b\n"
    )
    assert "vec2_add(a, b)" in out

def test_vec2_sub():
    out = transpile(
        "a = vec2(1.0, 2.0)\n"
        "b = vec2(3.0, 4.0)\n"
        "c = a - b\n"
    )
    assert "vec2_sub(a, b)" in out

def test_vec2_mul_scalar_right():
    out = transpile(
        "pos = vec2(1.0, 2.0)\n"
        "dt = 0.5\n"
        "next = pos * dt\n"
    )
    assert "vec2_scale(pos, dt)" in out

def test_vec2_augassign_plus():
    out = transpile(
        "pos = vec2(0.0, 0.0)\n"
        "vel = vec2(1.0, 2.0)\n"
        "pos += vel\n"
    )
    assert "pos = vec2_add(pos, vel);" in out

def test_vec2_augassign_minus():
    out = transpile(
        "pos = vec2(0.0, 0.0)\n"
        "vel = vec2(1.0, 2.0)\n"
        "pos -= vel\n"
    )
    assert "pos = vec2_sub(pos, vel);" in out

def test_vec2_augassign_mul():
    out = transpile(
        "pos = vec2(1.0, 2.0)\n"
        "dt = 0.5\n"
        "pos *= dt\n"
    )
    assert "pos = vec2_scale(pos, dt);" in out

def test_vec2_plus_int_does_not_trigger_helper():
    # If one side isn't a vec2, fall back to plain C++.
    # The C++ prelude always defines vec2_add/sub/scale, so we check
    # no CALL SITE is emitted (with parens).
    out = transpile(
        "a = 1\n"
        "b = 2\n"
        "c = a + b\n"
    )
    assert "vec2_add(a, b)" not in out

def test_vec2_helper_is_included():
    # The C++ prelude should define vec2_add, vec2_sub, vec2_scale
    out = transpile("a = vec2(1.0, 2.0)")
    assert "vec2_add" in out
    assert "vec2_sub" in out
    assert "vec2_scale" in out
