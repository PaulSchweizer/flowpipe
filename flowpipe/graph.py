"""A Graph of Nodes."""
from __future__ import print_function
from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from multiprocessing import Manager, Process
import pickle
import threading
import time
import warnings

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

    def evaluate(self, mode="linear", skip_clean=False,
                 submission_delay=0.1, raise_after=None):
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
            raise_after (int): The number of loops without currently running
                threads/processes after which to raise a RuntimeError.

        """
        LogObserver.push_message("Evaluating Graph '{0}'".format(self.name))

        eval_modes = {
            "linear": self._evaluate_linear,
            "threading": self._evaluate_threaded,
            "multiprocessing": self._evaluate_multiprocessed
        }

        try:
            eval_func = eval_modes[mode]
        except KeyError:
            mode_options = ""
            for m in eval_modes:
                mode_options += m + " "
            mode_options = mode_options[:-1]  # get rid of trailing space
            raise ValueError("Invalid mode {0}, options are {1}".format(
                mode, mode_options))

        eval_func(skip_clean=skip_clean, submission_delay=submission_delay,
                  raise_after=raise_after)

    def _evaluate_linear(self, skip_clean, **kwargs):
        """Iterate over all nodes in a single thread (the current one).

        Args:
            kwargs: included to allow for the factory pattern for eval modes
        """
        for node in self.evaluation_sequence:
            if node.is_dirty or not skip_clean:
                node.evaluate()

    def _evaluate_threaded(self, skip_clean, submission_delay, raise_after,
                           **kwargs):
        """Evaluate each node in a new thread.

        Args:
            kwargs: included to allow for the factory pattern for eval modes
        """
        threads = {}
        nodes_to_evaluate = [n for n in self.evaluation_sequence
                             if n.is_dirty or not skip_clean]
        empty_loops = 0
        while True:
            for node in nodes_to_evaluate:
                thread = threads.get(node.name)
                if thread and not thread.is_alive():
                    # If the node is done computing, drop it from the list
                    nodes_to_evaluate.remove(node)
                    continue
                if not thread and all(not n.is_dirty for n in node.upstream_nodes):
                    # If all deps are ready and no thread is active, create one
                    threads[node.name] = threading.Thread(
                        target=node.evaluate,
                        name="flowpipe.{0}.{1}".format(self.name, node.name))
                    threads[node.name].start()

            graph_threads = [t for t in threading.enumerate()
                             if t.name.startswith(
                                 "flowpipe.{0}".format(self.name))]
            all_clean = all(not n.is_dirty for n in nodes_to_evaluate)
            if len(graph_threads) == 0 and not all_clean:  # pragma: no cover
                # No more threads running after a round of submissions means
                # we're either done or stuck
                if raise_after is not None and empty_loops > raise_after:
                    raise RuntimeError(
                        "Could not sucessfully compute all nodes in the "
                        "graph {0}".format(self.name))
                else:
                    empty_loops += 1
            else:
                empty_loops = 0

            if not nodes_to_evaluate:
                break
            time.sleep(submission_delay)

    def _evaluate_multiprocessed(self, skip_clean, submission_delay, **kwargs):
        """Similar to the threaded evaluation but with multiprocessing.

        Nodes communicate via a manager and are evaluated in a dedicated
        function.
        The original node objects are updated with the results from the
        corresponding processes to reflect the evaluation.

        Args:
            kwargs: included to allow for the factory pattern for eval modes
        """
        manager = Manager()
        nodes_data = manager.dict()
        processes = {}
        nodes_to_evaluate = [n for n in self.evaluation_sequence
                             if n.is_dirty or not skip_clean]

        def upstream_ready(processes, node):
            for upstream in node.upstream_nodes:
                if upstream in nodes_to_evaluate:
                    return False
            return True

        while True:
            for node in nodes_to_evaluate:
                process = processes.get(node.name)
                if process and not process.is_alive():
                    # If the node is done computing, drop it from the list
                    nodes_to_evaluate.remove(node)
                    update_node(node, nodes_data[node.identifier])
                    continue
                if node.name not in processes and upstream_ready(
                        processes, node):
                    # If all deps are ready and no thread is active, create one
                    nodes_data[node.identifier] = node.to_json()
                    processes[node.name] = Process(
                        target=evaluate_node_in_process,
                        name='flowpipe.{0}.{1}'.format(self.name, node.name),
                        args=(node.identifier, nodes_data))
                    processes[node.name].daemon = True
                    processes[node.name].start()

            if not nodes_to_evaluate:
                break
            time.sleep(submission_delay)

    def to_pickle(self):
        """Serialize the graph into a pickle."""
        return pickle.dumps(self)

    def to_json(self):
        """Serialize the graph into a json."""
        return self._serialize()

    def serialize(self):  # pragma: no cover
        """Serialize the graph in it's grid form.

        Deprecated.
        """
        warnings.warn('Graph.serialize is deprecated. Instead, use one of '
                      'Graph.to_json or Graph.to_pickle',
                      DeprecationWarning)

        return self._serialize()

    def _serialize(self):
        """Serialize the graph in it's grid form."""
        data = OrderedDict(
            module=self.__module__,
            cls=self.__class__.__name__,
            name=self.name)
        data['nodes'] = [node.to_json() for node in self.nodes]
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
        warnings.warn('Graph.deserialize is deprecated. Instead, use one of '
                      'Graph.from_json or Graph.from_pickle',
                      DeprecationWarning)
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


def evaluate_node_in_process(identifier, nodes_data):
    """Evaluate a node when multiprocessing.

    1. Deserializing the node from the given nodes_data dict
    2. Retrieving upstream data from the nodes_data dict
    3. Evaluating the node
    4. Serializing the results back into the nodes_data

    Args:
        identifier (str): The identifier of the node to evaluate
        nodes_data (dict): Used like a "database" to store the nodes
    """
    from flowpipe.node import INode
    data = nodes_data[identifier]
    node = INode.from_json(data)

    for name, input_plug in data['inputs'].items():
        for input_identifier, output_plug in input_plug['connections'].items():
            upstream_node = INode.from_json(nodes_data[input_identifier])
            node.inputs[name].value = upstream_node.outputs[output_plug].value
        for sub_name, sub_plug in input_plug['sub_plugs'].items():
            for sub_id, sub_output in sub_plug['connections'].items():
                upstream_node = INode.from_json(nodes_data[sub_id])
                node.inputs[name][sub_name].value = (
                    upstream_node.all_outputs()[sub_output].value)

    node.evaluate()

    for name, plug in node.outputs.items():
        data['outputs'][name]['value'] = plug.value
        for sub_name, sub_plug in plug._sub_plugs.items():
            if sub_name not in data['outputs'][name]['sub_plugs']:
                data['outputs'][name]['sub_plugs'][sub_name] = (
                    sub_plug.serialize())
            data['outputs'][name]['sub_plugs'][sub_name]['value'] = (
                sub_plug.value)

    nodes_data[identifier] = data


def update_node(node, data):
    """Apply the plug values of the data dict to the node object."""
    for name, input_plug in data['inputs'].items():
        node.inputs[name].value = input_plug['value']
        for sub_name, sub_plug in input_plug['sub_plugs'].items():
            for sub_output in sub_plug['connections'].values():
                node.inputs[name][sub_name].value = sub_plug['value']
                node.inputs[name][sub_name].is_dirty = False
        node.inputs[name].is_dirty = False
    for name, output_plug in data['outputs'].items():
        node.outputs[name].value = output_plug['value']
        for sub_name, sub_plug in output_plug['sub_plugs'].items():
            for sub_output in sub_plug['connections'].values():
                node.outputs[name][sub_name].value = sub_plug['value']
                node.outputs[name][sub_name].is_dirty = False
        node.outputs[name].is_dirty = False
