from __future__ import print_function

import unittest

from flowpipe.node import FlowNode, InputPlug, OutputPlug
from flowpipe.app import FlowApp
from flowpipe.engine import FlowEngine


class TestNode(FlowNode):
    """This is the description for the TestNode."""

    def __init__(self, name=None):
        """@todo documentation for __init__."""
        super(TestNode, self).__init__(name)

        # Inputs
        InputPlug('Input', self)

        # Outputs
        OutputPlug('Output', self)
    # end def __init__

    def compute(self):
        pass


class TestFlowNode(unittest.TestCase):
    """Test the FlowNode."""

    def test_init(self):
        """"""
        node_a = TestNode('NodeA')
        node_b = TestNode('NodeB')
        node_c = TestNode('NodeC')

        # Connect the nodes
        node_a.outputs['Output'] >> node_b.inputs['Input']
        node_a.outputs['Output'] >> node_c.inputs['Input']

        print(node_a)
        print(node_b)
        print(node_c)

    # end def test_init

    def __test_change_input_sets_dirty(self):
        """@todo documentation for test_change_input_sets_dirty."""
        node = TestNode()

        self.assertTrue(node.is_dirty)
        node.evaluate()
        self.assertFalse(node.is_dirty)

        node.inputA = 'NewValue'
        # self.assertTrue(node.is_dirty)

    # end def test_change_input_sets_dirty
# end class TestFlowNode


if __name__ == '__main__':
    unittest.main()
# end if
