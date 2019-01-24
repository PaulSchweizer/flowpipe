import pytest

from flowpipe.graph import Graph
from flowpipe.node import INode

from flowpipe.plug import InputPlug, OutputPlug


class NodeForTesting(INode):

    def __init__(self, name=None, **kwargs):
        super(NodeForTesting, self).__init__(name, **kwargs)
        OutputPlug('out', self)
        InputPlug('in1', self, 0)
        InputPlug('in2', self, 0)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {'out': in1 * in2}


@pytest.fixture
def graph_order_tup():

    start = NodeForTesting('start')
    n11 = NodeForTesting('11')
    n12 = NodeForTesting('12')
    n21 = NodeForTesting('21')
    n31 = NodeForTesting('31')
    n32 = NodeForTesting('32')
    n33 = NodeForTesting('33')
    end = NodeForTesting('end')

    # Connect them
    start.outputs['out'] >> n11.inputs['in1']
    start.outputs['out'] >> n21.inputs['in1']
    start.outputs['out'] >> n31.inputs['in1']

    n31.outputs['out'] >> n32.inputs['in1']
    n32.outputs['out'] >> n33.inputs['in1']

    n11.outputs['out'] >> n12.inputs['in1']
    n33.outputs['out'] >> n12.inputs['in2']

    n12.outputs['out'] >> end.inputs['in1']
    n21.outputs['out'] >> end.inputs['in2']

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    order = [[start], [n11, n21, n31], [n32], [n33], [n12], [end]]

    yield (graph, order)
