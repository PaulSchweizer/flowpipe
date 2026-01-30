from __future__ import print_function

import time

import mock
import pytest

import flowpipe.graph
from flowpipe.errors import CycleError
from flowpipe.evaluator import Evaluator, LinearEvaluator
from flowpipe.graph import (
    Graph,
    get_default_graph,
    reset_default_graph,
    set_default_graph,
)
from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, InputPlugGroup, OutputPlug


@pytest.fixture
def clear_default_graph():
    reset_default_graph()


class NodeForTesting(INode):
    def __init__(self, name=None, in1=None, in2=None, **kwargs):
        super(NodeForTesting, self).__init__(name, **kwargs)
        OutputPlug("out", self)
        OutputPlug("out2", self)
        InputPlug("in1", self, in1)
        InputPlug("in2", self, in2)

    def compute(self, in1, in2):
        """Multiply the two inputs."""
        return {"out": in1 * in2, "out2": None}


@Node(outputs=["out"])
def FunctionNodeForTesting(in_, in_1, in_2):
    return {"out": None}


def test_evaluation_matrix(clear_default_graph):
    """The nodes as a 2D grid."""

    @Node(outputs=["out", "out2"])
    def DummyNode(in1, in2):
        pass

    start = DummyNode(name="start")
    n11 = DummyNode(name="11")
    n12 = DummyNode(name="12")
    n21 = DummyNode(name="21")
    n31 = DummyNode(name="31")
    n32 = DummyNode(name="32")
    n33 = DummyNode(name="33")
    end = DummyNode(name="end")

    # Connect them
    start.outputs["out"] >> n11.inputs["in1"]
    start.outputs["out"] >> n21.inputs["in1"]
    start.outputs["out"] >> n31.inputs["in1"]["0"]

    n31.outputs["out"] >> n32.inputs["in1"]
    n32.outputs["out"] >> n33.inputs["in1"]

    n11.outputs["out"] >> n12.inputs["in1"]
    n33.outputs["out"] >> n12.inputs["in2"]

    n12.outputs["out"] >> end.inputs["in1"]
    n21.outputs["out2"]["0"] >> end.inputs["in2"]

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    order = [[start], [n11, n21, n31], [n32], [n33], [n12], [end]]

    for i, row in enumerate(graph.evaluation_matrix):
        for node in row:
            assert node in order[i]
        assert len(row) == len(order[i])

    graph.evaluate()


def test_linar_evaluation_sequence(clear_default_graph):
    """A linear graph."""
    n1 = NodeForTesting("n1")
    n2 = NodeForTesting("n2")
    n3 = NodeForTesting("n3")
    n4 = NodeForTesting("n4")
    n1.outputs["out"] >> n2.inputs["in1"]
    n2.outputs["out"] >> n3.inputs["in1"]["0"]
    n3.outputs["out"]["0"] >> n4.inputs["in1"]
    nodes = [n2, n1, n3, n4]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert ["n1", "n2", "n3", "n4"] == seq


def test_branching_evaluation_sequence(clear_default_graph):
    """Branching graph."""
    n1 = NodeForTesting("n1")
    n2 = NodeForTesting("n2")
    n3 = NodeForTesting("n3")
    n1.outputs["out"] >> n2.inputs["in1"]
    n1.outputs["out"] >> n3.inputs["in1"]
    nodes = [n2, n1, n3]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert "n1" == seq[0]
    assert "n2" in seq[1:]
    assert "n3" in seq[1:]


def test_complex_branching_evaluation_sequence(clear_default_graph):
    """Connect and disconnect nodes."""
    # The Nodes
    start = NodeForTesting("start")
    n11 = NodeForTesting("11")
    n12 = NodeForTesting("12")
    n21 = NodeForTesting("21")
    n31 = NodeForTesting("31")
    n32 = NodeForTesting("32")
    n33 = NodeForTesting("33")
    end = NodeForTesting("end")

    # Connect them
    start.outputs["out"] >> n11.inputs["in1"]
    start.outputs["out"] >> n21.inputs["in1"]
    start.outputs["out"] >> n31.inputs["in1"]

    n31.outputs["out"] >> n32.inputs["in1"]
    n32.outputs["out"] >> n33.inputs["in1"]

    n11.outputs["out"] >> n12.inputs["in1"]
    n33.outputs["out"] >> n12.inputs["in2"]

    n12.outputs["out"] >> end.inputs["in1"]
    n21.outputs["out"] >> end.inputs["in2"]

    nodes = [start, n11, n12, n21, n31, n32, n33, end]
    graph = Graph(nodes=nodes)

    seq = [s.name for s in graph.evaluation_sequence]

    assert "start" == seq[0]

    assert "11" in seq[1:4]
    assert "21" in seq[1:4]
    assert "31" in seq[1:4]

    assert "32" in seq[4:6]
    assert "33" in seq[4:6]

    assert "12" == seq[-2]
    assert "end" == seq[-1]


def test_serialize_graph_to_json(clear_default_graph, branching_graph):
    serialized = branching_graph.to_json()
    deserialized = Graph.from_json(serialized)

    assert branching_graph.name == deserialized.name
    assert serialized == deserialized.to_json()


def test_serialize_graph_to_pickle(clear_default_graph, branching_graph):
    serialized = branching_graph.to_pickle()
    deserialized = Graph.from_pickle(serialized)
    assert deserialized.to_json() == branching_graph.to_json()


def test_string_representations(clear_default_graph, branching_graph):
    """Print the Graph."""
    assert (
        str(branching_graph)
        == "\
+------------------------------------------------------------------------+\n\
|                               TestGraph                                |\n\
|------------------------------------------------------------------------|\n\
| +------------+          +------------+          +--------------------+ |\n\
| |   Start    |          |   Node1    |          |        End         | |\n\
| |------------|          |------------|          |--------------------| |\n\
| o in1<>      |     +--->o in1<>      |          % in1<>              | |\n\
| o in2<>      |     |    o in2<>      |     +--->o  in1.1<>           | |\n\
| |      out<> o-----+    |      out<> o-----+--->o  in1.2<>           | |\n\
| |     out2<> o     |    |     out2<> o     |    o in2<>              | |\n\
| +------------+     |    +------------+     |    |              out<> o |\n\
|                    |    +------------+     |    |             out2<> o |\n\
|                    |    |   Node2    |     |    +--------------------+ |\n\
|                    |    |------------|     |                           |\n\
|                    +--->o in1<>      |     |                           |\n\
|                         o in2<>      |     |                           |\n\
|                         |      out<> o-----+                           |\n\
|                         |     out2<> o                                 |\n\
|                         +------------+                                 |\n\
+------------------------------------------------------------------------+\n\
                                                                          "
    )
    assert (
        branching_graph.list_repr()
        == """TestGraph
 Start
  [i] in1: null
  [i] in2: null
  [o] out >> Node1.in1, Node2.in1
  [o] out2: null
 Node1
  [i] in1 << Start.out
  [i] in2: null
  [o] out >> End.in1.1
  [o] out2: null
 Node2
  [i] in1 << Start.out
  [i] in2: null
  [o] out >> End.in1.2
  [o] out2: null
 End
  [i] in1
   [i] in1.1 << Node1.out
   [i] in1.2 << Node2.out
  [i] in2: null
  [o] out: null
  [o] out2: null"""
    )


def test_string_representations_with_subgraphs(clear_default_graph):
    """For nested graphs, graph names are shown in header of nodes."""
    main = Graph(name="main")
    sub1 = Graph(name="sub1")
    sub2 = Graph(name="sub2")

    start = NodeForTesting(name="Start", graph=main)
    n1 = NodeForTesting(name="Node1", graph=sub1)
    n2 = NodeForTesting(name="Node2", graph=sub1)
    end = NodeForTesting(name="End", graph=sub2)
    start.outputs["out"] >> n1.inputs["in1"]
    start.outputs["out"] >> n2.inputs["in1"]["0"]
    n1.outputs["out"] >> end.inputs["in1"]["1"]
    n2.outputs["out"]["0"] >> end.inputs["in1"]["2"]
    n2.outputs["out"]["0"] >> end.inputs["in2"]
    assert (
        str(main)
        == "\
+--------------------------------------------------------------------------------+\n\
|                                      main                                      |\n\
|--------------------------------------------------------------------------------|\n\
| +----main----+          +----sub1----+                  +--------sub2--------+ |\n\
| |   Start    |          |   Node1    |                  |        End         | |\n\
| |------------|          |------------|                  |--------------------| |\n\
| o in1<>      |     +--->o in1<>      |                  % in1<>              | |\n\
| o in2<>      |     |    o in2<>      |         +------->o  in1.1<>           | |\n\
| |      out<> o-----+    |      out<> o---------+   +--->o  in1.2<>           | |\n\
| |     out2<> o     |    |     out2<> o             |--->o in2<>              | |\n\
| +------------+     |    +------------+             |    |              out<> o |\n\
|                    |    +--------sub1--------+     |    |             out2<> o |\n\
|                    |    |       Node2        |     |    +--------------------+ |\n\
|                    |    |--------------------|     |                           |\n\
|                    |    % in1<>              |     |                           |\n\
|                    +--->o  in1.0<>           |     |                           |\n\
|                         o in2<>              |     |                           |\n\
|                         |              out<> %     |                           |\n\
|                         |           out.0<>  o-----+                           |\n\
|                         |             out2<> o                                 |\n\
|                         +--------------------+                                 |\n\
+--------------------------------------------------------------------------------+\n\
                                                                                  "
    )


def test_nodes_can_be_added_to_graph(clear_default_graph):
    """Nodes add themselves to their graph as their parent."""
    graph = Graph()
    graph.add_node(NodeForTesting())
    assert 1 == len(graph.nodes)


def test_nodes_can_be_deleted(clear_default_graph, branching_graph):
    """All connections are cleared before the node object is deleted."""
    branching_graph["Start"].outputs["out"]["0"].connect(
        branching_graph["Node2"].inputs["in1"]["0"]
    )
    branching_graph["Start"].outputs["out"]["1"].connect(
        branching_graph["Node2"].inputs["in1"]
    )
    branching_graph["Start"].outputs["out"].connect(
        branching_graph["Node2"].inputs["in1"]["1"]
    )

    branching_graph.delete_node(branching_graph["Node2"])
    assert 3 == len(branching_graph.nodes)

    branching_graph.delete_node(branching_graph["Node1"])
    assert 2 == len(branching_graph.nodes)

    branching_graph.delete_node(branching_graph["Start"])
    assert 1 == len(branching_graph.nodes)

    branching_graph.delete_node(branching_graph["End"])
    assert 0 == len(branching_graph.nodes)


def test_string_representation_with_inputpluggroups(branching_graph):
    InputPlugGroup(
        "in1",
        branching_graph,
        [
            branching_graph["Node1"].inputs["in1"],
            branching_graph["Node2"].inputs["in1"],
        ],
    )
    InputPlugGroup(
        "in2",
        branching_graph,
        [
            branching_graph["Node1"].inputs["in2"],
            branching_graph["Node2"].inputs["in2"],
        ],
    )
    assert (
        str(branching_graph)
        == """\
+------------------------------------------------------------------------+
|                               TestGraph                                |
|------------------------------------------------------------------------|
o in1                                                                    |
| `-Node1.in1                                                            |
| `-Node2.in1                                                            |
o in2                                                                    |
| `-Node1.in2                                                            |
| `-Node2.in2                                                            |
|------------------------------------------------------------------------|
| +------------+          +------------+          +--------------------+ |
| |   Start    |          |   Node1    |          |        End         | |
| |------------|          |------------|          |--------------------| |
| o in1<>      |     +--->o in1<>      |          % in1<>              | |
| o in2<>      |     |    o in2<>      |     +--->o  in1.1<>           | |
| |      out<> o-----+    |      out<> o-----+--->o  in1.2<>           | |
| |     out2<> o     |    |     out2<> o     |    o in2<>              | |
| +------------+     |    +------------+     |    |              out<> o |
|                    |    +------------+     |    |             out2<> o |
|                    |    |   Node2    |     |    +--------------------+ |
|                    |    |------------|     |                           |
|                    +--->o in1<>      |     |                           |
|                         o in2<>      |     |                           |
|                         |      out<> o-----+                           |
|                         |     out2<> o                                 |
|                         +------------+                                 |
+------------------------------------------------------------------------+
                                                                          """
    )
    # return
    assert (
        branching_graph.list_repr()
        == """TestGraph
 [Input Groups]
  [g] in1:
   Node1.in1
   Node2.in1
  [g] in2:
   Node1.in2
   Node2.in2
 Start
  [i] in1: null
  [i] in2: null
  [o] out >> Node1.in1, Node2.in1
  [o] out2: null
 Node1
  [i] in1 << Start.out
  [i] in2: null
  [o] out >> End.in1.1
  [o] out2: null
 Node2
  [i] in1 << Start.out
  [i] in2: null
  [o] out >> End.in1.2
  [o] out2: null
 End
  [i] in1
   [i] in1.1 << Node1.out
   [i] in1.2 << Node2.out
  [i] in2: null
  [o] out: null
  [o] out2: null"""
    )


def test_nested_graphs_expand_sub_graphs(clear_default_graph):
    """Nested Graphs expand all nodes of their sub graphs on evaluation.

    +----G1-----+          +----G2-----+          +----G3-----+          +----G3-----+          +----G2-----+          +----G1-----+
    |    N1     |          |    N3     |          |    N4     |          |    N5     |          |    N6     |          |    N7     |
    |-----------|          |-----------|          |-----------|          |-----------|          |-----------|          |-----------|
    o in_<>     |          o in_<>     |          o in_<>     |          o in_<>     |          o in_<>     |          o in_<>     |
    o in_1<>    |     +--->o in_1<>    |     +--->o in_1<>    |     +--->o in_1<>    |     +--->o in_1<>    |     +--->o in_1<>    |
    o in_2<>    |     |    o in_2<>----|-----|--->o in_2<>    |     +----o-in_2<>----|----------o-in_2<>----|--------->o in_2<>    |
    |       out o-----+----|-------out-o----------|-------out-o-----+    |       out o-----+    |       out o-----+    |       out o
    +-----------+          +-----------+          +-----------+          +-----------+          +-----------+          +-----------+
    +----G2-----+                 |
    |    N2     |                 |
    |-----------|                 |
    o in_<>     |                 |
    o in_1<>    |                 |
    o in_2<>    |                 |
    |       out o-----------------+
    +-----------+
    """

    # G 3
    #
    G3 = Graph(name="G3")
    N5 = FunctionNodeForTesting(name="N5", graph=G3)
    N4 = FunctionNodeForTesting(name="N4", graph=G3)
    N4.inputs["in_1"].promote_to_graph()
    N4.inputs["in_2"].promote_to_graph()
    N5.outputs["out"].promote_to_graph()
    N4.outputs["out"] >> N5.inputs["in_1"]

    # G 2
    #
    G2 = Graph(name="G2")
    N3 = FunctionNodeForTesting(name="N3", graph=G2)
    N2 = FunctionNodeForTesting(name="N2", graph=G2)
    N6 = FunctionNodeForTesting(name="N6", graph=G2)
    N3.inputs["in_1"].promote_to_graph()
    N6.outputs["out"].promote_to_graph()
    N3.outputs["out"] >> G3.inputs["in_1"]
    N2.outputs["out"] >> G3.inputs["in_2"]
    G3.outputs["out"] >> N6.inputs["in_1"]

    # G 1
    #
    G1 = Graph(name="G1")
    N1 = FunctionNodeForTesting(name="N1", graph=G1)
    N7 = FunctionNodeForTesting(name="N7", graph=G1)
    N1.outputs["out"] >> G2.inputs["in_1"]
    G2.outputs["out"] >> N7.inputs["in_1"]
    N1.outputs["out"] >> N7.inputs["in_2"]

    order = [["N1", "N2"], ["N3"], ["N4"], ["N5"], ["N6"], ["N7"]]

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
    new_default = Graph(name="new default")
    set_default_graph(new_default)
    direct = flowpipe.graph.default_graph
    assert direct is new_default

    new_default = "foo"
    with pytest.raises(TypeError):
        set_default_graph(new_default)


def test_reset_default_graph(clear_default_graph):
    new_default = Graph(name="new default")
    set_default_graph(new_default)
    assert get_default_graph().name == "new default"
    reset_default_graph()
    assert get_default_graph().name == "default"


def test_threaded_evaluation():
    """Testing the threaded evaluation by asserting the result value

    Also testing the evaluation time.
    +---------------+          +---------------+
    |   AddNode1    |          |   AddNode2    |
    |---------------|          |---------------|
    o number1<1>    |     +--->o number1<2>    |
    o number2<1>    |     |    o number2<1>    |
    |        result o-----+    |        result o
    +---------------+     |    +---------------+
                          |    +---------------+
                          |    |   AddNode3    |
                          |    |---------------|
                          +--->o number1<2>    |
                               o number2<1>    |
                               |        result o
                               +---------------+
    """
    sleep_time = 0.2
    graph = Graph(name="threaded")

    @Node(outputs=["result"])
    def AddNode(number1, number2):
        time.sleep(sleep_time)
        return {"result": number1 + number2}

    n1 = AddNode(name="AddNode1", graph=graph, number1=1, number2=1)
    n2 = AddNode(name="AddNode2", graph=graph, number2=1)
    n3 = AddNode(name="AddNode3", graph=graph, number2=1)

    n1.outputs["result"] >> n2.inputs["number1"]
    n1.outputs["result"] >> n3.inputs["number1"]

    start = time.time()
    graph.evaluate(mode="threading", max_workers=2)
    end = time.time()

    runtime = end - start

    assert runtime < len(graph.nodes) * sleep_time
    assert n2.outputs["result"].value == 3
    assert n3.outputs["result"].value == 3


def test_valid_evaluation_mode():
    eval_modes = ["linear", "threading", "multiprocessing"]
    for mode in eval_modes:
        Graph().evaluate(mode=mode)


def test_invalid_evaluation_mode():
    with pytest.raises(ValueError):
        Graph().evaluate(mode="foo")


def test_cycle_error_when_node_connects_to_itself():
    """Cycle Error:

        +----------+
        |    N1    |
        |----------|
    +-->o in_<>    |
    |   |      out o--+
    |   +----------+  |
    |                 |
    +-----------------+
    """
    graph = Graph()
    N1 = FunctionNodeForTesting(name="N1", graph=graph)
    with pytest.raises(CycleError):
        N1.outputs["out"] >> N1.inputs["in_"]


def test_cycle_error_when_node_connects_out_to_own_upstream():
    """Cycle Error:

        +----------+          +----------+          +----------+
        |    N1    |          |    N2    |          |    N3    |
        |----------|          |----------|          |----------|
    +-->o in_<>    |     +--->o in_<>    |     +--->o in_<>    |
    |   |      out o-----+    |      out o-----+    |      out o--+
    |   +----------+          +----------+          +----------+  |
    |                                                             |
    +-------------------------------------------------------------+
    """
    graph = Graph()
    N1 = FunctionNodeForTesting(name="N1", graph=graph)
    N2 = FunctionNodeForTesting(name="N2", graph=graph)
    N3 = FunctionNodeForTesting(name="N3", graph=graph)

    N1.outputs["out"] >> N2.inputs["in_"]
    N2.outputs["out"] >> N3.inputs["in_"]

    with pytest.raises(CycleError):
        N3.outputs["out"] >> N1.inputs["in_"]

    with pytest.raises(CycleError):
        N1.inputs["in_"] >> N3.outputs["out"]

    with pytest.raises(CycleError):
        N3.outputs["out"]["a"] >> N1.inputs["in_"]

    with pytest.raises(CycleError):
        N1.inputs["in_"]["a"] >> N3.outputs["out"]

    with pytest.raises(CycleError):
        N3.outputs["out"]["a"] >> N1.inputs["in_"]["a"]

    with pytest.raises(CycleError):
        N1.inputs["in_"]["a"] >> N3.outputs["out"]["a"]


def test_cycle_error_when_node_connects_out_to_own_upstream_across_subgraphs():
    """Cycle Error:

        +---graph1----+          +---graph2----+          +---graph3----+
        |     N1      |          |     N2      |          |     N3      |
        |-------------|          |-------------|          |-------------|
    +-->o in_<>       |     +--->o in_<>       |     +--->o in_<>       |
    |   |         out o-----+    |         out o-----+    |         out o--+
    |   +-------------+          +-------------+          +-------------+  |
    |                                                                      |
    +----------------------------------------------------------------------+

    """
    graph1 = Graph(name="graph1")
    graph2 = Graph(name="graph2")
    graph3 = Graph(name="graph3")
    N1 = FunctionNodeForTesting(name="N1", graph=graph1)
    N2 = FunctionNodeForTesting(name="N2", graph=graph2)
    N3 = FunctionNodeForTesting(name="N3", graph=graph3)

    N1.outputs["out"] >> N2.inputs["in_"]
    N2.outputs["out"] >> N3.inputs["in_"]

    with pytest.raises(CycleError):
        N3.outputs["out"] >> N1.inputs["in_"]

    with pytest.raises(CycleError):
        N1.inputs["in_"] >> N3.outputs["out"]

    with pytest.raises(CycleError):
        N3.outputs["out"]["a"] >> N1.inputs["in_"]

    with pytest.raises(CycleError):
        N1.inputs["in_"]["a"] >> N3.outputs["out"]

    with pytest.raises(CycleError):
        N3.outputs["out"]["a"] >> N1.inputs["in_"]["a"]

    with pytest.raises(CycleError):
        N1.inputs["in_"]["a"] >> N3.outputs["out"]["a"]


def test_clear_plugs_after_use_if_not_data_persistent():
    """
    +--------------------+          +----------+          +-----------------+
    |         N1         |          |    N2    |          |         N3      |
    |--------------------|          |----------|          |-----------------|
    o in2<>              |          o in2<>    |          o in2<>           |
    o in_<{"data": ">    |     +--->o in_<>    |     +--->o in_<>           |
    |                out o-----+    |      out o-----+    |             out o
    +--------------------+          +----------+          +-----------------+
    """

    @Node(outputs=["out"])
    def NodeForTesting(in_, in2):
        return {"out": in_}

    graph = Graph()
    N1 = NodeForTesting(name="N1", graph=graph)
    N2 = NodeForTesting(name="N2", graph=graph)
    N3 = NodeForTesting(name="N3", graph=graph)

    N1.outputs["out"] >> N2.inputs["in_"]
    N2.outputs["out"] >> N3.inputs["in_"]

    data = {"data": "data"}

    N1.inputs["in_"].value = data

    graph.evaluate(data_persistence=False)

    assert N1.inputs["in_"].value == data
    assert N1.outputs["out"].value is None

    assert N2.inputs["in_"].value is None
    assert N2.outputs["out"].value is None

    assert N3.inputs["in_"].value is None
    assert N3.outputs["out"].value == data


def test_passing_evaluator(clear_default_graph, branching_graph):
    """Test that passing an evalutor to graph.evaluate works."""
    graph = Graph(name="test_passing_evaluator")

    @Node(outputs=["result"])
    def AddNode(number1, number2):
        return {"result": number1 + number2}

    n1 = AddNode(name="AddNode1", graph=graph, number1=1, number2=1)
    n2 = AddNode(name="AddNode2", graph=graph, number2=1)
    n3 = AddNode(name="AddNode3", graph=graph, number2=1)

    n1.outputs["result"] >> n2.inputs["number1"]
    n1.outputs["result"] >> n3.inputs["number1"]

    graph.evaluate(mode=None, evaluator=LinearEvaluator())

    assert n2.outputs["result"].value == 3
    assert n3.outputs["result"].value == 3


def test_mode_and_evalutor_are_exclusive(clear_default_graph, branching_graph):
    """Test that passing both mode and evaluator raises an exception."""
    with pytest.raises(ValueError):
        branching_graph.evaluate(mode="linear", evaluator=LinearEvaluator())


def test_evaluate_can_skip_clean_nodes():
    graph = Graph()
    clean_node = FunctionNodeForTesting(name="n1", graph=graph)
    dirty_node = FunctionNodeForTesting(name="n2", graph=graph)
    for plug in clean_node.inputs:
        clean_node.inputs[plug].is_dirty = False
    nodes = Evaluator()._nodes_to_evaluate(graph, skip_clean=True)
    assert len(nodes) == 1
    assert nodes[0] == dirty_node


def test_on_node_event_linear_order(clear_default_graph):
    graph = Graph(name="on_node_event_linear")

    @Node(outputs=["out"])
    def Add(in_):
        return {"out": in_}

    n1 = Add(name="n1", graph=graph, in_=1)
    n2 = Add(name="n2", graph=graph)
    n1.outputs["out"] >> n2.inputs["in_"]

    events: list[tuple[str, str, object | None]] = []

    def on_node_event(node, event, info):
        events.append((node.name, event, info))

    graph.evaluate(mode="linear", on_node_event=on_node_event)

    assert [e[:2] for e in events] == [
        ("n1", "started"),
        ("n1", "finished"),
        ("n2", "started"),
        ("n2", "finished"),
    ]
    assert all(info is None for _, _, info in events)


def test_on_node_event_failed_linear(clear_default_graph):
    graph = Graph(name="on_node_event_failed")

    @Node(outputs=["out"])
    def Fail(in_):
        raise ValueError("boom")

    Fail(name="n1", graph=graph, in_=1)

    events: list[tuple[str, str, object | None]] = []

    def on_node_event(node, event, info):
        events.append((node.name, event, info))

    with pytest.raises(ValueError):
        graph.evaluate(mode="linear", on_node_event=on_node_event)

    assert [e[:2] for e in events] == [("n1", "started"), ("n1", "failed")]
    assert isinstance(events[1][2]["error"], ValueError)


def test_on_node_event_threading(clear_default_graph):
    graph = Graph(name="on_node_event_threading")

    @Node(outputs=["out"])
    def Add(in_):
        return {"out": in_}

    n1 = Add(name="n1", graph=graph, in_=1)
    n2 = Add(name="n2", graph=graph)
    n1.outputs["out"] >> n2.inputs["in_"]

    events: list[tuple[str, str]] = []

    def on_node_event(node, event, info):
        events.append((node.name, event))

    graph.evaluate(
        mode="threading", max_workers=2, on_node_event=on_node_event
    )

    assert ("n1", "started") in events
    assert ("n1", "finished") in events
    assert ("n2", "started") in events
    assert ("n2", "finished") in events


def test_is_dirty_only_gets_updated_if_is_dirty_status_actually_changes(
    clear_default_graph,
):
    graph = Graph(name="test_passing_evaluator")

    @Node(outputs=["result"])
    def AddNode(number1, number2):
        return {"result": number1 + number2}

    with mock.patch.object(
        INode,
        "on_input_plug_set_dirty",
        wraps=INode.on_input_plug_set_dirty,
        autospec=True,
    ) as set_dirty_spy:
        n1 = AddNode(name="AddNode1", graph=graph, number1=1, number2=1)
        n2 = AddNode(name="AddNode2", graph=graph, number2=1)
        n3 = AddNode(name="AddNode3", graph=graph, number2=1)

        n1.outputs["result"] >> n2.inputs["number1"]
        n1.outputs["result"] >> n3.inputs["number1"]

        graph.evaluate(mode=None, evaluator=LinearEvaluator())
        assert set_dirty_spy.call_count == 0
