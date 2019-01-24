import os
import re


def test_graphml_serialization(graph_order_tup):
    graph, _ = graph_order_tup
    file_name = "graphml_tmp.xml"

    graph.serialize_graphml(file_name)

    file_content = open(file_name, 'r').read()
    os.remove(file_name)

    expected_content = """<?xml version=?>
        <graphml>
        <graph id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    <edge id=
                    source=
                    target=/>
                    </graph></graphml>"""

    file_content_no_id = re.sub(r"\".*\"", "", file_content)

    assert expected_content == file_content_no_id
