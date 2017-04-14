"""Nodes manipulate incoming data and provide the outgoing data."""
from abc import ABCMeta, abstractmethod
__all__ = ['INode']


class INode(object):
    """Holds inputs, outputs and a method for computing."""

    __metaclass__ = ABCMeta

    def __init__(self, name=None):
        """Initialize the input and output dictionaries and the name.

        Args:
            name (str): If not provided, the class name is taken.
        """
        self.name = name if name is not None else self.__class__.__name__
        self.inputs = dict()
        self.outputs = dict()
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
        """@todo documentation for __str__."""
        return unicode(self).encode('utf-8')
    # end def __str__

    @property
    def is_dirty(self):
        """@todo documentation for is_dirty."""
        for input_ in self.inputs.values():
            if input_.is_dirty:
                return True
        # end for
        return False
    # end def is_dirty

    @property
    def upstream_nodes(self):
        """@todo documentation for upstream_nodes."""
        upstream_nodes = list()
        for input_ in self.inputs.values():
            upstream_nodes += [c.node for c in input_.connections]
        # end for
        return list(set(upstream_nodes))
    # end def upstream_nodes

    @property
    def downstream_nodes(self):
        """@todo documentation for downstream_nodes."""
        downstream_nodes = list()
        for output in self.outputs.values():
            downstream_nodes += [c.node for c in output.connections]
        # end for
        return list(set(downstream_nodes))
    # end def downstream_nodes

    def evaluate(self):
        """@todo documentation for evaluate."""
        self.compute()
        for input_ in self.inputs.values():
            input_.is_dirty = False
        # end for
        print(self)
    # end def evaluate

    @abstractmethod
    def compute(self):
        pass
    # end def compute
# end class INode
