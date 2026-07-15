import unittest
from unittest.mock import MagicMock

from sfmonitor.facebook import FacebookLoginRequiredError, FacebookSession


class TestFacebookSession(unittest.TestCase):
    def test_refuses_to_run_without_session_file(self):
        session = FacebookSession(playwright=MagicMock(), session_path="/nonexistent/fb_session.json")
        with self.assertRaises(FacebookLoginRequiredError):
            session.__enter__()


if __name__ == "__main__":
    unittest.main()
