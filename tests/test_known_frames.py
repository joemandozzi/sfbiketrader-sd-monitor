import os
import tempfile
import unittest

from sfmonitor import known_frames


class TestKnownFrames(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))

    def test_load_missing_file(self):
        self.assertEqual(known_frames.load_known_frames(self.path), set())

    def test_add_and_reload(self):
        known_frames.add_known_frames({("Bianchi", "Volpe")}, self.path)
        self.assertEqual(known_frames.load_known_frames(self.path), {("Bianchi", "Volpe")})

    def test_add_is_cumulative_across_calls(self):
        known_frames.add_known_frames({("Bianchi", "Volpe")}, self.path)
        known_frames.add_known_frames({("Surly", "Cross-Check")}, self.path)
        self.assertEqual(
            known_frames.load_known_frames(self.path),
            {("Bianchi", "Volpe"), ("Surly", "Cross-Check")},
        )


if __name__ == "__main__":
    unittest.main()
