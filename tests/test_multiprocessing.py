import time

from flowpipe.graph import Graph
from flowpipe.node import Node


# A value lower than 1 does not make a difference since starting the different
# processes eats up time
SLEEP_TIME = 3


@Node(outputs=["out"])
def Sleeper(in1):
    time.sleep(SLEEP_TIME)


def test_multiprocessed_evaluation_is_faster():
    """Test by having sleeper nodes sleep in parallel and check total grah timing.
    +---------------+          +---------------+
    |   Sleeper1    |          |   Sleeper2    |
    |---------------|          |---------------|
    o in1<>         |     +--->o in1<>         |
    |           out o-----+    |           out o
    +---------------+     |    +---------------+
                          |    +---------------+
                          |    |   Sleeper3    |
                          |    |---------------|
                          +--->o in1<>         |
                          |    |           out o
                          |    +---------------+
                          |    +---------------+
                          |    |   Sleeper4    |
                          |    |---------------|
                          +--->o in1<>         |
                               |           out o
                               +---------------+
    """
    delay = 0.05
    graph = Graph(name="threaded")

    s1 = Sleeper(name="Sleeper1", graph=graph)
    s2 = Sleeper(name="Sleeper2", graph=graph)
    s3 = Sleeper(name="Sleeper3", graph=graph)
    s4 = Sleeper(name="Sleeper4", graph=graph)

    s1.outputs["out"] >> s2.inputs["in1"]
    s1.outputs["out"] >> s3.inputs["in1"]
    s1.outputs["out"] >> s4.inputs["in1"]

    start = time.time()
    graph.evaluate(mode="multiprocessing")
    end = time.time()

    runtime = end - start

    assert runtime < len(graph.nodes) * SLEEP_TIME + len(graph.nodes) * delay


@Node(outputs=["result", "results"])
def AddNode(number1, number2, numbers):
    """'numbers' and 'results' are used as compound plug."""
    result = {"result": number1 + number2}
    if numbers is not None:
        for i, _ in enumerate(numbers.keys()):
            result["results.{0}".format(i)] = i
    return result


def test_multiprocessing_evaluation_updates_the_original_graph():
    """Multi processing updates the original graph object.

    +---------------+          +---------------+                   +------------------------+
    |   AddNode1    |          |   AddNode2    |                   |        AddNode5        |
    |---------------|          |---------------|                   |------------------------|
    o number1<1>    |     +--->o number1<2>    |                   o number1<1>             |
    o number2<1>    |     |    o number2<1>    |                   o number2<1>             |
    o numbers<>     |     |    o numbers<>     |              +--->% numbers                |
    |        result o-----+    |        result o              |--->o  numbers.0<>           |
    |       results o     |    |       results o              |--->o  numbers.1<>           |
    +---------------+     |    +---------------+              |    |                 result o
                          |    +---------------+              |    |                results o
                          |    |   AddNode3    |              |    +------------------------+
                          |    |---------------|              |
                          +--->o number1<2>    |              |
                          |    o number2<1>    |              |
                          |    o numbers<>     |              |
                          |    |        result o              |
                          |    |       results o              |
                          |    +---------------+              |
                          |    +------------------------+     |
                          |    |        AddNode4        |     |
                          |    |------------------------|     |
                          +--->o number1<2>             |     |
                          |    o number2<1>             |     |
                          |    % numbers                |     |
                          +--->o  numbers.0<2>          |     |
                          +--->o  numbers.1<2>          |     |
                               |                 result o     |
                               |                results %-----+
                               |             results.0  o-----+
                               |             results.1  o-----+
                               +------------------------+
    """
    graph = Graph(name="multiprocessing")

    n1 = AddNode(name="AddNode1", graph=graph, number1=1, number2=1)
    n2 = AddNode(name="AddNode2", graph=graph, number2=1)
    n3 = AddNode(name="AddNode3", graph=graph, number2=1)
    n4 = AddNode(name="AddNode4", graph=graph, number2=1)
    n5 = AddNode(name="AddNode5", graph=graph, number1=1, number2=1)

    n1.outputs["result"] >> n2.inputs["number1"]
    n1.outputs["result"] >> n3.inputs["number1"]

    n1.outputs["result"] >> n4.inputs["number1"]
    n1.outputs["result"] >> n4.inputs["numbers"]["0"]
    n1.outputs["result"] >> n4.inputs["numbers"]["1"]

    n4.outputs["results"]["0"] >> n5.inputs["numbers"]["0"]
    n4.outputs["results"]["1"] >> n5.inputs["numbers"]["1"]

    n4.outputs["results"] >> n5.inputs["numbers"]

    graph.evaluate(mode="multiprocessing", submission_delay=0.05)

    assert n2.outputs["result"].value == 3
    assert n3.outputs["result"].value == 3

    assert n4.outputs["results"].value == {"0": 0, "1": 1}
    assert n5.outputs["results"].value == {"0": 0, "1": 1}

    assert not n1.is_dirty
    assert not n2.is_dirty
    assert not n3.is_dirty
    assert not n4.is_dirty
    assert not n5.is_dirty
