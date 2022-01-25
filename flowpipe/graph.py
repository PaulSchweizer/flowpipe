"""A Graph of Nodes."""
from __future__ import absolute_import, print_function

import logging
import pickle
import warnings

from ascii_canvas import canvas, item

from .errors import CycleError
from .evaluator import (
    LegacyMultiprocessingEvaluator,
    LinearEvaluator,
    ThreadedEvaluator,
)
from .plug import InputPlug, InputPlugGroup, OutputPlug
from .utilities import deserialize_graph

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

log = logging.getLogger(__name__)


class Graph(object):
    """A graph of Nodes."""

    def __init__(self, name=None, nodes=None):
        """Initialize the list of Nodes, inputs and outpus."""
        self.name = name or self.__class__.__name__
        self.nodes = nodes or []
        self.inputs = {}
        self.outputs = {}

    def __unicode__(self):
        """Display the Graph."""
        return self.node_repr()

    def __str__(self):
        """Show all input and output Plugs."""
        return self.__unicode__().encode("utf-8").decode()

    def __getitem__(self, key):
        """Grant access to Nodes via their name."""
        for node in self.nodes:
            if node.name == key:
                return node
        # Search through subgraphs if no node found on graph itself
        if "." in key:
            subgraph_name = key.split(".")[0]
            node_name = key.split(".")[-1]
            for node in self.all_nodes:
                if node.name == node_name and node.graph.name == subgraph_name:
                    return node

        raise KeyError(
            "Graph does not contain a Node named '{0}'. "
            "If the node is part of a subgraph of this graph, use this "
            "form to access the node: '{{subgraph.name}}.{{node.name}}', "
            "e.g. 'sub.node'".format(key)
        )

    @property
    def all_nodes(self):
        """Expand the graph with all its subgraphs into a flat list of nodes.

        Please note that in this expanded list, the node names are no longer
        guaranteed to be unique!

        Returns:
            (list of INode): All nodes, including the nodes from subgraphs
        """
        nodes = [n for n in self.nodes]
        for subgraph in self.subgraphs.values():
            nodes += subgraph.nodes
        return list(set(nodes))

    @property
    def subgraphs(self):
        """All other graphs that the nodes of this graph are connected to.

        Returns:
            A dict in the form of ``{graph.name: graph}``
        """
        subgraphs = {}
        for node in self.nodes:
            for downstream in node.downstream_nodes:
                if downstream.graph is not self:
                    subgraphs[downstream.graph.name] = downstream.graph
            for upstream in node.upstream_nodes:
                if upstream.graph is not self:
                    subgraphs[upstream.graph.name] = upstream.graph
        return subgraphs

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
        nodes_to_sort = set(self.all_nodes)
        levels = {}

        cache_upstream = {
            node: set(node.upstream_nodes) for node in nodes_to_sort
        }

        current_level = 0
        while nodes_to_sort:
            sorted_this_loop = False
            for node in nodes_to_sort:
                up_levels = [
                    levels.get(up_node) for up_node in cache_upstream[node]
                ]
                # Add level -1 to properly sort nodes without dependencies
                up_levels += [-1]

                if None not in up_levels and max(up_levels) < current_level:
                    # all upstream nodes are assigned lower levels,
                    # so this node goes on the this level
                    levels[node] = current_level
                    sorted_this_loop = True
            nodes_to_sort -= set(levels.keys())
            current_level += 1

            # this theoretically can't occur, but let's catch it anyways
            if not sorted_this_loop:  # pragma: no cover
                raise RuntimeError("Dependencies could not be resoled")

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

    @property
    def input_groups(self):
        """Return all inputs that are actually input groups."""
        return {
            k: v
            for k, v in self.inputs.items()
            if isinstance(v, InputPlugGroup)
        }

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
                        "a Graph have to be unique.".format(node.name)
                    )
            self.nodes.append(node)
            node.graph = self
        else:
            log.warning(
                'Node "{0}" is already part of this Graph'.format(node.name)
            )

    def delete_node(self, node):
        """Disconnect all plugs and then delete the node object."""
        if node in self.nodes:
            for plug in node.all_inputs().values():
                for connection in plug.connections:
                    plug.disconnect(connection)
            for plug in node.all_outputs().values():
                for connection in plug.connections:
                    plug.disconnect(connection)
            del self.nodes[self.nodes.index(node)]

    def add_plug(self, plug, name=None):
        """Promote the given plug this graph.

        Args:
            plug (flowpipe.plug.IPlug): The plug to promote to this graph
            name (str): Optionally use the given name instead of the name of
                the given plug
        """
        if isinstance(plug, InputPlug):
            if plug not in self.inputs.values():
                self.inputs[name or plug.name] = plug
            else:
                key = list(self.inputs.keys())[
                    list(self.inputs.values()).index(plug)
                ]
                raise ValueError(
                    "The given plug '{0}' has already been promoted to this "
                    "Graph und the key '{1}'".format(plug.name, key)
                )
        elif isinstance(plug, OutputPlug):
            if plug not in self.outputs.values():
                self.outputs[name or plug.name] = plug
            else:
                key = list(self.outputs.keys())[
                    list(self.outputs.values()).index(plug)
                ]
                raise ValueError(
                    "The given plug {0} has already been promoted to this "
                    "Graph und the key '{1}'".format(plug.name, key)
                )
        else:
            raise TypeError(
                "Plugs of type '{0}' can not be promoted directly to a Graph. "
                "Only plugs of type '{1}' or '{2}' can be promoted.".format(
                    type(plug), InputPlug, OutputPlug
                )
            )

    def accepts_connection(self, output_plug, input_plug):
        """Raise exception if new connection would violate integrity of graph.

        Args:
            output_plug (flowpipe.plug.OutputPlug): The output plug
            input_plug (flowpipe.plug.InputPlug): The input plug
        Raises:
            CycleError and ValueError
        Returns:
            True if the connection is accepted
        """
        out_node = output_plug.node
        in_node = input_plug.node

        # Plugs can't be connected to other plugs on their own node
        if in_node is out_node:
            raise CycleError(
                "Can't connect plugs that are part of the same node."
            )

        # If that is downstream of this
        if out_node in in_node.downstream_nodes:
            raise CycleError(
                "Can't connect OutputPlugs to plugs of an upstream node."
            )

        # Names of subgraphs have to be unique
        if (
            in_node.graph.name in self.subgraphs
            and in_node.graph not in self.subgraphs.values()
        ):
            raise ValueError(
                "This node is part of graph '{0}', but a different "
                "graph with the same name is already part of this "
                "graph. Subgraph names on a Graph have to "
                "be unique".format(in_node.graph.name)
            )

        return True

    def evaluate(
        self,
        mode="linear",
        skip_clean=False,
        submission_delay=0.1,
        max_workers=None,
        data_persistence=True,
        evaluator=None,
    ):
        """Evaluate all Nodes in the graph.

        Sorts the nodes in the graph into a resolution order and evaluates the
        nodes. Evaluation can be parallelized by utilizing the dependencies
        between the nodes - see the "mode" keyword for the options.

        Note that no checks are in place whether the node execution is actually
        thread-safe or fit for multiprocessing. It is assumed to be given if
        the respective mode is selected.

        Some keyword arguments do not affect all evaluation modes.

        Args:
            mode (str): The evaluation mode. Possible modes are
                * linear : Iterates over all nodes in a single thread
                * threading : Evaluates each node in a new thread
                * multiprocessing : Evaluates each node in a new process
            skip_clean (bool): Whether to skip nodes that are 'clean' (as
                tracked by the 'is_dirty' attribute on the node), i.e. whose
                inputs have not changed since their output was computed
            submission_delay (float): The delay in seconds between loops
                issuing new threads/processes if nodes are ready to process.
            max_workers (int): The maximum number of parallel threads to spawn.
                None defaults to your pythons ThreadPoolExecutor default.
            data_persistence (bool): If false, the data on plugs that have
                connections gets cleared (set to None). This reduces the
                reference count of objects.
            evaluator (flowpipe.evaluators.Evaluator): The evaluator to use.
                For the basic evaluation modes will be picked by 'mode'.
        """
        log.info('Evaluating Graph "{0}"'.format(self.name))

        # map mode keywords to evaluation functions and their arguments
        eval_modes = {
            "linear": (LinearEvaluator, {}),
            "threading": (ThreadedEvaluator, {"max_workers": max_workers}),
            "multiprocessing": (
                LegacyMultiprocessingEvaluator,
                {"submission_delay": submission_delay},
            ),
        }

        if mode and evaluator:
            raise ValueError("Both 'mode' and 'evaluator' arguments passed.")
        elif mode:
            try:
                eval_cls, eval_args = eval_modes[mode]
            except KeyError:
                raise ValueError("Unkown mode: {0}".format(mode))
            evaluator = eval_cls(**eval_args)

        evaluator.evaluate(graph=self, skip_clean=skip_clean)

        if not data_persistence:
            for node in self.nodes:
                for input_plug in node.all_inputs().values():
                    if input_plug.connections:
                        input_plug.value = None
                for output_plug in node.all_outputs().values():
                    if output_plug.connections:
                        output_plug.value = None

    def to_pickle(self):
        """Serialize the graph into a pickle."""
        return pickle.dumps(self)

    def to_json(self):
        """Serialize the graph into a json."""
        return self._serialize()

    def serialize(self):  # pragma: no cover
        """Serialize the graph in its grid form.

        Deprecated.
        """
        warnings.warn(
            "Graph.serialize is deprecated. Instead, use one of "
            "Graph.to_json or Graph.to_pickle",
            DeprecationWarning,
        )

        return self._serialize()

    def _serialize(self, with_subgraphs=True):
        """Serialize the graph in its grid form.

        Args:
            with_subgraphs (bool): Set to false to avoid infinite recursion
        """
        data = OrderedDict(
            module=self.__module__, cls=self.__class__.__name__, name=self.name
        )
        data["nodes"] = [node.to_json() for node in self.nodes]
        if with_subgraphs:
            data["subgraphs"] = [
                graph._serialize(with_subgraphs=False)
                for graph in sorted(
                    self.subgraphs.values(), key=lambda g: g.name
                )
            ]
        return data

    @staticmethod
    def from_pickle(data):
        """De-serialize from the given pickle data."""
        return pickle.loads(data)

    @staticmethod
    def from_json(data):
        """De-serialize from the given json data."""
        return deserialize_graph(data)

    @staticmethod
    def deserialize(data):  # pragma: no cover
        """De-serialize from the given json data."""
        warnings.warn(
            "Graph.deserialize is deprecated. Instead, use one of "
            "Graph.from_json or Graph.from_pickle",
            DeprecationWarning,
        )
        return deserialize_graph(data)

    def node_repr(self):
        """Format to visualize the Graph."""
        canvas_ = canvas.Canvas()
        x = 0

        evaluation_matrix = self.evaluation_matrix

        for row in evaluation_matrix:
            y = 0
            x_diff = 0
            for node in row:
                item_ = item.Item(str(node), [x, y])
                node.item = item_
                x_diff = (
                    item_.bbox[2] - item_.bbox[0] + 4
                    if item_.bbox[2] - item_.bbox[0] + 4 > x_diff
                    else x_diff
                )
                y += item_.bbox[3] - item_.bbox[1]
                canvas_.add_item(item_)
            x += x_diff

        # Include the input groups if any have been set
        y_off = 2
        locked_items = []
        if self.input_groups:
            for input_group in self.input_groups.values():
                y_off += 1
                i = item.Item("o {0}".format(input_group.name), [0, y_off])
                canvas_.add_item(i)
                locked_items.append(i)
                for p in input_group.plugs:
                    y_off += 1
                    i = item.Item(
                        "`-{0}.{1}".format(p.node.name, p.name), [2, y_off]
                    )
                    canvas_.add_item(i)
                    locked_items.append(i)

        # Move all items down by Y
        for i in canvas_.items:
            if i not in locked_items:
                i.position[0] += 2
                i.position[1] += y_off + 1 + int(bool(self.input_groups))

        canvas_.add_item(item.Rectangle(x, canvas_.bbox[3] + 1, [0, 0]), 0)

        # Crop the name of the graph if it is too long
        name = self.name
        if len(name) > x - 2:
            name = name[: x - 2]
        canvas_.add_item(
            item.Item("{name:^{x}}".format(name=name, x=x), [0, 1]), 0
        )
        canvas_.add_item(item.Rectangle(x, 3, [0, 0]), 0)

        if self.input_groups:
            canvas_.add_item(item.Rectangle(x, y_off + 2, [0, 0]), 0)

        for node in self.all_nodes:
            for i, plug in enumerate(node._sort_plugs(node.all_outputs())):
                for connection in node._sort_plugs(node.all_outputs())[
                    plug
                ].connections:
                    dnode = connection.node
                    start = [
                        node.item.position[0] + node.item.bbox[2],
                        node.item.position[1] + 3 + len(node.all_inputs()) + i,
                    ]
                    end = [
                        dnode.item.position[0],
                        dnode.item.position[1]
                        + 3
                        + list(
                            dnode._sort_plugs(dnode.all_inputs()).values()
                        ).index(connection),
                    ]
                    canvas_.add_item(item.Line(start, end), 0)

        return canvas_.render()

    def list_repr(self):
        """List representation of the graph showing Nodes and connections."""
        pretty = []
        pretty.append(self.name)

        if self.input_groups:
            pretty.append("[Input Groups]")
            for name in sorted(self.input_groups.keys()):
                input_group = self.input_groups[name]
                pretty.append(" [g] {0}:".format(name))
                for p in input_group.plugs:
                    pretty.append("  {0}.{1}".format(p.node.name, p.name))
        for node in self.evaluation_sequence:
            pretty.append(node.list_repr())
        return "\n ".join(pretty)


default_graph = Graph(name="default")


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
