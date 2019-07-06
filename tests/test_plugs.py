from __future__ import print_function

import pytest

from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug


class NodeForTesting(INode):

    def compute(self):
        pass


def test_connecting_different_input_disconnects_existing_ones():

    @Node(outputs=["a_out"])
    def A(a):
        pass

    @Node(outputs=["b_out"])
    def B(b, b_compound):
        pass

    @Node(outputs=["c_out"])
    def C(c):
        pass

    a = A()
    b = B()
    c = C()

    a.outputs["a_out"].connect(b.inputs["b"])
    c.outputs["c_out"].connect(b.inputs["b"])

    assert not a.outputs["a_out"].connections

    b.inputs["b"].connect(a.outputs["a_out"])

    assert a.outputs["a_out"].connections

    b.inputs["b"].connect(c.outputs["c_out"])

    assert not a.outputs["a_out"].connections

    b.inputs["b_compound"]["0"].connect(a.outputs["a_out"])
    assert b.inputs["b_compound"]["0"].connections[0] == a.outputs["a_out"]

    b.inputs["b_compound"]["0"].connect(c.outputs["c_out"])
    assert b.inputs["b_compound"]["0"].connections[0] == c.outputs["c_out"]


def test_connect_and_dicsonnect_nodes():
    """Connect and disconnect nodes."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug_a = OutputPlug('out', n1)
    in_plug_a = InputPlug('in', n2)
    in_plug_b = InputPlug('in', n2)

    # Connect the out to the in
    out_plug_a >> in_plug_a
    assert 1 == len(out_plug_a.connections)
    assert 1 == len(in_plug_a.connections)

    # Connect the same nodes multiple times
    out_plug_a >> in_plug_a
    assert 1 == len(out_plug_a.connections)
    assert 1 == len(in_plug_a.connections)

    # Connect the in to the out
    in_plug_b >> out_plug_a
    assert 2 == len(out_plug_a.connections)
    assert 1 == len(in_plug_b.connections)

    # Connect the in to the multiple times
    in_plug_b >> out_plug_a
    assert 2 == len(out_plug_a.connections)
    assert 1 == len(in_plug_b.connections)


def test_change_connections_sets_plug_dirty():
    """Connecting and disconnecting sets the plug dirty."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('in', n1)
    in_plug = InputPlug('in', n2)

    in_plug.is_dirty = False
    out_plug >> in_plug
    assert in_plug.is_dirty

    in_plug.is_dirty = False
    out_plug << in_plug
    assert in_plug.is_dirty


def test_set_value_sets_plug_dirty():
    """Connecting and disconnecting sets the plug dirty."""
    n = NodeForTesting()
    in_plug = InputPlug('in', n)

    in_plug.is_dirty = False
    assert not in_plug.is_dirty
    in_plug.value = 'NewValue'
    assert in_plug.is_dirty


def test_set_output_pushes_value_to_connected_input():
    """OutPlugs push their values to their connected input plugs."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('in', n1)
    in_plug = InputPlug('in', n2)

    out_plug.value = 'OldValue'
    assert in_plug.value != out_plug.value

    out_plug >> in_plug
    in_plug.is_dirty = False
    assert in_plug.value == out_plug.value
    assert not in_plug.is_dirty

    out_plug.value = 'NewValue'
    assert in_plug.is_dirty
    assert in_plug.value == out_plug.value


def test_assign_initial_value_to_input_plug():
    """Assign an initial value to an InputPlug."""
    n = NodeForTesting()
    in_plug = InputPlug('in', n)
    assert in_plug.value is None

    in_plug = InputPlug('in', n, 123)
    assert 123 == in_plug.value


def test_serialize():
    """Serialize the Plug to json."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('out', n1)
    out_plug.value = 'out_value'
    in_plug = InputPlug('in', n2)
    in_plug_with_value = InputPlug('in_value', n2, 'value')
    compound_in_plug = InputPlug('compound_in', n2)
    out_plug >> in_plug
    out_plug >> compound_in_plug['incoming']

    compound_in_plug['0'].value = 0
    compound_in_plug['key'].value = 'value'

    in_serialized = in_plug.serialize()
    assert in_serialized == {
        'name': 'in',
        'value': 'out_value',
        'connections': {
            out_plug.node.identifier: ['out']
        },
        'sub_plugs': {}
    }

    in_plug_with_value_serialized = in_plug_with_value.serialize()
    assert in_plug_with_value_serialized == {
        'name': 'in_value',
        'value': 'value',
        'connections': {},
        'sub_plugs': {}
    }

    compound_in_serialized = compound_in_plug.serialize()
    assert compound_in_serialized == {
        'name': 'compound_in',
        'value': None,
        'connections': {},
        'sub_plugs': {
            '0': {
                'connections': {},
                'name': 'compound_in.0',
                'value': 0,
                'sub_plugs': {}
            },
            'incoming': {
                'connections': {
                    out_plug.node.identifier: ['out']
                },
                'name': 'compound_in.incoming',
                'value': 'out_value',
                'sub_plugs': {}
            },
            'key': {
                'connections': {},
                'name': 'compound_in.key',
                'value': 'value',
                'sub_plugs': {}
            }
        }
    }

    out_serialized = out_plug.serialize()
    assert out_serialized == {
        'name': 'out',
        'value': 'out_value',
        'connections': {
            in_plug.node.identifier: ['in', 'compound_in.incoming']
        },
        'sub_plugs': {}
    }


def test_pretty_printing():
    node = NodeForTesting()
    in_plug = InputPlug('in', node)
    out_plug = OutputPlug('out', node)
    print(in_plug)
    print(out_plug)


def test_compound_plugs_can_only_be_strings():
    @Node()
    def A(compound_in):
        pass

    node = A()

    with pytest.raises(Exception):
        node.inputs['compound_in'][0].value = 0


def test_compound_input_plugs_are_accessible_by_index():

    @Node(outputs=['value'])
    def A(value):
        return {'value': value}

    @Node(outputs=['sum'])
    def B(compound_in):
        return {'sum': sum(compound_in.values())}

    a1 = A(value=1)
    a2 = A(value=2)
    a3 = A(value=3)
    b = B()

    a1.outputs['value'].connect(b.inputs['compound_in']['0'])
    a2.outputs['value'].connect(b.inputs['compound_in']['1'])
    a3.outputs['value'].connect(b.inputs['compound_in']['2'])

    a1.evaluate()
    a2.evaluate()
    a3.evaluate()

    b.evaluate()

    assert b.outputs['sum'].value == 6


def test_compound_plugs_can_be_connected_individually():

    @Node(outputs=['value'])
    def A(compound_in):
        pass

    a1 = A()
    a2 = A()

    a2.inputs['compound_in']['0'].connect(a1.outputs['value'])


def test_compound_plugs_are_not_dirty_if_parent_plug_is_dirty():

    @Node()
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    node.inputs['compound_in'].is_dirty = False
    node.inputs['compound_in']['0'].is_dirty = False
    node.inputs['compound_in']['1'].is_dirty = False

    node.inputs['compound_in'].is_dirty = True

    assert not node.inputs['compound_in']['0'].is_dirty
    assert not node.inputs['compound_in']['1'].is_dirty


def test_compound_plugs_propagate_dirty_state_to_their_parent():

    @Node()
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    node.inputs['compound_in'].is_dirty = False
    node.inputs['compound_in']['0'].is_dirty = False
    node.inputs['compound_in']['1'].is_dirty = False

    node.inputs['compound_in']['0'].is_dirty = True

    assert node.inputs['compound_in'].is_dirty


def test_compound_plug_exception_if_value_is_assigned_to_it_plug_directly():

    @Node()
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    with pytest.raises(Exception):
        node.inputs['compound_in'].value = 2
