"""tests/test_batch8f.py

Batch 8f: list.pop() actually removes the last element.
...
"""

from tests.conftest import run_is, assert_runs, assert_transpile_fails

def test_pop_returns_last(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        x = xs.pop()
        print(x)
    """, "3", tmp_path)


def test_pop_removes_last(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        x = xs.pop()
        print(len(xs))
    """, "2", tmp_path)


def test_pop_twice(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        a = xs.pop()
        b = xs.pop()
        print(a)
        print(b)
        print(len(xs))
    """, "3\n2\n1", tmp_path)


def test_pop_bare_statement(tmp_path):
    assert_runs("""
        xs = [1, 2, 3]
        xs.pop()
        print(len(xs))
    """, "2", tmp_path)


def test_pop_string_list(tmp_path):
    assert_runs("""
        xs = ["a", "b", "c"]
        s = xs.pop()
        print(s)
        print(len(xs))
    """, "c\n2", tmp_path)


def test_pop_after_push(tmp_path):
    assert_runs("""
        xs = [1, 2]
        xs.append(3)
        x = xs.pop()
        print(x)
        print(len(xs))
    """, "3\n2", tmp_path)


def test_pop_in_loop(tmp_path):
    assert_runs("""
        xs = [10, 20, 30]
        while len(xs) > 0:
            print(xs.pop())
    """, "30\n20\n10", tmp_path)


def test_pop_takes_no_args(tmp_path):
    rc, out, err = run_is("""
        xs = [1, 2, 3]
        x = xs.pop(0)
    """, tmp_path)
    assert rc != 0, f"expected failure, got rc=0\nOUT:\n{out}\nERR:\n{err}"
    assert "pop() takes no arguments" in (out + err), (
        f"expected arity error, got:\n{out}\n{err}"
    )
