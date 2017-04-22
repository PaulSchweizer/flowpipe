from __future__ import print_function

import unittest
import mock

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class SquareNode(INode):
    """Square the given value."""

    def __init__(self, name=None):
        """Init the node."""
        super(SquareNode, self).__init__(name)

        # Inputs
        InputPlug('in1', self)

        # Outputs
        OutputPlug('out', self)
    # end def __init__

    def compute(self, in1):
        """Square the given input and send to the output."""
        self.outputs['out'].value = in1**2
    # end def compute
# end class SquareNode


class SimpleNode(INode):
    """A simple node."""

    called_args = None

    def __init__(self, name=None):
        """Init the node."""
        super(SimpleNode, self).__init__(name)
        InputPlug('in1', self)
        InputPlug('in2', self)
        InputPlug('in3', self)
    # end def __init__

    def compute(self, **args):
        """Don't do anything."""
        SimpleNode.called_args = args
    # end def compute
# end class SimpleNode


class TestNode(unittest.TestCase):
    """Test the INode."""

    def test_downstream_upstream_nodes(self):
        """Verify downstream and upstream Nodes."""
        node_a = SquareNode('NodeA')
        node_b = SquareNode('NodeB')
        node_c = SquareNode('NodeC')
        node_a.outputs['out'] >> node_b.inputs['in1']
        node_a.outputs['out'] >> node_c.inputs['in1']

        self.assertEqual(2, len(node_a.downstream_nodes))
        self.assertIn(node_b, node_a.downstream_nodes)
        self.assertIn(node_c, node_a.downstream_nodes)

        self.assertEqual(1, len(node_b.upstream_nodes))
        self.assertIn(node_a, node_b.upstream_nodes)
    # end def test_downstream_upstream_nodes

    def test_evaluate(self):
        """Evaluate the Node will push the new data to it's output."""
        node = SquareNode()
        test_input = 2
        self.assertIsNone(node.outputs['out'].value)
        node.inputs['in1'].value = test_input
        node.evaluate()
        self.assertEqual(test_input**2, node.outputs['out'].value)
    # end def test_evaluate

    # @mock.patch('flowpipe.node.INode.compute')
    def test_compute_receives_inputs(self):
        """The values from the inputs are sent to compute."""
        node = SimpleNode()
        node.inputs['in1'].value = 1
        node.inputs['in2'].value = 2
        node.inputs['in3'].value = 3

        node.evaluate()

        test = {'in1': 1, 'in2': 2, 'in3': 3}
        self.assertEqual(len(test.keys()), len(SimpleNode.called_args.keys()))
        for k, v in SimpleNode.called_args.items():
            self.assertEqual(test[k], v)
    # end def test_compute_receives_inputs

    def test_dirty_depends_on_inputs(self):
        """Dirty status of a Node depends on it's Plugs."""
        node = SquareNode()
        self.assertTrue(node.is_dirty)

        node.inputs['in1'].is_dirty = False
        self.assertFalse(node.is_dirty)

        node.inputs['in1'].value = 2
        self.assertTrue(node.is_dirty)
    # end def test_dirty_depends_on_inputs

    def test_evaluate_sets_all_inputs_clean(self):
        """After the evaluation, the inputs are considered clean."""
        node = SquareNode()
        node.inputs['in1'].value = 2
        self.assertTrue(node.is_dirty)
        node.evaluate()
        self.assertFalse(node.is_dirty)
    # end def test_evaluate_sets_all_inputs_clean

    def test_cannot_connect_node_to_itself(self):
        """A node can not create a cycle by connecting to itself."""
        node = SquareNode()
        with self.assertRaises(Exception):
            node.outputs['out'] >> node.inputs['in1']
    # end def test_cannot_connect_node_to_itself
# end class TestNode


if __name__ == '__main__':
    unittest.main()
# end if
