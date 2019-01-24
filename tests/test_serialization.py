

def test_graphml_serialization(graph_order_tup):
    graph, _ = graph_order_tup
    file_name = "graphml_tmp.xml"

    graph.serialize_graphml(graph, file_name)

    file_content = open(file_name, 'r').read()
    expected_content = """
    """

    assert expected_content == file_content
