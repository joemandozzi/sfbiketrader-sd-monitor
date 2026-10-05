import unittest
from unittest.mock import MagicMock, patch

import impit

from sfmonitor.apify_client import _with_retry


@patch("sfmonitor.apify_client.time.sleep")  # skip real backoff delays in tests
class TestWithRetry(unittest.TestCase):
    def test_returns_result_on_first_success(self, mock_sleep):
        fn = MagicMock(return_value="ok")
        self.assertEqual(_with_retry(fn), "ok")
        mock_sleep.assert_not_called()

    def test_retries_on_connect_error_then_succeeds(self, mock_sleep):
        # A real run hit exactly this -- a DNS blip during the Apify fetch
        # crashed the whole pipeline with no retry at all before this fix.
        fn = MagicMock(side_effect=[impit.ConnectError("dns error"), "ok"])
        self.assertEqual(_with_retry(fn), "ok")
        self.assertEqual(fn.call_count, 2)

    def test_gives_up_after_max_attempts(self, mock_sleep):
        fn = MagicMock(side_effect=impit.ConnectError("still down"))
        with self.assertRaises(impit.ConnectError):
            _with_retry(fn)
        self.assertEqual(fn.call_count, 5)  # RETRY_ATTEMPTS

    def test_does_not_catch_unrelated_exceptions(self, mock_sleep):
        fn = MagicMock(side_effect=ValueError("not a network error"))
        with self.assertRaises(ValueError):
            _with_retry(fn)
        self.assertEqual(fn.call_count, 1)


if __name__ == "__main__":
    unittest.main()
