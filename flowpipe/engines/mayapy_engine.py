"""Evaluate a graph with Autodesk Maya's mayapy python interpreter."""
import json
import subprocess

from flowpipe.engine import IEngine


class MayapyEngine(IEngine):
    """Evaluate the graph in a separate mayapy session.

    The graph is being serialized.
    """

    mayapy_location = 'C:/Program Files/Autodesk/Maya2016/bin/mayapy.exe'

    def evaluate_entire_graph(self, graph):
        """Evaluate all nodes in the graph."""
        cmd = [MayapyEngine.mayapy_location, '-c', self.command(graph)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        # Wait for it to complete, or just send it off depending on input param
        #
        # Or rather pipe this into the log observer
        print out, err

    def command(self, graph):
        """@todo documentation for command."""
        serialized_graph = json.dumps(graph.serialize())
        return """
import json
import maya.standalone
maya.standalone.initialize(name='python')

from flowpipe.node import INode
from flowpipe.graph import Graph

serialized_data = json.loads('{0}')

nodes = [INode.deserialize(d) for d in serialized_data]

print nodes

graph = Graph("GraphNameHasToBeSerialized", nodes)
graph.compute()
        """.format(serialized_graph)


if __name__ == '__main__':
    from flowpipe.nodes.value_node import ValueNode
    from flowpipe.graph import Graph
    node = ValueNode()
    graph = Graph("MayapyGraph", [node])
    MayapyEngine().evaluate_entire_graph(graph)
