import pytest
from flowpipe import Graph, InputPlugGroup, Node


@Node(outputs=["out"])
def DemoNode(in_):
    """
    +-----------+
    | DemoNode  |
    |-----------|
    o in_<>     |
    |     out<> o
    +-----------+
    """
    return {"out": in_}


@pytest.fixture
def demo_graph_fixture():
    """
    +---main----+          +---sub----+
    |     A     |          |    C1    |
    |-----------|          |----------|
    o in_<>     |     +--->o in_<>    |
    |     out<> o-----+    |    out<> o
    +-----------+     |    +----------+
                      |    +---sub----+
                      |    |    C2    |
                      |    |----------|
                      +--->o in_<>    |
                           |    out<> o
                           +----------+
    """
    # Sub graph
    sub = Graph("sub")
    c1 = DemoNode(graph=sub, name="C1")
    c2 = DemoNode(graph=sub, name="C2")

    # Main graph
    main = Graph("main")
    DemoNode(graph=main, name="A")

    # Group inputs in the sub graph
    InputPlugGroup("graph_in", sub, [
        c1.inputs["in_"],
        c2.inputs["in_"],
    ])
    return sub, main


def test_connect_groupinput_to_output(demo_graph_fixture):
    sub, main = demo_graph_fixture
    sub.input_groups["graph_in"].connect(main["A"].outputs["out"])

    assert main["A"].outputs["out"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] in sub["C2"].inputs["in_"].connections

    sub.input_groups["graph_in"].disconnect(main["A"].outputs["out"])

    assert main["A"].outputs["out"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] not in sub["C2"].inputs["in_"].connections


def test_connect_output_to_groupinput(demo_graph_fixture):
    sub, main = demo_graph_fixture
    main["A"].outputs["out"].connect(sub.input_groups["graph_in"])

    assert main["A"].outputs["out"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] in sub["C2"].inputs["in_"].connections

    main["A"].outputs["out"].disconnect(sub.input_groups["graph_in"])

    assert main["A"].outputs["out"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] not in sub["C2"].inputs["in_"].connections


def test_rshift_connect_groupinput_to_output(demo_graph_fixture):
    sub, main = demo_graph_fixture
    sub.input_groups["graph_in"] >> main["A"].outputs["out"]

    assert main["A"].outputs["out"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] in sub["C2"].inputs["in_"].connections

    sub.input_groups["graph_in"] << main["A"].outputs["out"]

    assert main["A"].outputs["out"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] not in sub["C2"].inputs["in_"].connections


def test_rshift_connect_output_to_groupinput(demo_graph_fixture):
    sub, main = demo_graph_fixture
    main["A"].outputs["out"] >> sub.input_groups["graph_in"]

    assert main["A"].outputs["out"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] in sub["C2"].inputs["in_"].connections

    main["A"].outputs["out"] << sub.input_groups["graph_in"]

    assert main["A"].outputs["out"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"] not in sub["C2"].inputs["in_"].connections


def test_connect_groupinput_to_suboutput(demo_graph_fixture):
    sub, main = demo_graph_fixture
    sub.input_groups["graph_in"].connect(main["A"].outputs["out"]["1"])

    assert main["A"].outputs["out"]["1"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"]["1"] in sub["C2"].inputs["in_"].connections

    sub.input_groups["graph_in"].disconnect(main["A"].outputs["out"]["1"])

    assert main["A"].outputs["out"]["1"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"]["1"] not in sub["C2"].inputs["in_"].connections


def test_connect_suboutput_to_groupinput(demo_graph_fixture):
    sub, main = demo_graph_fixture
    main["A"].outputs["out"]["1"].connect(sub.input_groups["graph_in"])

    assert main["A"].outputs["out"]["1"] in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"]["1"] in sub["C2"].inputs["in_"].connections

    main["A"].outputs["out"]["1"].disconnect(sub.input_groups["graph_in"])

    assert main["A"].outputs["out"]["1"] not in sub["C1"].inputs["in_"].connections
    assert main["A"].outputs["out"]["1"] not in sub["C2"].inputs["in_"].connections
