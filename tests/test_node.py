from __future__ import print_function
import json

import unittest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug


class SquareNode(INode):
    """Square the given value."""

    def __init__(self, name=None):
        """Init the node."""
        super(SquareNode, self).__init__(name)
        InputPlug('in1', self)
        OutputPlug('out', self)

    def compute(self, in1):
        """Square the given input and send to the output."""
        return {'out': in1**2}


class SimpleNode(INode):
    """A simple node."""

    called_args = None

    def __init__(self, name=None):
        """Init the node."""
        super(SimpleNode, self).__init__(name)
        InputPlug('in1', self)
        InputPlug('in2', self)
        InputPlug('in3', self)

    def compute(self, **args):
        """Don't do anything."""
        SimpleNode.called_args = args


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

    def test_evaluate(self):
        """Evaluate the Node will push the new data to it's output."""
        node = SquareNode()
        test_input = 2
        self.assertIsNone(node.outputs['out'].value)
        node.inputs['in1'].value = test_input
        node.evaluate()
        self.assertEqual(test_input**2, node.outputs['out'].value)

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

    def test_dirty_depends_on_inputs(self):
        """Dirty status of a Node depends on it's Plugs."""
        node = SquareNode()
        self.assertTrue(node.is_dirty)

        node.inputs['in1'].is_dirty = False
        self.assertFalse(node.is_dirty)

        node.inputs['in1'].value = 2
        self.assertTrue(node.is_dirty)

    def test_evaluate_sets_all_inputs_clean(self):
        """After the evaluation, the inputs are considered clean."""
        node = SquareNode()
        node.inputs['in1'].value = 2
        self.assertTrue(node.is_dirty)
        node.evaluate()
        self.assertFalse(node.is_dirty)

    def test_cannot_connect_node_to_itself(self):
        """A node can not create a cycle by connecting to itself."""
        node = SquareNode()
        with self.assertRaises(Exception):
            node.outputs['out'] >> node.inputs['in1']

    def test_string_representation(self):
        """Print the node."""
        node = SquareNode()
        node1 = SquareNode()
        node.outputs['out'] >> node1.inputs['in1']
        node.inputs['in1'].value = "Test"
        print(node)
        print(node.list_repr())
        print(node1.list_repr())

    def test_node_has_unique_identifier(self):
        """A Node gets a unique identifiers assigned."""
        ids = [SquareNode().identifier for n in range(1000)]
        self.assertTrue(len(ids), len(set(ids)))

    def test_node_identifier_can_be_set_explicitely(self):
        """The identifier can be set manually."""
        node = SquareNode()
        node.identifier = 'Explicit'
        self.assertEqual('Explicit', node.identifier)

    def test_serialize_node_also_serializes_connections(self):
        """Serialize the node to json with it's connections."""
        node1 = SquareNode('Node1')
        node2 = SquareNode('Node2')
        node1.inputs['in1'].value = 1
        node1.outputs['out'] >> node2.inputs['in1']
        print(json.dumps(node1.serialize(), indent=2))

    def test_deserialize_from_json(self):
        """De-serialize the node from json."""
        node1 = SquareNode('Node1ToSerialize')
        node2 = SquareNode('Node2ToSerialize')
        node1.inputs['in1'].value = 1
        node1.outputs['out'] >> node2.inputs['in1']

        serialized_data = node1.serialize()

        new_node1 = INode.deserialize(serialized_data)

        self.assertEqual(node1.name, new_node1.name)
        self.assertEqual(node1.identifier, new_node1.identifier)
        self.assertEqual(node1.inputs['in1'].value, new_node1.inputs['in1'].value)


if __name__ == '__main__':
    unittest.main()
