"""Demonstrating the basic capabilities of flowpipe.

A graph implementation of a world clock for demonstrational purposes:

+------------------+          +---------------------+          +----------------------+
|   CurrentTime    |          |       London        |          |      WorldClock      |
|------------------|          |---------------------|          |----------------------|
|             time o-----+--->o time<>              |          % times                |
+------------------+     |    o timezone<0>         |     +--->o  times.London<>      |
                         |    |      converted_time o-----+--->o  times.Munich<>      |
                         |    +---------------------+     +--->o  times.Vancouver<>   |
                         |    +---------------------+     |    +----------------------+
                         |    |       Munich        |     |
                         |    |---------------------|     |
                         |--->o time<>              |     |
                         |    o timezone<1>         |     |
                         |    |      converted_time o-----|
                         |    +---------------------+     |
                         |    +---------------------+     |
                         |    |      Vancouver      |     |
                         |    |---------------------|     |
                         +--->o time<>              |     |
                              o timezone<-8>        |     |
                              |      converted_time o-----+
                              +---------------------+
"""
from datetime import datetime
import logging
from time import time

from flowpipe import logger
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.node import INode, Node

from flowpipe.graph import Graph


@Node(outputs=['time'])
def CurrentTime():
    """The @Node decorator turns the wrapped function into a Node object.

    Any arguments to the function are used as input plugs to the Node.
    The outputs are defined in the decorator explicitely.
    """
    return {'time': time()}


class ConvertTime(INode):
    """A node can be derived from the INode interface.

    The plugs are defined in the init method.
    The compute method received the inputs from any connected upstream nodes.
    """

    def __init__(self, time=None, timezone=0, **kwargs):
        super(ConvertTime, self).__init__(**kwargs)
        InputPlug('time', self)
        InputPlug('timezone', self, timezone)
        OutputPlug('converted_time', self)

    def compute(self, time, timezone):
        return {
            'converted_time': time + timezone * 60 * 60
        }


@Node()
def ShowTimes(times):
    """Nodes do not necessarily have to define output and input plugs."""
    print('-- World Clock -------------------')
    for location, t in times.items():
        print('It is now: {time:%H:%M} in {location}'.format(
            time=datetime.fromtimestamp(t), location=location))
    print('----------------------------------')


# The Graph holds the nodes
graph = Graph(name='World Clock')
current_time = CurrentTime(graph=graph)
van = ConvertTime(name='Vancouver', timezone=-8, graph=graph)
ldn = ConvertTime(name='London', timezone=0, graph=graph)
muc = ConvertTime(name='Munich', timezone=1, graph=graph)
world_clock = ShowTimes(graph=graph)

# Connecting nodes can be done via the bit shift operator as well
current_time.outputs['time'].connect(van.inputs['time'])
current_time.outputs['time'].connect(ldn.inputs['time'])
current_time.outputs['time'].connect(muc.inputs['time'])
van.outputs['converted_time'] >> world_clock.inputs['times']['Vancouver']
ldn.outputs['converted_time'] >> world_clock.inputs['times']['London']
muc.outputs['converted_time'] >> world_clock.inputs['times']['Munich']

# Display the graph
print(graph)

# Evaluate with debug logs
logger.setLevel(logging.DEBUG)
graph.evaluate()
