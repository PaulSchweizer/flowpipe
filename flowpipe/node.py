"""Nodes manipulate incoming data and provide the outgoing data."""
from abc import ABCMeta, abstractmethod
__all__ = ['FlowNode']


class OutputPlug(object):
    """A OutputPlug for a Connection."""

    def __init__(self, name, node):
        """Initialize the OutputPlug.

        @param name The name of the plug
        @param node The Node holding the OutputPlug
        """
        self.name = name
        self.node = node
        self.node.outputs[self.name] = self
        self.connections = list()
    # end def __init__

    def __unicode__(self):
        """@todo documentation for __unicode__."""
        pretty = u'\u2190 {0} (OUT)'.format(self.name)
        pretty += u''.join([u'\n\t\t\u2192 {0}.{1}'.format(
            c.name, c.node.name) for c in self.connections])
        return pretty
    # end def __unicode__

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __rshift__(self, other):
        """Create a Connection to the given InputPlug.

        @param other The InputPlug
        """
        if isinstance(other, InputPlug):
            self.connect(other)
        # end if
    # end def __rshift__

    def connect(self, plug):
        """@todo documentation for connect."""
        if plug not in self.connections:
            self.connections.append(plug)
        if self not in plug.connections:
            plug.connections.append(self)
    # end def connect
# end class OutputPlug


class InputPlug(object):
    """A InputPlug for a Connection."""

    def __init__(self, name, node):
        """Initialize the InputPlug.

        @param name The name of the plug
        @param node The Node holding the InputPlug
        """
        self.name = name
        self.node = node
        self.node.inputs[self.name] = self
        self.connections = list()
    # end def __init__

    def __unicode__(self):
        """@todo documentation for __unicode__."""
        pretty = u'\u2192 {0} (IN)'.format(self.name)
        pretty += u''.join([u'\n\t\t\u2190 {0}.{1}'.format(
            c.name, c.node.name) for c in self.connections])
        return pretty
    # end def __unicode__

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __lshift__(self, other):
        """Create a Connection to the given OutputPlug.

        @param other The OutputPlug
        """
        if isinstance(other, OutputPlug):
            self.connect(other)
        # end if
    # end def __rshift__

    def connect(self, plug):
        """@todo documentation for connect."""
        if plug not in self.connections:
            self.connections.append(plug)
        if self not in plug.connections:
            plug.connections.append(self)
    # end def connect
# end class InputPlug


class FlowNode(object):

    __metaclass__ = ABCMeta

    def __init__(self, name=None):
        self.name = name if name is not None else self.__class__.__name__
        self.is_dirty = True
        self.inputs = dict()
        self.outputs = dict()
        self.connections = dict()
        self.downstream_nodes = list()
        self.upstream_nodes = list()
    # end def __init__

    def __unicode__(self):
        """@todo documentation for __unicode__."""
        pretty = '--- ' + self.name + ' -----------------------------'
        if self.__doc__ is not None:
            pretty += '\n\t{}'.format(self.__doc__)
        pretty += u''.join([u'\n\t{}'.format(i) for i in self.inputs.values()])
        pretty += u''.join([u'\n\t{}'.format(i)
                            for i in self.outputs.values()])
        return pretty
    # end def __unicode__

    def __str__(self):
        return unicode(self).encode('utf-8')

    def connect(self, flow_out, in_node, flow_in):
        if flow_out not in self.connections.keys():
            self.connections[flow_out] = list()
        self.connections[flow_out].append((in_node, flow_in))
        in_node.add_upstream_node(self)
        self.add_downstream_node(in_node)
    # end def connect

    def add_upstream_node(self, node):
        if node not in self.upstream_nodes:
            self.upstream_nodes.append(node)
    # end def add_upstream_node

    def add_downstream_node(self, node):
        if node not in self.downstream_nodes:
            self.downstream_nodes.append(node)
    # end def add_downstream_node

    def evaluate(self):
        self.compute()
        for flow_out, inputs in self.connections.items():
            for flow_in in inputs:
                setattr(flow_in[0], flow_in[1], getattr(self, flow_out))
            # end for
        # end for
        print(self)
        self.is_dirty = False
    # end def evaluate

    @abstractmethod
    def compute(self):
        pass
    # end def compute
# end class FlowNode
