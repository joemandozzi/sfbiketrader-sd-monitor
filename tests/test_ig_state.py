import json
import os
import tempfile
import unittest

from sfmonitor import ig_state


class TestIgState(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)  # start from "file doesn't exist yet"
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))

    def test_load_seen_missing_file(self):
        self.assertEqual(ig_state.load_seen(self.path), set())

    def test_mark_and_reload(self):
        ig_state.mark_seen(["abc", "def"], self.path)
        self.assertEqual(ig_state.load_seen(self.path), {"abc", "def"})

    def test_mark_seen_is_additive(self):
        ig_state.mark_seen(["abc"], self.path)
        ig_state.mark_seen(["def"], self.path)
        self.assertEqual(ig_state.load_seen(self.path), {"abc", "def"})

    def test_mark_seen_writes_timestamps(self):
        ig_state.mark_seen(["abc"], self.path)
        with open(self.path) as f:
            data = json.load(f)
        self.assertIn("abc", data)
        self.assertTrue(data["abc"])


if __name__ == "__main__":
    unittest.main()
