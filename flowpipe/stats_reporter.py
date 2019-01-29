"""Hook into the stats reporter to receive reports from flowpipe."""
from __future__ import print_function
from __future__ import absolute_import

from typing import Callable, Dict, List

__all__ = ['StatsReporter']


class StatsReporter(object):
    """Receive reports during node graph evaluation."""

    listeners: List[Callable] = list()

    @staticmethod
    def register_listener(listener: Callable) -> None:
        """Add the given function as a listener."""
        if listener not in StatsReporter.listeners:
            StatsReporter.listeners.append(listener)

    @staticmethod
    def deregister_listener(listener: Callable) -> None:
        """Remove the given function from the listeners."""
        if listener in StatsReporter.listeners:
            StatsReporter.listeners.pop(
                StatsReporter.listeners.index(listener))

    @staticmethod
    def push_stats(stats: Dict) -> None:
        """Push the stats to all registered listeners."""
        for listener in StatsReporter.listeners:
            listener(stats)
