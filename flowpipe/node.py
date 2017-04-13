"""Nodes manipulate incoming data and provide the outgoing data."""
from abc import ABCMeta, abstractmethod
__all__ = ['FlowNode']


class FlowNode(object):

    __metaclass__ = ABCMeta

    flow_ins = list()
    flow_outs = list()

    def __init__(self):
        self.name = self.__class__.__name__
        self.is_dirty = True
        self.connections = dict()
        self.downstream_nodes = list()
        self.upstream_nodes = list()
    # end def __init__

    def __str__(self):
        pretty = self.name
        if self.__doc__ is not None:
            pretty += '\n\t{}'.format(self.__doc__)
        pretty += ''.join(['\n\t(IN) {0} ({1})'.format(i, getattr(self, i))
                           for i in self.flow_ins])
        pretty += ''.join(['\n\t(OUT) {0} ({1})'.format(i, getattr(self, i))
                           for i in self.flow_outs])
        return pretty

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
        for flow_out, flow_ins in self.connections.items():
            for flow_in in flow_ins:
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
