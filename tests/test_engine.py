from __future__ import print_function

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.engine import Engine


class TestNode(INode):

    def __init__(self, name=None):
        super(TestNode, self).__init__(name)
        OutputPlug('out', self)
        InputPlug('in1', self)
        InputPlug('in2', self)

    def compute(self):
        pass


class TestEngine(unittest.TestCase):
    """Test the Plugs."""

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
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')
        n4 = TestNode('n4')

        n1.outputs['out'] >> n2.inputs['in1']
        n1.outputs['out'] >> n3.inputs['in1']
        n1.outputs['out'] >> n4.inputs['in1']
        n2.outputs['out'] >> n4.inputs['in2']

        seq = [s.name for s in Engine.evaluation_sequence([n3, n4, n1, n2])]

        self.assertEqual('n1', seq[0])
        self.assertEqual('n4', seq[-1])
        self.assertIn('n2', seq[1:3])
        self.assertIn('n3', seq[1:3])
    # end def test_complex_branching_evaluation_sequence

    def test_evaluate(self):
        """@todo documentation for test_evaluate."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')

        n1.outputs['out'] >> n2.inputs['in1']
        n1.outputs['out'] >> n3.inputs['in1']

        n1.inputs['in1'].value = 'NewValue'

        Engine.evaluate([n1, n2, n3])
    # end def test_evaluate

# end class TestEngine


if __name__ == '__main__':
    unittest.main()
# end if
