"""Evaluate a Graph of Nodes."""
from __future__ import print_function
__all__ = ['Engine']


class Engine(object):
    """Evaluate a Graph of Nodes."""

    @staticmethod
    def evaluate_entire_graph(graph):
        """Evaluate the dirty nodes in the graph."""
        for node in graph.evaluation_sequence:
            node.evaluate()
    # end def evaluate_entire_graph

    @staticmethod
    def evaluate_dirty_nodes(graph):
        """Evaluate the dirty nodes in the graph."""
        for node in graph.evaluation_sequence:
            if node.is_dirty:
                node.evaluate()
    # end def evaluate_dirty_nodes
# end class Engine
