"""Central structured logging module for Roam.

Initialises structlog at import time and exports helpers for use
throughout the application.

Environment variables
---------------------
LOG_LEVEL : str
    Minimum log level (default: ``INFO``).
    Accepted values: TRACE, DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL.
LOG_FORMAT : str
    Output format — ``json`` for machine-readable output or ``pretty``
    for human-readable coloured output (default: ``pretty``).
"""

import logging
import os
import re
import sys

import structlog


# ---------------------------------------------------------------------------
# Custom TRACE level (below DEBUG)
# ---------------------------------------------------------------------------
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
_VALID_LEVELS = {
    "TRACE": TRACE_LEVEL,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = _VALID_LEVELS.get(_LOG_LEVEL_NAME, logging.INFO)
_LOG_FORMAT = os.environ.get("LOG_FORMAT", "pretty").lower()

# ---------------------------------------------------------------------------
# Redaction helper
# ---------------------------------------------------------------------------
_REDACT_PATTERNS = [
    re.compile(r"(token|password|secret|api_key|private_key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9+/]{40,}", re.IGNORECASE),
]


def redact(value):
    """Replace sensitive data in *value* with ``[REDACTED]``.

    Handles tokens, passwords, API keys, and private keys.
    """
    if not isinstance(value, str):
        return value
    result = value
    for pattern in _REDACT_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


# ---------------------------------------------------------------------------
# structlog configuration
# ---------------------------------------------------------------------------
def _configureStructlog():
    """Configure structlog processors and output format."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if _LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


_configureStructlog()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def getLogger(name):
    """Return a named structured logger instance.

    Usage::

        from gameLogging.logger import getLogger
        logger = getLogger(__name__)
        logger.info("something happened", key="value")
    """
    return structlog.get_logger(name)


class LoggerFactory:
    """Singleton service registered in the DI container.

    Provides ``getLogger(name)`` so DI-wired classes can obtain loggers.
    """

    def getLogger(self, name):
        return getLogger(name)
