"""Classes to evaluate flowpipe Graphs in various ways."""

import logging
import time
from concurrent import futures
from multiprocessing import Manager, Process
from pickle import PicklingError

from .errors import FlowpipeMultiprocessingError

log = logging.getLogger(__name__)


class Evaluator:
    """An engine to evaluate a Graph."""

    @staticmethod
    def _evaluation_sequence(graph):
        """Sort Nodes into a sequential, flat execution order.

        Replicated here for flexibility; defaults to Graph's implementation.

        Args:
            graph (flowpipe.Graph): The graph to evaluate.
        Returns:
            (list of INode): The nodes in the order in which to compute them.
        """
        return graph.evaluation_sequence

    def _nodes_to_evaluate(self, graph, skip_clean):
        """Get the nodes to evaluate, in order."""
        nodes = self._evaluation_sequence(graph)
        if skip_clean:
            nodes = [n for n in nodes if n.is_dirty]
        return nodes

    def _evaluate_nodes(self, nodes):
        """Perform the actual node evaluation."""
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, graph, skip_clean=False):
        """Evaluate the graph.

        Args:
            graph (flowpipe.Graph): The graph to evaluate.
            skip_clean (bool): Whether to skip nodes that are clean.
            data_persistence (bool): If false, the data on plugs that have
                connections gets cleared (set to None). This reduces the
                reference count of objects.
        """
        nodes = self._nodes_to_evaluate(graph, skip_clean)
        self._evaluate_nodes(nodes)


class LinearEvaluator(Evaluator):
    """Evaluate the graph linearly in a single thread."""

    def _evaluate_nodes(self, nodes):
        """Evaluate the graph linearly in a single thread.

        Args:
            nodes (list of INode): The nodes to evaluate

        """
        for node in nodes:
            node.evaluate()


class ThreadedEvaluator(Evaluator):
    """Evaluate each node in a separate thread."""

    def __init__(self, max_workers=None):
        """Intialize with the graph and how many threads to use.

        Args:
            graph (flowpipe.Graph): The graph to evaluate.
            max_workers (int): The number of threads to use in parallel,
                defaults to the futures.ThreadPoolExecutor default.

        """
        self.max_workers = max_workers

    def _evaluate_nodes(self, nodes):
        """Evaluate each node in a separate thread.

        Args:
            nodes (list of INode): The nodes to evaluate

        """
        # create copy to prevent side effects
        nodes_to_evaluate = list(nodes)

        def node_runner(node):
            node.evaluate()
            return node

        running_futures = {}
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as tpe:
            while nodes_to_evaluate or running_futures:
                log.debug(
                    "Iterating thread submission with %s nodes to "
                    "evaluate and %s running futures",
                    len(nodes_to_evaluate),
                    len(running_futures),
                )
                # Submit new nodes that are ready to be evaluated
                not_submitted = []
                for node in nodes_to_evaluate:
                    if not any(n.is_dirty for n in node.upstream_nodes):
                        fut = tpe.submit(node_runner, node)
                        running_futures[node.name] = fut
                    else:
                        not_submitted.append(node)
                nodes_to_evaluate = not_submitted

                # A deadlock situation:
                # No nodes running means no nodes can turn clean but nodes on
                # nodes_to_evaluate not submitted means dirty upstream nodes
                # and while loop will never terminate
                if nodes_to_evaluate and not running_futures:
                    for node in nodes_to_evaluate:  # pragma: no cover
                        dirty_upstream = [
                            nn.name
                            for nn in node.upstream_nodes
                            if nn.is_dirty
                        ]
                        log.debug(
                            "Node to evaluate: %s\n"
                            "- Dirty upstream nodes:\n%s",
                            node.name,
                            "\n".join(dirty_upstream),
                        )
                    raise RuntimeError(
                        f"Execution hit deadlock: {len(nodes_to_evaluate)} "
                        "nodes left to evaluate, but no nodes running."
                    )  # pragma: no cover

                # Wait until a future finishes, then remove all finished nodes
                # from the relevant lists
                status = futures.wait(
                    list(running_futures.values()),
                    return_when=futures.FIRST_COMPLETED,
                )
                for future in status.done:
                    del running_futures[future.result().name]


class LegacyMultiprocessingEvaluator(Evaluator):
    """Evaluate nodes in separate processes."""

    def __init__(self, submission_delay=0.1):
        """Initialize with the graph and the delay between launching nodes.

        Args:
            submission_delay (float): The delay in seconds between loops
                issuing new threads/processes if nodes are ready to process.

        """
        self.submission_delay = submission_delay

    def _evaluate_nodes(self, nodes):
        # create copy to prevent side effects
        nodes_to_evaluate = list(nodes)
        manager = Manager()
        nodes_data = manager.dict()
        processes = {}

        def upstream_ready(node):
            """Check whether all upstream nodes have been evaluated."""
            for upstream in node.upstream_nodes:
                if upstream in nodes_to_evaluate:
                    return False
            return True

        while nodes_to_evaluate:
            for node in nodes_to_evaluate:
                process = processes.get(node.name)
                if process and not process.is_alive():
                    # If the node is done computing, drop it from the list
                    nodes_to_evaluate.remove(node)
                    _update_node(node, nodes_data[node.identifier])
                    continue
                if node.name not in processes and upstream_ready(node):
                    # If all deps are ready and no thread is active, create one
                    try:
                        nodes_data[node.identifier] = node.to_json()
                    except PicklingError as exc:
                        raise FlowpipeMultiprocessingError(
                            "Error pickling/unpickling node.\n"
                            "This is most likely due to input values that can not "
                            "be pickled/unpickled properly.\n"
                            "If any of your input plugs contain flowpipe graphs, "
                            "that in turn are made up of Nodes created with the "
                            "@Node decorator, please consider reworking your Nodes. "
                            "You can either switch to class based nodes by "
                            "subclassing from Node or invoke the FunctionNode "
                            "explicitly instead. Refer to: https://github.com/PaulSchweizer/flowpipe/issues/168#issuecomment-1767779623 "  # pylint: disable=line-too-long
                            "for details."
                        ) from exc
                    processes[node.name] = Process(
                        target=_evaluate_node_in_process,
                        name=f"flowpipe.{node.graph.name}.{node.name}",
                        args=(node.identifier, nodes_data),
                    )
                    processes[node.name].daemon = True
                    processes[node.name].start()

            time.sleep(self.submission_delay)


def _evaluate_node_in_process(identifier, nodes_data):
    """Evaluate a node when multiprocessing.

    1. Deserializing the node from the given nodes_data dict
    2. Retrieving upstream data from the nodes_data dict
    3. Evaluating the node
    4. Serializing the results back into the nodes_data

    Args:
        identifier (str): The identifier of the node to evaluate
        nodes_data (dict): Used like a "database" to store the nodes
    """
    # pylint: disable=import-outside-toplevel, cyclic-import
    from flowpipe.node import INode

    data = nodes_data[identifier]
    node = INode.from_json(data)

    for name, input_plug in data["inputs"].items():
        for input_identifier, output_plug in input_plug["connections"].items():
            upstream_node = INode.from_json(nodes_data[input_identifier])
            node.inputs[name].value = upstream_node.outputs[output_plug].value
        for sub_name, sub_plug in input_plug["sub_plugs"].items():
            for sub_id, sub_output in sub_plug["connections"].items():
                upstream_node = INode.from_json(nodes_data[sub_id])
                node.inputs[name][
                    sub_name
                ].value = upstream_node.all_outputs()[sub_output].value

    node.evaluate()

    for name, plug in node.outputs.items():
        data["outputs"][name]["value"] = plug.value
        for sub_name, sub_plug in plug.sub_plugs.items():
            if sub_name not in data["outputs"][name]["sub_plugs"]:
                data["outputs"][name]["sub_plugs"][
                    sub_name
                ] = sub_plug.serialize()
            data["outputs"][name]["sub_plugs"][sub_name][
                "value"
            ] = sub_plug.value

    nodes_data[identifier] = data


def _update_node(node, data):
    """Apply the plug values of the data dict to the node object."""
    for name, input_plug in data["inputs"].items():
        node.inputs[name].value = input_plug["value"]
        for sub_name, sub_plug in input_plug["sub_plugs"].items():
            node.inputs[name][sub_name].value = sub_plug["value"]
            node.inputs[name][sub_name].is_dirty = False
        node.inputs[name].is_dirty = False
    for name, output_plug in data["outputs"].items():
        node.outputs[name].value = output_plug["value"]
        for sub_name, sub_plug in output_plug["sub_plugs"].items():
            node.outputs[name][sub_name].value = sub_plug["value"]
            node.outputs[name][sub_name].is_dirty = False
        node.outputs[name].is_dirty = False
