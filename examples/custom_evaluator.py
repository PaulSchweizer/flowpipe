"""Example that shows how to create a custom evaluator for flowpipe graphs.

+-------------------------------------------------+
|                      Math                       |
|-------------------------------------------------|
| +----------------+          +-----------------+ |
| |   First Sum    |          |   Second Sum    | |
| |----------------|          |-----------------| |
| o number_1<2>    |          o number_1<4>     | |
| o number_2<2>    |     +--->o number_2<>      | |
| |          sum<> o-----+    |           sum<> o |
| +----------------+          +-----------------+ |
+-------------------------------------------------+
"""

from flowpipe import Evaluator, Graph, Node
import json


class CustomEvaluator(Evaluator):
    """A custom evaluator that prints the nodes being evaluated.

    Evaluators inherit from the Evaluator class and implement the
    `_evaluate_nodes` method.
    """

    def _evaluate_nodes(self, nodes):
        """Perform the actual node evaluation."""
        for node in nodes:
            print(f"Evaluating node: {node.name}")
            print(f"With Metadata: {json.dumps(node.metadata, indent=2)}")
            node.evaluate()


@Node(outputs=["sum"], metadata={"key": "value"})
def Add(number_1: int, number_2: int = 2):
    """A simple node that adds two numbers together."""
    return {"sum": number_1 + number_2}


# create graph
math_graph = Graph(name="Math")

# create nodes and set values
first_sum = Add(name="First Sum", number_1=2, number_2=2, graph=math_graph)
second_sum = Add(name="Second Sum", number_1=4, graph=math_graph)

# connect nodes
first_sum.outputs["sum"].connect(second_sum.inputs["number_2"])

print(math_graph)

# evaluate the graph using the custom evaluator
custom_eval = CustomEvaluator()
custom_eval.evaluate(math_graph)

print(f"Result of first sum: {first_sum.outputs['sum'].value}")
print(f"Result of second sum: {second_sum.outputs['sum'].value}")
