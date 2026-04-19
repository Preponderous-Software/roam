"""Dependency injection package — public API re-exports.

All consumer code should import from ``di`` rather than ``di.container``.
"""

from di.container import Container
from di.error import DIError

__all__ = ["Container", "DIError"]
