"""Module-level DI container singleton.

Provides a shared ``Container`` instance and a ``component`` decorator
that can be used on class definitions to register them at import time::

    from appContainer import component

    @component
    class MyService:
        ...

Factory registrations and runtime instances are added in
``bootstrap.py`` using the same ``container`` reference.
"""

from di import Container

container = Container()
component = container.component
