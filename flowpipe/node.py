"""Nodes manipulate incoming data and provide the outgoing data."""

from __future__ import absolute_import, annotations, print_function

import copy
import inspect
import json
import logging
import pickle
import time
import uuid
import warnings
from abc import ABCMeta, abstractmethod
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    cast,
)

from .event import Event
from .graph import Graph, get_default_graph
from .plug import InputPlug, InputPlugGroup, OutputPlug, SubOutputPlug, SubPlug
from .utilities import (
    NodeEncoder,
    deserialize_node,
    import_class,
    sanitize_string_input,
)

log = logging.getLogger(__name__)

DefaultGraph = Literal["default"]

P = ParamSpec("P")
R = TypeVar("R")


class INode:
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    EVENT_TYPES = [
        "evaluation-omitted",
        "evaluation-started",
        "evaluation-finished",
        "evaluation-exception",
    ]

    def __init__(
        self,
        name: str | None = None,
        identifier: str | None = None,
        metadata: dict | None = None,
        graph: Graph | DefaultGraph | None = "default",
    ):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
            identifier (str): If not provided, a unique identifier is generated.
            metadata (dict): Arbitrary metadata to store with the Node.
            graph (Graph): The graph to add the node to.
                If set to 'default', the Node is added to the default graph.
                If set to None, the Node is not added to any grpah.
        """
        self.events = {ev_type: Event(ev_type) for ev_type in self.EVENT_TYPES}

        self.name = name if name is not None else self.__class__.__name__
        self.identifier = (
            identifier
            if identifier is not None
            else f"{self.name}-{uuid.uuid4()}"
        )
        self.inputs: dict[str, InputPlug] = {}
        self.outputs: dict[str, OutputPlug] = {}
        self.metadata: dict = metadata or {}
        self.omit = False
        try:
            self.file_location: str | None = inspect.getfile(self.__class__)
        except TypeError as error:  # pragma: no cover
            # Excluded from tests, as this is a hard-to test fringe case
            if all(s in str(error) for s in ("__main__", "built-in class")):
                warnings.warn("Cannot serialize nodes defined in '__main__'")
                self.file_location = None
            else:
                raise
        self.class_name = self.__class__.__name__

        if isinstance(graph, Graph):
            self.graph = graph
        elif graph == "default":
            self.graph = get_default_graph()
        else:
            self.graph = Graph()
        self.graph.add_node(self)
        self.stats: dict = {}

    def __str__(self) -> str:
        """Show all input and output Plugs."""
        return self.node_repr()

    @property
    def is_dirty(self) -> bool:
        """Whether any of the input Plug data has changed and is dirty."""
        for input_ in self.inputs.values():
            if input_.is_dirty:
                return True
        return False

    @property
    def parents(self) -> set[INode]:
        """Nodes connected directly to inputs of this Node."""
        parents = set()
        for input_ in self.inputs.values():
            for conn in input_.connections:
                parents.add(conn.node)
            for sub_plug in input_.sub_plugs.values():
                for conn in sub_plug.connections:
                    parents.add(conn.node)
        return parents

    @property
    def upstream_nodes(self) -> list[INode]:
        """Nodes connected directly or indirectly to inputs of this Node."""
        upstream_nodes = {}
        for input_ in self.inputs.values():
            upstreams = [c.node for c in input_.connections]
            for sub_plug in input_.sub_plugs.values():
                upstreams += [c.node for c in sub_plug.connections]
            for upstream in upstreams:
                if upstream.identifier not in upstream_nodes:
                    upstream_nodes[upstream.identifier] = upstream
                    for upstream2 in upstream.upstream_nodes:
                        if upstream2.identifier not in upstream_nodes:
                            upstream_nodes[upstream2.identifier] = upstream2
        return list(upstream_nodes.values())

    @property
    def children(self) -> set[INode]:
        """Nodes connected directly to outputs of this Node."""
        children = set()
        for output in self.outputs.values():
            for conn in output.connections:
                children.add(conn.node)
            for sub_plug in output.sub_plugs.values():
                for conn in sub_plug.connections:
                    children.add(conn.node)
        return children

    @property
    def downstream_nodes(self):
        """Nodes connected directly or indirectly to outputs of this Node."""
        downstream_nodes = {}
        for output in self.outputs.values():
            downstreams = [c.node for c in output.connections]
            for sub_plug in output.sub_plugs.values():
                downstreams += [c.node for c in sub_plug.connections]
            for downstream in downstreams:
                if downstream.identifier not in downstream_nodes:
                    downstream_nodes[downstream.identifier] = downstream
                    for downstream2 in downstream.downstream_nodes:
                        if downstream2.identifier not in downstream_nodes:
                            downstream_nodes[
                                downstream2.identifier
                            ] = downstream2
        return list(downstream_nodes.values())

    def evaluate(self) -> dict[str, Any] | None:
        """Compute this Node, log it and clean the input Plugs.

        Also push a stat report in the following form containing the Node,
        evaluation time and timestamp the computation started.
        """
        if self.omit:
            self.events["evaluation-omitted"].emit(self)
            return {}

        self.events["evaluation-started"].emit(self)

        inputs = {}
        for name, plug in self.inputs.items():
            inputs[name] = plug.value

        # Compute and redirect the output to the output plugs
        start_time = time.time()
        try:
            outputs = self.compute(**inputs) or {}
        except Exception:
            self.events["evaluation-exception"].emit(self)
            raise
        eval_time = time.time() - start_time

        self.stats = {"eval_time": eval_time, "start_time": start_time}

        # all_outputs = self.all_outputs()
        for name, value in outputs.items():
            if "." in name:
                parent_plug, sub_plug = name.split(".")
                self.outputs[parent_plug][sub_plug].value = value
            else:
                self.outputs[name].value = value

        # Set the inputs clean
        for input_ in self.all_inputs().values():
            input_.is_dirty = False

        self.events["evaluation-finished"].emit(self)

        return outputs

    @abstractmethod
    def compute(
        self, *args, **kwargs
    ) -> dict[str, Any] | None:  # pragma: no cover
        """Implement the data manipulation in the subclass.

        Return a dictionary with the outputs from this function.
        """
        raise NotImplementedError("Compute must be overwritten")

    def __rshift__(self, other: INode | InputPlug | InputPlugGroup) -> None:
        """Syntactic sugar for connecting this node by output names."""
        self.connect(other)

    # pylint: disable=too-many-branches
    def connect(self, other: INode | InputPlug | InputPlugGroup) -> None:
        """Connect this node's outputs to another plug's input by name.

        If other is an InputPlug, connect the output with matching name.
        If other is an INode, connect all outputs with matching names.

        Note: This will also connect up sub-plugs if, and only if, they already
        exist. As they are dynamically created, they will come into existence
        only after being referenced explicity at least once. Before, the
        connect() method will not pick them up.
        """
        connections = []  # keep track of the connections established
        if isinstance(other, INode):
            for key, plug in self.outputs.items():
                if key in other.inputs:
                    plug.connect(other.inputs[key])
                    connections.append(f"Node: {other.name}, Plug: {key}")
                    for sub in plug.sub_plugs:
                        plug[sub].connect(other.inputs[key][sub])
                        connections.append(
                            f"Node: {other.name}, Plug: {key}, SubPlug: {sub}"
                        )
            if not connections:
                raise ValueError(f"{other.name} has no matching inputs")
        elif isinstance(other, (InputPlug, InputPlugGroup)):
            try:
                if isinstance(other, SubPlug):
                    out_name, sub_name = other.name.split(".")
                    out = self.outputs[out_name][sub_name]
                else:
                    out = self.outputs[other.name]
            except KeyError as exc:
                raise KeyError(f"No output named {other.name}") from exc
            else:
                out.connect(other)
                connections.append(f"Plug: {other.name}")

                if isinstance(other, InputPlug):
                    for sub in out.sub_plugs:
                        out.sub_plugs[sub].connect(other[sub])
                        connections.append(
                            f"Plug: {other.name}, Subplug: {sub}"
                        )
        else:
            raise TypeError(f"Cannot connect outputs to {type(other)}")
        log.debug(
            "Connected node %s with %s", self.name, "\n".join(connections)
        )

    def on_input_plug_set_dirty(self) -> None:
        """Propagate the dirty state to the connected downstream nodes."""
        for output_plug in self.outputs.values():
            for connected_plug in output_plug.connections:
                connected_plug.is_dirty = True

    def to_pickle(self) -> bytes:  # pragma: no cover
        """Serialize the node into a pickle."""
        return pickle.dumps(self)

    def to_json(self) -> dict:
        """Serialize the node to json."""
        return self._serialize()

    def serialize(self) -> dict:
        """Serialize the node to json.

        Deprecated and kept for backwards compatibility.
        """
        warnings.warn(
            "Node.serialize is deprecated. Instead, use one of "
            "Node.to_json or Node.to_pickle",
            DeprecationWarning,
        )
        return self._serialize()

    def _serialize(self) -> dict:
        """Perform the serialization to json."""
        if self.file_location is None:  # pragma: no cover
            raise RuntimeError(
                "Cannot serialize a node that was not defined in a file"
            )
        inputs = {}
        for in_plug in self.inputs.values():
            inputs[in_plug.name] = in_plug.serialize()
        outputs = {}
        for out_plug in self.outputs.values():
            outputs[out_plug.name] = out_plug.serialize()
        return {
            "file_location": self.file_location,
            "module": self.__module__,
            "cls": self.__class__.__name__,
            "name": self.name,
            "identifier": self.identifier,
            "inputs": inputs,
            "outputs": outputs,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_pickle(data: bytes) -> INode:
        """De-serialize from the given pickle data."""
        return pickle.loads(data)

    @staticmethod
    def from_json(data: dict) -> INode:
        """De-serialize from the given json data."""
        return deserialize_node(data)

    @staticmethod
    def deserialize(data: dict) -> INode:  # pragma: no cover
        """De-serialize from the given json data."""
        warnings.warn(
            "Node.deserialize is deprecated. Instead, use one of "
            "Node.from_json or Node.from_pickle",
            DeprecationWarning,
        )
        return deserialize_node(data)

    def post_deserialize(self, data: dict) -> None:
        """Perform more data operations after initial serialization."""
        self.name = data["name"]
        self.identifier = data["identifier"]
        self.metadata = data["metadata"]
        self.file_location = data["file_location"]
        for name, input_ in data["inputs"].items():
            self.inputs[name].value = input_["value"]
            for sub_name, sub_plug in input_["sub_plugs"].items():
                self.inputs[name][sub_name].value = sub_plug["value"]
        for name, output in data["outputs"].items():
            self.outputs[name].value = output["value"]
            for sub_name, sub_plug in output["sub_plugs"].items():
                self.outputs[name][sub_name].value = sub_plug["value"]

    def node_repr(self) -> str:
        """The node formated into a string looking like a node.

        ::

            +--Node.graph.name--+
            |     Node.Name     |
            |-------------------|
            % compound_in       |
            o  compound_in-1    |
            o  compound_in-2    |
            o in                |
            |               out o
            |      compound_out %
            |   compound_out-1  o
            |   compound_out-2  o
            +-------------------+
        """
        max_value_length = 10

        all_inputs = self.all_inputs()
        all_outputs = self.all_outputs()

        offset = ""
        if [i for i in all_inputs.values() if i.connections]:
            offset = " " * 3

        width = (
            len(
                max(
                    list(all_inputs)
                    + list(all_outputs)
                    + [self.name]
                    + list(
                        plug.name
                        + "".join(
                            [
                                s
                                for i, s in enumerate(str(plug.value))
                                if i < max_value_length
                            ]
                        )
                        for plug in all_inputs.values()
                        if plug.value is not None
                    )
                    + list(
                        plug.name
                        + "".join(
                            [
                                s
                                for i, s in enumerate(str(plug.value))
                                if i < max_value_length
                            ]
                        )
                        for plug in all_outputs.values()
                        if plug.value is not None
                    ),
                    key=len,
                )
            )
            + 7
        )

        if self.graph is not None and self.graph.subgraphs:
            width = max([width, len(self.graph.name) + 7])
            pretty = f"{offset}+{self.graph.name:-^{width}}+"
        else:
            pretty = offset + "+" + "-" * width + "+"

        pretty += f"\n{offset}|{self.name:^{width}}|"
        pretty += "\n" + offset + "|" + "-" * width + "|"

        def _short_value(plug):
            if plug.value is not None and not plug.sub_plugs:
                value = str(plug.value)
                if len(value) > max_value_length:
                    return f"<{value[: max_value_length - 3]}...>"
                return f"<{value}>"
            return "<>"

        # Inputs
        for input_ in sorted(all_inputs.keys()):
            pretty += "\n"
            in_plug = all_inputs[input_]
            if in_plug.connections:
                pretty += "-->"
            else:
                pretty += offset
            symbol = "%" if in_plug.sub_plugs else "o"
            in_dist = " " if isinstance(in_plug, SubPlug) else ""
            value_in_plug = _short_value(in_plug)
            value_in_plug = sanitize_string_input(value_in_plug)
            plug = f"{symbol} {in_dist}{input_}{value_in_plug}".format()
            pretty += f"{plug:{width + 1}}|"

        # Outputs
        for output in sorted(all_outputs.keys()):
            out_plug = all_outputs[output]
            out_dist = 2 if isinstance(out_plug, SubPlug) else 1
            value_out_plug = _short_value(out_plug)
            value_out_plug = sanitize_string_input(value_out_plug)
            symbol = "%" if out_plug.sub_plugs else "o"
            pretty += (
                f"\n{offset}|{output:>{width - out_dist - len(value_out_plug)}}"
                f"{value_out_plug}{out_dist * ' '}{symbol}"
            )
            if all_outputs[output].connections:
                pretty += "---"

        pretty += "\n" + offset + "+" + "-" * width + "+"
        return pretty

    def list_repr(self) -> str:
        """List representation of the node showing inputs and their values.

        ::

            Node
              [i] in: "A"
              [i] in_compound
               [i] in_compound.0: "B"
               [i] in_compound.1 << Node1.out
              [o] compound_out
               [o] in_compound.0: null
               [o] compound_out.1 >> Node2.in, Node3.in
              [o] out >> Node4.in
        """
        pretty = []
        pretty.append(self.name)
        for name, in_plug in sorted(self.all_inputs().items()):
            if in_plug.sub_plugs:
                pretty.append(f"  [i] {name}")
                continue
            if in_plug.connections:
                indent = "   " if isinstance(in_plug, SubPlug) else "  "
                node_name = in_plug.connections[0].node.name
                plug_name = in_plug.connections[0].name
                pretty.append(f"{indent}[i] {name} << {node_name}.{plug_name}")
            else:
                indent = "   " if isinstance(in_plug, SubPlug) else "  "
                pretty.append(
                    f"{indent}[i] {name}: {json.dumps(in_plug.value, cls=NodeEncoder)}"
                )
        for name, out_plug in sorted(self.all_outputs().items()):
            if out_plug.sub_plugs:
                pretty.append(f"  [o] {name}")
                continue
            if out_plug.connections:
                connections = ", ".join(
                    [f"{c.node.name}.{c.name}" for c in out_plug.connections]
                )
                indent = "   " if isinstance(out_plug, SubPlug) else "  "
                pretty.append(f"{indent}[o] {name} >> {connections}")
            else:
                indent = "   " if isinstance(out_plug, SubPlug) else "  "
                pretty.append(
                    f"{indent}[o] {name}: {json.dumps(out_plug.value, cls=NodeEncoder)}"
                )

        return "\n".join(pretty)

    def all_inputs(self) -> dict[str, InputPlug]:
        """Collate all input plugs and their sub_plugs into one dictionary."""
        all_inputs = {}
        for plug in self.inputs.values():
            all_inputs[plug.name] = plug
            for sub in plug.sub_plugs.values():
                if isinstance(sub, InputPlug):
                    all_inputs[sub.name] = sub
        return all_inputs

    def all_outputs(self) -> dict[str, OutputPlug]:
        """Collate all output plugs and their sub_plugs into one dictionary."""
        all_outputs = {}
        for plug in self.outputs.values():
            all_outputs[plug.name] = plug
            for sub in plug.sub_plugs.values():
                if isinstance(sub, OutputPlug):
                    all_outputs[sub.name] = sub
        return all_outputs

    @staticmethod
    def sort_plugs(plugs) -> dict:
        """Sort the given plugs alphabetically into a dict."""
        sorted_plugs = {}
        for i in sorted(plugs, key=lambda x: x.lower()):
            sorted_plugs[i] = plugs[i]
        return sorted_plugs


class FunctionNode(INode, Generic[P]):
    """Wrap a function into a Node."""

    # Some names have to stay reserved as they are used to construct the Node
    RESERVED_INPUT_NAMES = (
        "func",
        "name",
        "identifier",
        "inputs",
        "outputs",
        "metadata",
        "omit",
        "graph",
    )

    def __init__(
        self,
        *,
        func: Callable[P, dict[str, Any] | None] | None = None,
        outputs=None,
        name: str | None = None,
        identifier: str | None = None,
        metadata: dict | None = None,
        graph: Graph | DefaultGraph | None = None,
        **kwargs,
    ):
        """The data on the function is used to drive the Node.
        The function itself becomes the compute method.
        The function input args become the InputPlugs.
        Other function attributes, name, __doc__ also transfer to the Node.
        """
        super().__init__(
            name or getattr(func, "__name__", None),
            identifier,
            metadata,
            graph,
        )
        self._initialize(func, outputs or [], metadata)  # type: ignore
        for plug, value in kwargs.items():
            self.inputs[plug].value = value

    def __call__(
        self,
        *,
        name: str | None = None,
        identifier: str | None = None,
        metadata: dict[str, Any] | None = None,
        graph: Graph | DefaultGraph | None = "default",
        **input_plug_values: Any,
    ) -> FunctionNode[P]:
        """Create and return an instance of the Node."""
        metadata_payload: dict[str, Any] = copy.deepcopy(self.metadata)
        if metadata:
            metadata_payload.update(metadata)
        outputs = []
        for output in self.outputs.values():
            outputs.append(output.name)
            for key in output.sub_plugs.keys():
                outputs.append(f"{output.name}.{key}")
        return cast(
            FunctionNode[P],
            self.__class__(
                func=self.func,
                outputs=outputs,
                name=name,
                identifier=identifier,
                metadata=metadata_payload,
                graph=graph,
                **input_plug_values,
            ),
        )

    def compute(self, *args: P.args, **kwargs: P.kwargs):
        """Call and return the wrapped function."""
        if self._use_self:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)

    def _serialize(self) -> dict:
        """Also serialize the location of the wrapped function."""
        data = super()._serialize()
        data["func"] = {
            "module": self.func.__module__,
            "name": self.func.__name__,
        }
        return data

    def post_deserialize(self, data: dict) -> None:
        """Apply the function back to the node."""
        self.name = data["name"]
        self.identifier = data["identifier"]
        self.metadata = data["metadata"]
        self.file_location = data["file_location"]

        # The function could either be a function or, if the function is
        # wrapped with the @Node decorator, it would already be a Node class.
        node_or_function = import_class(
            data["func"]["module"], data["func"]["name"], data["file_location"]
        )
        if isinstance(node_or_function, FunctionNode):
            node: FunctionNode[Any] = node_or_function
        else:
            node = FunctionNode(
                name=self.name,
                identifier=self.identifier,
                metadata=self.metadata,
                func=node_or_function,
                outputs=list(data["outputs"].keys()),
            )
            node.file_location = self.file_location

        node_instance: FunctionNode = node(graph=None)

        self._initialize(
            node_instance.func, data["outputs"].keys(), data["metadata"]
        )
        for name, input_ in data["inputs"].items():
            self.inputs[name].value = input_["value"]
            for sub_name, sub_plug in input_["sub_plugs"].items():
                self.inputs[name][sub_name].value = sub_plug["value"]
        for name, output in data["outputs"].items():
            self.outputs[name].value = output["value"]
            for sub_name, sub_plug in output["sub_plugs"].items():
                self.outputs[name][sub_name].value = sub_plug["value"]

    def _initialize(
        self, func: Callable, outputs: list[str], metadata: dict
    ) -> None:
        """Use the function and the list of outputs to setup the Node."""
        self.func = func
        self.__doc__ = func.__doc__
        self._use_self = False
        self.metadata = metadata or {}
        if func is not None:
            self.file_location = inspect.getfile(func)
            self.class_name = self.func.__name__
            arg_spec = inspect.getfullargspec(
                func
            )  # pylint: disable=deprecated-method
            defaults = {}
            if arg_spec.defaults is not None:
                defaults = dict(
                    zip(
                        arg_spec.args[-len(arg_spec.defaults) :],
                        arg_spec.defaults,
                    )
                )
            forbidden_inputs = []
            for input_ in arg_spec.args:
                if input_ in self.RESERVED_INPUT_NAMES:
                    forbidden_inputs.append(input_)
                    continue
                if input_ != "self":
                    plug = InputPlug(input_, self)
                    plug.value = defaults.get(input_, None)
                else:
                    self._use_self = True
            if forbidden_inputs:
                raise ValueError(
                    f"{', '.join(forbidden_inputs)} are reserved names and "
                    "can not be used as inputs!\n"
                    f"Reserved names are: {self.RESERVED_INPUT_NAMES}"
                )

        if outputs is not None:
            for output in outputs:
                if "." in output:
                    parent, subplug = output.split(".")
                    parent_plug = self.outputs.get(parent)
                    if parent_plug is None:
                        parent_plug = OutputPlug(parent, self)
                    SubOutputPlug(subplug, self, parent_plug)
                else:
                    if self.outputs.get(output) is None:
                        OutputPlug(output, self)

    def to_pickle(self) -> bytes:  # pragma: no cover
        """Pickle the node. -- DOES NOT WORK FOR FunctionNode."""
        raise NotImplementedError(
            "Pickling is not implemented for FunctionNode. "
            "Consider subclassing flowpipe.node.INode to pickle nodes."
        )


def Node(  # pylint: disable=invalid-name
    *args: Any,
    cls: Type[FunctionNode] = FunctionNode,
    outputs: Sequence[str] | None = None,
    name: str | None = None,
    identifier: str | None = None,
    metadata: dict[str, Any] | None = None,
    graph: Graph | DefaultGraph | None = None,
    **plug_defaults: Any,
) -> Callable[[Callable[P, dict[str, Any] | None]], FunctionNode]:
    """Wrap the given function into a Node."""
    node_kwargs: dict[str, Any] = {
        "outputs": outputs,
        "name": name,
        "identifier": identifier,
        "metadata": metadata,
        "graph": graph,
        **plug_defaults,
    }

    def node(func: Callable[..., Any]) -> FunctionNode:
        return cast(FunctionNode, cls(func=func, *args, **node_kwargs))

    return node
