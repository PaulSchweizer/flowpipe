import os
import json
import tempfile


location = 'C:\PROJECTS\\flowpipe\\flowpipe\____TEMP' # tempfile.gettempdir()



def evaluate(node):
    """Grab inputs from disc, evaluate node and dump result to disc."""

    # 1. Inputs
    for input_ in node.inputs.values():
        for c in input_.connections:
            data = json.load(open(os.path.join(location, c.node.name + '.json'), 'r'))
            input_.value = data['outputs'][c.name]

    # 2.Evaluate
    node.evaluate()

    # 3. Dump
    data = node.dump()
    f = os.path.join(location, node.name + '.json')
    json.dump(data, open(f, 'w'), indent=2)
# end def evaluate




#######################################################################
from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class TestNode(INode):

    def __init__(self, name=None):
        super(TestNode, self).__init__(name)
        OutputPlug('out', self)
        InputPlug('in1', self, 0)
        InputPlug('in2', self, 0)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {'out': in1 * in2}


if __name__ == '__main__':
    node1 = TestNode(name='t1')
    node1.inputs['in1'].value = 2
    node1.inputs['in2'].value = 1

    node2 = TestNode(name='t2')
    node1.outputs['out'] >> node2.inputs['in1']
    node2.inputs['in2'].value = 2

    # Done by celery
    evaluate(node1)
    evaluate(node2)
