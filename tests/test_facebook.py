import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from sfmonitor.facebook import FacebookLoginRequiredError, FacebookSession


def _mock_playwright(cookies):
    """Build a mock playwright whose browser/context/page chain returns the
    given cookie list from context.cookies(), mirroring what a real
    Playwright session returns after loading facebook.com.
    """
    page = MagicMock()
    context = MagicMock()
    context.new_page.return_value = page
    context.cookies.return_value = cookies
    browser = MagicMock()
    browser.new_context.return_value = context
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser
    return playwright, browser, context


class TestFacebookSession(unittest.TestCase):
    def test_refuses_to_run_without_session_file(self):
        session = FacebookSession(playwright=MagicMock(), session_path="/nonexistent/fb_session.json")
        with self.assertRaises(FacebookLoginRequiredError):
            session.__enter__()

    def test_refuses_when_session_file_exists_but_expired(self):
        # A session file existing isn't enough -- Facebook can silently stop
        # honoring an expired one. This is what let ~580 mislabeled Midwest
        # listings through on 2026-08-14 before this check existed.
        with tempfile.TemporaryDirectory() as tmp:
            session_path = Path(tmp) / "fb_session.json"
            session_path.write_text("{}")
            playwright, browser, context = _mock_playwright(cookies=[])  # no c_user cookie
            session = FacebookSession(playwright=playwright, session_path=session_path)
            with self.assertRaises(FacebookLoginRequiredError):
                session.__enter__()
            browser.close.assert_called_once()

    def test_proceeds_when_session_is_still_logged_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_path = Path(tmp) / "fb_session.json"
            session_path.write_text("{}")
            playwright, browser, context = _mock_playwright(cookies=[{"name": "c_user", "value": "123"}])
            session = FacebookSession(playwright=playwright, session_path=session_path)
            result = session.__enter__()
            self.assertIs(result, session)
            browser.close.assert_not_called()


if __name__ == "__main__":
    unittest.main()
