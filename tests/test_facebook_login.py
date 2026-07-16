import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from facebook_login import _ensure_private_dir, _lock_down_session_file

# chmod's numeric mode bits are POSIX-specific -- Windows doesn't enforce
# owner-only 0700/0600 the same way, so these assertions only make sense
# on macOS/Linux (which is what this change is required to handle).
_SKIP_MODE_CHECKS = sys.platform == "win32"


def _mode(path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


@unittest.skipIf(_SKIP_MODE_CHECKS, "POSIX-only permission bits")
class TestEnsurePrivateDir(unittest.TestCase):
    def test_creates_missing_dir_as_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "data"
            self.assertFalse(target.exists())
            _ensure_private_dir(target)
            self.assertTrue(target.is_dir())
            self.assertEqual(_mode(target), 0o700)

    def test_locks_down_an_already_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "data"
            target.mkdir()
            os.chmod(target, 0o755)  # simulate a pre-existing, too-open dir
            _ensure_private_dir(target)
            self.assertEqual(_mode(target), 0o700)


@unittest.skipIf(_SKIP_MODE_CHECKS, "POSIX-only permission bits")
class TestLockDownSessionFile(unittest.TestCase):
    def test_restricts_file_to_owner_read_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "fb_session.json"
            target.write_text("{}")
            os.chmod(target, 0o644)  # simulate the default, too-open mode
            _lock_down_session_file(target)
            self.assertEqual(_mode(target), 0o600)


if __name__ == "__main__":
    unittest.main()
