[![Build Status](https://travis-ci.org/PaulSchweizer/flowpipe.svg?branch=master)](https://travis-ci.org/PaulSchweizer/flowpipe) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=PaulSchweizer/flowpipe&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/6ac650d8580d43dbaf7de96a3171e76f)](https://www.codacy.com/app/paulschweizer/flowpipe?utm_source=github.com&utm_medium=referral&utm_content=PaulSchweizer/flowpipe&utm_campaign=Badge_Coverage)

# Flow-based Pipeline
A lightweight framework for flow-based programming in python.

## Example
Please refer to the [jupyter notebook](docs/example.ipynb) for a demo.

## Code Documentation
https://paulschweizer.github.io/flowpipe/

# Features of version 0.1.0
- Api:
    - Create Nodes with arbitrary Inputs and Outputs
    - Node can execute arbitrary python code
    - Nodes can be connected via their inputs and outputs to form a Graph
- Graphs behave like Nodes and can be used within other Graphs
- Graph Evaluation in arbitray environments (Engines)
- Graph is JSON serializable and deserializable
- Comprehensive string representation for Graph and Nodes

# Planned Features
- Visual Editor
- Celery Integration
- API simplifications
