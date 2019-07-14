"""Plugs are ins and outs for Nodes through which they exchange data."""
from __future__ import print_function
from abc import abstractmethod
__all__ = ['OutputPlug', 'InputPlug']

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


class IPlug(object):
    """The interface for the plugs.

    Plugs are associated with a Node and can be connected, disconnected
    and hold a value, that can be accesses by the associated Node.
    """

    def __init__(self, name, node, accepted_plugs):
        """Initialize the Interface.

        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
            accepted_plugs (list of IPlug): Plugs types that are
                                            possible for connections.
        """
        self.name = name
        self.node = node
        self.connections = []
        self.accepted_plugs = accepted_plugs
        self._sub_plugs = OrderedDict()
        self._value = None
        self._is_dirty = True

    def __rshift__(self, other):
        """Create a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to connect to.
        """
        if isinstance(other, self.accepted_plugs):
            self.connect(other)

    def __lshift__(self, other):
        """Break a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to disconnect.
        """
        if isinstance(other, self.accepted_plugs):
            self.disconnect(other)

    @property
    def value(self):
        """Access to the value on this Plug."""
        return self._value

    @value.setter
    def value(self, value):
        """Set the Plug dirty when the value is being changed."""
        self._value = value
        self.is_dirty = True

    @property
    def is_dirty(self):
        """Access to the dirty status on this Plug."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status):
        """Set the Plug dirty informs the node this Plug belongs to."""
        self._is_dirty = status
        if status:
            self.node.on_input_plug_set_dirty()

    @abstractmethod
    def connect(self, plug):
        """Has to be implemented in the subclass."""

    def disconnect(self, plug):
        """Break the connection to the given Plug."""
        if plug in self.connections:
            self.connections.pop(self.connections.index(plug))
            self.is_dirty = True
        if self in plug.connections:
            plug.connections.pop(plug.connections.index(self))
            plug.is_dirty = True

    def serialize(self):
        """Serialize the Plug containing all it's connections."""
        connections = {}
        for connection in self.connections:
            connections.setdefault(connection.node.identifier, [])
            connections[connection.node.identifier].append(connection.name)
        return {
            'name': self.name,
            'value': self.value if not self._sub_plugs else None,
            'connections': connections,
            'sub_plugs': {
                name: sub_plug.serialize()
                for name, sub_plug in self._sub_plugs.items()
            }
        }


class OutputPlug(IPlug):
    """Provides data to an InputPlug."""

    def __init__(self, name, node):
        """Initialize the OutputPlug.

        Can be connected to an InputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        super(OutputPlug, self).__init__(name, node, (InputPlug, SubInputPlug))
        self.node.outputs[self.name] = self

    def __getitem__(self, key):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if self._value is not None:
            raise ValueError(
                'Plug already has a value directly assigned and can '
                'therefore not be used as a compound plug.')
        if not isinstance(key, str):
            raise TypeError(
                'Only strings are allowed as sub-plug keys! '
                'This is due to the fact that JSON serialization only allows '
                'strings as keys.')
        if not self._sub_plugs.get(key):
            self._sub_plugs[key] = SubOutputPlug(
                name='{0}.{1}'.format(self.name, key),
                node=self.node,
                parent_plug=self)
        return self._sub_plugs[key]

    @property
    def value(self):
        """Access to the value on this Plug."""
        if self._sub_plugs:
            return {name: plug.value for name, plug in self._sub_plugs.items()}
        return self._value

    @value.setter
    def value(self, value):
        """Propagate the dirty state to all connected Plugs as well."""
        if self._sub_plugs:
            raise ValueError(
                'This plug is used as a compound plug, values can only be '
                'assigned to the individual sub plugs via indexing, '
                'e.g. Plug[0].value = "value"')
        self._value = value
        self.is_dirty = True
        for plug in self.connections:
            plug.value = value

    def connect(self, plug):
        """Connect this Plug to the given InputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise ValueError(
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
    """Receives data from an OutputPlug."""

    def __init__(self, name, node, value=None):
        """Initialize the InputPlug.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        super(InputPlug, self).__init__(name, node, (OutputPlug, SubOutputPlug))
        self.value = value
        self.is_dirty = True
        self.node.inputs[self.name] = self

    def __getitem__(self, key):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if self._value is not None:
            raise ValueError(
                'Plug already has a value directly assigned and can '
                'therefore not be used as a compound plug.')
        if not isinstance(key, str):
            raise TypeError(
                'Only strings are allowed as sub-plug keys! '
                'This is due to the fact that JSON serialization only allows '
                'strings as keys.')
        if not self._sub_plugs.get(key):
            self._sub_plugs[key] = SubInputPlug(
                name='{0}.{1}'.format(self.name, key),
                node=self.node,
                parent_plug=self)
        return self._sub_plugs[key]

    @property
    def value(self):
        """Access to the value on this Plug."""
        if self._sub_plugs:
            return {name: plug.value for name, plug in self._sub_plugs.items()}
        return self._value

    @value.setter
    def value(self, value):
        """Set the Plug dirty when the value is being changed."""
        if self._sub_plugs:
            raise ValueError(
                'This plug is used as a compound plug, values can only be '
                'assigned to the individual sub plugs via indexing, '
                'e.g. Plug[0].value = "value"')
        self._value = value
        self.is_dirty = True

    def connect(self, plug):
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise ValueError(
                'Can\'t connect Plugs that are part of the same Node.')

        for connection in self.connections:
            self.disconnect(connection)

        self.connections = [plug]
        self.is_dirty = True
        if self not in plug.connections:
            plug.connections.append(self)
            plug.is_dirty = True


class SubInputPlug(IPlug):
    """Held by a parent input plug to form a compound plug."""

    def __init__(self, name, node, parent_plug, value=None):
        """Initialize the plug.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the Plug has to be in the form:
                {parent_plug.name}.{name}.
            node (INode): The Node holding the Plug.
            parent_plug (InputPlug): The parent plug holding this Plug.
        """
        super(SubInputPlug, self).__init__(name, node, (OutputPlug, SubOutputPlug))
        self.parent_plug = parent_plug
        self.value = value
        self.is_dirty = True

    @property
    def is_dirty(self):
        """Access to the dirty status on this Plug."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status):
        """Setting the Plug dirty informs its parent plug."""
        self._is_dirty = status
        if status:
            self.parent_plug.is_dirty = status

    def connect(self, plug):
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise ValueError(
                'Can\'t connect Plugs that are part of the same Node.')

        for connection in self.connections:
            self.disconnect(connection)

        self.connections = [plug]
        self.is_dirty = True
        if self not in plug.connections:
            plug.connections.append(self)
            plug.is_dirty = True


class SubOutputPlug(IPlug):
    """Held by a parent output plug to form a compound plug."""

    def __init__(self, name, node, parent_plug, value=None):
        """Initialize the plug.

        Can be connected to an InputPlug.
        Args:
            name (str): The name of the Plug has to be in the form:
                {parent_plug.name}.{name}.
            node (INode): The Node holding the Plug.
            parent_plug (InputPlug): The parent plug holding this Plug.
        """
        super(SubOutputPlug, self).__init__(
            name, node, (InputPlug, SubInputPlug))
        self.parent_plug = parent_plug
        self.value = value
        self.is_dirty = True

    @property
    def value(self):
        """Access to the value on this Plug."""
        return self._value

    @value.setter
    def value(self, value):
        """Propagate the dirty state to all connected Plugs as well."""
        self._value = value
        self.is_dirty = True
        for plug in self.connections:
            plug.value = value

    @property
    def is_dirty(self):
        """Access to the dirty status on this Plug."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status):
        """Setting the Plug dirty informs its parent plug."""
        self._is_dirty = status
        if status:
            self.parent_plug.is_dirty = status

    def connect(self, plug):
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if plug.node is self.node:
            raise ValueError(
                'Can\'t connect Plugs that are part of the same Node.')

        for connection in plug.connections:
            plug.disconnect(connection)

        if plug not in self.connections:
            self.connections.append(plug)
            plug.value = self.value
            self.is_dirty = True
        if self not in plug.connections:
            plug.connections = [self]
