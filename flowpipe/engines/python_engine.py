"""Evaluate Graphs in the current Python session."""
from flowpipe.engine import IEngine


class PythonEngine(IEngine):
    """Evaluate Graphs in the current Python session."""

    def evaluate_entire_graph(self, graph):
        """Evaluate all nodes in the graph."""
        graph.evaluate()

    def evaluate_dirty_nodes(self, graph):
        """Evaluate the dirty nodes in the graph."""
        for node in graph.evaluation_sequence:
            if node.is_dirty:
                node.evaluate()
