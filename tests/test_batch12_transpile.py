"""Batch 12: input() builtin. Transpile-only."""
import pytest
from kofty.transpiler import transpile, TranspileError


# --- basic input() -----------------------------------------------------------

def test_input_no_args():
    out = transpile('''
name = input()
''')
    assert "std::getline" in out
    assert "std::cin" in out


def test_input_with_prompt():
    out = transpile('''
name = input("What is your name? ")
''')
    # Prompt should be printed before the read.
    assert "What is your name?" in out
    assert "std::getline" in out


def test_input_result_is_string():
    out = transpile('''
name = input()
''')
    # `name` should be usable in string contexts; is_to_string should not
    # be called since it's already std::string. Simple sanity: input emits
    # a std::string declaration.
    assert "std::string" in out or "auto name" in out


# --- int(input()) and float(input()) -----------------------------------------

def test_int_of_input():
    out = transpile('''
x = int(input())
''')
    # Should parse via std::stoi.
    assert "std::stoi" in out


def test_int_of_input_with_prompt():
    out = transpile('''
n = int(input("How many? "))
''')
    assert "How many?" in out
    assert "std::stoi" in out


def test_float_of_input():
    out = transpile('''
y = float(input())
''')
    assert "std::stod" in out


# --- integration: input flows into string concatenation ----------------------

def test_input_used_in_concat():
    out = transpile('''
name = input("Name: ")
print("Hello, " + name)
''')
    # Should not accidentally wrap `name` in std::to_string.
    assert "std::getline" in out
    assert "Hello, " in out


def test_input_used_in_fstring():
    out = transpile('''
name = input()
print(f"Hi {name}")
''')
    assert "std::getline" in out
    assert "is_to_string" in out


# --- error: input() arity ----------------------------------------------------

def test_input_too_many_args_raises():
    with pytest.raises(TranspileError):
        transpile('x = input("a", "b")\n')


# --- regression: input not used, program still compiles cleanly ---------------

def test_program_without_input_does_not_call_input_line():
    out = transpile('x = 5\nprint(x)\n')
    # The preamble always contains input_line; what matters is that
    # the user code (inside main) never calls it.
    main_body = out.split("int main()")[1] if "int main()" in out else out
    assert "input_line(" not in main_body
    assert "std::cin" not in main_body
