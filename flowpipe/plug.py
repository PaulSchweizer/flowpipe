"""Plugs are ins and outs for Nodes through which they exchange data."""
from __future__ import print_function
from abc import abstractmethod
from typing import List, Any, Dict, Tuple

from flowpipe.node import INode

__all__ = ['OutputPlug', 'InputPlug']


class IPlug(object):

    """The interface for the plugs.

    Plugs are associated with a Node and can be connected, disconnected
    and hold a value, that can be accesses by the associated Node.
    """

    def __init__(self, name: str, node: INode, accepted_plugs: Tuple) -> None:
        """Initialize the Interface.

        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
            accepted_plugs (list of IPlug): Plugs types that are
                                            possible for connections.
        """
        self.name = name
        self.node = node
        self.connections: List[IPlug] = list()
        self.accepted_plugs = accepted_plugs
        self._value = None
        self._is_dirty = True

    def __str__(self) -> str:
        """Generate a pretty string."""
        return self.__unicode__().encode('utf-8').decode()

    @abstractmethod
    def __unicode__(self) -> str:
        """Show this Plug's type and it's connections."""

    def __rshift__(self, other: "IPlug") -> None:
        """Create a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to connect to.
        """
        if isinstance(self, OutputPlug):
            if isinstance(other, InputPlug):
                self.connect(other)

        if isinstance(self, InputPlug):
            if isinstance(other, OutputPlug):
                self.connect(other)

    def __lshift__(self, other) -> None:
        """Break a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to disconnect.
        """
        if isinstance(self, OutputPlug):
            if isinstance(other, InputPlug):
                self.disconnect(other)

        if isinstance(self, InputPlug):
            if isinstance(other, OutputPlug):
                self.disconnect(other)

    @property
    def value(self) -> Any:
        """Access to the value on this Plug."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Set the Plug dirty when the value is being changed."""
        self._value = value
        self.is_dirty = True

    @property
    def is_dirty(self) -> bool:
        """Access to the dirty status on this Plug."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status: bool) -> None:
        """Set the Plug dirty informs the node this Plug belongs to."""
        self._is_dirty = status
        if not status:
            self.node.on_input_plug_set_dirty()

    @abstractmethod
    def connect(self, plug: "IPlug") -> None:
        """Has to be implemented in the subclass."""

    def disconnect(self, plug: "IPlug"):
        """Break the connection to the given Plug."""
        if plug in self.connections:
            self.connections.pop(self.connections.index(plug))
            self.is_dirty = True
        if self in plug.connections:
            plug.connections.pop(plug.connections.index(self))
            plug.is_dirty = True

    def serialize(self) -> Dict[str, Any]:
        """Serialize the Plug containing all it's connections."""
        connections = {}
        for connection in self.connections:
            connections[connection.node.identifier] = connection.name
        return {
            'name': self.name,
            'value': self.value,
            'connections': connections
        }


class OutputPlug(IPlug):
    """Provides data to an InputPlug."""

    def __init__(self, name: str, node: INode):
        """Initialize the OutputPlug.

        Can be connected to an InputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        super(OutputPlug, self).__init__(name, node, (InputPlug, ))
        self.node.outputs[self.name] = self

    def __unicode__(self) -> str:
        """Show this Plug's type and it's connections."""
        pretty = '\u2190 {0} (OUT)'.format(self.name)
        pretty += ''.join(['\n\t\t\u2192 {0}.{1}'.format(
            c.node.name, c.name) for c in self.connections])
        return pretty

    @property
    def value(self) -> Any:
        """Access to the value on this Plug."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Propagate the dirty state to all connected Plugs as well."""
        self._value = value
        self.is_dirty = True
        for plug in self.connections:
            plug.value = value

    def connect(self, plug: IPlug):
        """Connect this Plug to the given InputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise Exception(
                'Can\'t connect Plugs that are part of the same Node.')

        for connection in plug.connections:
            plug.disconnect(connection)

        if plug not in self.connections:
            self.connections.append(plug)
            plug.value = self.value
            self.is_dirty = True
        if self not in plug.connections:
            plug.connections = [self]


class InputPlug(IPlug):
    from flowpipe.node import INode
    """Receives data from an OutputPlug."""

    def __init__(self, name: str, node: INode, value: Any = None):
        """Initialize the InputPlug.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        super(InputPlug, self).__init__(name, node, (OutputPlug, ))
        self.value = value
        self.is_dirty = True
        self.node.inputs[self.name] = self

    def __unicode__(self) -> str:
        """Show this Plug's type and it's connections."""
        pretty = '\u2192 {0} (IN) {1}'.format(self.name, self.is_dirty)
        pretty += ''.join(['\n\t\t\u2190 {0}.{1}'.format(
            c.node.name, c.name) for c in self.connections])
        return pretty

    def connect(self, plug: IPlug) -> None:
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise Exception(
                'Can\'t connect Plugs that are part of the same Node.')

        for connection in self.connections:
            self.disconnect(connection)

        self.connections = [plug]
        self.is_dirty = True
        if self not in plug.connections:
            plug.connections.append(self)
            plug.is_dirty = True
