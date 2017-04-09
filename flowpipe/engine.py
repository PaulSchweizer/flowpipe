"""Evaluate a graph of FlowNodes."""
__all__ = ['FlowEngine']


class FlowEngine(object):
    """Evaluate a graph of FlowNodes."""

    nodes = list()

    def load_app(self, app):
        """Load an application into the engine."""
        self.nodes = app.nodes
    # end def load_app

    def evaluate(self):
        """Evaluate the registered nodes."""
        for node in self.evaluation_sequence:
            node.evaluate()
        # end for
    # end def evaluate

    @property
    def evaluation_sequence(self):
        """The sequence in which the nodes need to be evaluated."""
        levels = dict()

        for node in self.nodes:
            self._sort_node(node, levels, level=0)
        # end for

        sequence = list()
        for level in sorted(list(set(levels.values()))):
            for node in [n for n in levels if levels[n] == level]:
                sequence.append(node)
        # end for

        return sequence
    # end def evaluation_sequence

    def _sort_node(self, node, parent, level):
        """Sort the node into the correct level."""
        if node in parent.keys():
            if level > parent[node]:
                parent[node] = level
        else:
            parent[node] = level

        for downstream_node in node.downstream_nodes:
            self._sort_node(downstream_node, parent, level=level + 1)
        # end for
    # end def _sort_node
# end class FlowEngine
