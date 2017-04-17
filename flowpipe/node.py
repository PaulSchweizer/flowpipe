"""Nodes manipulate incoming data and provide the outgoing data."""
from __future__ import print_function
from abc import ABCMeta, abstractmethod

from flowpipe.log_observer import LogObserver
__all__ = ['INode']


class INode(object):
    """Holds input and output Plugs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is used.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.inputs = dict()
        self.outputs = dict()
    # end def __init__

    def __unicode__(self):
        """Show all input and output Plugs."""
        pretty = '--- ' + self.name + ' -----------------------------'
        if self.__doc__ is not None:
            pretty += '\n\t{}'.format(self.__doc__)
        pretty += u''.join([u'\n\t{}'.format(i) for i in self.inputs.values()])
        pretty += u''.join([u'\n\t{}'.format(i)
                            for i in self.outputs.values()])
        return pretty
    # end def __unicode__

    def __str__(self):
        """Show all input and output Plugs."""
        return self.__unicode__().encode('utf-8')
    # end def __str__

    @property
    def is_dirty(self):
        """Whether any of the input Plug data has changed and is dirty."""
        for input_ in self.inputs.values():
            if input_.is_dirty:
                return True
        return False
    # end def is_dirty

    @property
    def upstream_nodes(self):
        """The upper level Nodes that feed inputs into this Node."""
        upstream_nodes = list()
        for input_ in self.inputs.values():
            upstream_nodes += [c.node for c in input_.connections]
        return list(set(upstream_nodes))
    # end def upstream_nodes

    @property
    def downstream_nodes(self):
        """The next level Nodes that this Node feed outputs into."""
        downstream_nodes = list()
        for output in self.outputs.values():
            downstream_nodes += [c.node for c in output.connections]
        return list(set(downstream_nodes))
    # end def downstream_nodes

    def evaluate(self):
        """Compute this Node, log it and clean the input Plugs."""
        self.compute()
        for input_ in self.inputs.values():
            input_.is_dirty = False
        LogObserver.push_message(self)
    # end def evaluate

    @abstractmethod
    def compute(self):
        """Implement the data manipulation in the subclass.

        Also update the output Plugs through this function.
        """
        pass
    # end def compute
# end class INode
