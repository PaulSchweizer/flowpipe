import inspect
from io import TextIOWrapper
from typing import TextIO, Union

from flowpipe.node import INode

from flowpipe.graph import Graph


class Serializer:
    @staticmethod
    def _write_start_xml(file_handle: TextIO):
        start_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <graphml xmlns="http://graphml.graphdrawing.org/xmlns"  
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
        """

        file_handle.writelines(start_xml)

    @staticmethod
    def _write_node_attr_defs(file_handle: TextIO):
        attributes = """
        <key id="name" for="node" attr.name="name" attr.type="string"></key>
        <key id="compute_src" for="node" attr.name="compute_src" attr.type="string"></key>
        """

        file_handle.writelines(attributes)

    def serialize_graphml(self, graph: Graph, file_name: str):
        with open(file_name, "w") as serial_file:
            self._write_start_xml(serial_file)

            self._serialize_graph(graph, serial_file)

            serial_file.writelines("</graphml>")

    def _serialize_graph(self, graph: Graph, file_handle: TextIO):
        file_handle.write(f"""< graph id="{graph.name}" edgedefault="directed">""")

        for node in graph._nodes:
            self._serialize_node(node, file_handle)

        for node in graph.nodes:
            self._serialize_edges(node, file_handle)

        file_handle.write("</graph>")

    def _serialize_node(self, node_or_graph: Union[Graph, INode], file_handle: TextIO):
        if isinstance(node_or_graph, Graph):
            self._serialize_graph(node_or_graph, file_handle)
        else:
            node = node_or_graph
            f"""<node id="{node.identifier}">
                    <data key="name">{node.name}</data>
                    <data key="compute_src">{inspect.getsource(node.compute)}</data>
            </node>"""

    @staticmethod
    def _serialize_edges(node: INode, file_handle: TextIO):
        for output in node.outputs.values():
            for conn in output.connections():
                other_node_id = conn.node.identifier
                file_handle.write(
                    f"""
                    <edge id="{node.identifier}-{other_node_id}"
                    source="{node.identifier}"
                    target="{other_node_id}"/>
                    """
                )

    def deserialize_graphml(self):
        pass
