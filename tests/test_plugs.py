from __future__ import print_function

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
    def B(b):
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
    in_plug = InputPlug('in', n2)
    out_plug >> in_plug

    in_serialized = in_plug.serialize()
    out_serialized = out_plug.serialize()

    assert in_plug.name == in_serialized['name']
    assert in_plug.value == in_serialized['value']
    assert 'out' == in_serialized['connections'][out_plug.node.identifier]

    assert out_plug.name == out_serialized['name']
    assert out_plug.value == out_serialized['value']
    assert 'in' == out_serialized['connections'][in_plug.node.identifier]


def test_pretty_printing():
    node = NodeForTesting()
    in_plug = InputPlug('in', node)
    out_plug = OutputPlug('out', node)
    print(in_plug)
    print(out_plug)
