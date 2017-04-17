from __future__ import print_function

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.engine import Engine


class TestNode(INode):

    def __init__(self, name=None):
        super(TestNode, self).__init__(name)
        OutputPlug('out', self)
        InputPlug('in1', self, 0)
        InputPlug('in2', self, 0)

    def compute(self):
        """Multiply the two inputs."""
        result = self.inputs['in1'].value * self.inputs['in2'].value
        self.outputs['out'].value = result


class TestEngine(unittest.TestCase):
    """Test the Engine."""

    def test_linar_evaluation_sequence(self):
        """Connect and disconnect nodes."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')

        n1.outputs['out'] >> n2.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in1']

        seq = [s.name for s in Engine.evaluation_sequence([n2, n1, n3])]

        self.assertEqual(['n1', 'n2', 'n3'], seq)
    # end def test_linar_evaluation_sequence

    def test_branching_evaluation_sequence(self):
        """Connect and disconnect nodes."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')

        n1.outputs['out'] >> n2.inputs['in1']
        n1.outputs['out'] >> n3.inputs['in1']

        seq = [s.name for s in Engine.evaluation_sequence([n3, n1, n2])]

        self.assertEqual('n1', seq[0])
        self.assertIn('n2', seq[1:])
        self.assertIn('n3', seq[1:])
    # end def test_branching_evaluation_sequence

    def test_complex_branching_evaluation_sequence(self):
        """Connect and disconnect nodes."""
        # The Nodes
        start = TestNode('start')
        n11 = TestNode('11')
        n12 = TestNode('12')
        n21 = TestNode('21')
        n31 = TestNode('31')
        n32 = TestNode('32')
        n33 = TestNode('33')
        end = TestNode('end')

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

        seq = [s.name for s in Engine.evaluation_sequence([start, n11,
                                                          n12, n21, n31,
                                                          n32, n33, end])]

        self.assertEqual('start', seq[0])

        self.assertIn('11', seq[1:4])
        self.assertIn('21', seq[1:4])
        self.assertIn('31', seq[1:4])

        self.assertIn('32', seq[4:6])
        self.assertIn('33', seq[4:6])

        self.assertEqual('12', seq[-2])
        self.assertEqual('end', seq[-1])
    # end def test_complex_branching_evaluation_sequence

    def test_simple_evaluate(self):
        """Evaluate a simple graph of nodes."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')

        # Multiply 2 * 3, the result should be 6
        n1.outputs['out'] >> n3.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in2']

        n1.outputs['out'].value = 2
        n2.outputs['out'].value = 3

        nodes = [n1, n2, n3]

        Engine.evaluate(nodes)
        self.assertEqual(6, n3.outputs['out'].value)

        # Change input value from 3 to 4, result will be 8
        n2.outputs['out'].value = 4
        Engine.evaluate(nodes)
        self.assertEqual(8, n3.outputs['out'].value)
    # end def test_simple_evaluate

    def test_evaluate_only_dirty_nodes(self):
        """Only evaluate the nodes that need evaluation."""
        # The Nodes
        v11 = TestNode('v11')
        v12 = TestNode('v12')
        r1 = TestNode('r1')

        v21 = TestNode('v21')
        r2 = TestNode('r2')

        v31 = TestNode('v31')
        v32 = TestNode('v32')
        r3 = TestNode('r3')

        result = TestNode('result')

        v11.outputs['out'] >> r1.inputs['in1']
        v12.outputs['out'] >> r1.inputs['in2']

        v21.outputs['out'] >> r2.inputs['in1']
        r1.outputs['out'] >> r2.inputs['in2']

        v31.outputs['out'] >> r3.inputs['in1']
        v32.outputs['out'] >> r3.inputs['in2']

        r2.outputs['out'] >> result.inputs['in1']
        r3.outputs['out'] >> result.inputs['in2']

        nodes = [v11, v12, r1, v21, r2, v31, v32, r3, result]

        seq = [s.name for s in Engine.evaluation_sequence(nodes)]

        # Calculate an initial value
        v11.inputs['in1'].value = 1
        v11.inputs['in2'].value = 2

        v12.inputs['in1'].value = 1
        v12.inputs['in2'].value = 3

        v21.inputs['in1'].value = 1
        v21.inputs['in2'].value = 4

        v31.inputs['in1'].value = 1
        v31.inputs['in2'].value = 5

        v32.inputs['in1'].value = 1
        v32.inputs['in2'].value = 6

        Engine.evaluate(nodes)
        self.assertEqual(24*30, result.outputs['out'].value)

        v11.inputs['in2'].value = 3
        Engine.evaluate(nodes)
        self.assertEqual(36*30, result.outputs['out'].value)
    # end def test_evaluate_only_dirty_nodes

# end class TestEngine


if __name__ == '__main__':
    unittest.main()
# end if
