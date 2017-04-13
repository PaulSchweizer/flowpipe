from __future__ import print_function

import unittest

from flowpipe.node import FlowNode
from flowpipe.app import FlowApp
from flowpipe.engine import FlowEngine


class TestNode(FlowNode):
    """This is the description"""

    inputA = None
    outputA = None

    flow_ins = ['inputA']
    flow_outs = ['outputA']

    def compute(self):
        pass


class TestFlowNode(unittest.TestCase):
    """Test the FlowNode."""

    def test_init(self):
        """"""
        node = TestNode()
        print(node)
    # end def test_init

    def test_change_input_sets_dirty(self):
        """@todo documentation for test_change_input_sets_dirty."""
        node = TestNode()

        self.assertTrue(node.is_dirty)
        node.evaluate()
        self.assertFalse(node.is_dirty)

        node.inputA = 'NewValue'
        self.assertTrue(node.is_dirty)

    # end def test_change_input_sets_dirty
# end class TestFlowNode


if __name__ == '__main__':
    unittest.main()
# end if
