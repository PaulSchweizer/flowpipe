from __future__ import print_function
import json
import unittest

from flowpipe.node import INode, function_to_node


@function_to_node(outputs=['out'])
def test_function():
    """Test documentation."""
    return {'out': 'TestHasPassed'}


class TestConvertFunctionToNode(unittest.TestCase):
    """Convert functions to instances of Nodes."""

    def test_input_plugs_are_taken_from_func_inputs(self):
        """Input args to the unction are used as input plugs for the node."""
        @function_to_node()
        def function(arg, kwarg='intial_value'):
            pass
        node = function()
        self.assertEqual(2, len(node.inputs.keys()))
        self.assertIn('arg', node.inputs.keys())
        self.assertIn('kwarg', node.inputs.keys())

    def test_name_is_taken_from_func_name(self):
        """Function name is converted to node name."""
        @function_to_node()
        def function():
            pass
        node = function()
        self.assertEqual('function', node.name)

    def test_doc_is_taken_from_func(self):
        """Docstring is taken from the function."""
        @function_to_node()
        def function():
            """Function Documentation"""
        node = function()
        self.assertEqual(function.__doc__, node.__doc__)

    def test_define_outputs(self):
        """Outputs have to be defined as a list of strings."""
        @function_to_node(outputs=['out1', 'out2'])
        def function():
            pass
        node = function()
        self.assertEqual(2, len(node.outputs.keys()))
        self.assertIn('out1', node.outputs.keys())
        self.assertIn('out2', node.outputs.keys())

    def test_decorator_returns_node_instances(self):
        """A call to the decorated function returns a Node instance."""
        @function_to_node()
        def function():
            pass
        node1 = function()
        node2 = function()
        self.assertNotEqual(node1, node2)

    def test_serialize_function_node(self):
        """Serialization also stored the location of the function."""
        node = test_function()
        data = json.dumps(node.serialize())
        deserialized_node = INode.deserialize(json.loads(data))
        self.assertEqual(node.__doc__, deserialized_node.__doc__)
        self.assertEqual(node.name, deserialized_node.name)
        self.assertEqual(node.compute(), deserialized_node.compute())


if __name__ == '__main__':
    unittest.main()
