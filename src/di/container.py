"""Lightweight, self-contained dependency injection container.

Uses only Python standard library modules. Designed to be extracted and
reused in other projects with no modifications.
"""

import inspect
import threading
import typing


class DIError(Exception):
    """Raised when the container encounters a resolution or registration problem."""


class _Registration:
    """Internal record that stores how a type should be resolved."""

    __slots__ = ("factory", "lifetime", "instance")

    def __init__(self, factory, lifetime):
        self.factory = factory
        self.lifetime = lifetime
        self.instance = None


class Container:
    """Dependency injection container with singleton and transient lifetimes.

    Supports registration by type, auto-wiring via type hints, explicit
    instance registration, and a decorator for registration at definition time.
    """

    def __init__(self):
        self._registrations = {}
        self._lock = threading.Lock()

    def register(self, abstractType, concreteType, lifetime="singleton"):
        """Register a concrete type or factory callable against an abstract type.

        Args:
            abstractType: The type used as the lookup key when resolving.
            concreteType: A class or callable that produces the instance.
            lifetime: Either ``"singleton"`` (default) or ``"transient"``.
        """
        if lifetime not in ("singleton", "transient"):
            raise DIError(
                "Invalid lifetime '"
                + str(lifetime)
                + "'. Must be 'singleton' or 'transient'."
            )
        with self._lock:
            self._registrations[abstractType] = _Registration(concreteType, lifetime)

    def registerInstance(self, abstractType, instance):
        """Register a pre-built instance against an abstract type.

        The instance is returned on every subsequent resolve call for the type.
        """
        with self._lock:
            reg = _Registration(None, "singleton")
            reg.instance = instance
            self._registrations[abstractType] = reg

    def resolve(self, abstractType):
        """Resolve an instance for the given type.

        Auto-wires constructor parameters by recursively resolving type hints.
        Raises ``DIError`` for unregistered types or circular dependencies.
        """
        return self._resolve(abstractType, ())

    def component(self, cls=None, *, lifetime="singleton"):
        """Decorator that registers a class with the container at definition time.

        Can be used with or without arguments::

            @container.component
            class MyService:
                ...

            @container.component(lifetime="transient")
            class MyOtherService:
                ...
        """
        if cls is not None:
            self.register(cls, cls, lifetime=lifetime)
            return cls

        def decorator(innerCls):
            self.register(innerCls, innerCls, lifetime=lifetime)
            return innerCls

        return decorator

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, abstractType, resolutionPath):
        """Recursively resolve *abstractType*, detecting circular dependencies."""
        if abstractType not in self._registrations:
            raise DIError(
                "Type '"
                + str(abstractType)
                + "' is not registered with the container."
            )

        reg = self._registrations[abstractType]

        # Return cached singleton instance if available.
        if reg.instance is not None:
            return reg.instance

        # Circular dependency guard.
        if abstractType in {t for t in resolutionPath}:
            chain = " -> ".join(str(t) for t in resolutionPath)
            chain += " -> " + str(abstractType)
            raise DIError("Circular dependency detected: " + chain)

        resolutionPath = resolutionPath + (abstractType,)

        # Build the instance via auto-wiring.
        instance = self._createInstance(reg.factory, resolutionPath)

        # Cache singletons.
        if reg.lifetime == "singleton":
            with self._lock:
                if reg.instance is None:
                    reg.instance = instance

            return reg.instance

        return instance

    def _createInstance(self, factory, resolutionPath):
        """Instantiate *factory* by resolving its ``__init__`` parameters."""
        try:
            if inspect.isclass(factory):
                hintsSource = factory.__init__
            else:
                hintsSource = factory
            hints = typing.get_type_hints(hintsSource)
        except Exception as exc:
            raise DIError(
                "Failed to evaluate type hints for '"
                + str(factory)
                + "': "
                + str(exc)
            ) from exc

        sig = inspect.signature(factory)
        kwargs = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            paramType = hints.get(name)
            if paramType is not None and paramType in self._registrations:
                kwargs[name] = self._resolve(paramType, resolutionPath)
            elif param.default is not inspect.Parameter.empty:
                continue
            else:
                if paramType is not None:
                    raise DIError(
                        "Cannot resolve parameter '"
                        + name
                        + "' of type '"
                        + str(paramType)
                        + "' for '"
                        + str(factory)
                        + "'. Type is not registered."
                    )
                raise DIError(
                    "Cannot resolve parameter '"
                    + name
                    + "' for '"
                    + str(factory)
                    + "'. No type hint and no default value."
                )
        return factory(**kwargs)
