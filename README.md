
[![Version](https://img.shields.io/pypi/v/flowpipe.svg)](https://pypi.org/project/flowpipe/)
[![Build Status](https://travis-ci.org/PaulSchweizer/flowpipe.svg?branch=master)](https://travis-ci.org/PaulSchweizer/flowpipe)
[![Codacy_Badge_Grade](https://api.codacy.com/project/badge/Grade/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PaulSchweizer/flowpipe&amp;utm_campaign=Badge_Grade)
[![Codacy_Badge_Coverage](https://api.codacy.com/project/badge/Coverage/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&utm_medium=referral&utm_content=PaulSchweizer/flowpipe&utm_campaign=Badge_Coverage) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![python 2.7](https://img.shields.io/badge/python-2.7%2B-blue.svg)](https://www.python.org/downloads/) [![python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)


# Flow-based Programming
A lightweight framework for flow-based programming in python.

```
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

# Quick Example

Consider this simple example on how to represent the construction of a house with Flowpipe:

```python
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.node import INode, Node
from flowpipe.graph import Graph


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

```
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
graph.evaluate(threaded=True)  # The default graph evaluation is not threaded
```

Output:

```
4 workers are hired to build the house.
Michelle, Mike are building the roof
Jane, John are building the walls
Mike, John, Michelle, Jane and Homeowner are having a great party!
```

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

```
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

Using the command pattern with flowpipe successfully:
[workflow_design_pattern.py](examples/workflow_design_pattern.py)!

Use flowpipe on a remote cluster of machines, commonly refered to as a "render farm" in the VFX/Animation industry:
[vfx_render_farm_conversion.py](examples/vfx_render_farm_conversion.py)!

An example graph showcasing a common workflow encountered in the VFX/Animation industry:
[vfx_rendering.py](examples/vfx_rendering.py)!

## VFX Pipeline

If you are working in the VFX/Animation industry, please check out this extensive guide on how to use [flowpipe in a vfx pipeline](flowpipe-for-vfx-pipelines.md)!
