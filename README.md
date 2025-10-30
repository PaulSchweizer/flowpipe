[![Version](https://img.shields.io/pypi/v/flowpipe.svg)](https://pypi.org/project/flowpipe/)

<!-- Pytest Coverage Comment:Begin -->
<a href="https://github.com/thtom/flowpipe/blob/main/README.md"><img alt="Coverage" src="https://img.shields.io/badge/Coverage-98%25-brightgreen.svg" /></a><details><summary>Coverage Report </summary><table><tr><th>File</th><th>Stmts</th><th>Miss</th><th>Cover</th><th>Missing</th></tr><tbody><tr><td colspan="5"><b>flowpipe</b></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/__init__.py">__init__.py</a></td><td>4</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/errors.py">errors.py</a></td><td>2</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/evaluator.py">evaluator.py</a></td><td>109</td><td>21</td><td>81%</td><td><a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/evaluator.py#L187-L188">187&ndash;188</a>, <a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/evaluator.py#L224-L253">224&ndash;253</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/event.py">event.py</a></td><td>22</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/graph.py">graph.py</a></td><td>211</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/node.py">node.py</a></td><td>355</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/plug.py">plug.py</a></td><td>208</td><td>2</td><td>99%</td><td><a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/plug.py#L62-L67">62&ndash;67</a></td></tr><tr><td>&nbsp; &nbsp;<a href="https://github.com/thtom/flowpipe/blob/main/flowpipe/utilities.py">utilities.py</a></td><td>71</td><td>0</td><td>100%</td><td>&nbsp;</td></tr><tr><td><b>TOTAL</b></td><td><b>982</b></td><td><b>23</b></td><td><b>98%</b></td><td>&nbsp;</td></tr></tbody></table></details>
<!-- Pytest Coverage Comment:End -->

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flowpipe) [![Documentation Status](https://readthedocs.org/projects/flowpipe/badge/?version=latest)](https://flowpipe.readthedocs.io/en/latest) [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![Flowpipe Logo](https://raw.githubusercontent.com/PaulSchweizer/flowpipe/master/logo.png)

# Flow-based Programming

A lightweight framework for flow-based programming in python.

```c
+-------------------+          +---------------------+
|   Invite People   |          |   Birthday Party    |
|-------------------|          |---------------------|
o amount<4>         |   +----->o attendees<>         |
|            people o---+ +--->o cake<>              |
+-------------------+     |    +---------------------+
                          |
+-------------------+     |
|    Bake a cake    |     |
+-------------------+     |
o type<"Chocolate"> |     |
|              cake o-----+
+-------------------+
```

Benefits:

- Visualize code
- Re-usability
- Streamlined code design
- Built-in concurrency
- Represent workflows one to one in the code

[![Flowpipe - VFX Production Proven Flow-based Programming](http://img.youtube.com/vi/pbroOzT42F8/0.jpg)](http://www.youtube.com/watch?v=pbroOzT42F8 "Flowpipe - VFX Production Proven Flow-based Programming")
<br>
Flowpipe Presentation Open Source Days 2025

# Quick Example

Consider this simple example on how to represent the construction of a house with Flowpipe:

```python
from flowpipe import Graph, INode, Node, InputPlug, OutputPlug


class HireWorkers(INode):
    """A node can be derived from the INode interface.

    The plugs are defined in the init method.
    The compute method received the inputs from any connected upstream nodes.
    """

    def __init__(self, amount=None, **kwargs):
        super(HireWorkers, self).__init__(**kwargs)
        InputPlug('amount', self, amount)
        OutputPlug('workers', self)

    def compute(self, amount):
        workers = ['John', 'Jane', 'Mike', 'Michelle']
        print('{0} workers are hired to build the house.'.format(amount))
        return {'workers.{0}'.format(i): workers[i] for i in range(amount)}


@Node(outputs=['workers'])
def Build(workers, section):
    """A node can also be created by the Node decorator.outputs

    The inputs to the function are turned into InputsPlugs, otuputs are defined
    in the decorator itself. The wrapped function is used as the compute method.
    """
    print('{0} are building the {1}'.format(', '.join(workers.values()), section))
    return {'workers.{0}'.format(i): worker for i, worker in workers.items()}


@Node()
def Party(attendees):
    print('{0} and {1} are having a great party!'.format(
        ', '.join(list(attendees.values())[:-1]), list(attendees.values())[-1]))


# Create a graph with the necessary nodes
graph = Graph(name='How to build a house')
workers = HireWorkers(graph=graph, amount=4)
build_walls = Build(graph=graph, name='Build Walls', section='walls')
build_roof = Build(graph=graph, name='Build Roof', section='roof')
party = Party(graph=graph, name='Housewarming Party')

# Wire up the connections between the nodes
workers.outputs['workers']['0'].connect(build_walls.inputs['workers']['0'])
workers.outputs['workers']['1'].connect(build_walls.inputs['workers']['1'])
workers.outputs['workers']['2'].connect(build_roof.inputs['workers']['0'])
workers.outputs['workers']['3'].connect(build_roof.inputs['workers']['1'])
build_walls.outputs['workers']['0'] >> party.inputs['attendees']['0']
build_walls.outputs['workers']['1'] >> party.inputs['attendees']['2']
build_roof.outputs['workers']['0'] >> party.inputs['attendees']['1']
build_roof.outputs['workers']['1'] >> party.inputs['attendees']['3']
party.inputs['attendees']['4'].value = 'Homeowner'
```

Visualize the code as a graph or as a listing:

```python
print(graph.name)
print(graph)
print(graph.list_repr())
```

Output:

```c
How to build a house
+------------------------+          +------------------------+          +---------------------------+
|      HireWorkers       |          |       Build Roof       |          |    Housewarming Party     |
|------------------------|          |------------------------|          |---------------------------|
o amount<4>              |          o section<"roof">        |          % attendees                 |
|                workers %          % workers                |     +--->o  attendees.0<>            |
|             workers.0  o-----+--->o  workers.0<>           |     |--->o  attendees.1<>            |
|             workers.1  o-----|--->o  workers.1<>           |     |--->o  attendees.2<>            |
|             workers.2  o-----|    |                workers %     |--->o  attendees.3<>            |
|             workers.3  o-----|    |             workers.0  o-----|    o  attendees.4<"Homeowner>  |
+------------------------+     |    |             workers.1  o-----|    +---------------------------+
                               |    +------------------------+     |
                               |    +------------------------+     |
                               |    |      Build Walls       |     |
                               |    |------------------------|     |
                               |    o section<"walls">       |     |
                               |    % workers                |     |
                               +--->o  workers.0<>           |     |
                               +--->o  workers.1<>           |     |
                                    |                workers %     |
                                    |             workers.0  o-----+
                                    |             workers.1  o-----+
                                    +------------------------+

Build a House
 HireWorkers
  [i] amount: 4
  [o] workers
   [o] workers.0 >> Build Walls.workers.0
   [o] workers.1 >> Build Walls.workers.1
   [o] workers.2 >> Build Roof.workers.0
   [o] workers.3 >> Build Roof.workers.1
 Build Roof
  [i] section: "roof"
  [i] workers
   [i] workers.0 << HireWorkers.workers.2
   [i] workers.1 << HireWorkers.workers.3
  [o] workers
   [o] workers.0 >> Housewarming Party.attendees.1
   [o] workers.1 >> Housewarming Party.attendees.3
 Build Walls
  [i] section: "walls"
  [i] workers
   [i] workers.0 << HireWorkers.workers.0
   [i] workers.1 << HireWorkers.workers.1
  [o] workers
   [o] workers.0 >> Housewarming Party.attendees.0
   [o] workers.1 >> Housewarming Party.attendees.2
 Housewarming Party
  [i] attendees
   [i] attendees.0 << Build Walls.workers.0
   [i] attendees.1 << Build Roof.workers.0
   [i] attendees.2 << Build Walls.workers.1
   [i] attendees.3 << Build Roof.workers.1
   [i] attendees.4: "Homeowner"
```

Now build the house:

```python
graph.evaluate(mode='threading')  # Options are linear, threading and multiprocessing
```

Output:

```c
4 workers are hired to build the house.
Michelle, Mike are building the roof
Jane, John are building the walls
Mike, John, Michelle, Jane and Homeowner are having a great party!
```

(Note: for more elaborate evaluation schemes, see [Evaluators](#evaluators))

We now know how to throw a party, so let's invite some people and re-use these skills for a birthday:

```python
graph = Graph(name='How to throw a birthday party')

@Node(outputs=['people'])
def InvitePeople(amount):
    people = ['John', 'Jane', 'Mike', 'Michelle']
    d = {'people.{0}'.format(i): people[i] for i in range(amount)}
    d['people'] = {people[i]: people[i] for i in range(amount)}
    return d

invite = InvitePeople(graph=graph, amount=4)
birthday_party = Party(graph=graph, name='Birthday Party')
invite.outputs['people'] >> birthday_party.inputs['attendees']

print(graph.name)
print(graph)
graph.evaluate()
```

Output:

```c
How to throw a birthday party
+-------------------+          +---------------------+
|   InvitePeople    |          |   Birthday Party    |
|-------------------|          |---------------------|
o amount<4>         |     +--->o attendees<>         |
|            people o-----+    +---------------------+
+-------------------+

Jane, Michelle, Mike and John are having a great party!
```

## More Examples

There are more examples for common use cases of flowpipe:

The code for these examples:
[house_and_birthday.py](examples/house_and_birthday.py)!

Another simple example:
[world_clock.py](examples/world_clock.py)!

How to make use of nested subgraphs:
[nested_graphs.py](examples/nested_graphs.py)!

Using the command pattern with flowpipe successfully:
[workflow_design_pattern.py](examples/workflow_design_pattern.py)!

Use flowpipe on a remote cluster of machines, commonly refered to as a "render farm" in the VFX/Animation industry:
[vfx_render_farm_conversion.py](examples/vfx_render_farm_conversion.py)!

An example graph showcasing a common workflow encountered in the VFX/Animation industry:
[vfx_rendering.py](examples/vfx_rendering.py)!

An example graph showcasing how to use plugs on graph level.
[graph_plugs.py](examples/graph_plugs.py)!

An example showing how to create your own custom evaluator for flowpipe graphs.
[custom_evaluator.py](examples/custom_evaluator.py)!

## VFX Pipeline

If you are working in the VFX/Animation industry, please check out this extensive guide on how to use [flowpipe in a vfx pipeline](flowpipe-for-vfx-pipelines.md)!

# Evaluators

If your nodes just need sequential, threaded or multiprocessing evaluation, the `Graph.evaluate()` method will serve you just fine. If you want to take more control over the way your Graph is being evaluated, `Evaluators` are for you. This can also be used to add, e.g. logging or tracing to node evaluation.

Evaluators allow you to take control of node evaluation order, or their scheduling.
See `flowpipe/evaluator.py` to see the `Graph.evaluate()` method's evaluation schemes.

To use a custom evaluator, subclass `flowpipe.evaluator.Evaluator`, and provide at least an `_evaluate_nodes(self, nodes)` method.
This method should take a list of nodes and call their respective `node.evalaute()` methods (along with any other task you want to do for each node being evaluated).
To use a cusom evaluator, create it and call its `Evalator.evaluate()` method with the Graph to evaluate as an argument:

```py
from flowpipe.evaluators import LinearEvaluator

# assuming you created a graph to evaluate above, called `graph`
lin_eval = LinearEvaluator()
lin_eval.evaluate(graph)
```
# Reference Projects

[flowpipe-editor](https://github.com/jonassorgenfrei/flowpipe-editor) a Qt based visualizer for flowpipe graphs

[flowpipe-celery-adapter](https://github.com/PaulSchweizer/flowpipe-celery-adapter) Easily evaluate Flowpipe Graphs in Celery
