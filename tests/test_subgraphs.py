
from flowpipe import Graph
from flowpipe import Node


@Node(outputs=["out"])
def ANode(in_):
    return {"out": in_}



"""
TODOs:

Test that the nodes always have a graph attr!!!!
graph.add_node
node.__init__
remove node from graph???

"""

def test_create_nested_subgraphs():
    """Nested subgraphs
    +------------+          +------------+          +------------+          +------------+
    |   ANode    |          |   ANode    |          |   ANode    |          |   ANode    |
    |------------|          |------------|          |------------|          |------------|
    o in_<>      |     +--->o in_<>      |       -->o in_<>      |       -->o in_<>      |
    |        out o-----+    |        out o---       |        out o---       |        out o
    +------------+          +------------+          +------------+          +------------+
    """
    main = Graph("main")
    main_node = ANode(graph=main)

    parent = main
    for i in range(3):
        sub = Graph("sub" + str(i))
        sub_node_1 = ANode(graph=sub)
        sub_node_2 = ANode(graph=sub, name="sub" + str(i) + "-2")
        parent["ANode"].outputs["out"] >> sub["ANode"].inputs["in_"]
        parent = sub

    assert len(main.nodes) == 1

    print [g.name for g in main.subgraphs]
    print [n.identifier for n in main.all_nodes]

    print main.parent_graphs
    for sub in main.subgraphs:
        print sub.parent_graphs


    print main





# test_access_subgraph_nodes_directly
#

# propagate plugs to graph
#

# graph.members
#

# graph.subgraphs
#

# print the graph
#
