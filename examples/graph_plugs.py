"""
This examples demonstrates how to promote input and output plugs
to the graph level, allowing them to be used as global inputs and outputs.

This is useful for creating reusable components that can be easily integrated
into larger graphs.

+------------------------------------------------+
|                     Graph                      |
|------------------------------------------------|
o value                                          |
| `-AddNode.input_0                              |
| `-AddNode.input_1                              |
| `-AddNode 2.input_0                            |
| `-AddNode 2.input_1                            |
|------------------------------------------------|
| +---------------+           +----------------+ |
| |    AddNode    |           |   AddNode 3    | |
| |---------------|           |----------------| |
| o input_0<5>    |      +--->o input_0<>      | |
| o input_1<5>    |      |--->o input_1<>      | |
| |         sum<> o------+    |          sum<> o |
| +---------------+      |    +----------------+ |
| +----------------+     |                       |
| |   AddNode 2    |     |                       |
| |----------------|     |                       |
| o input_0<5>     |     |                       |
| o input_1<5>     |     |                       |
| |          sum<> o-----+                       |
| +----------------+                             |
+------------------------------------------------+
"""

from flowpipe import Graph, INode, InputPlug, InputPlugGroup, OutputPlug


class AddNode(INode):
    def __init__(self, input_0=None, input_1=None, **kwargs):
        super().__init__(**kwargs)

        InputPlug("input_0", self, input_0)
        InputPlug("input_1", self, input_1)
        OutputPlug("sum", self)

    def compute(self, **kwargs):
        input_0 = kwargs.pop("input_0")
        input_1 = kwargs.pop("input_1")

        return {"sum": input_0 + input_1}


if __name__ == "__main__":
    graph = Graph()

    # Create nodes
    add_node_1 = AddNode(graph=graph, name="AddNode")
    add_node_2 = AddNode(graph=graph, name="AddNode 2")
    add_node_3 = AddNode(graph=graph, name="AddNode 3")

    add_node_1.outputs["sum"].connect(add_node_3.inputs["input_0"])
    add_node_2.outputs["sum"].connect(add_node_3.inputs["input_1"])

    # a single graph input plug can be connected to multiple node
    # input plugs
    InputPlugGroup(
        "value",
        graph,
        [
            add_node_1.inputs["input_0"],
            add_node_1.inputs["input_1"],
            add_node_2.inputs["input_0"],
            add_node_2.inputs["input_1"],
        ],
    )

    # Connects global graph ouputs to node plugs
    graph.add_plug(add_node_1.outputs["sum"], "sum_add1")
    graph.add_plug(add_node_2.outputs["sum"], "sum_add2")
    graph.add_plug(add_node_3.outputs["sum"], "graph_sum")

    # Set input values
    graph.inputs["value"].value = 5

    print(graph)
    # Run the graph
    graph.evaluate()

    # Print the result
    print("Sum Add 1:", graph.outputs["sum_add1"].value)
    print("Sum Add 2:", graph.outputs["sum_add2"].value)
    print("Final Sum (Add 3):", graph.outputs["graph_sum"].value)
