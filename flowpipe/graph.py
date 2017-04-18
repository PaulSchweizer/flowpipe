"""A Graph of Nodes."""
from __future__ import print_function
__all__ = ['Graph']


class Graph(object):
    """A graph of Nodes."""

    def __init__(self, nodes=list()):
        """Initialize the list of Nodes."""
        self.nodes = nodes
    # end def __init__

    @property
    def is_dirty(self):
        """Test whether any of the given nodes needs evaluation."""
        return True in [n.is_dirty for n in self.nodes]
    # end def is_dirty

    @property
    def dirty_nodes(self):
        """Test whether any of the given nodes needs evaluation."""
        return [n for n in self.nodes if n.is_dirty]
    # end def dirty_nodes

    @property
    def evaluation_grid(self):
        """The nodes sorted into a 2D grid based on their dependency.

        Rows affect each other and have to be evaluated in sequence.
        The Nodes on each row however can be evaluated in parallel as
        they are independent of each other.
        The amount of Nodes in each row can vary.
        Returns:
            (list of list of INode): Each sub list represents a row.
        """
        levels = dict()
        for node in self.nodes:
            self._sort_node(node, levels, level=0)

        grid = list()
        for level in sorted(list(set(levels.values()))):
            row = list()
            for node in [n for n in levels if levels[n] == level]:
                row.append(node)
            grid.append(row)

        return grid
    # end def evaluation_grid

    @property
    def evaluation_sequence(self):
        """A flat sequence in which the nodes need to be evaluated.

        Returns:
            (list of INode): A one dimensional representation of the
                evaluation grid.
        """
        return [node for row in self.evaluation_grid for node in row]
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
    # end def _sort_node
# end class Engine
