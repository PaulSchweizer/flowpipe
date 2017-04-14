"""PLugs provide inputs and outputs for Nodes."""
from abc import abstractmethod


class IPlug(object):
    """The interface for the plugs."""

    def __init__(self, name, node, accepted_plugs):
        """Initialize the IPlug.

        Args:
            name (str): The name of the plug.
            node (INode): The Node holding the IPlug.
            accepted_plugs (list of IPLug): Plugs for connections.
        """
        self.name = name
        self.node = node
        self.connections = list()
        self.accepted_plugs = accepted_plugs
        self._value = None
        self.is_dirty = False
    # end def __init__

    def __str__(self):
        """@todo documentation for __str__."""
        return unicode(self).encode('utf-8')
    # end def __str__

    def __rshift__(self, other):
        """Create a Connection to the given IPlug.

        @param other The IPlug
        """
        if isinstance(other, self.accepted_plugs):
            self.connect(other)
        # end if
    # end def __rshift__

    def __lshift__(self, other):
        """Create a Connection to the given OutputPlug.

        @param other The OutputPlug
        """
        if isinstance(other, self.accepted_plugs):
            self.disconnect(other)
        # end if
    # end def __rshift__

    @property
    def value(self):
        """@todo documentation for value."""
        return self._value
    # end def value

    @value.setter
    def value(self, value):
        """@todo documentation for value."""
        self._value = value
        self.is_dirty = True
    # end def value

    @abstractmethod
    def connect(self, plug):
        """@todo documentation for connect."""
        pass
    # end def connect

    def disconnect(self, plug):
        """@todo documentation for disconnect."""
        if plug in self.connections:
            self.connections.pop(self.connections.index(plug))
            self.is_dirty = True
        if self in plug.connections:
            plug.connections.pop(plug.connections.index(self))
            plug.is_dirty = True
    # end def disconnect
# end class IPlug


class OutputPlug(IPlug):
    """A OutputPlug for a Connection."""

    def __init__(self, name, node):
        """Initialize the OutputPlug.

        Can be connected to the `InputPlug`.
        Args:
            name (str): The name of the plug.
            node (INode): The Node holding the `IPlug`.
        """
        super(OutputPlug, self).__init__(name, node, (InputPlug, ))
        self.node.outputs[self.name] = self
    # end def __init__

    def __unicode__(self):
        """@todo documentation for __unicode__."""
        pretty = u'\u2190 {0} (OUT)'.format(self.name)
        pretty += u''.join([u'\n\t\t\u2192 {0}.{1}'.format(
            c.name, c.node.name) for c in self.connections])
        return pretty
    # end def __unicode__

    @property
    def value(self):
        """@todo documentation for value."""
        return self._value
    # end def value

    @value.setter
    def value(self, value):
        """@todo documentation for value."""
        self._value = value
        self.is_dirty = True
        for plug in self.connections:
            plug.value = value
        # end for
    # end def value

    def connect(self, plug):
        """@todo documentation for connect."""
        if plug not in self.connections:
            self.connections.append(plug)
            plug.value = self.value
            self.is_dirty = True
        if self not in plug.connections:
            plug.connections = [self]
    # end def connect
# end class OutputPlug


class InputPlug(IPlug):
    """A InputPlug for a Connection."""

    def __init__(self, name, node):
        """Initialize the InputPlug.

        Can be connected to the `OutputPlug`.
        Args:
            name (str): The name of the plug.
            node (INode): The Node holding the `IPlug`.
        """
        super(InputPlug, self).__init__(name, node, (OutputPlug, ))
        self.node.inputs[self.name] = self
    # end def __init__

    def __unicode__(self):
        """@todo documentation for __unicode__."""
        pretty = u'\u2192 {0} (IN) {1}'.format(self.name, self.is_dirty)
        pretty += u''.join([u'\n\t\t\u2190 {0}.{1}'.format(
                c.name, c.node.name) for c in self.connections])
        return pretty
    # end def __unicode__

    def connect(self, plug):
        """@todo documentation for connect."""
        self.connections = [plug]
        self.is_dirty = True
        if self not in plug.connections:
            plug.connections.append(self)
            plug.is_dirty = True
    # end def connect
# end class InputPlug
