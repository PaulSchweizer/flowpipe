"""Basic Node for storing an arbitrary value."""
from __future__ import print_function

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class ValueNode(INode):
    """Holding a simple value."""

    def __init__(self, name=None, value=None):
        """Init the node."""
        super(ValueNode, self).__init__(name)
        InputPlug('value', self, value=value)
        OutputPlug('value', self)

    def compute(self, value):
        """Propagate the input value to the output."""
        return {'value': value}
