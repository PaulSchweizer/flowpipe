"""Evaluate a graph of Nodes."""
__all__ = ['Engine']


class Engine(object):
    """Evaluate a graph of Nodes."""

    @staticmethod
    def evaluation_sequence(nodes):
        """The sequence in which the nodes need to be evaluated."""
        levels = dict()

        for node in nodes:
            Engine._sort_node(node, levels, level=0)
        # end for

        sequence = list()
        for level in sorted(list(set(levels.values()))):
            for node in [n for n in levels if levels[n] == level]:
                sequence.append(node)
        # end for

        return sequence
    # end def evaluation_sequence

    @staticmethod
    def _sort_node(node, parent, level):
        """Sort the node into the correct level."""
        if node in parent.keys():
            if level > parent[node]:
                parent[node] = level
        else:
            parent[node] = level

        for downstream_node in node.downstream_nodes:
            Engine._sort_node(downstream_node, parent, level=level + 1)
        # end for
    # end def _sort_node

    @staticmethod
    def evaluate(nodes):
        """Evaluate the dirty nodes in the graph."""
        for node in Engine.evaluation_sequence(nodes):
            if node.is_dirty:
                node.evaluate()
            # end if
        # end for
    # end def evaluate
# end class Engine
