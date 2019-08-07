from __future__ import print_function
import json

import pytest

from flowpipe.node import INode, FunctionNode, Node


@Node(outputs=['out'])
def function_for_testing(input1, input2):
    """Test documentation."""
    return {'out': 'TestHasPassed'}


def test_input_plugs_are_taken_from_func_inputs(clear_default_graph):
    """Input args to the unction are used as input plugs for the node."""
    @Node()
    def function(arg, kwarg='intial_value'):
        pass
    node = function()
    assert 2 == len(node.inputs.keys())
    assert 'arg' in node.inputs.keys()
    assert 'kwarg' in node.inputs.keys()


def test_name_is_taken_from_func_name_if_not_provided(clear_default_graph):
    """Function name is converted to node name if not provided."""
    @Node()
    def function():
        pass
    node = function()
    assert 'function' == node.name


def test_name_can_be_provided_as_kwarg(clear_default_graph):
    """Name and identifier can be provided."""
    @Node()
    def function():
        pass
    node = function(name='ProvidedNodeName', identifier='TestIdentifier')
    assert 'ProvidedNodeName' == node.name
    assert 'TestIdentifier' == node.identifier


def test_doc_is_taken_from_func(clear_default_graph):
    """Docstring is taken from the function."""
    @Node()
    def function():
        """Function Documentation"""
    node = function()
    assert function.__doc__ == node.__doc__


def test_define_outputs(clear_default_graph):
    """Outputs have to be defined as a list of strings."""
    @Node(outputs=['out1', 'out2'])
    def function():
        pass
    node = function()
    assert 2 == len(node.outputs.keys())
    assert 'out1' in node.outputs.keys()
    assert 'out2' in node.outputs.keys()


def test_decorator_returns_node_instances(clear_default_graph):
    """A call to the decorated function returns a Node instance."""
    @Node()
    def function():
        pass
    node1 = function(graph=None)
    node2 = function(graph=None)
    assert node1 != node2


def test_serialize_function_node(clear_default_graph):
    """Serialization also stored the location of the function."""
    node = function_for_testing(graph=None)
    data = json.dumps(node.serialize())
    deserialized_node = INode.deserialize(json.loads(data))
    assert node.__doc__ == deserialized_node.__doc__
    assert node.name == deserialized_node.name
    assert node.inputs.keys() == deserialized_node.inputs.keys()
    assert node.outputs.keys() == deserialized_node.outputs.keys()
    assert node.evaluate() == deserialized_node.evaluate()


def test_use_self_as_first_arg_if_present(clear_default_graph):
    """If wrapped function has self as first arg, it's used reference to class like in a method."""
    @Node(outputs=['test'])
    def function(self, arg1, arg2):
        return {'test': self.test}
    node = function(graph=None)
    node.test = 'test'
    assert 'test' == node.evaluate()['test']

    @Node(outputs=['test'])
    def function(arg1, arg2):
        return {'test': 'Test without self'}
    node = function(graph=None)
    assert 'Test without self' == node.evaluate()['test']


def test_assign_input_args_to_function_input_plugs(clear_default_graph):
    """Assign inputs to function to the input plugs."""
    @Node(outputs=['test'])
    def function(arg):
        return {'test': arg}
    node = function(arg="test")
    assert 'test' == node.evaluate()['test']


def test_provide_custom_node_class(clear_default_graph):
    """The 'node' key is used to pass a custom class to be used as the Node."""
    class CustomFunctionNode(FunctionNode):
        pass

    @Node(cls=CustomFunctionNode, outputs=['test'])
    def function(arg):
        return {'test': arg}

    node = function(arg="test")
    assert isinstance(node, CustomFunctionNode)


def test_passing_metadata_updates_exisiting_metadata(clear_default_graph):

    @Node(metadata={"arg_1": "value", "arg_2": "value"})
    def function(arg):
        return {}

    node = function(graph=None)
    assert node.metadata == {"arg_1": "value", "arg_2": "value"}

    node = function(metadata={"arg_1": "new_value", "arg3": "new_value"},
                    graph=None)
    assert node.metadata == {"arg_1": "new_value", "arg_2": "value", "arg3": "new_value"}


def test_default_args_are_assigned_to_input_plugs(clear_default_graph):
    @Node()
    def function(arg_1, arg_2="test_1", arg_3="test_2"):
        return {}

    node = function()

    assert node.inputs["arg_1"].value is None
    assert node.inputs["arg_2"].value is "test_1"
    assert node.inputs["arg_3"].value is "test_2"


def test_metadata_is_unique_for_each_node_created(clear_default_graph):
    @Node(metadata={"key": [1, 2, 3]})
    def function():
        pass

    node1 = function(graph=None)
    node2 = function(graph=None)

    assert node1.metadata is not node2.metadata


def test_class_name_restored_after_deserialization(clear_default_graph):
    """Serialization also stored the location of the function."""
    node = function_for_testing(graph=None)
    data = json.dumps(node.serialize())
    deserialized_node = INode.deserialize(json.loads(data))

    assert node.class_name == "function_for_testing"
    assert deserialized_node.class_name == "function_for_testing"
