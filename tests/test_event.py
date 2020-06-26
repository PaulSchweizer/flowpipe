from __future__ import print_function

from flowpipe.event import Event


def test_listeners_only_registered_once():
    def listener(x, y):
        pass

    event = Event("test")
    event.register(listener)
    event.register(listener)
    assert event.is_registered(listener)
    assert 1 == len(event._listeners)


def test_deregister_if_registered():
    def listener(x, y):
        pass

    event = Event("test")
    event.register(listener)
    event.deregister(listener)
    assert not event.is_registered(listener)

    event.deregister(listener)


def test_event_emitt():
    def listener(arg, kwarg):
        assert arg == 123
        assert kwarg == "test"

    event = Event("test")
    event.register(listener)
    event.emit(123, kwarg="test")


def test_event_clear():
    def listener(arg, kwarg):
        pass

    event = Event("test")
    event.register(listener)
    event.clear()

    assert not event.is_registered(listener)
    assert len(event._listeners) == 0
