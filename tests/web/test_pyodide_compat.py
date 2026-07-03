"""Tests for the Pyodide-compatibility executor shim (web/pyodide_compat.py).

These run in standard CPython — no Pyodide dependency required.
"""
import pytest

from pyodide_compat import _PyodideExecutor, _PyodideFuture


# ── _PyodideExecutor constructor ─────────────────────────────────────────────


def test_executor_no_args():
    ex = _PyodideExecutor()
    assert ex is not None


def test_executor_positional_max_workers():
    ex = _PyodideExecutor(4)
    assert ex is not None


def test_executor_keyword_max_workers():
    ex = _PyodideExecutor(max_workers=2)
    assert ex is not None


def test_executor_all_threadpoolexecutor_kwargs():
    ex = _PyodideExecutor(max_workers=4, thread_name_prefix="worker", initializer=None)
    assert ex is not None


# ── submit: successful calls ──────────────────────────────────────────────────


def test_submit_returns_future():
    ex = _PyodideExecutor()
    f = ex.submit(lambda: 42)
    assert isinstance(f, _PyodideFuture)


def test_submit_runs_callable_inline():
    calls = []
    ex = _PyodideExecutor()
    ex.submit(calls.append, "ran")
    assert calls == ["ran"]


def test_submit_positional_args():
    ex = _PyodideExecutor()
    f = ex.submit(lambda x, y: x + y, 3, 4)
    assert f.result() == 7


def test_submit_keyword_args():
    ex = _PyodideExecutor()
    f = ex.submit(lambda a=0, b=0: a * b, a=3, b=5)
    assert f.result() == 15


def test_submit_mixed_args():
    ex = _PyodideExecutor()
    f = ex.submit(lambda x, y=0: x - y, 10, y=3)
    assert f.result() == 7


def test_submit_string_result():
    ex = _PyodideExecutor()
    f = ex.submit(str, 99)
    assert f.result() == "99"


# ── submit: exception capture ─────────────────────────────────────────────────


def test_submit_captures_exception():
    ex = _PyodideExecutor()
    f = ex.submit(lambda: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        f.result()


def test_submit_captures_value_error():
    ex = _PyodideExecutor()
    f = ex.submit(int, "not-a-number")
    with pytest.raises(ValueError):
        f.result()


def test_future_result_raises_same_exception_instance():
    ex = _PyodideExecutor()
    err = RuntimeError("boom")
    f = ex.submit(lambda: (_ for _ in ()).throw(err))
    with pytest.raises(RuntimeError, match="boom"):
        f.result()


# ── context manager ───────────────────────────────────────────────────────────


def test_context_manager_returns_executor():
    with _PyodideExecutor() as ex:
        assert isinstance(ex, _PyodideExecutor)


def test_context_manager_submit_works():
    with _PyodideExecutor() as ex:
        f = ex.submit(lambda: "ok")
    assert f.result() == "ok"


# ── shutdown ──────────────────────────────────────────────────────────────────


def test_shutdown_is_safe_to_call():
    ex = _PyodideExecutor()
    ex.shutdown()
    ex.shutdown(wait=False, cancel_futures=True)
