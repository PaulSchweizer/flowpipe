"""Plugs are ins and outs for Nodes through which they exchange data."""
from __future__ import print_function
from abc import abstractmethod
import sys
import warnings
from .utilities import get_hash
__all__ = ['OutputPlug', 'InputPlug']

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

if sys.version_info.major > 2:  # pragma: no cover
    basestring = str

class IterationPlug(list):
    """ This is a special output type, it's basically a list, but for the
    INode objects it's a trigger to itertate over the input """
    def get_nested(self, attr):
        """ Special __getitem__ to get subvalue(s) from the (nested) IterationPlug """
        nested_list = IterationPlug()
        for v in self:
            if isinstance(v, (list, tuple)):
                nested_list.append(IterationPlug(v).get_nested(attr))
            elif isinstance(v, dict):
                nested_list.append(v[attr])
            else:
                nested_list.append(getattr(v, attr))
        return nested_list

class IPlug(object):
    """The interface for the plugs.

    Plugs are associated with a Node and can be connected, disconnected
    and hold a value, that can be accesses by the associated Node.
    """

    def __init__(self, name, node):
        """Initialize the Interface.

        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        if '.' in name and not isinstance(self, SubPlug):
            raise ValueError(
                'Names for plugs can not contain dots "." as these are '
                'reserved to identify sub plugs.')
        self.name = name
        self.node = node
        self.connections = []
        self._sub_plugs = OrderedDict()
        self._value = None
        self._is_dirty = True

    def __rshift__(self, other):
        """Create a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to connect to.
        """
        warnings.warn("Use the connect method instead",
                      DeprecationWarning, stacklevel=2)
        self.connect(other)

    def __lshift__(self, other):
        """Break a connection to the given IPlug.

        Args:
            other (IPlug): The IPlug to disconnect.
        """
        warnings.warn("Use the disconnect method instead",
                      DeprecationWarning, stacklevel=2)
        self.disconnect(other)

    # Extra function to make re-use in subclasses easier
    def _update_value(self, value):
        """Update the internal value."""
        old_hash = get_hash(self._value)
        new_hash = get_hash(value)
        self._value = value
        if old_hash is None or new_hash is None or (old_hash != new_hash):
            self.is_dirty = True

    @property
    def value(self):
        """Access to the value on this Plug."""
        if self._sub_plugs:
            return {name: plug.value for name, plug in self._sub_plugs.items()}
        return self._value

    @value.setter
    def value(self, value):
        """Set the Plug dirty when the value is being changed."""
        self._update_value(value)

    @property
    def is_dirty(self):
        """Access to the dirty status on this Plug."""
        if self._sub_plugs:
            for sub_plug in self._sub_plugs.values():
                if sub_plug.is_dirty:
                    return True
            return False
        else:
            return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, status):
        """Set the Plug dirty informs the node this Plug belongs to."""
        self._is_dirty = status
        if status:
            self.node.on_input_plug_set_dirty()

    @abstractmethod
    def connect(self, plug):  # pragma: no cover
        """Has to be implemented in the subclass."""
        raise NotImplementedError("The subclass has to define connect()")

    def disconnect(self, plug):
        """Break the connection to the given Plug."""
        if plug in self.connections:
            self.connections.pop(self.connections.index(plug))
            self.is_dirty = True
        if self in plug.connections:
            plug.connections.pop(plug.connections.index(self))
            plug.is_dirty = True

    def promote_to_graph(self, name=None):
        """Add this plug to the graph of this plug's node.

        Args:
            name (str): Optionally provide a different name for the Plug
        """
        self.node.graph.add_plug(self, name=name)


class OutputPlug(IPlug):
    """Provides data to an InputPlug."""

    def __init__(self, name, node, accepted_plugs=None):
        """Initialize the OutputPlug.

        Can be connected to an InputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        self.accepted_plugs = (InputPlug,)
        super(OutputPlug, self).__init__(name, node)
        if not isinstance(self, SubPlug):
            self.node.outputs[self.name] = self

    def __rshift__(self, other):
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

    def connect(self, plug):
        """Connect this Plug to the given InputPlug.

        Set both participating Plugs dirty.
        """
        if not isinstance(plug, self.accepted_plugs):
            raise TypeError("Cannot connect {0} to {1}".format(
                type(self), type(plug)))
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

    def __getitem__(self, key):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if not isinstance(key, basestring):
            raise TypeError(
                'Only strings are allowed as sub-plug keys! '
                'This is due to the fact that JSON serialization only allows '
                'strings as keys.')
        if not self._sub_plugs.get(key):
            self._sub_plugs[key] = SubOutputPlug(
                key=key,
                node=self.node,
                parent_plug=self)
        return self._sub_plugs[key]

    def _update_value(self, value):
        """Propagate the dirty state to all connected Plugs as well."""
        super(OutputPlug, self)._update_value(value)
        for plug in self.connections:
            plug.value = value

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


class InputPlug(IPlug):
    """Receives data from an OutputPlug."""

    def __init__(self, name, node, value=None):
        """Initialize the InputPlug.

        Can be connected to an OutputPlug.
        Args:
            name (str): The name of the Plug.
            node (INode): The Node holding the Plug.
        """
        self.accepted_plugs = (OutputPlug,)

        super(InputPlug, self).__init__(name, node)
        self.value = value
        self.is_dirty = True
        if not isinstance(self, SubPlug):
            self.node.inputs[self.name] = self

    def connect(self, plug):
        """Connect this Plug to the given OutputPlug.

        Set both participating Plugs dirty.
        """
        if not isinstance(plug, self.accepted_plugs):
            raise TypeError("Cannot connect {0} to {1}".format(
                type(self), type(plug)))
        plug.connect(self)

    def __getitem__(self, key):
        """Retrieve a sub plug by key.

        If it does not exist yet, it is created automatically!
        Args:
            key (str): The name of the sub plug
        """
        if not isinstance(key, basestring):
            raise TypeError(
                'Only strings are allowed as sub-plug keys! '
                'This is due to the fact that JSON serialization only allows '
                'strings as keys.')
        if not self._sub_plugs.get(key):
            self._sub_plugs[key] = SubInputPlug(
                key=key,
                node=self.node,
                parent_plug=self)
        return self._sub_plugs[key]

    def _update_value(self, value):
        if self._sub_plugs:
            return
        super(InputPlug, self)._update_value(value)

    def serialize(self):
        """Serialize the Plug containing all it's connections."""
        connections = {}
        if self.connections:
            connections[self.connections[0].node.identifier] = self.connections[0].name
        return {
            'name': self.name,
            'value': self.value if not self._sub_plugs else None,
            'connections': connections,
            'sub_plugs': {
                name: sub_plug.serialize()
                for name, sub_plug in self._sub_plugs.items()
            }
        }


class SubPlug(object):
    """Mixin that unifies common properties of subplugs."""

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

    def promote_to_graph(self, name=None):
        """Add this plug to the graph of this plug's node.

        NOTE: Subplugs can only be added to a graph via their parent plug.

        Args:
            name (str): Optionally provide a different name for the Plug
        """
        # prevent adding SubPlug to the graph witout their parents
        raise TypeError(
            "Cannot add SubPlug to graph! Add the parent plug instead.")


class SubInputPlug(SubPlug, InputPlug):
    """Held by a parent input plug to form a compound plug."""

    def __init__(self, key, node, parent_plug, value=None):
        """Initialize the plug.

        Can be connected to an OutputPlug.
        Args:
            key (str): The key will be used to form the name of the Plug:
                {parent_plug.name}.{key}.
            node (INode): The Node holding the Plug.
            parent_plug (InputPlug): The parent plug holding this Plug.
        """
        # super().__init__() refers to self.parent_plug, so need to set it here
        self.key = key
        self.parent_plug = parent_plug
        self.parent_plug._sub_plugs[key] = self

        super(SubInputPlug, self).__init__(
            '{0}.{1}'.format(parent_plug.name, key), node)
        self.value = value
        self.is_dirty = True

    def serialize(self):
        """Serialize the Plug containing all it's connections."""
        connections = {}
        if self.connections:
            connections[self.connections[0].node.identifier] = \
                self.connections[0].name
        return {
            'name': self.name,
            'value': self.value,
            'connections': connections
        }


class SubOutputPlug(SubPlug, OutputPlug):
    """Held by a parent output plug to form a compound plug."""

    def __init__(self, key, node, parent_plug, value=None):
        """Initialize the plug.

        Can be connected to an InputPlug.
        Args:
            key (str): The key will be used to form the name of the Plug:
                {parent_plug.name}.{key}.
            node (INode): The Node holding the Plug.
            parent_plug (InputPlug): The parent plug holding this Plug.
        """
        # super().__init__() refers to self.parent_plug, so need to set it here
        self.key = key
        self.parent_plug = parent_plug
        self.parent_plug._sub_plugs[key] = self

        super(SubOutputPlug, self).__init__(
            '{0}.{1}'.format(parent_plug.name, key), node)
        self.value = value
        self.is_dirty = True

    def _update_value(self, value):
        """Propagate the dirty state to all connected Plugs as well."""
        super(SubOutputPlug, self)._update_value(value)
        for plug in self.connections:
            plug.value = value
        parent_value = self.parent_plug.value or {}
        parent_value[self.key] = value
        self.parent_plug.value = parent_value

    def serialize(self):
        """Serialize the Plug containing all it's connections."""
        connections = {}
        for connection in self.connections:
            connections.setdefault(connection.node.identifier, [])
            connections[connection.node.identifier].append(connection.name)
        return {
            'name': self.name,
            'value': self.value,
            'connections': connections
        }
