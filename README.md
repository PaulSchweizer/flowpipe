[![Build Status](https://travis-ci.org/PaulSchweizer/flowpipe.svg?branch=master)](https://travis-ci.org/PaulSchweizer/flowpipe) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PaulSchweizer/flowpipe&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&utm_medium=referral&utm_content=PaulSchweizer/flowpipe&utm_campaign=Badge_Coverage)

# Flow-based Pipeline

## Code Documentation
https://paulschweizer.github.io/flowpipe/

## Notes
http://stackoverflow.com/questions/29547695/celery-access-all-previous-results-in-a-chain




# User Guide
flowpipe is a lightweight framework for evaluating node-based graphs.

## Engines
Different Engines can be used to evaluate the graph. Support for these engines is built in, but the list can be extended:
    * Python27
    * mayapy

## Graphs and Nodes
Graphs can be constructed like this:
```
start = TestNode('start')
end = TestNode('end')
start.outputs['out'] >> end.inputs['in']
```
This will result in the most simple graph of two nodes, connected via one connection.

    TODO: Image of the graph

## Graph Execution
The Graph will be run in the given Engine. flowpipe parses the dependency tree and sorts the nodes into a grid. The rows in the grid are executed in sequential order, whereas the Nodes in each row can be executed in parallel.

Parallel evaluation is currently only possible through the built in Celery integration.

## Celery Integration
The flowpipe graph can be serialized into a structure for Celery. Redis is used as a backend for the data serialization.

### Installation Guide
Celery is in the requirements for flowpipe, but additional software needs to be made available:

    * Redis  TODO: Link
    * Install RabbitMq  TODO: Link
    * Celery Flower (optional) TODO: Link




