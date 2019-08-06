from __future__ import print_function

import pytest

import flowpipe.graph
from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph
from flowpipe.graph import reset_default_graph
from flowpipe.graph import set_default_graph, get_default_graph


@pytest.fixture
def clear_default_graph():
    reset_default_graph()
    yield
    reset_default_graph()


class NodeForTesting(INode):

    def __init__(self, name=None, in1=None, in2=None, **kwargs):
        super(NodeForTesting, self).__init__(name, **kwargs)
        OutputPlug('out', self)
        OutputPlug('out2', self)
        InputPlug('in1', self, in1)
        InputPlug('in2', self, in2)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {'out': in1 * in2, 'out2': None}


def test_evaluation_matrix(clear_default_graph):
    """The nodes as a 2D grid."""
    @Node(outputs=["out", "out2"])
    def DummyNode(in1, in2):
        pass

    start = DummyNode(name='start')
    n11 = DummyNode(name='11')
    n12 = DummyNode(name='12')
    n21 = DummyNode(name='21')
    n31 = DummyNode(name='31')
    n32 = DummyNode(name='32')
    n33 = DummyNode(name='33')
    end = DummyNode(name='end')

    # Connect them
    start.outputs['out'] >> n11.inputs['in1']
    start.outputs['out'] >> n21.inputs['in1']
    start.outputs['out'] >> n31.inputs['in1']['0']

    n31.outputs['out'] >> n32.inputs['in1']
    n32.outputs['out'] >> n33.inputs['in1']

    n11.outputs['out'] >> n12.inputs['in1']
    n33.outputs['out'] >> n12.inputs['in2']

    n12.outputs['out'] >> end.inputs['in1']
    n21.outputs['out2']['0'] >> end.inputs['in2']

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    order = [[start], [n11, n21, n31], [n32], [n33], [n12], [end]]

    for i, row in enumerate(graph.evaluation_matrix):
        for node in row:
            assert node in order[i]

    graph.evaluate()


def test_linar_evaluation_sequence(clear_default_graph):
    """A linear graph."""
    n1 = NodeForTesting('n1')
    n2 = NodeForTesting('n2')
    n3 = NodeForTesting('n3')
    n4 = NodeForTesting('n4')
    n1.outputs['out'] >> n2.inputs['in1']
    n2.outputs['out'] >> n3.inputs['in1']['0']
    n3.outputs['out']['0'] >> n4.inputs['in1']
    nodes = [n2, n1, n3, n4]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert ['n1', 'n2', 'n3', 'n4'] == seq


def test_branching_evaluation_sequence(clear_default_graph):
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


def test_complex_branching_evaluation_sequence(clear_default_graph):
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


def test_serialize_graph(clear_default_graph):
    """
    +------------+          +------------+          +--------------------+
    |   Start    |          |   Node2    |          |        End         |
    |------------|          |------------|          |--------------------|
    o in1<0>     |     +--->o in1<>      |          % in1                |
    o in2<0>     |     |    o in2<0>     |     +--->o  in1.1<>           |
    |        out o-----+    |        out o-----|--->o  in1.2<>           |
    |       out2 o     |    |       out2 o     |    o in2<0>             |
    +------------+     |    +------------+     |    |                out o
                       |    +------------+     |    |               out2 o
                       |    |   Node1    |     |    +--------------------+
                       |    |------------|     |
                       +--->o in1<>      |     |
                            o in2<0>     |     |
                            |        out o-----+
                            |       out2 o
                            +------------+
    """
    graph = Graph()
    start = NodeForTesting(name='Start', graph=graph)
    n1 = NodeForTesting(name='Node1', graph=graph)
    n2 = NodeForTesting(name='Node2', graph=graph)
    end = NodeForTesting(name='End', graph=graph)
    start.outputs['out'] >> n1.inputs['in1']
    start.outputs['out'] >> n2.inputs['in1']
    n1.outputs['out'] >> end.inputs['in1']['1']
    n2.outputs['out'] >> end.inputs['in1']['2']

    serialized = graph.serialize()
    deserialized = graph.deserialize(serialized).serialize()

    assert serialized == deserialized


def test_string_representations(clear_default_graph):
    """Print the Graph."""
    graph = Graph()
    start = NodeForTesting(name='Start', graph=graph)
    n1 = NodeForTesting(name='Node1', graph=graph)
    n2 = NodeForTesting(name='Node2', graph=graph)
    end = NodeForTesting(name='End', graph=graph)
    start.outputs['out'] >> n1.inputs['in1']
    start.outputs['out'] >> n2.inputs['in1']['0']
    n1.outputs['out'] >> end.inputs['in1']['1']
    n2.outputs['out']['0'] >> end.inputs['in1']['2']
    n2.outputs['out']['0'] >> end.inputs['in2']

    assert str(graph) == '\
+------------+          +------------+                  +--------------------+\n\
|   Start    |          |   Node1    |                  |        End         |\n\
|------------|          |------------|                  |--------------------|\n\
o in1<>      |     +--->o in1<>      |                  % in1                |\n\
o in2<>      |     |    o in2<>      |         +------->o  in1.1<>           |\n\
|        out o-----+    |        out o---------+   +--->o  in1.2<>           |\n\
|       out2 o     |    |       out2 o             |--->o in2<>              |\n\
+------------+     |    +------------+             |    |                out o\n\
                   |    +--------------------+     |    |               out2 o\n\
                   |    |       Node2        |     |    +--------------------+\n\
                   |    |--------------------|     |                          \n\
                   |    % in1                |     |                          \n\
                   +--->o  in1.0<>           |     |                          \n\
                        o in2<>              |     |                          \n\
                        |                out %     |                          \n\
                        |             out.0  o-----+                          \n\
                        |               out2 o                                \n\
                        +--------------------+                                '

    assert graph.list_repr() == '''\
Graph
 Start
  [i] in1: null
  [i] in2: null
  [o] out >> Node1.in1, Node2.in1.0
  [o] out2: null
 Node1
  [i] in1 << Start.out
  [i] in2: null
  [o] out >> End.in1.1
  [o] out2: null
 Node2
  [i] in1
   [i] in1.0 << Start.out
  [i] in2: null
  [o] out
   [o] out.0 >> End.in1.2, End.in2
  [o] out2: null
 End
  [i] in1
   [i] in1.1 << Node1.out
   [i] in1.2 << Node2.out.0
  [i] in2 << Node2.out.0
  [o] out: null
  [o] out2: null'''


def test_nodes_can_be_added_to_graph(clear_default_graph):
    """Nodes add themselves to their graph as their parent."""
    graph = Graph()
    graph.add_node(NodeForTesting())
    assert 1 == len(graph.nodes)


def test_nested_graphs_expand_sub_graphs(clear_default_graph):
    """Nested Graphs expand all nodes of their sub graphs on evaluation."""

    @Node(outputs=["out_put"])
    def N(in_put_1, in_put_2):
        return {"out_put": "G1_Node1"}

    # G 3 #############################
    #
    G3 = Graph(name="G3")
    N5 = N(name="N5")
    N4 = N(name="N4")
    G3.add_node(N5)
    G3.add_node(N4)
    N4.outputs["out_put"] >> N5.inputs["in_put_1"]

    # G 2 #############################
    #
    G2 = Graph(name="G2")
    N3 = N(name="N3")
    N2 = N(name="N2")
    N6 = N(name="N6")
    G2.add_node(N3)
    G2.add_node(N2)
    G2.add_node(N6)
    G2.add_node(G3)
    N3.outputs["out_put"] >> N4.inputs["in_put_1"]
    N2.outputs["out_put"] >> N4.inputs["in_put_2"]
    N5.outputs["out_put"] >> N6.inputs["in_put_1"]

    # G 1 #############################
    #
    G1 = Graph(name="G1")
    N1 = N(name="N1")
    N7 = N(name="N7")
    G1.add_node(N1)
    G1.add_node(N7)
    G1.add_node(G2)

    N1.outputs["out_put"] >> N3.inputs["in_put_1"]
    N6.outputs["out_put"] >> N7.inputs["in_put_1"]
    N1.outputs["out_put"] >> N7.inputs["in_put_2"]

    order = [['N1', 'N2'], ['N3'], ['N4'], ['N5'], ['N6'], ['N7']]

    for i, nodes in enumerate(G1.evaluation_matrix):
        assert sorted([n.name for n in nodes]) == sorted(order[i])


def test_nodes_can_be_accessed_via_name_through_indexing(clear_default_graph):
    graph = Graph()
    test_name = "TestName"
    node = NodeForTesting(name=test_name)
    graph.add_node(node)

    assert graph[test_name] == node

    with pytest.raises(KeyError):
        graph["Does not exist"]


def test_node_names_on_graph_have_to_be_unique(clear_default_graph):
    graph = Graph()
    same_name = "Same Name"
    node_1 = NodeForTesting(name=same_name, graph=None)
    graph.add_node(node_1)
    node_2 = NodeForTesting(name=same_name, graph=None)

    with pytest.raises(ValueError):
        graph.add_node(node_2)


def test_nodes_are_only_added_once(clear_default_graph):
    graph = Graph()
    node = NodeForTesting()
    for i in range(10):
        graph.add_node(node)

    assert len(graph.nodes) == 1


def test_nodes_can_add_to_graph_on_init(clear_default_graph):
    graph = Graph()
    node = NodeForTesting(graph=graph)
    assert graph["NodeForTesting"] == node

    @Node()
    def function():
        pass
    node = function(graph=graph)
    assert graph["function"] == node


def test_get_default_graph():
    direct = flowpipe.graph.default_graph
    getter = get_default_graph()
    assert direct is getter


def test_set_default_graph(clear_default_graph):
    new_default = Graph(name='new default')
    set_default_graph(new_default)
    direct = flowpipe.graph.default_graph
    assert direct is new_default

    new_default = "foo"
    with pytest.raises(TypeError):
        set_default_graph(new_default)


def test_reset_default_graph(clear_default_graph):
    new_default = Graph(name='new default')
    set_default_graph(new_default)
    assert get_default_graph().name == 'new default'
    reset_default_graph()
    assert get_default_graph().name == 'default'
