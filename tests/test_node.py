from __future__ import print_function
import json

import pytest

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


def test_downstream_upstream_nodes():
    """Verify downstream and upstream Nodes."""
    node_a = SquareNode('NodeA')
    node_b = SquareNode('NodeB')
    node_c = SquareNode('NodeC')
    node_a.outputs['out'] >> node_b.inputs['in1']
    node_a.outputs['out'] >> node_c.inputs['in1']

    assert 2 == len(node_a.downstream_nodes)
    assert node_b in node_a.downstream_nodes
    assert node_c in node_a.downstream_nodes

    assert 1 == len(node_b.upstream_nodes)
    assert node_a in node_b.upstream_nodes


def test_evaluate():
    """Evaluate the Node will push the new data to it's output."""
    node = SquareNode()
    test_input = 2
    assert node.outputs['out'].value is None
    node.inputs['in1'].value = test_input
    node.evaluate()
    assert test_input**2 == node.outputs['out'].value


def test_compute_receives_inputs():
    """The values from the inputs are sent to compute."""
    node = SimpleNode()
    node.inputs['in1'].value = 1
    node.inputs['in2'].value = 2
    node.inputs['in3'].value = 3

    node.evaluate()

    test = {'in1': 1, 'in2': 2, 'in3': 3}
    assert len(test.keys()) == len(SimpleNode.called_args.keys())
    for k, v in SimpleNode.called_args.items():
        assert test[k] == v


def test_dirty_depends_on_inputs():
    """Dirty status of a Node depends on it's Plugs."""
    node = SquareNode()
    assert node.is_dirty

    node.inputs['in1'].is_dirty = False
    assert not node.is_dirty

    node.inputs['in1'].value = 2
    assert node.is_dirty


def test_evaluate_sets_all_inputs_clean():
    """After the evaluation, the inputs are considered clean."""
    node = SquareNode()
    node.inputs['in1'].value = 2
    assert node.is_dirty
    node.evaluate()
    assert not node.is_dirty


def test_cannot_connect_node_to_it():
    """A node can not create a cycle by connecting to it."""
    node = SquareNode()
    with pytest.raises(Exception):
        node.outputs['out'] >> node.inputs['in1']
    with pytest.raises(Exception):
        node.inputs['in1'] >> node.outputs['out']


def test_string_representations():
    """Print the node."""
    node = SquareNode()
    node1 = SquareNode()
    node.outputs['out'] >> node1.inputs['in1']
    node.inputs['in1'].value = "Test"
    print(node)
    print(node.list_repr())
    print(node1.list_repr())


def test_node_has_unique_identifier():
    """A Node gets a unique identifiers assigned."""
    ids = [SquareNode().identifier for n in range(1000)]
    assert len(ids) == len(set(ids))


def test_node_identifier_can_be_set_explicitely():
    """The identifier can be set manually."""
    node = SquareNode()
    node.identifier = 'Explicit'
    assert 'Explicit' == node.identifier


def test_serialize_node_also_serializes_connections():
    """Serialize the node to json with it's connections."""
    node1 = SquareNode('Node1')
    node2 = SquareNode('Node2')
    node1.inputs['in1'].value = 1
    node1.outputs['out'] >> node2.inputs['in1']
    print(json.dumps(node1.serialize(), indent=2))


def test_deserialize_from_json():
    """De-serialize the node from json."""
    node1 = SquareNode('Node1ToSerialize')
    node2 = SquareNode('Node2ToSerialize')
    node1.inputs['in1'].value = 1
    node1.outputs['out'] >> node2.inputs['in1']

    serialized_data = node1.serialize()

    new_node1 = INode.deserialize(serialized_data)

    assert node1.name == new_node1.name
    assert node1.identifier == new_node1.identifier
    assert node1.inputs['in1'].value == new_node1.inputs['in1'].value


def test_omitting_node_does_not_evaluate_it():
    node = SquareNode()
    node.omit = True
    node.outputs['out'].value = 666
    output = node.evaluate()
    assert {} == output
    assert 666 == node.outputs['out'].value
