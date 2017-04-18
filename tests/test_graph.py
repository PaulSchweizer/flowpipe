from __future__ import print_function

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph


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


class TestGraph(unittest.TestCase):
    """Test the Graph."""

    def test_evaluation_grid(self):
        """The nodes as a 2D grid."""
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

        nodes = [start, n11, n12, n21, n31, n32, n33, end]
        graph = Graph(nodes)

        order = [[start], [n11, n21, n31], [n32], [n33], [n12], [end]]

        for i, row in enumerate(graph.evaluation_grid):
            for node in row:
                self.assertIn(node, order[i])
    # end def test_evaluation_grid

    def test_linar_evaluation_sequence(self):
        """A linear graph."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')
        n1.outputs['out'] >> n2.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in1']
        nodes = [n2, n1, n3]
        graph = Graph(nodes)

        seq = [s.name for s in graph.evaluation_sequence]

        self.assertEqual(['n1', 'n2', 'n3'], seq)
    # end def test_linar_evaluation_sequence

    def test_branching_evaluation_sequence(self):
        """Branching graph."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')
        n1.outputs['out'] >> n2.inputs['in1']
        n1.outputs['out'] >> n3.inputs['in1']
        nodes = [n2, n1, n3]
        graph = Graph(nodes)

        seq = [s.name for s in graph.evaluation_sequence]

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

        nodes = [start, n11, n12, n21, n31, n32, n33, end]
        graph = Graph(nodes)

        seq = [s.name for s in graph.evaluation_sequence]

        self.assertEqual('start', seq[0])

        self.assertIn('11', seq[1:4])
        self.assertIn('21', seq[1:4])
        self.assertIn('31', seq[1:4])

        self.assertIn('32', seq[4:6])
        self.assertIn('33', seq[4:6])

        self.assertEqual('12', seq[-2])
        self.assertEqual('end', seq[-1])
    # end def test_complex_branching_evaluation_sequence
# end class TestGraph


if __name__ == '__main__':
    unittest.main()
# end if
