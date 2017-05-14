"""A Graph of Nodes."""
from __future__ import print_function

from flowpipe.node import INode
__all__ = ['Graph']


class Graph(INode):
    """A graph of Nodes."""

    def __init__(self, name=None, nodes=list()):
        """Initialize the list of Nodes."""
        super(Graph, self).__init__(name=name)
        self.nodes = nodes

    def __unicode__(self):
        """Show all input and output Plugs."""
        pretty = super(Graph, self).__unicode__()
        for row in self.evaluation_grid:
            pretty += '\n' + ' | '.join([n.name for n in row])
        return pretty

    @property
    def is_dirty(self):
        """Test whether any of the given nodes needs evaluation."""
        return True in [n.is_dirty for n in self.nodes]

    @property
    def dirty_nodes(self):
        """Test whether any of the given nodes needs evaluation."""
        return [n for n in self.nodes if n.is_dirty]

    @property
    def all_nodes(self):
        """Return all nodes, also from subgraphs."""
        all_nodes = list()
        for node in self.nodes:
            if isinstance(node, Graph):
                all_nodes += node.nodes
            elif isinstance(node, INode):
                all_nodes.append(node)
        return all_nodes

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

        for node in self.all_nodes:
            self._sort_node(node, levels, level=0)

        grid = list()
        for level in sorted(list(set(levels.values()))):
            row = list()
            for node in [n for n in levels if levels[n] == level]:
                row.append(node)
            grid.append(row)

        return grid

    @property
    def evaluation_sequence(self):
        """A flat sequence in which the nodes need to be evaluated.

        Returns:
            (list of INode): A one dimensional representation of the
                evaluation grid.
        """
        return [node for row in self.evaluation_grid for node in row]

    def compute(self, **args):
        """Evaluate all sub nodes."""
        for node in self.evaluation_sequence:
            node.evaluate()

    def serialize(self):
        """Serialize the graph in it's grid form."""
        return [node.serialize() for node in self.evaluation_sequence]

    def _sort_node(self, node, parent, level):
        """Sort the node into the correct level."""
        if node in parent.keys():
            if level > parent[node]:
                parent[node] = level
        else:
            parent[node] = level

        for downstream_node in node.downstream_nodes:
            self._sort_node(downstream_node, parent, level=level + 1)
