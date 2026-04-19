"""Tests for the gameLogging.logger module."""

from gameLogging.logger import getLogger, redact, LoggerFactory


def test_getLogger_returns_bound_logger():
    logger = getLogger("test.module")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")


def test_getLogger_different_names_return_loggers():
    logger1 = getLogger("module.a")
    logger2 = getLogger("module.b")
    assert logger1 is not None
    assert logger2 is not None


def test_redact_replaces_token():
    result = redact("token: abc123def456")
    assert "abc123def456" not in result
    assert "[REDACTED]" in result


def test_redact_replaces_password():
    result = redact("password=mysecretpassword")
    assert "mysecretpassword" not in result
    assert "[REDACTED]" in result


def test_redact_non_string_passthrough():
    assert redact(42) == 42
    assert redact(None) is None
    assert redact([1, 2]) == [1, 2]


def test_redact_safe_string_unchanged():
    safe = "hello world"
    assert redact(safe) == safe


def test_logger_factory_get_logger():
    factory = LoggerFactory()
    logger = factory.getLogger("test")
    assert logger is not None
    assert hasattr(logger, "info")
