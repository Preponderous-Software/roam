"""Synchronous stand-ins for thread-based concurrency primitives in Pyodide.

Pyodide's CDN WASM build cannot spawn OS threads, so
``concurrent.futures.ThreadPoolExecutor`` usage would fail at runtime.
These classes run submitted tasks inline so all callers work without
modification.

This module has no Pyodide dependency so it can be imported and tested in a
normal CPython environment.
"""


class _PyodideFuture:
    """Minimal Future-like container returned by _PyodideExecutor.submit()."""

    _result = None
    _exc = None

    def result(self, timeout=None):
        if self._exc is not None:
            raise self._exc
        return self._result


class _PyodideExecutor:
    """Synchronous stand-in for ``concurrent.futures.ThreadPoolExecutor``.

    Accepts the same constructor signature (``max_workers``, ``thread_name_prefix``,
    etc.) so existing call-sites like ``ThreadPoolExecutor(max_workers=4)`` work
    without change.  Every ``submit()`` call runs the callable inline on the
    current thread and wraps the result in a ``_PyodideFuture``.
    """

    def __init__(self, *args, **kwargs):
        pass

    def submit(self, fn, /, *args, **kwargs):
        f = _PyodideFuture()
        try:
            f._result = fn(*args, **kwargs)
        except Exception as e:
            f._exc = e
        return f

    def shutdown(self, wait=True, cancel_futures=False):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.shutdown()
