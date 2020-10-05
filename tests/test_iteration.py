from __future__ import print_function

import pytest
import random

from flowpipe.node import Node
from flowpipe.plug import IterationList
from flowpipe.graph import Graph

@Node(outputs=['out'])
def foo(n_values = None):
    n_values = random.randint(1, 10) if n_values is None else n_values
    return {'out': IterationList([i for i in range(n_values)])}

@Node(outputs=['value'])
def baz(value):
    if hasattr(value, '__iter__'):
        return {'value': sum(value)}
    else:
        return {'value': value}


def test_iteration_random_count():
    graph = Graph(name='Iteration concept')
    node_foo = foo(graph=graph, name='Creating random number of values')

    graph.evaluate()
    assert isinstance(node_foo.outputs['out'].value, IterationList), "Output of foo is not an iteration plug"
    
def test_iteration_10_count():
    graph = Graph(name='Iteration concept')
    node_foo = foo(graph=graph, name='Creating random number of values', n_values=10)
    node_baz = baz(graph=graph, name='Passing the values', iteration_count=10)

    node_foo.outputs['out'] >> node_baz.inputs['value']

    graph.evaluate()
    assert isinstance(node_baz.outputs['value'].value, IterationList), "Output of baz is not an iteration plug"
    
    assert node_baz.outputs['value'].value == IterationList([i for i in range(10)]), "Baz did not pass the values properly"

def test_disable_iteration():
    graph = Graph(name='Iteration concept')
    node_foo = foo(graph=graph, name='Creating random number of values', n_values=10)
    node_baz = baz(graph=graph, name='Passing the values', iteration_count=-1)

    node_foo.outputs['out'] >> node_baz.inputs['value']

    graph.evaluate()
    assert isinstance(node_baz.outputs['value'].value, int), "Output of baz is not an integer"
    
    assert node_baz.outputs['value'].value == 45

def test_invalid_iteration_count():
    graph = Graph(name='Iteration concept')
    node_foo = foo(graph=graph, name='Creating random number of values', n_values=8)
    node_baz = baz(graph=graph, name='Passing the values', iteration_count=10)

    node_foo.outputs['out'] >> node_baz.inputs['value']

    with pytest.raises(ValueError):
        graph.evaluate()

def test_invalid_iteration_count_value():
    graph = Graph(name='Iteration concept')
    with pytest.raises(ValueError):
        node_foo = foo(graph=graph, name='Creating random number of values', n_values=10, iteration_count=-2)
    
if __name__ == "__main__":
    pytest.main()