"""Push log messages to observer for redistribution.

Allows to easily pipe logs and messages to a UI.
"""
import logging

from flowpipe import logger


class LogObserver(object):
    """Redistributes messages to observing listener functions."""

    ## Registered listener functions
    listeners = list()

    @staticmethod
    def register_listener(listener):
        """Add the given function as a listener."""
        if listener not in LogObserver.listeners:
            LogObserver.listeners.append(listener)
    # end def register_listener

    @staticmethod
    def deregister_listener(listener):
        """Remove the given function from the listeners."""
        if listener in LogObserver.listeners:
            LogObserver.listeners.pop(LogObserver.listeners.index(listener))
    # end def deregister_listener

    @staticmethod
    def push_message(message, level=logging.DEBUG):
        """Push the message to all registered listeners and log it."""
        for listener in LogObserver.listeners:
            listener(message, level)
        logger.log(level, message)
    # end def push_message
# end class LogObserver
