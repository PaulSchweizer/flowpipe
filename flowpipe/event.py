"""Events are emitted during node evaluation.

They an be used to observe the evaluation process.
"""

import logging
from collections.abc import Callable

log = logging.getLogger(__name__)


class Event:
    """Very simple implementation of an event system.event

    The event simply calls the registered functions with the given arguments.
    Please note that the integrity of the listeners is not enforced or checked.
    """

    def __init__(self, name: str):
        """Initialize the list of listeners

        Args:
            name (str): The (unique) name of the signal
        """
        self.name = name
        self._listeners:list[Callable] = []

    def emit(self, *args, **kwargs) -> None:
        """Call all the listeners with the given args and kwargs."""
        for listener in self._listeners:
            listener(*args, **kwargs)

    def register(self, listener: Callable) -> None:
        """Register the given function object if it is not yet registered."""
        if not self.is_registered(listener):
            self._listeners.append(listener)

    def deregister(self, listener: Callable) -> None:
        """Deregister the given function object if it is registered."""
        if self.is_registered(listener):
            self._listeners.pop(self._listeners.index(listener))
            log.debug("%s deregistered", listener)
        else:
            log.exception("%s was never registered", listener)

    def is_registered(self, listener: Callable) -> bool:
        """Whether the given function object is already registered."""
        return listener in self._listeners

    def clear(self) -> None:
        """Remove all listeners from this event."""
        for listener in self._listeners:
            self.deregister(listener)
