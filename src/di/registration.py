"""Internal registration record used by the DI container."""


class _Registration:
    """Internal record that stores how a type should be resolved."""

    __slots__ = ("factory", "lifetime", "instance")

    def __init__(self, factory, lifetime):
        self.factory = factory
        self.lifetime = lifetime
        self.instance = None
