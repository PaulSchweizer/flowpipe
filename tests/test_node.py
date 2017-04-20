from __future__ import print_function

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class SquareNode(INode):
    """Square the given value."""

    def __init__(self, name=None):
        """Init the node."""
        super(SquareNode, self).__init__(name)

        # Inputs
        InputPlug('in', self)

        # Outputs
        OutputPlug('out', self)
    # end def __init__

    def compute(self):
        """Square the given input and send to the output."""
        squared = self.inputs['in'].value**2
        self.outputs['out'].value = squared
    # end def compute
# end class SquareNode


class TestPlugs(unittest.TestCase):
    """Test the INode."""

    def test_downstream_upstream_nodes(self):
        """Verify downstream and upstream Nodes."""
        node_a = SquareNode('NodeA')
        node_b = SquareNode('NodeB')
        node_c = SquareNode('NodeC')
        node_a.outputs['out'] >> node_b.inputs['in']
        node_a.outputs['out'] >> node_c.inputs['in']

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
        node.inputs['in'].value = test_input
        node.evaluate()
        self.assertEqual(test_input**2, node.outputs['out'].value)
    # end def test_evaluate

    def test_dirty_depends_on_inputs(self):
        """Dirty status of a Node depends on it's Plugs."""
        node = SquareNode()
        self.assertTrue(node.is_dirty)

        node.inputs['in'].is_dirty = False
        self.assertFalse(node.is_dirty)

        node.inputs['in'].value = 2
        self.assertTrue(node.is_dirty)
    # end def test_dirty_depends_on_inputs

    def test_evaluate_sets_all_inputs_clean(self):
        """After the evaluation, the inputs are considered clean."""
        node = SquareNode()
        node.inputs['in'].value = 2
        self.assertTrue(node.is_dirty)
        node.evaluate()
        self.assertFalse(node.is_dirty)
    # end def test_evaluate_sets_all_inputs_clean
    
    def test_cannot_connect_node_to_itself(self):
        """A node can not create a cycle by connecting to itself."""
        node = SquareNode()
        with self.assertRaises(Exception):
            node.outputs['out'] >> node.inputs['in']
    # end def test_cannot_connect_node_to_itself
# end class TestPlugs


if __name__ == '__main__':
    unittest.main()
# end if
