"""Evaluate a graph of Nodes."""
from __future__ import print_function
__all__ = ['Engine']


class Engine(object):
    """Evaluate a graph of Nodes."""

    @staticmethod
    def evaluation_sequence(nodes):
        """The sequence in which the nodes need to be evaluated."""
        levels = dict()

        for node in nodes:
            Engine._sort_node(node, levels, level=0)

        sequence = list()
        for level in sorted(list(set(levels.values()))):
            for node in [n for n in levels if levels[n] == level]:
                sequence.append(node)

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
    # end def _sort_node

    @staticmethod
    def evaluate(nodes):
        """Evaluate the dirty nodes in the graph."""
        sequence = Engine.evaluation_sequence(nodes)
        dirty_nodes = Engine.get_dirty_nodes(sequence)
        while dirty_nodes:
            for node in dirty_nodes:
                node.evaluate()
            dirty_nodes = Engine.get_dirty_nodes(sequence)
    # end def evaluate

    @staticmethod
    def get_dirty_nodes(nodes):
        """Test whether any of the given nodes needs evaluation."""
        return [n for n in nodes if n.is_dirty]
    # end def get_dirty_nodes

    @staticmethod
    def graph_is_dirty(nodes):
        """Test whether any of the given nodes needs evaluation."""
        return True in [n.is_dirty for n in nodes]
    # end def graph_is_dirty
# end class Engine
