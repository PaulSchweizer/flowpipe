from __future__ import print_function

import unittest

from flowpipe.node import FlowNode
from flowpipe.app import FlowApp
from flowpipe.engine import FlowEngine


class TestNode(FlowNode):
    """This is the description"""
    def compute(self):
        pass


class TestFlowNode(unittest.TestCase):
    """Test the FlowNode."""

    def test_init(self):
        """"""
        node = TestNode()
        node.inputA = None
        node.outputA = None

        node.flow_ins = ['inputA']
        node.flow_outs = ['outputA']

        print(node)

    # end def test_init
# end class TestFlowNode


if __name__ == '__main__':
    unittest.main()
# end if
