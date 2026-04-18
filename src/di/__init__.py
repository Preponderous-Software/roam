"""Dependency injection package — public API re-exports.

All consumer code should import from ``di`` rather than ``di.container``.
"""

from di.container import Container, DIError

__all__ = ["Container", "DIError"]
