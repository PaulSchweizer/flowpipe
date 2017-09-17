"""Evaluate a Graph of Nodes."""
from __future__ import print_function
__all__ = ['IEngine']


class IEngine(object):
    """Implement per Interpreter."""

    def evaluate_entire_graph(self, graph):
        """Evaluate all nodes in the graph."""
        raise NotImplementedError

    def evaluate_dirty_nodes(self, graph):
        """Evaluate the dirty nodes in the graph."""
        raise NotImplementedError
