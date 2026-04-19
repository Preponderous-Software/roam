"""Tests for the dependency injection container."""

import pytest
from di import Container, DIError


# ---------------------------------------------------------------------------
# Helper classes used by the tests
# ---------------------------------------------------------------------------


class ServiceA:
    pass


class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a


class ServiceC:
    def __init__(self, b: ServiceB):
        self.b = b


class CircularA:
    def __init__(self, other: "CircularB"):
        self.other = other


class CircularB:
    def __init__(self, other: CircularA):
        self.other = other


class WithDefault:
    def __init__(self, a: ServiceA, name: str = "default"):
        self.a = a
        self.name = name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_resolve_class_with_no_dependencies():
    container = Container()
    container.register(ServiceA, ServiceA)
    instance = container.resolve(ServiceA)
    assert isinstance(instance, ServiceA)


def test_resolve_recursive_dependencies():
    container = Container()
    container.register(ServiceA, ServiceA)
    container.register(ServiceB, ServiceB)
    container.register(ServiceC, ServiceC)
    instance = container.resolve(ServiceC)
    assert isinstance(instance, ServiceC)
    assert isinstance(instance.b, ServiceB)
    assert isinstance(instance.b.a, ServiceA)


def test_singleton_lifetime_returns_same_instance():
    container = Container()
    container.register(ServiceA, ServiceA, lifetime="singleton")
    first = container.resolve(ServiceA)
    second = container.resolve(ServiceA)
    assert first is second


def test_transient_lifetime_returns_different_instances():
    container = Container()
    container.register(ServiceA, ServiceA, lifetime="transient")
    first = container.resolve(ServiceA)
    second = container.resolve(ServiceA)
    assert first is not second


def test_register_and_resolve_prebuilt_instance():
    container = Container()
    prebuilt = ServiceA()
    container.registerInstance(ServiceA, prebuilt)
    resolved = container.resolve(ServiceA)
    assert resolved is prebuilt


def test_error_on_unregistered_type():
    container = Container()
    with pytest.raises(DIError, match="not registered"):
        container.resolve(ServiceA)


def test_error_on_circular_dependency():
    container = Container()
    container.register(CircularA, CircularA)
    container.register(CircularB, CircularB)
    with pytest.raises(DIError, match="Circular dependency") as exc_info:
        container.resolve(CircularA)
    # Verify the chain is deterministically ordered
    msg = str(exc_info.value)
    assert "CircularA" in msg
    assert "CircularB" in msg
    arrow_idx_a = msg.index("CircularA")
    arrow_idx_b = msg.index("CircularB")
    assert arrow_idx_a < arrow_idx_b


def test_component_decorator_registers_class():
    container = Container()

    @container.component
    class Decorated:
        pass

    instance = container.resolve(Decorated)
    assert isinstance(instance, Decorated)


def test_component_decorator_with_lifetime():
    container = Container()

    @container.component(lifetime="transient")
    class TransientDecorated:
        pass

    first = container.resolve(TransientDecorated)
    second = container.resolve(TransientDecorated)
    assert first is not second


def test_resolve_with_default_parameter():
    container = Container()
    container.register(ServiceA, ServiceA)
    container.register(WithDefault, WithDefault)
    instance = container.resolve(WithDefault)
    assert isinstance(instance, WithDefault)
    assert isinstance(instance.a, ServiceA)
    assert instance.name == "default"


def test_invalid_lifetime_raises_error():
    container = Container()
    with pytest.raises(DIError, match="Invalid lifetime"):
        container.register(ServiceA, ServiceA, lifetime="invalid")


def test_instance_registration_used_in_autowiring():
    container = Container()
    prebuilt_a = ServiceA()
    container.registerInstance(ServiceA, prebuilt_a)
    container.register(ServiceB, ServiceB)
    b = container.resolve(ServiceB)
    assert b.a is prebuilt_a


def test_factory_function_autowiring():
    container = Container()
    container.register(ServiceA, ServiceA)

    def create_b(a: ServiceA) -> ServiceB:
        return ServiceB(a)

    container.register(ServiceB, create_b)
    b = container.resolve(ServiceB)
    assert isinstance(b, ServiceB)
    assert isinstance(b.a, ServiceA)


def test_reset_singletons_clears_cached_instances():
    container = Container()
    container.register(ServiceA, ServiceA)
    first = container.resolve(ServiceA)
    assert first is container.resolve(ServiceA)
    container.resetSingletons()
    second = container.resolve(ServiceA)
    assert second is not first
    assert isinstance(second, ServiceA)


def test_reset_singletons_preserves_explicit_instances():
    container = Container()
    prebuilt = ServiceA()
    container.registerInstance(ServiceA, prebuilt)
    assert container.resolve(ServiceA) is prebuilt
    container.resetSingletons()
    # Explicit instances (factory=None) survive the reset.
    assert container.resolve(ServiceA) is prebuilt
