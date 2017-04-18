from __future__ import print_function

import mock
import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph
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


class TestCounterNode(INode):

    def __init__(self, name=None):
        super(TestCounterNode, self).__init__(name)
        OutputPlug('out', self)
        InputPlug('in1', self)
        InputPlug('in2', self)
        self.counter = 0

    def compute(self):
        """Multiply the two inputs."""
        self.counter += 1


class TestEngine(unittest.TestCase):
    """Test the Engine."""

    def test_evaluate_entire_graph(self):
        """Evaluate the entire graph ignoring the dirty status."""
        n1 = TestCounterNode('n1')
        n2 = TestCounterNode('n2')
        n3 = TestCounterNode('n3')
        n1.outputs['out'] >> n3.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in2']
        graph = Graph([n1, n2, n3])

        # All nodes are dirty
        for n in graph.nodes:
            self.assertTrue(n.is_dirty)

        # Evaluate all
        Engine.evaluate_entire_graph(graph)
        self.assertEqual(3, sum([n.counter for n in graph.nodes]))

        # All nodes are now clean
        for n in graph.nodes:
            self.assertFalse(n.is_dirty)

        # Evaluate all
        Engine.evaluate_entire_graph(graph)
        self.assertEqual(6, sum([n.counter for n in graph.nodes]))
    # end def test_evaluate_entire_graph

    def test_evaluate_dirty_nodes(self):
        """@todo documentation for test_evaluate_dirty_nodes."""
        n1 = TestCounterNode('n1')
        n2 = TestCounterNode('n2')
        n3 = TestCounterNode('n3')
        n1.outputs['out'] >> n3.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in2']
        graph = Graph([n1, n2, n3])

        # All nodes are dirty
        for n in graph.nodes:
            self.assertTrue(n.is_dirty)

        # Evaluate all
        Engine.evaluate_dirty_nodes(graph)
        self.assertEqual(3, sum([n.counter for n in graph.nodes]))

        # All nodes are now clean
        for n in graph.nodes:
            self.assertFalse(n.is_dirty)

        graph.nodes[1].inputs['in1'].is_dirty = True

        # Evaluate only the dirty nodes
        Engine.evaluate_dirty_nodes(graph)
        self.assertEqual(5, sum([n.counter for n in graph.nodes]))
    # end def test_evaluate_dirty_nodes

    def test_simple_evaluate(self):
        """Evaluate a simple graph of nodes."""
        n1 = TestNode('n1')
        n2 = TestNode('n2')
        n3 = TestNode('n3')

        # Multiply 2 * 3, the result should be 6
        n1.outputs['out'] >> n3.inputs['in1']
        n2.outputs['out'] >> n3.inputs['in2']

        n1.inputs['in1'].value = 1
        n1.inputs['in2'].value = 2
        n2.inputs['in1'].value = 1
        n2.inputs['in2'].value = 3

        graph = Graph([n1, n2, n3])

        Engine.evaluate_dirty_nodes(graph)
        self.assertEqual(6, n3.outputs['out'].value)

        # Change input value from 3 to 4, result will be 8
        n2.inputs['in2'].value = 4
        Engine.evaluate_dirty_nodes(graph)
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

        graph = Graph([v11, v12, r1, v21, r2, v31, v32, r3, result])

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

        Engine.evaluate_dirty_nodes(graph)
        self.assertEqual(24*30, result.outputs['out'].value)

        v11.inputs['in2'].value = 3
        Engine.evaluate_dirty_nodes(graph)
        self.assertEqual(36*30, result.outputs['out'].value)
    # end def test_evaluate_only_dirty_nodes

# end class TestEngine


if __name__ == '__main__':
    unittest.main()
# end if
