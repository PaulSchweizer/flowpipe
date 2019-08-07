import pytest

from flowpipe.graph import reset_default_graph


@pytest.fixture
def clear_default_graph():
    reset_default_graph()
