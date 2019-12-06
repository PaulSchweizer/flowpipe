import pytest

from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph

class NodeForTesting(INode):

    def __init__(self, name=None, in1=None, in2=None, **kwargs):
        super(NodeForTesting, self).__init__(name, **kwargs)
        OutputPlug('out', self)
        OutputPlug('out2', self)
        InputPlug('in1', self, in1)
        InputPlug('in2', self, in2)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {'out': in1 * in2, 'out2': None}

@pytest.fixture
def branching_graph():
    graph = Graph(name="TestGraph")
    start = NodeForTesting(name='Start', graph=graph)
    n1 = NodeForTesting(name='Node1', graph=graph)
    n2 = NodeForTesting(name='Node2', graph=graph)
    end = NodeForTesting(name='End', graph=graph)
    start.outputs['out'] >> n1.inputs['in1']
    start.outputs['out'] >> n2.inputs['in1']
    n1.outputs['out'] >> end.inputs['in1']['1']
    n2.outputs['out'] >> end.inputs['in1']['2']

    yield graph