"""Exceptions raised by flowpipe."""


class CycleError(Exception):
    """Raised when an action would result in a cycle in a graph."""


class FlowpipeMultiprocessingError(Exception):
    """Raised when a Node can not be pickled, most likely due to inputs not being picklable."""
