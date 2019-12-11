"""Events are emitted during node evaluation.

They an be used to observe the evaluation process.
"""
import logging


log = logging.getLogger(__name__)


class Event(object):
    """Very simple implementation of an event system.event

    The event simply calls the registered functions with the given arguments.
    Please note that the integrity of the listeners is not enforced or checked.
    """

    def __init__(self, name):
        """Initialize the list of listeners

        Args:
            name (str): The (unique) name of the signal
        """
        self.name = name
        self._listeners = []

    def emit(self, *args, **kwargs):
        """Call all the listeners with the given args and kwargs."""
        for listener in self._listeners:
            listener(*args, **kwargs)

    def register(self, listener):
        """Register the given function object if it is not yet registered."""
        if not self.is_registered(listener):
            self._listeners.append(listener)

    def deregister(self, listener):
        """Deregister the given function object if it is registered."""
        if self.is_registered(listener):
            self._listeners.pop(self._listeners.index(listener))
            log.debug("{0} deregistered".format(listener))
        else:
            log.exception("{0} was never registered".format(listener))

    def is_registered(self, listener):
        """Whether the given function object is already registered."""
        return listener in self._listeners
