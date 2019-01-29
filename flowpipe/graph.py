"""A Graph of Nodes."""
from __future__ import print_function
from __future__ import absolute_import

from typing import Optional, List, Union, Dict, Any

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict # type: ignore

from ascii_canvas.canvas import Canvas
from ascii_canvas.item import Item
from ascii_canvas.item import Line

from .node import INode
from .log_observer import LogObserver
from .utilities import import_class
__all__ = ['Graph']


class Graph(object):
    """A graph of Nodes."""

    def __init__(self, name: Optional[str] = None, nodes: List[Union[INode, "Graph"]] = None) -> None:
        """Initialize the list of Nodes."""
        self.name = name or self.__class__.__name__
        self._nodes = nodes or []

    def __unicode__(self) -> str:
        """Display the Graph."""
        return self.node_repr()

    def __str__(self) -> str:
        """Show all input and output Plugs."""
        return self.__unicode__().encode('utf-8').decode()

    def __getitem__(self, key) -> INode:
        """Grant access to Nodes via their name."""
        for node in self.nodes:
            if node.name == key:
                return node
        raise Exception(
            "Graph does not contain a Node named '{0}'".format(key))

    @property
    def nodes(self) -> List[INode]:
        """Aggregate the Nodes of this Graph and all it's sub graphs."""
        nodes: List[INode] = []
        for node in self._nodes:
            if isinstance(node, Graph):
                nodes += node.nodes
            else:
                nodes.append(node)
        return nodes

    @property
    def evaluation_matrix(self) -> List[List[INode]]:
        """Sort nodes into a 2D matrix based on their dependency.

        Rows affect each other and have to be evaluated in sequence.
        The Nodes on each row however can be evaluated in parallel as
        they are independent of each other.
        The amount of Nodes in each row can vary.

        Returns:
            (list of list of INode): Each sub list represents a row.
        """
        levels: Dict[INode, int] = {}

        for node in self.nodes:
            self._sort_node(node, levels, level=0)

        matrix = []
        for level in sorted(list(set(levels.values()))):
            row = []
            for node in [n for n in levels if levels[n] == level]:
                row.append(node)
            matrix.append(row)

        return matrix

    @property
    def evaluation_sequence(self) -> List[INode]:
        """Sort Nodes into a sequential, flat execution order.

        Returns:
            (list of INode): A one dimensional representation of the
                evaluation matrix.
        """
        return [node for row in self.evaluation_matrix for node in row]

    def add_node(self, node: Union[INode, "Graph"]) -> None:
        """Add given Node to the Graph.

        Nodes on a Graph have to have unique names.
        """
        if node not in self.nodes:
            for existing_node in self.nodes:
                if existing_node.name == node.name:
                    raise Exception(
                        "Can not add Node of name '{0}', a Node with this "
                        "name already exists on this Graph. Node names on "
                        "a Graph have to be unique.".format(node.name))
            self._nodes.append(node)
        else:
            LogObserver.push_message(
                "Node '{0}' is already part of this Graph".format(node.name))

    def evaluate(self, *args, **kwargs) -> None:
        """Evaluate all Nodes."""
        LogObserver.push_message("Evaluating Graph '{0}'".format(self.name))
        for node in self.evaluation_sequence:
            node.evaluate()

    def serialize(self) -> OrderedDict:
        """Serialize the graph in it's grid form."""
        data: OrderedDict[str, Any] = OrderedDict(
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name)
        data['nodes'] = [node.serialize() for node in self.nodes]
        return data

    @staticmethod
    def deserialize(data: OrderedDict) -> "Graph":
        """De-serialize from the given json data."""
        graph = import_class(data['module'], data['cls'])()
        graph._nodes = []

        for node in data['nodes']:
            graph._nodes.append(INode.deserialize(node))

        for node in data['nodes']:
            this = [n for n in graph.nodes
                    if n.identifier == node['identifier']][0]

            for name, input_ in node['inputs'].items():
                for identifier, plug in input_['connections'].items():
                    upstream = [n for n in graph.nodes
                                if n.identifier == identifier][0]
                    upstream.outputs[plug] >> this.inputs[name]

        return graph

    def _sort_node(self, node: INode, parent: Dict[INode, int], level: int) -> None:
        """Sort the node into the correct level."""
        if node in parent.keys():
            if level > parent[node]:
                parent[node] = level
        else:
            parent[node] = level

        for downstream_node in node.downstream_nodes:
            self._sort_node(downstream_node, parent, level=level + 1)

    def node_repr(self) -> str:
        """Format to visualize the Graph."""
        canvas = Canvas()
        x = 0
        for row in self.evaluation_matrix:
            y = 0
            x_diff = 0

            node: INode
            for j, node in enumerate(row):
                item = Item(str(node), [x, y])
                node.item = item
                x_diff = (item.bbox[2] - item.bbox[0] + 4 if
                          item.bbox[2] - item.bbox[0] + 4 > x_diff else x_diff)
                y += item.bbox[3] - item.bbox[1]
                canvas.add_item(item)
            x += x_diff

        for node in self.nodes:
            for j, plug in enumerate(node.sort_plugs(node.outputs)):
                for connection in node.sort_plugs(node.outputs)[plug].connections:
                    dnode = connection.node
                    start = [node.item.position[0] + node.item.bbox[2],
                             node.item.position[1] + 3 + len(node.inputs) + j]

                    end = [dnode.item.position[0],
                           dnode.item.position[1] + 3 +
                           list(dnode.sort_plugs(dnode.inputs).values()).index(connection)]

                    canvas.add_item(Line(start, end), 0)
        return canvas.render()

    def list_repr(self) -> str:
        """List representation of the graph showing Nodes and connections."""
        pretty = list()
        pretty.append(self.name)
        for node in self.evaluation_sequence:
            pretty.append(node.list_repr())

        return '\n '.join(pretty)
