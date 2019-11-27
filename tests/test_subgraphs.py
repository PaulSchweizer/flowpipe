import pytest

from flowpipe import Graph
from flowpipe import Node


@Node(outputs=["out"])
def DemoNode(in_):
    return {"out": in_}


def _nested_graph():
    """Create this nested subgraph:
    +---------------+          +---------------+          +---------------+          +---------------+
    |   DemoNode    |          |   DemoNode    |          |   DemoNode    |          |   DemoNode    |
    |---------------|          |---------------|          |---------------|          |---------------|
    o in_<>         |     +--->o in_<>         |     +--->o in_<>         |     +--->o in_<>         |
    |           out o-----+    |           out o-----+    |           out o-----+    |           out o
    +---------------+          +---------------+          +---------------+          +---------------+
    +-------------+
    |   sub0-2    |
    |-------------|
    o in_<>       |
    |         out o
    +-------------+
    +-------------+
    |   sub1-2    |
    |-------------|
    o in_<>       |
    |         out o
    +-------------+
    +-------------+
    |   sub2-2    |
    |-------------|
    o in_<>       |
    |         out o
    +-------------+
    """
    main = Graph("main")
    DemoNode(graph=main)

    parent = main
    for i in range(3):
        sub = Graph("sub" + str(i))
        DemoNode(graph=sub)
        DemoNode(graph=sub, name="sub" + str(i) + "-2")
        parent["DemoNode"].outputs["out"] >> sub["DemoNode"].inputs["in_"]
        parent = sub
    return main


def test_nodes_only_contains_levels_of_graph():
    graph = _nested_graph()
    assert len(graph.nodes) == 1


def test_subgraph_names_need_to_be_unique():
    """
    +--------------------+          +--------------------+
    |       node1        |          |       node1        |
    |--------------------|          |--------------------|
    o in_<>              |     +--->o in_<{"a": null>    |
    |                out %-----+    |                out o
    |             out.a  o     |    +--------------------+
    +--------------------+     |    +--------------------+
    +------------+             |    |       node2        |
    |   node2    |             |    |--------------------|
    |------------|             +--->o in_<{"a": null>    |
    o in_<>      |                  |                out o
    |        out o                  +--------------------+
    +------------+
    """
    main = Graph("main")
    DemoNode(name="node1", graph=main)
    DemoNode(name="node2", graph=main)

    sub1 = Graph("sub")
    DemoNode(name="node1", graph=sub1)
    DemoNode(name="node2", graph=sub1)

    sub2 = Graph("sub")
    DemoNode(name="node1", graph=sub2)
    DemoNode(name="node2", graph=sub2)

    main["node1"].outputs["out"] >> sub1["node1"].inputs["in_"]
    with pytest.raises(ValueError):
        main["node1"].outputs["out"] >> sub2["node1"].inputs["in_"]

    with pytest.raises(ValueError):
        main["node1"].outputs["out"]["a"] >> sub2["node1"].inputs["in_"]

    with pytest.raises(ValueError):
        main["node1"].outputs["out"]["a"] >> sub2["node1"].inputs["in_"]["a"]

    with pytest.raises(ValueError):
        main["node1"].outputs["out"] >> sub2["node1"].inputs["in_"]["a"]

    # Connecting to the same graph does not throw an error
    #
    main["node1"].outputs["out"] >> sub1["node2"].inputs["in_"]


def test_subgraphs_can_be_accessed_by_name():
    graph = _nested_graph()

    assert len(graph.subgraphs) == 3
    assert graph.subgraphs['sub0'].name == 'sub0'
    assert graph.subgraphs['sub1'].name == 'sub1'
    assert graph.subgraphs['sub2'].name == 'sub2'


def test_plugs_can_be_promoted_to_graph_level_under_new_name():
    main = Graph("main")
    DemoNode(name="node1", graph=main)

    main["node1"].inputs["in_"].promote_to_graph()
    main["node1"].outputs["out"].promote_to_graph(name="graph_out")

    assert main.inputs["in_"] is main["node1"].inputs["in_"]
    assert main.outputs["graph_out"] is main["node1"].outputs["out"]


def test_plugs_can_only_be_promoted_once_to_graph_level():
    main = Graph("main")
    DemoNode(name="node1", graph=main)

    main["node1"].inputs["in_"].promote_to_graph()
    main["node1"].outputs["out"].promote_to_graph()

    with pytest.raises(ValueError):
        main["node1"].inputs["in_"].promote_to_graph(name="different_name")
    with pytest.raises(ValueError):
        main["node1"].outputs["out"].promote_to_graph(name="different_name")


def test_subplugs_can_not_be_promoted_individually():
    main = Graph("main")
    DemoNode(name="node1", graph=main)

    with pytest.raises(TypeError):
        main["node1"].inputs["in_"]["sub"].promote_to_graph()
    with pytest.raises(TypeError):
        main["node1"].outputs["out"]["sub"].promote_to_graph()

    # Promoting the main plug will of course give access to subplugs as well
    main["node1"].inputs["in_"].promote_to_graph()
    assert main.inputs["in_"]["sub"] == main["node1"].inputs["in_"]["sub"]


def test_serialize_nested_graph_to_json():
    graph = _nested_graph()

    serialized = graph.to_json()
    deserialized = Graph.from_json(serialized).to_json()

    assert serialized == deserialized
