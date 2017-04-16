from __future__ import print_function
import unittest
import mock

from flowpipe.log_observer import LogObserver


class TestLogObserver(unittest.TestCase):
    """Test the LogObserver."""

    @classmethod
    def tearDown(cls):
        """@todo documentation for tearDown."""
        LogObserver.listeners = list()
    # end def tearDown

    def test_register_listener(self):
        """Register listeners that receive messages."""
        def listener(x, y): None

        LogObserver.register_listener(listener)
        self.assertIn(listener, LogObserver.listeners)

        LogObserver.register_listener(listener)
        self.assertEqual(1, len(LogObserver.listeners))

        LogObserver.deregister_listener(listener)
        self.assertNotIn(listener, LogObserver.listeners)

        LogObserver.deregister_listener(listener)
    # end def test_register_listener

    @mock.patch('logging.Logger.log')
    def test_push_message(self, log):
        """Register listeners that receive messages."""
        calls = list()
        def listener_a(x, y, z=calls): calls.append(1)
        def listener_b(x, y, z=calls): calls.append(1)
        LogObserver.register_listener(listener_a)
        LogObserver.register_listener(listener_b)

        LogObserver.push_message('Hello')

        self.assertEqual(2, len(calls))
        self.assertEqual(1, log.call_count)

        LogObserver.push_message('Hello')

        self.assertEqual(4, len(calls))
        self.assertEqual(2, log.call_count)
    # end def test_push_message
# end class TestLogObserver


if __name__ == '__main__':
    unittest.main()
# end if
