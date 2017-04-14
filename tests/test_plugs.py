from __future__ import print_function

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class TestNode(INode):

    def __init__(self):
        super(TestNode, self).__init__()

    def compute(self):
        pass


class TestPlugs(unittest.TestCase):
    """Test the Plugs."""

    def test_connect_and_dicsonnect_nodes(self):
        """Connect and disconnect nodes."""
        n = TestNode()
        out_plug_a = OutputPlug('in', n)
        out_plug_b = OutputPlug('in', n)
        in_plug_a = InputPlug('in', n)
        in_plug_b = InputPlug('in', n)

        # Connect the out to the in
        out_plug_a >> in_plug_a
        self.assertEqual(1, len(out_plug_a.connections))
        self.assertEqual(1, len(in_plug_a.connections))

        # Connect the same nodes multiple times
        out_plug_a >> in_plug_a
        self.assertEqual(1, len(out_plug_a.connections))
        self.assertEqual(1, len(in_plug_a.connections))

        # Connect the in to the out
        in_plug_b >> out_plug_a
        self.assertEqual(2, len(out_plug_a.connections))
        self.assertEqual(1, len(in_plug_b.connections))

        # Connect the in to the multiple times
        in_plug_b >> out_plug_a
        self.assertEqual(2, len(out_plug_a.connections))
        self.assertEqual(1, len(in_plug_b.connections))

        # Connecting a different input disconnects the existing one
        self.assertEqual(out_plug_a, in_plug_a.connections[0])
        out_plug_b >> in_plug_a
        self.assertEqual(out_plug_b, in_plug_a.connections[0])
    # end def test_connect_and_dicsonnect_nodes

    def test_change_connections_sets_plug_dirty(self):
        """Connecting and disconnecting sets the plug dirty."""
        n = TestNode()
        out_plug = OutputPlug('in', n)
        in_plug = InputPlug('in', n)

        self.assertFalse(in_plug.is_dirty)
        out_plug >> in_plug
        self.assertTrue(in_plug.is_dirty)

        in_plug.is_dirty = False
        out_plug << in_plug
        self.assertTrue(in_plug.is_dirty)
    # end def test_change_connections_sets_plug_dirty

    def test_set_value_sets_plug_dirty(self):
        """Connecting and disconnecting sets the plug dirty."""
        n = TestNode()
        in_plug = InputPlug('in', n)

        self.assertFalse(in_plug.is_dirty)
        in_plug.value = 'NewValue'
        self.assertTrue(in_plug.is_dirty)
    # end def test_set_value_sets_plug_dirty

    def test_set_output_pushes_value_to_connected_input(self):
        """OutPlugs push their values to their connected input plugs."""
        n = TestNode()
        out_plug = OutputPlug('in', n)
        in_plug = InputPlug('in', n)

        out_plug.value = 'OldValue'
        self.assertNotEqual(in_plug.value, out_plug.value)

        out_plug >> in_plug
        in_plug.is_dirty = False
        self.assertEqual(in_plug.value, out_plug.value)
        self.assertFalse(in_plug.is_dirty)

        out_plug.value = 'NewValue'
        self.assertTrue(in_plug.is_dirty)
        self.assertEqual(in_plug.value, out_plug.value)
    # end def test_set_output_pushes_value_to_connected_input
# end class TestPlugs


if __name__ == '__main__':
    unittest.main()
# end if
