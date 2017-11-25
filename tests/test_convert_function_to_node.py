from __future__ import print_function
import json
import unittest

from flowpipe.node import INode, function_to_node


@function_to_node(outputs=['out'])
def test_function(input1, input2):
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
        node.inputs["input1"].value = "Test"
        data = json.dumps(node.serialize())
        deserialized_node = INode.deserialize(json.loads(data))
        self.assertEqual(node.__doc__, deserialized_node.__doc__)
        self.assertEqual(node.name, deserialized_node.name)
        self.assertEqual(node.inputs.keys(), deserialized_node.inputs.keys())
        self.assertEqual([v.value for v in node.inputs.values()],
                         [v.value for v in deserialized_node.inputs.values()])
        self.assertEqual(node.outputs.keys(), deserialized_node.outputs.keys())
        self.assertEqual(node.evaluate(), deserialized_node.evaluate())

    def test_use_self_as_first_arg_if_present(self):
        """If wrapped function has self as first arg, it's used reference to class like in a method."""
        @function_to_node(outputs=['test'])
        def function(self, arg1, arg2):
            return {'test': self.test}
        node = function()
        node.test = 'test'
        self.assertEqual('test', node.evaluate()['test'])

        @function_to_node(outputs=['test'])
        def function(arg1, arg2):
            return {'test': 'Test without self'}
        node = function()
        self.assertEqual('Test without self', node.evaluate()['test'])

    def test_assign_input_args_to_function_input_plugs(self):
        """Assign inputs to function to the input plugs."""
        @function_to_node(outputs=['test'])
        def function(arg):
            return {'test': arg}
        node = function(arg="test")
        self.assertEqual('test', node.evaluate()['test'])


if __name__ == '__main__':
    unittest.main()
