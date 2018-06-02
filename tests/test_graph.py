from __future__ import print_function

import pytest

from flowpipe.node import INode
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph


class NodeForTesting(INode):

    def __init__(self, name=None):
        super(NodeForTesting, self).__init__(name)
        OutputPlug('out', self)
        InputPlug('in1', self, 0)
        InputPlug('in2', self, 0)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {'out': in1 * in2}


def test_evaluation_matrix():
    """The nodes as a 2D grid."""
    start = NodeForTesting('start')
    n11 = NodeForTesting('11')
    n12 = NodeForTesting('12')
    n21 = NodeForTesting('21')
    n31 = NodeForTesting('31')
    n32 = NodeForTesting('32')
    n33 = NodeForTesting('33')
    end = NodeForTesting('end')

    # Connect them
    start.outputs['out'] >> n11.inputs['in1']
    start.outputs['out'] >> n21.inputs['in1']
    start.outputs['out'] >> n31.inputs['in1']

    n31.outputs['out'] >> n32.inputs['in1']
    n32.outputs['out'] >> n33.inputs['in1']

    n11.outputs['out'] >> n12.inputs['in1']
    n33.outputs['out'] >> n12.inputs['in2']

    n12.outputs['out'] >> end.inputs['in1']
    n21.outputs['out'] >> end.inputs['in2']

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    order = [[start], [n11, n21, n31], [n32], [n33], [n12], [end]]

    for i, row in enumerate(graph.evaluation_matrix):
        for node in row:
            assert node in order[i]


def test_linar_evaluation_sequence():
    """A linear graph."""
    n1 = NodeForTesting('n1')
    n2 = NodeForTesting('n2')
    n3 = NodeForTesting('n3')
    n1.outputs['out'] >> n2.inputs['in1']
    n2.outputs['out'] >> n3.inputs['in1']
    nodes = [n2, n1, n3]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert ['n1', 'n2', 'n3'] == seq


def test_branching_evaluation_sequence():
    """Branching graph."""
    n1 = NodeForTesting('n1')
    n2 = NodeForTesting('n2')
    n3 = NodeForTesting('n3')
    n1.outputs['out'] >> n2.inputs['in1']
    n1.outputs['out'] >> n3.inputs['in1']
    nodes = [n2, n1, n3]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert 'n1' == seq[0]
    assert 'n2' in seq[1:]
    assert 'n3' in seq[1:]


def test_complex_branching_evaluation_sequence():
    """Connect and disconnect nodes."""
    # The Nodes
    start = NodeForTesting('start')
    n11 = NodeForTesting('11')
    n12 = NodeForTesting('12')
    n21 = NodeForTesting('21')
    n31 = NodeForTesting('31')
    n32 = NodeForTesting('32')
    n33 = NodeForTesting('33')
    end = NodeForTesting('end')

    # Connect them
    start.outputs['out'] >> n11.inputs['in1']
    start.outputs['out'] >> n21.inputs['in1']
    start.outputs['out'] >> n31.inputs['in1']

    n31.outputs['out'] >> n32.inputs['in1']
    n32.outputs['out'] >> n33.inputs['in1']

    n11.outputs['out'] >> n12.inputs['in1']
    n33.outputs['out'] >> n12.inputs['in2']

    n12.outputs['out'] >> end.inputs['in1']
    n21.outputs['out'] >> end.inputs['in2']

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert 'start' == seq[0]

    assert '11' in seq[1:4]
    assert '21' in seq[1:4]
    assert '31' in seq[1:4]

    assert '32' in seq[4:6]
    assert '33' in seq[4:6]

    assert '12' == seq[-2]
    assert 'end' == seq[-1]


def test_serialize_graph():
    """Serialize the graph to a json-serializable dictionary."""
    start = NodeForTesting('start')
    n11 = NodeForTesting('11')
    n12 = NodeForTesting('12')
    n21 = NodeForTesting('21')
    n31 = NodeForTesting('31')
    n32 = NodeForTesting('32')
    n33 = NodeForTesting('33')
    end = NodeForTesting('end')

    # Connect them
    start.outputs['out'] >> n11.inputs['in1']
    start.outputs['out'] >> n21.inputs['in1']
    start.outputs['out'] >> n31.inputs['in1']

    n31.outputs['out'] >> n32.inputs['in1']
    n32.outputs['out'] >> n33.inputs['in1']

    n11.outputs['out'] >> n12.inputs['in1']
    n33.outputs['out'] >> n12.inputs['in2']

    n12.outputs['out'] >> end.inputs['in1']
    n21.outputs['out'] >> end.inputs['in2']

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    serialized = graph.serialize()
    deserialized = graph.deserialize(serialized)

    assert len(deserialized.nodes) == len(graph.nodes)
    assert graph.identifier == deserialized.identifier
    assert graph.name == deserialized.name

    # Connections need to be deserialized as well
    for i in range(len(graph.nodes)):
        assert graph.nodes[i].identifier == deserialized.nodes[i].identifier
        # inputs
        for name, plug in graph.nodes[i].inputs.items():
            ds_plug = deserialized.nodes[i].inputs[name]
            for j in range(len(plug.connections)):
                connection = plug.connections[j]
                ds_connection = ds_plug.connections[j]
                assert ds_connection.name == connection.name
                assert ds_connection.node.identifier == connection.node.identifier
        # outputs
        for name, plug in graph.nodes[i].outputs.items():
            ds_plug = deserialized.nodes[i].outputs[name]
            for j in range(len(plug.connections)):
                connection = plug.connections[j]
                ds_connection = ds_plug.connections[j]
                assert ds_connection.name == connection.name
                assert ds_connection.node.name == connection.node.name


def test_access_nodes_in_graph_by_name():
    """Access nodes by their name in a Graph."""
    node = NodeForTesting()
    graph = Graph(nodes=[node])
    assert node == graph.node(node.name)[0]
    with pytest.raises(Exception):
        graph.node("DoesNotExist")


def test_access_nodes_in_graph_by_identifier():
    """Access nodes by their identifier in a Graph."""
    node = NodeForTesting()
    graph = Graph(nodes=[node])
    assert node == graph.node_by_id(node.identifier)
    with pytest.raises(Exception):
        graph.node_by_id("DoesNotExist")


def test_string_representations():
    """Print the Graph."""
    start = NodeForTesting('start')
    end = NodeForTesting('end')
    start.outputs['out'] >> end.inputs['in1']
    graph = Graph(nodes=[start, end])
    print(graph)
    print(graph.list_repr())


def test_if_on_node_is_dirty_the_entire_graph_is_dirty():
    start = NodeForTesting('start')
    end = NodeForTesting('end')
    start.outputs['out'] >> end.inputs['in1']
    graph = Graph(nodes=[start, end])
    graph.evaluate()

    assert not graph.is_dirty

    start.inputs["in1"].is_dirty = True
    assert graph.is_dirty


def test_nodes_can_be_added_to_graph():
    """Nodes add themselves to their graph as their parent."""
    graph = Graph()
    graph.add_node(NodeForTesting())
    assert 1 == len(graph.nodes)


def test_nodes_in_graph_can_have_same_name():
    graph = Graph()
    nodes = []
    for i in range(100):
        node = NodeForTesting("SameName")
        graph.add_node(node)
        nodes.append(node)

    print(graph.node("SameName"))


def test_graph_behaves_like_a_node():
    """A Graph can be used the same way as a Node."""
    start = NodeForTesting('Start')
    node = NodeForTesting('Node')
    inner_graph = Graph('InnerGraph', nodes=[node])
    InputPlug('in', inner_graph)
    start.outputs['out'] >> inner_graph.inputs['in']
    outer_graph = Graph('OuterGraph', nodes=[start, inner_graph])

    order = ['Start', 'InnerGraph']
    i = 0
    for r in outer_graph.evaluation_matrix:
        for c in r:
            assert c.name == order[i]
            i += 1
