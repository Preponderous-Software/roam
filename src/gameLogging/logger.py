"""Central structured logging module for Roam.

Initialises structlog at import time and exports helpers for use
throughout the application.

Environment variables
---------------------
LOG_LEVEL : str
    Minimum log level (default: ``INFO``).
    Accepted values: DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL.
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
# Configuration from environment
# ---------------------------------------------------------------------------
_VALID_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LOG_LEVEL_NAME = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
_LOG_LEVEL = _VALID_LEVELS.get(_LOG_LEVEL_NAME, logging.INFO)
_LOG_FORMAT = os.environ.get("LOG_FORMAT", "pretty").strip().lower()

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
    """Configure structlog processors and output format.

    Uses stdlib logging as the backend so that ``_LOG_LEVEL`` is respected
    for filtering.
    """
    # Configure stdlib root logger so the level gate works.
    logging.basicConfig(format="%(message)s", stream=sys.stderr, level=_LOG_LEVEL)

    shared_processors = [
        structlog.stdlib.filter_by_level,
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
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Install a ProcessorFormatter on the root handler so structlog
    # processors render the final output.
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
    )
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


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
