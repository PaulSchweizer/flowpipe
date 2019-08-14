from __future__ import print_function

import mock
import pytest

from flowpipe.node import INode, Node
from flowpipe.stats_reporter import StatsReporter

@pytest.fixture
def clear_listeners():
    """Remove the listeners."""
    yield
    StatsReporter.listeners = list()


def test_register_listener(clear_listeners):
    """Register listeners that receive messages."""
    def listener(x, y): None

    StatsReporter.register_listener(listener)
    assert listener in StatsReporter.listeners

    StatsReporter.register_listener(listener)
    assert 1 == len(StatsReporter.listeners)

    StatsReporter.deregister_listener(listener)
    assert listener not in StatsReporter.listeners

    StatsReporter.deregister_listener(listener)


def test_push_stats(clear_listeners):
    """Register listeners that receive messages."""
    global test_calls
    test_calls = []

    def listener_a(stats):
        global test_calls
        test_calls.append(1)

    def listener_b(stats):
        global test_calls
        test_calls.append(1)

    StatsReporter.register_listener(listener_a)
    StatsReporter.register_listener(listener_b)

    StatsReporter.push_stats({"log": "data"})

    assert 2 == len(test_calls)

    StatsReporter.push_stats({"log": "data"})

    assert 4 == len(test_calls)


def test_node_reports_stats(clear_listeners):
    """Nodes report stats on evaluation."""
    global test_stats

    def stats_listener(stats):
        global test_stats
        test_stats = stats

    StatsReporter.register_listener(stats_listener)

    @Node()
    def SimpleNode():
        pass

    node = SimpleNode()

    node.evaluate()

    assert "node" in test_stats
    assert "timestamp" in test_stats
    assert "eval_time" in test_stats
