from datetime import datetime
import logging
from time import time

from flowpipe import logger
from flowpipe.node import INode, function_to_node
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph


@function_to_node(outputs=['time'])
def CurrentTime():
    return {'time': time()}


class ConvertTime(INode):

    def __init__(self, time=None, timezone=0, city=None):
        super(ConvertTime, self).__init__()
        InputPlug('time', self)
        InputPlug('timezone', self, timezone)
        InputPlug('city', self, city)
        OutputPlug('converted_time', self)

    def compute(self, time, timezone, city):
        return {'converted_time': [time + timezone * 60 * 60, city]}


@function_to_node()
def WorldClock(time1, time2, time3):
    print('-- World Clock -------------------')
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time1[0]).strftime("%H:%M"), time1[1]))
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time2[0]).strftime("%H:%M"), time2[1]))
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time3[0]).strftime("%H:%M"), time3[1]))
    print('----------------------------------')


def test_a():
    """@todo documentation for test_a."""
    logger.setLevel(logging.DEBUG)

    current_time = CurrentTime()
    van = ConvertTime(city='Vancouver', timezone=-8)
    ldn = ConvertTime(city='London', timezone=0)
    muc = ConvertTime(city='Munich', timezone=1)
    world_clock = WorldClock()


    current_time.outputs['time'] >> van.inputs['time']
    current_time.outputs['time'] >> ldn.inputs['time']
    current_time.outputs['time'] >> muc.inputs['time']
    van.outputs['converted_time'] >> world_clock.inputs['time1']
    ldn.outputs['converted_time'] >> world_clock.inputs['time2']
    muc.outputs['converted_time'] >> world_clock.inputs['time3']

    graph = Graph(name="WorldClockGraph", nodes=[current_time, van, ldn, muc, world_clock])

    # print(graph)

    graph.evaluate()
