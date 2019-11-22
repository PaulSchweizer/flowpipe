"""Exceptions raised by flowpipe."""


class CycleError(Exception):
    """Raised when an action would result in a cycle in a graph."""
