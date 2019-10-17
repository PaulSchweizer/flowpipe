from __future__ import print_function

import hashlib
import mock
import pytest

from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import reset_default_graph, get_default_graph
from flowpipe.utilities import get_hash


@pytest.fixture
def clear_default_graph():
    reset_default_graph()


class SquareNode(INode):
    """Square the given value."""

    def __init__(self, name=None, *args, **kwargs):
        """Init the node."""
        super(SquareNode, self).__init__(name, *args, **kwargs)
        InputPlug('in1', self)
        InputPlug('compound_in', self)
        OutputPlug('out', self)
        OutputPlug('compound_out', self)

    def compute(self, in1, compound_in=None):
        """Square the given input and send to the output."""
        return {'out': in1**2}


@Node(outputs=['out', 'compound_out'])
def SquareFunctionNode(in1, compound_in):
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


def test_downstream_upstream_nodes(clear_default_graph):
    """Verify downstream and upstream Nodes."""
    node_a = SquareNode('NodeA')
    node_b = SquareNode('NodeB')
    node_c = SquareNode('NodeC')
    node_a.outputs['out'] >> node_b.inputs['in1']
    node_a.outputs['out'] >> node_c.inputs['compound_in']['0']

    assert 2 == len(node_a.downstream_nodes)
    assert node_b in node_a.downstream_nodes
    assert node_c in node_a.downstream_nodes

    assert 1 == len(node_b.upstream_nodes)
    assert node_a in node_b.upstream_nodes
    assert node_a in node_c.upstream_nodes


def test_evaluate(clear_default_graph):
    """Evaluate the Node will push the new data to it's output."""
    node = SquareNode()
    test_input = 2
    assert node.outputs['out'].value is None
    node.inputs['in1'].value = test_input
    node.evaluate()
    assert test_input**2 == node.outputs['out'].value

    @Node(outputs=['compound_out'])
    def CompoundNode(compound_in):
        return {
            'compound_out.0': compound_in['0'],
            'compound_out.1': compound_in['1'],
            'compound_out.2': compound_in['2']
        }

    compound_node = CompoundNode(compound_in={'0': 0, '1': 1, '2': 2})
    compound_node.evaluate()
    assert compound_node.outputs['compound_out']['0'].value == 0
    assert compound_node.outputs['compound_out']['1'].value == 1
    assert compound_node.outputs['compound_out']['2'].value == 2


def test_compute_receives_inputs(clear_default_graph):
    """The values from the inputs are sent to compute."""
    node = SimpleNode()
    node.inputs['in1'].value = 1
    node.inputs['in2'].value = 2
    node.inputs['in3']['0'].value = 3
    node.inputs['in3']['key'].value = 4

    node.evaluate()

    test = {'in1': 1, 'in2': 2, 'in3': {'0': 3, 'key': 4}}
    assert len(test.keys()) == len(SimpleNode.called_args.keys())
    for k, v in SimpleNode.called_args.items():
        assert test[k] == v


def test_dirty_depends_on_inputs(clear_default_graph):
    """Dirty status of a Node depends on it's Plugs."""
    node = SquareNode()
    assert node.is_dirty

    node.inputs['in1'].is_dirty = False
    node.inputs['compound_in'].is_dirty = False
    assert not node.is_dirty

    node.inputs['compound_in']['0'].is_dirty = True
    node.inputs['compound_in']['1'].is_dirty = False
    assert node.is_dirty

    node.inputs['compound_in']['0'].is_dirty = False
    assert not node.is_dirty

    node.inputs['in1'].value = 42
    assert node.is_dirty


def test_evaluate_sets_all_inputs_clean(clear_default_graph):
    """After the evaluation, the inputs are considered clean."""
    node = SquareNode()
    node.inputs['in1'].value = 2
    node.inputs['compound_in']['0'].value = 0
    assert node.is_dirty
    node.evaluate()
    assert not node.is_dirty


def test_cannot_connect_node_to_itself(clear_default_graph):
    """A node can not create a cycle by connecting to itself."""
    node = SquareNode()
    with pytest.raises(ValueError):
        node.outputs['out'] >> node.inputs['in1']
    with pytest.raises(ValueError):
        node.inputs['in1']['0'] >> node.outputs['out']
    with pytest.raises(ValueError):
        node.outputs['out']['0'] >> node.inputs['in1']['0']
    with pytest.raises(ValueError):
        node.inputs['in1'] >> node.outputs['out']


def test_string_representations(clear_default_graph):
    """Print the node."""
    node = SquareNode(name='Node1')
    node1 = SquareNode(name='Node2')
    node2 = SquareNode(name='Node3')
    node1.inputs['in1'].value = 'Test'
    node1.inputs['compound_in']['key-1'].value = 'value'
    node1.inputs['compound_in']['0'].value = 0
    node.outputs['out'] >> node1.inputs['in1']
    node.outputs['compound_out']['1'] >> node1.inputs['compound_in']['1']
    node1.outputs['compound_out']['1'] >> node2.inputs['in1']

    assert str(node) == '''\
+-----------------------------+
|            Node1            |
|-----------------------------|
o compound_in<>               |
o in1<>                       |
|                compound_out %
|             compound_out.1  o---
|                         out o---
+-----------------------------+'''

    assert str(node1) == '''\
   +-----------------------------+
   |            Node2            |
   |-----------------------------|
   % compound_in                 |
   o  compound_in.0<0>           |
-->o  compound_in.1<>            |
   o  compound_in.key-1<"value"> |
-->o in1<>                       |
   |                compound_out %
   |             compound_out.1  o---
   |                         out o
   +-----------------------------+'''

    assert node.list_repr() == '''\
Node1
  [i] compound_in: null
  [i] in1: null
  [o] compound_out
   [o] compound_out.1 >> Node2.compound_in.1
  [o] out >> Node2.in1'''

    assert node1.list_repr() == '''\
Node2
  [i] compound_in
   [i] compound_in.0: 0
   [i] compound_in.1 << Node1.compound_out.1
   [i] compound_in.key-1: "value"
  [i] in1 << Node1.out
  [o] compound_out
   [o] compound_out.1 >> Node3.in1
  [o] out: null'''


def test_node_has_unique_identifier(clear_default_graph):
    """A Node gets a unique identifiers assigned."""
    ids = [SquareNode(graph=None).identifier for n in range(1000)]
    assert len(ids) == len(set(ids))


def test_node_identifier_can_be_set_explicitely(clear_default_graph):
    """The identifier can be set manually."""
    node = SquareNode()
    node.identifier = 'Explicit'
    assert 'Explicit' == node.identifier


@mock.patch('inspect.getfile', return_value='/path/to/node/implementation.py')
def test_serialize_node_serialize_to_json(mock_inspect, clear_default_graph):
    """Serialize the node to json with it's connections."""
    node1 = SquareNode('Node1')
    node2 = SquareFunctionNode(name='Node2')
    node1.inputs['in1'].value = 1
    node1.outputs['out'] >> node2.inputs['in1']
    node1.outputs['compound_out']['key'] >> node2.inputs['compound_in']['key']
    node1.outputs['compound_out']['1'] >> node2.inputs['compound_in']['1']

    node1.outputs['out'].value = 'value'
    node1.outputs['compound_out']['key'].value = 'value_key'
    node1.outputs['compound_out']['1'].value = 'value_1'

    node2.outputs['out'].value = 'value'
    node2.outputs['compound_out']['key'].value = 'value_key'
    node2.outputs['compound_out']['1'].value = 'value_1'

    data = node1.to_json()
    assert data == {
        'inputs': {
            'compound_in': {
                'connections': {},
                'name': 'compound_in',
                'value': None,
                'sub_plugs': {}
            },
            'in1': {
                'connections': {},
                'name': 'in1',
                'value': 1,
                'sub_plugs': {}
            }
        },
        'outputs': {
            'compound_out': {
                'connections': {},
                'name': 'compound_out',
                'value': None,
                'sub_plugs': {
                    '1': {
                        'connections': {
                            node2.identifier: [
                                'compound_in.1'
                            ]
                        },
                        'name': 'compound_out.1',
                        'value': 'value_1'
                    },
                    'key': {
                        'connections': {
                            node2.identifier: [
                                'compound_in.key'
                            ]
                        },
                        'name': 'compound_out.key',
                        'value': 'value_key'
                    }
                }
            },
            'out': {
                'connections': {
                    node2.identifier: [
                        'in1'
                    ]
                },
                'name': 'out',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'name': 'Node1',
        'metadata': {},
        'module': 'test_node',
        'file_location': '/path/to/node/implementation.py',
        'identifier': node1.identifier,
        'cls': 'SquareNode'
    }
    data2 = node2.to_json()
    assert data2 == {
        'inputs': {
            'compound_in': {
                'connections': {},
                'name': 'compound_in',
                'value': None,
                'sub_plugs': {
                    '1': {
                        'connections': {
                            node1.identifier: 'compound_out.1'
                        },
                        'name': 'compound_in.1',
                        'value': 'value_1'
                    },
                    'key': {
                        'connections': {
                            node1.identifier: 'compound_out.key'
                        },
                        'name': 'compound_in.key',
                        'value': 'value_key'
                    }
                }
            },
            'in1': {
                'connections': {
                    node1.identifier: 'out'
                },
                'name': 'in1',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'name': 'Node2',
        'outputs': {
            'compound_out': {
                'connections': {},
                'name': 'compound_out',
                'value': None,
                'sub_plugs': {
                    '1': {
                        'connections': {},
                        'name': 'compound_out.1',
                        'value': 'value_1'
                    },
                    'key': {
                        'connections': {},
                        'name': 'compound_out.key',
                        'value': 'value_key'
                    }
                }
            },
            'out': {
                'connections': {},
                'name': 'out',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'metadata': {},
        'module': 'flowpipe.node',
        'file_location': '/path/to/node/implementation.py',
        'identifier': node2.identifier,
        'cls': 'FunctionNode',
        'func': {
            'name': 'SquareFunctionNode',
            'module': 'test_node'
        }
    }


@mock.patch('inspect.getfile', return_value='/path/to/node/implementation.py')
def test_deserialize_from_json(mock_inspect, clear_default_graph):
    """De-serialize the node from json."""
    node1 = SquareNode('Node1')
    node2 = SquareFunctionNode(name='Node2')
    node1.inputs['in1'].value = 1
    node1.outputs['out'] >> node2.inputs['in1']
    node1.outputs['compound_out']['key'] >> node2.inputs['compound_in']['key']
    node1.outputs['compound_out']['1'] >> node2.inputs['compound_in']['1']

    node1.outputs['out'].value = 'value'
    node1.outputs['compound_out']['key'].value = 'value_key'
    node1.outputs['compound_out']['1'].value = 'value_1'

    node2.outputs['out'].value = 'value'
    node2.outputs['compound_out']['key'].value = 'value_key'
    node2.outputs['compound_out']['1'].value = 'value_1'

    deserialized_data = INode.from_json(node1.to_json()).to_json()
    assert deserialized_data == {
        'inputs': {
            'compound_in': {
                'connections': {},
                'name': 'compound_in',
                'value': None,
                'sub_plugs': {}
            },
            'in1': {
                'connections': {},
                'name': 'in1',
                'value': 1,
                'sub_plugs': {}
            }
        },
        'name': 'Node1',
        'outputs': {
            'compound_out': {
                'connections': {},
                'name': 'compound_out',
                'value': None,
                'sub_plugs': {
                    'key': {
                            'connections': {},
                            'name': 'compound_out.key',
                            'value': 'value_key'
                    },
                    '1': {
                            'connections': {},
                            'name': 'compound_out.1',
                            'value': 'value_1'
                    }
                }
            },
            'out': {
                'connections': {},
                'name': 'out',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'metadata': {},
        'module': 'test_node',
        'file_location': '/path/to/node/implementation.py',
        'identifier': node1.identifier,
        'cls': 'SquareNode'
    }

    deserialized_data2 = INode.from_json(node2.to_json()).to_json()
    assert deserialized_data2 == {
        'inputs': {
            'compound_in': {
                'connections': {},
                'name': 'compound_in',
                'value': None,
                'sub_plugs': {
                    '1': {
                        'connections': {},
                        'name': 'compound_in.1',
                        'value': 'value_1'
                    },
                    'key': {
                        'connections': {},
                        'name': 'compound_in.key',
                        'value': 'value_key'
                    }
                }
            },
            'in1': {
                'connections': {},
                'name': 'in1',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'name': 'Node2',
        'outputs': {
            'compound_out': {
                'connections': {},
                'name': 'compound_out',
                'value': None,
                'sub_plugs': {
                    'key': {
                        'connections': {},
                        'name': 'compound_out.key',
                        'value': 'value_key'
                    },
                    '1': {
                        'connections': {},
                        'name': 'compound_out.1',
                        'value': 'value_1'
                    }
                }
            },
            'out': {
                'connections': {},
                'name': 'out',
                'value': 'value',
                'sub_plugs': {}
            }
        },
        'metadata': {},
        'module': 'flowpipe.node',
        'file_location': '/path/to/node/implementation.py',
        'identifier': node2.identifier,
        'cls': 'FunctionNode',
        'func': {
            'module': 'test_node',
            'name': 'SquareFunctionNode'
        }
    }


def test_serialize_node_serialize_to_pickle(clear_default_graph):
    node1 = SquareNode('Node1')
    node2 = SquareNode(name='Node2')
    node1.inputs['in1'].value = 1
    node1.outputs['out'] >> node2.inputs['in1']
    node1.outputs['compound_out']['key'] >> node2.inputs['compound_in']['key']
    node1.outputs['compound_out']['1'] >> node2.inputs['compound_in']['1']

    node1.outputs['out'].value = 'value'
    node1.outputs['compound_out']['key'].value = 'value_key'
    node1.outputs['compound_out']['1'].value = 'value_1'

    node2.outputs['out'].value = 'value'
    node2.outputs['compound_out']['key'].value = 'value_key'
    node2.outputs['compound_out']['1'].value = 'value_1'

    rec1 = INode.from_pickle(node1.to_pickle())
    # Using the to_json serialization as a check here is suboptimal, but we
    # don't have another INode.__eq__(self, other)
    assert rec1.to_json() == node1.to_json()
    rec2 = INode.from_pickle(node2.to_pickle())
    assert rec2.to_json() == node2.to_json()


def test_deserialize_node_does_not_add_to_default_graph(clear_default_graph):
    node1 = SquareNode('Node1')
    node2 = SquareFunctionNode(name='Node2')

    node1.from_json(node1.to_json())
    node1.from_json(node1.to_json())

    node2.from_json(node2.to_json())
    node2.from_json(node2.to_json())

    assert len(get_default_graph().nodes) == 2


def test_omitting_node_does_not_evaluate_it(clear_default_graph):
    node = SquareNode()
    node.omit = True
    node.outputs['out'].value = 666
    output = node.evaluate()
    assert {} == output
    assert 666 == node.outputs['out'].value


def test_all_inputs_contains_all_sub_input_plugs(clear_default_graph):
    node = SquareNode()
    node.inputs['in1'].value = 'Test'
    node.inputs['compound_in']['key-1'].value = 'value'
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = None

    assert sorted(node.all_inputs().keys()) == sorted([
        'in1',
        'compound_in',
        'compound_in.key-1',
        'compound_in.0',
        'compound_in.1'])


def test_all_outputs_contains_all_sub_output_plugs(clear_default_graph):
    node = SquareNode()
    node.outputs['out'].value = 'Test'
    node.outputs['compound_out']['key-1'].value = 'value'
    node.outputs['compound_out']['0'].value = 0
    node.outputs['compound_out']['1'].value = None

    assert sorted(node.all_outputs().keys()) == sorted([
        'out',
        'compound_out',
        'compound_out.key-1',
        'compound_out.0',
        'compound_out.1'])
