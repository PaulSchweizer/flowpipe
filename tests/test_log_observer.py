from __future__ import print_function

import mock
import pytest

from flowpipe.log_observer import LogObserver


@pytest.fixture
def clear_log():
    """Remove the listeners."""
    yield
    LogObserver.listeners = list()


def test_register_listener(clear_log):
    """Register listeners that receive messages."""
    def listener(x, y): None

    LogObserver.register_listener(listener)
    assert listener in LogObserver.listeners

    LogObserver.register_listener(listener)
    assert 1 == len(LogObserver.listeners)

    LogObserver.deregister_listener(listener)
    assert listener not in LogObserver.listeners

    LogObserver.deregister_listener(listener)


@mock.patch('logging.Logger.log')
def test_push_message(log, clear_log):
    """Register listeners that receive messages."""
    calls = list()
    def listener_a(x, y, z=calls): calls.append(1)
    def listener_b(x, y, z=calls): calls.append(1)
    LogObserver.register_listener(listener_a)
    LogObserver.register_listener(listener_b)

    LogObserver.push_message('Hello')

    assert 2 == len(calls)
    assert 1 == log.call_count

    LogObserver.push_message('Hello')

    assert 4 == len(calls)
    assert 2 == log.call_count
