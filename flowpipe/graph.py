"""A Graph of Nodes."""
from __future__ import print_function
from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import threading
import time

from ascii_canvas import canvas
from ascii_canvas import item

from .log_observer import LogObserver
from .utilities import deserialize_graph
__all__ = ['Graph']


class Graph(object):
    """A graph of Nodes."""

    def __init__(self, name=None, nodes=None):
        """Initialize the list of Nodes."""
        self.name = name or self.__class__.__name__
        self._nodes = nodes or []

    def __unicode__(self):
        """Display the Graph."""
        return self.node_repr()

    def __str__(self):
        """Show all input and output Plugs."""
        return self.__unicode__().encode('utf-8').decode()

    def __getitem__(self, key):
        """Grant access to Nodes via their name."""
        for node in self.nodes:
            if node.name == key:
                return node
        raise KeyError(
            "Graph does not contain a Node named '{0}'".format(key))

    @property
    def nodes(self):
        """Aggregate the Nodes of this Graph and all it's sub graphs."""
        nodes = []
        for node in self._nodes:
            if isinstance(node, Graph):
                nodes += node.nodes
            else:
                nodes.append(node)
        return nodes

    @property
    def evaluation_matrix(self):
        """Sort nodes into a 2D matrix based on their dependency.

        Rows affect each other and have to be evaluated in sequence.
        The Nodes on each row however can be evaluated in parallel as
        they are independent of each other.
        The amount of Nodes in each row can vary.

        Returns:
            (list of list of INode): Each sub list represents a row.
        """
        levels = {}

        for node in self.nodes:
            self._sort_node(node, levels, level=0)

        matrix = []
        for level in sorted(list(set(levels.values()))):
            row = []
            for node in [n for n in levels if levels[n] == level]:
                row.append(node)
            row.sort(key=lambda key: key.name)
            matrix.append(row)

        return matrix

    @property
    def evaluation_sequence(self):
        """Sort Nodes into a sequential, flat execution order.

        Returns:
            (list of INode): A one dimensional representation of the
                evaluation matrix.
        """
        return [node for row in self.evaluation_matrix for node in row]

    def add_node(self, node):
        """Add given Node to the Graph.

        Nodes on a Graph have to have unique names.
        """
        if node not in self.nodes:
            for existing_node in self.nodes:
                if existing_node.name == node.name:
                    raise ValueError(
                        "Can not add Node of name '{0}', a Node with this "
                        "name already exists on this Graph. Node names on "
                        "a Graph have to be unique.".format(node.name))
            self._nodes.append(node)
        else:
            LogObserver.push_message(
                "Node '{0}' is already part of this Graph".format(node.name))

    def evaluate(self, threaded=False, submission_delay=0.1, raise_after=None):
        """Evaluate all Nodes.

        Args:
            threaded (bool): Whether to execute each node in a separate thread.
            submission_delay (float): The delay in seconds between loops
                issuing new threads if nodes are ready to process.
            raise_after (int): The number of loops without currently running
                threads after which to raise a RuntimeError.

        """
        LogObserver.push_message("Evaluating Graph '{0}'".format(self.name))
        if not threaded:
            for node in self.evaluation_sequence:
                node.evaluate()
        else:
            self._evaluate_threaded(submission_delay, raise_after)

    def _evaluate_threaded(self, submission_delay, raise_after_loops=None):
        threads = {}
        nodes_to_evaluate = list(self.evaluation_sequence)
        empty_loops = 0
        while True:
            for node in nodes_to_evaluate:
                if not node.is_dirty:
                    # If the node is done computing, drop it from the list
                    nodes_to_evaluate.remove(node)
                    continue
                if (node.name not in threads
                        and all(not n.is_dirty for n in node.upstream_nodes)):
                    # If all deps are ready and no thread is active, create one
                    threads[node.name] = threading.Thread(
                        target=node.evaluate,
                        name="flowpipe.{0}.{1}".format(self.name, node.name))
                    threads[node.name].start()

            graph_threads = [t for t in threading.enumerate()
                             if t.name.startswith(
                                 "flowpipe.{0}".format(self.name))]
            if len(graph_threads) == 0 \
                    and not all(not n.is_dirty for n in nodes_to_evaluate):  # pragma: no cover
                # No more threads running after a round of submissions means
                # we're either done or stuck
                if raise_after_loops is not None \
                        and empty_loops > raise_after_loops:
                    raise RuntimeError(
                        "Could not sucessfully compute all nodes in the "
                        "graph {0}".format(self.name))
                else:
                    empty_loops += 1

            if not nodes_to_evaluate:
                break
            time.sleep(submission_delay)

    def serialize(self):
        """Serialize the graph in it's grid form."""
        data = OrderedDict(
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name)
        data['nodes'] = [node.serialize() for node in self.nodes]
        return data

    @staticmethod
    def deserialize(data):
        """De-serialize from the given json data."""
        return deserialize_graph(data)

    def _sort_node(self, node, parent, level):
        """Sort the node into the correct level."""
        if node in parent.keys():
            if level > parent[node]:
                parent[node] = level
        else:
            parent[node] = level

        for downstream_node in node.downstream_nodes:
            self._sort_node(downstream_node, parent, level=level + 1)

    def node_repr(self):
        """Format to visualize the Graph."""
        canvas_ = canvas.Canvas()
        x = 0
        for row in self.evaluation_matrix:
            y = 0
            x_diff = 0
            for j, node in enumerate(row):
                item_ = item.Item(str(node), [x, y])
                node.item = item_
                x_diff = (item_.bbox[2] - item_.bbox[0] + 4 if
                          item_.bbox[2] - item_.bbox[0] + 4 > x_diff else x_diff)
                y += item_.bbox[3] - item_.bbox[1]
                canvas_.add_item(item_)
            x += x_diff

        for node in self.nodes:
            for j, plug in enumerate(node._sort_plugs(node.all_outputs())):
                for connection in node._sort_plugs(
                        node.all_outputs())[plug].connections:
                    dnode = connection.node
                    start = [node.item.position[0] + node.item.bbox[2],
                             node.item.position[1] + 3 + len(node.all_inputs()) + j]
                    end = [dnode.item.position[0],
                           dnode.item.position[1] + 3 +
                           list(dnode._sort_plugs(
                                dnode.all_inputs()).values()).index(
                                    connection)]
                    canvas_.add_item(item.Line(start, end), 0)
        return canvas_.render()

    def list_repr(self):
        """List representation of the graph showing Nodes and connections."""
        pretty = []
        pretty.append(self.name)
        for node in self.evaluation_sequence:
            pretty.append(node.list_repr())
        return '\n '.join(pretty)


default_graph = Graph(name='default')


def get_default_graph():
    """Retrieve the default graph."""
    return default_graph


def set_default_graph(graph):
    """Set a graph as the default graph."""
    if not isinstance(graph, Graph):
        raise TypeError("Can only set 'Graph' instances as default graph!")

    global default_graph
    default_graph = graph


def reset_default_graph():
    """Reset the default graph to an empty graph."""
    set_default_graph(Graph(name="default"))
