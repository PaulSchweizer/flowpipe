
[![Version](https://img.shields.io/pypi/v/flowpipe.svg)](https://pypi.org/project/flowpipe/)
[![Build Status](https://travis-ci.org/PaulSchweizer/flowpipe.svg?branch=master)](https://travis-ci.org/PaulSchweizer/flowpipe)
[![Codacy_Badge_Grade](https://api.codacy.com/project/badge/Grade/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PaulSchweizer/flowpipe&amp;utm_campaign=Badge_Grade)
[![Codacy_Badge_Coverage](https://api.codacy.com/project/badge/Coverage/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&utm_medium=referral&utm_content=PaulSchweizer/flowpipe&utm_campaign=Badge_Coverage)


# Flow-based Pipeline
A lightweight framework for flow-based programming in python.

## Install

```
pip install flowpipe
```

## Example: Implement a world clock with Flowpipe

This is very simple and in the end it is just a one liner in python, but a simple example makes it easier to demonstrate the idea behind flowpipe.

Let's import the necessary classes:

```python
from datetime import datetime
import logging
from time import time

from flowpipe import logger
from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug
from flowpipe.graph import Graph
```

Then the desired functionality has to be implemented into Nodes. We need two nodes, one to get the current time and one to convert it to a timezone.

```python
@Node(outputs=['time'])
def CurrentTime():
    return {'time': time()}
```

The above Node is created via the shortcut decorator.

For more complex Nodes, the INode interface can be implemented directly.

```python
class ConvertTime(INode):

    def __init__(self, time=None, timezone=0, city=None, **kwargs):
        super(ConvertTime, self).__init__(**kwargs)
        InputPlug('time', self)
        InputPlug('timezone', self, timezone)
        InputPlug('city', self, city)
        OutputPlug('converted_time', self)

    def compute(self, time, timezone, city):
        return {'converted_time': [time + timezone * 60 * 60, city]}
```

The World Clock will receive the times and locations and display it.

```python
@Node()
def WorldClock(time1, time2, time3):
    print('-- World Clock -------------------')
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time1[0]).strftime("%H:%M"), time1[1]))
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time2[0]).strftime("%H:%M"), time2[1]))
    print('It is now {0} in {1}'.format(
        datetime.fromtimestamp(time3[0]).strftime("%H:%M"), time3[1]))
    print('----------------------------------')
```

Now we can create the Graph that represents the world clock:

```python
graph = Graph(name="WorldClockGraph")
```

Now we create all the necessary Nodes:

```python
current_time = CurrentTime(graph=graph)
van = ConvertTime(city='Vancouver', timezone=-8, graph=graph)
ldn = ConvertTime(city='London', timezone=0, graph=graph)
muc = ConvertTime(city='Munich', timezone=1, graph=graph)
world_clock = WorldClock(graph=graph)
```

By specifying the "graph" attribute on the Nodes get added to the Graph automatically.

The Nodes can now be wired together. The bitshift operator is used as a shorthand to connect the plugs.

```python

current_time.outputs['time'] >> van.inputs['time']
current_time.outputs['time'] >> ldn.inputs['time']
current_time.outputs['time'] >> muc.inputs['time']
van.outputs['converted_time'] >> world_clock.inputs['time1']
ldn.outputs['converted_time'] >> world_clock.inputs['time2']
muc.outputs['converted_time'] >> world_clock.inputs['time3']
```

The Graph can be visualized.

```python
print(graph)
```

```
 0 | +----------------+          +-------------------+          +---------------+
 1 | |  CurrentTime   |          |    ConvertTime    |          |  WorldClock   |
 2 | |----------------|          |-------------------|          |---------------|
 3 | |           time o-----+    o city<"Vancouver>  |     +--->o time1<>       |
 4 | +----------------+     +--->o time<>            |     |--->o time2<>       |
 5 |                        |    o timezone<-8>      |     |--->o time3<>       |
 6 |                        |    |    converted_time o-----+    +---------------+
 7 |                        |    +-------------------+     |
 8 |                        |    +-------------------+     |
 9 |                        |    |    ConvertTime    |     |
10 |                        |    |-------------------|     |
11 |                        |    o city<"Munich">    |     |
12 |                        |--->o time<>            |     |
13 |                        |    o timezone<1>       |     |
14 |                        |    |    converted_time o-----|
15 |                        |    +-------------------+     |
16 |                        |    +-------------------+     |
17 |                        |    |    ConvertTime    |     |
18 |                        |    |-------------------|     |
19 |                        |    o city<"London">    |     |
20 |                        +--->o time<>            |     |
21 |                             o timezone<0>       |     |
22 |                             |    converted_time o-----+
23 |                             +-------------------+
```

The Graph is can now be evaluated.


```python
graph.evaluate()
```

```
-- World Clock -------------------
It is now 14:55 in Vancouver
It is now 22:55 in London
It is now 23:55 in Munich
----------------------------------
```

For a more verbose output, set the flowpipe logger to DEBUG.


```python
import logging
from flowpipe import logger

logger.setLevel(logging.DEBUG)

graph.evaluate()
```

```
flowpipe DEBUG: Evaluating c:\projects\flowpipe\flowpipe\graph.pyc -> Graph.compute(**{})
flowpipe DEBUG: Evaluating C:\PROJECTS\flowpipe\tests\test_a.py -> CurrentTime.compute(**{})
flowpipe DEBUG: Evaluation result for C:\PROJECTS\flowpipe\tests\test_a.py -> CurrentTime: {
  "time": 1528040105.439
}
flowpipe DEBUG: Evaluating C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime.compute(**{
  "city": "Munich",
  "time": 1528040105.439,
  "timezone": 1
})
flowpipe DEBUG: Evaluation result for C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime: {
  "converted_time": [
    1528043705.439,
    "Munich"
  ]
}
flowpipe DEBUG: Evaluating C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime.compute(**{
  "city": "Vancouver",
  "time": 1528040105.439,
  "timezone": -8
})
flowpipe DEBUG: Evaluation result for C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime: {
  "converted_time": [
    1528011305.439,
    "Vancouver"
  ]
}
flowpipe DEBUG: Evaluating C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime.compute(**{
  "city": "London",
  "time": 1528040105.439,
  "timezone": 0
})
flowpipe DEBUG: Evaluation result for C:\PROJECTS\flowpipe\tests\test_a.py -> ConvertTime: {
  "converted_time": [
    1528040105.439,
    "London"
  ]
}
flowpipe DEBUG: Evaluating C:\PROJECTS\flowpipe\tests\test_a.py -> WorldClock.compute(**{
  "time1": [
    1528011305.439,
    "Vancouver"
  ],
  "time2": [
    1528040105.439,
    "London"
  ],
  "time3": [
    1528043705.439,
    "Munich"
  ]
})
-- World Clock -------------------
It is now 08:35 in Vancouver
It is now 16:35 in London
It is now 17:35 in Munich
----------------------------------
flowpipe DEBUG: Evaluation result for C:\PROJECTS\flowpipe\tests\test_a.py -> WorldClock: {}
flowpipe DEBUG: Evaluation result for c:\projects\flowpipe\flowpipe\graph.pyc -> Graph: {}
```

# Planned Features
- Visual Editor
- Celery Integration
- API simplifications
