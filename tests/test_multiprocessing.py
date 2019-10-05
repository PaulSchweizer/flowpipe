from flowpipe.node import Node
from flowpipe.graph import Graph

import time
import logging

from flowpipe.graph import Graph
from flowpipe.node import Node
from flowpipe import logger


SLEEP_TIME = 3  # A value lower than 1 does not make a difference
                # since starting the different processes eats up time


@Node(outputs=['out'])
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
    delay = .05
    graph = Graph(name='threaded')

    s1 = Sleeper(name='Sleeper1', graph=graph)
    s2 = Sleeper(name='Sleeper2', graph=graph)
    s3 = Sleeper(name='Sleeper3', graph=graph)
    s4 = Sleeper(name='Sleeper4', graph=graph)

    s1.outputs['out'] >> s2.inputs['in1']
    s1.outputs['out'] >> s3.inputs['in1']
    s1.outputs['out'] >> s4.inputs['in1']

    start = time.time()
    graph.evaluate_multiprocessed()
    end = time.time()

    runtime = end - start

    assert runtime < len(graph.nodes) * SLEEP_TIME + len(graph.nodes) * delay


@Node(outputs=['result'])
def AddNode(number1, number2):
    return {'result': number1 + number2}


def test_multiprocessing_evaluation_updates_the_original_graph():
    """Multi processing updates the original graph object.
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
    delay = .05
    graph = Graph(name='multiprocessing')

    n1 = AddNode(name='AddNode1', graph=graph, number1=1, number2=1)
    n2 = AddNode(name='AddNode2', graph=graph, number2=1)
    n3 = AddNode(name='AddNode3', graph=graph, number2=1)

    n1.outputs['result'] >> n2.inputs['number1']
    n1.outputs['result'] >> n3.inputs['number1']

    graph.evaluate_multiprocessed(submission_delay=delay)

    assert n2.outputs['result'].value == 3
    assert n3.outputs['result'].value == 3

    assert not n1.is_dirty
    assert not n2.is_dirty
    assert not n3.is_dirty
