from flowpipe.node import Node
from flowpipe.graph import Graph


@Node(outputs=['result'])
def AddNode(number1, number2):
    return {'result': number1 + number2}


def test_multiprocessing_evaluation():
    """Testing the multi processing evaluation by asserting the result value.
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
