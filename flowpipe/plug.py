"""Plugs are ins and outs for Nodes through which they exchange data."""

from __future__ import annotations, print_function

import warnings
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from .utilities import get_hash

if TYPE_CHECKING:  # pragma: no cover
    from .graph import Graph
    from .node import INode


class IPlug:
    """The interface for the plugs.

    Plugs are associated with a Node and can be connected, disconnected
    and hold a value, that can be accesses by the associated Node.
    """

    def __init__(self, name: str, node: INode):
        """Initialize the Interface.

        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        if "." in name and not isinstance(self, SubPlug):
            raise ValueError(
                'Names for plugs can not contain dots "." as these are '
                "reserved to identify sub plugs."
            )
        self.name = name
        self.node = node
        self.connections: list = []
        self.sub_plugs: dict[str, OutputPlug | InputPlug] = {}
        self._value = None
        self._is_dirty = True

    def __rshift__(self, other) -> None:
        """Create a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to connect to.
        """
        warnings.warn(
            "Use the connect method instead", DeprecationWarning, stacklevel=2
        )
        self.connect(other)

    def __lshift__(self, other: IPlug) -> None:
        """Break a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to disconnect.
        """
        warnings.warn(
            "Use the disconnect method instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.disconnect(other)

    @property
    def _sub_plugs(self) -> dict[str, OutputPlug | InputPlug]:
        """Deprecated but included for backwards compatibility."""
        warnings.warn(
            "`_sub_plugs` is deprecated, please use `sub_plugs` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.sub_plugs

    # Extra function to make re-use in subclasses easier
    def _update_value(self, value: Any) -> None:
        """Update the internal value."""
        old_hash = get_hash(self._value)
        new_hash = get_hash(value)
        self._value = value
        if old_hash is None or new_hash is None or (old_hash != new_hash):
            self.is_dirty = True

    @property
    def value(self) -> Any:
        """Access to the value on this Plug."""
        if self.sub_plugs:
            return {name: plug.value for name, plug in self.sub_plugs.items()}
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Set the Plug dirty when the value is being changed."""
        self._update_value(value)

    @property
    def is_dirty(self) -> bool:
        """Access to the dirty status on this Plug."""
        if self.sub_plugs:
            for sub_plug in self.sub_plugs.values():
                if sub_plug.is_dirty:
                    return True
            return False
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status: bool) -> None:
        """Set the Plug dirty informs the node this Plug belongs to."""
        if self._is_dirty == status:
            return
        self._is_dirty = status
        if status:
            self.node.on_input_plug_set_dirty()

    @abstractmethod
    def connect(self, plug) -> None:  # pragma: no cover
        """Has to be implemented in the subclass."""
        raise NotImplementedError("The subclass has to define connect()")

    def disconnect(self, plug: IPlug) -> None:
        """Break the connection to the given Plug."""
        if isinstance(plug, InputPlugGroup):
            for plug_ in plug:
                self.disconnect(plug_)
            return
        if plug in self.connections:
            self.connections.pop(self.connections.index(plug))
            self.is_dirty = True
        if self in plug.connections:
            plug.connections.pop(plug.connections.index(self))
            plug.is_dirty = True
        # Invalidate connection caches for both nodes
        self.node._invalidate_connection_caches()
        plug.node._invalidate_connection_caches()

    def promote_to_graph(self, name: str | None = None) -> None:
        """Add this plug to the graph of this plug's node.

        Args:
            name (str): Optionally provide a different name for the Plug
        """
        self.node.graph.add_plug(self, name=name)


class OutputPlug(IPlug):
    """Provides data to an InputPlug."""

    def __init__(self, name: str, node: INode):
        """Initialize the OutputPlug.

        Can be connected to an InputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        self.accepted_plugs = (InputPlug, InputPlugGroup)
        super().__init__(name, node)
        if not isinstance(self, SubPlug):
            self.node.outputs[self.name] = self

    def __rshift__(self, other: INode | InputPlugGroup | InputPlug) -> None:
        """Syntactic sugar for the connect() method.

        If `other` is a INode with an input matching this plug's name, connect.
        """
        # softly check if the "other" is a Node with inputs
        if hasattr(other, "inputs"):
            for iname, iplug in other.inputs.items():
                if iname == self.name:
                    target = iplug
        else:
            target = other
        self.connect(target)

    def connect(self, plug: InputPlug | InputPlugGroup) -> None:
        """Connect this Plug to the given InputPlug.

        Set both participating Plugs dirty.
        """
        if not isinstance(plug, self.accepted_plugs):
            raise TypeError(f"Cannot connect {type(self)} to {type(plug)}")
        if isinstance(plug, InputPlugGroup):
            for plug_ in plug:
                self.connect(plug_)
            return

        if self.node.graph.accepts_connection(self, plug):
            for connection in plug.connections:
                plug.disconnect(connection)
            if plug not in self.connections:
                self.connections.append(plug)
                plug.value = self.value
                self.is_dirty = True
                plug.is_dirty = True
            if self not in plug.connections:
                plug.connections = [self]
                plug.is_dirty = True
            # Invalidate connection caches for both nodes
            self.node._invalidate_connection_caches()
            plug.node._invalidate_connection_caches()

    def __getitem__(self, key: str):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if not isinstance(key, str):
            raise TypeError(
                "Only strings are allowed as sub-plug keys! "
                "This is due to the fact that JSON serialization only allows "
                "strings as keys."
            )
        if not self.sub_plugs.get(key):
            self.sub_plugs[key] = SubOutputPlug(
                key=key, node=self.node, parent_plug=self
            )
        return self.sub_plugs[key]

    def _update_value(self, value: Any) -> None:
        """Propagate the dirty state to all connected Plugs as well."""
        super()._update_value(value)
        for plug in self.connections:
            plug.value = value

    def serialize(self) -> dict:
        """Serialize the Plug containing all it's connections."""
        connections: dict = {}
        for connection in self.connections:
            connections.setdefault(connection.node.identifier, [])
            connections[connection.node.identifier].append(connection.name)
        return {
            "name": self.name,
            "value": self.value if not self.sub_plugs else None,
            "connections": connections,
            "sub_plugs": {
                name: sub_plug.serialize() for name, sub_plug in self.sub_plugs.items()
            },
        }


class InputPlug(IPlug):
    """Receives data from an OutputPlug."""

    def __init__(self, name: str, node: INode, value: Any = None):
        """Initialize the InputPlug.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        self.accepted_plugs = (OutputPlug,)

        super().__init__(name, node)
        self.value = value
        self.is_dirty = True
        if not isinstance(self, SubPlug):
            self.node.inputs[self.name] = self

    def connect(self, plug: OutputPlug) -> None:
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if not isinstance(plug, self.accepted_plugs):
            raise TypeError(f"Cannot connect {type(self)} to {type(plug)}")
        plug.connect(self)

    def __getitem__(self, key: str):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if not isinstance(key, str):
            raise TypeError(
                "Only strings are allowed as sub-plug keys! "
                "This is due to the fact that JSON serialization only allows "
                "strings as keys."
            )
        if not self.sub_plugs.get(key):
            self.sub_plugs[key] = SubInputPlug(
                key=key, node=self.node, parent_plug=self
            )
        return self.sub_plugs[key]

    def _update_value(self, value: Any) -> None:
        if self.sub_plugs:
            return
        super()._update_value(value)

    def serialize(self) -> dict:
        """Serialize the Plug containing all it's connections."""
        connections = {}
        if self.connections:
            connections[self.connections[0].node.identifier] = self.connections[0].name
        return {
            "name": self.name,
            "value": self.value if not self.sub_plugs else None,
            "connections": connections,
            "sub_plugs": {
                name: sub_plug.serialize() for name, sub_plug in self.sub_plugs.items()
            },
        }


class SubPlug:
    """Mixin that unifies common properties of subplugs."""

    @property
    def is_dirty(self):
        """Access to the dirty status on this Plug."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status: bool) -> None:
        """Setting the Plug dirty informs its parent plug."""
        self._is_dirty = status
        if status:
            # pylint: disable=no-member
            self.parent_plug.is_dirty = status  # type: ignore

    def promote_to_graph(self, name: str | None = None) -> None:
        """Add this plug to the graph of this plug's node.

        NOTE: Subplugs can only be added to a graph via their parent plug.

        Args:
            name (str): Optionally provide a different name for the Plug
        """
        # prevent adding SubPlug to the graph witout their parents
        raise TypeError("Cannot add SubPlug to graph! Add the parent plug instead.")


class SubInputPlug(SubPlug, InputPlug):
    """Held by a parent input plug to form a compound plug."""

    def __init__(
        self, key: str, node: INode, parent_plug: InputPlug, value: Any = None
    ):
        """Initialize the plug.

        Can be connected to an OutputPlug.
        Args:
            key (str): The key will be used to form the name of the Plug:
                {parent_plug.name}.{key}.
            node (INode): The Node holding the Plug.
            parent_plug (OuInputPlugtputPlug): The parent plug holding this Plug.
        """
        # super().__init__() refers to self.parent_plug, so need to set it here
        self.key = key
        self.parent_plug = parent_plug
        self.parent_plug.sub_plugs[key] = self

        super().__init__(f"{parent_plug.name}.{key}", node)
        self.value = value
        self.is_dirty = True

    def serialize(self) -> dict:
        """Serialize the Plug containing all it's connections."""
        connections = {}
        if self.connections:
            connections[self.connections[0].node.identifier] = self.connections[0].name
        return {
            "name": self.name,
            "value": self.value,
            "connections": connections,
        }


class SubOutputPlug(SubPlug, OutputPlug):
    """Held by a parent output plug to form a compound plug."""

    def __init__(
        self, key: str, node: INode, parent_plug: OutputPlug, value: Any = None
    ):
        """Initialize the plug.

        Can be connected to an InputPlug.
        Args:
            key (str): The key will be used to form the name of the Plug:
                {parent_plug.name}.{key}.
            node (INode): The Node holding the Plug.
            parent_plug (OutputPlug): The parent plug holding this Plug.
        """
        # super().__init__() refers to self.parent_plug, so need to set it here
        self.key = key
        self.parent_plug = parent_plug
        self.parent_plug.sub_plugs[key] = self

        super().__init__(f"{parent_plug.name}.{key}", node)
        self.value = value
        self.is_dirty = True

    def _update_value(self, value: Any) -> None:
        """Propagate the dirty state to all connected Plugs as well."""
        super()._update_value(value)
        for plug in self.connections:
            plug.value = value
        parent_value = self.parent_plug.value or {}
        parent_value[self.key] = value
        self.parent_plug.value = parent_value

    def serialize(self) -> dict:
        """Serialize the Plug containing all it's connections."""
        connections: dict = {}
        for connection in self.connections:
            connections.setdefault(connection.node.identifier, [])
            connections[connection.node.identifier].append(connection.name)
        return {
            "name": self.name,
            "value": self.value,
            "connections": connections,
        }


class InputPlugGroup:
    """Group plugs inside a group into one entry point on the graph."""

    def __init__(self, name: str, graph: Graph, plugs: list[InputPlug] | None = None):
        """Initialize the group and assigning it to the `Graph.input_groups`.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the InputPlugGroup.
            graph (Graph): The Graph holding the PlugGroup.
            plugs (list of InputPlug): The plugs in this group.
        """
        self.name = name
        self.graph = graph
        self.plugs = plugs or []
        self.graph.inputs[self.name] = self

    def connect(self, plug: OutputPlug) -> None:
        """Connect all plugs in this group to the given plug."""
        for input_plug in self.plugs:
            plug.connect(input_plug)

    def disconnect(self, plug: OutputPlug) -> None:
        """Disconnect all plugs in this group from the given plug."""
        for input_plug in self.plugs:
            plug.disconnect(input_plug)

    def __iter__(self):
        """Convenience to iterate over the plugs in this group."""
        yield from self.plugs

    def __rshift__(self, other: OutputPlug) -> None:
        """Syntactic sugar for the connect() method."""
        self.connect(other)

    def __lshift__(self, other: OutputPlug) -> None:
        """Syntactic sugar for the disconnect() method."""
        self.disconnect(other)

    @property
    def value(self) -> Any:
        """Getting the value of an InputPlugGroup is not supported.

        The value property is implemented nonetheless, in order to allow for
        convenient setting of the value of all plugs in the InputPlugGroup.
        """
        raise AttributeError("Getting the value of an InputPlugGroup is not supported")

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the value for all grouped plugs."""
        for plug in self.plugs:
            plug.value = new_value
