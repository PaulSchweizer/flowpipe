"""Push log messages to observer for redistribution.

Allows to easily pipe logs and messages to a UI.
"""
from __future__ import print_function
from __future__ import absolute_import
import logging
from typing import Callable, List

from . import logger
__all__ = ['LogObserver']


class LogObserver(object):
    """Redistributes messages to observing listener functions."""

    # Registered listener functions
    listeners: List[Callable] = list()

    @staticmethod
    def register_listener(listener: Callable) -> None:
        """Add the given function as a listener."""
        if listener not in LogObserver.listeners:
            LogObserver.listeners.append(listener)

    @staticmethod
    def deregister_listener(listener: Callable) -> None:
        """Remove the given function from the listeners."""
        if listener in LogObserver.listeners:
            LogObserver.listeners.pop(LogObserver.listeners.index(listener))

    @staticmethod
    def push_message(message: str, level: int = logging.DEBUG) -> None:
        """Push the message to all registered listeners and log it."""
        for listener in LogObserver.listeners:
            listener(message, level)
        logger.log(level, message)
