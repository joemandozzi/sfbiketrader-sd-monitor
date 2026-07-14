import unittest

from sfmonitor.matcher import title_matches_keyword


class TestTitleMatchesKeyword(unittest.TestCase):
    def test_exact_phrase_matches(self):
        self.assertTrue(title_matches_keyword("Bianchi Volpe 58cm, great shape", "Bianchi Volpe"))

    def test_case_insensitive(self):
        self.assertTrue(title_matches_keyword("SURLY CROSS-CHECK 56", "surly cross-check"))

    def test_missing_phrase_rejected(self):
        self.assertFalse(title_matches_keyword("Trek 520 touring bike", "Bianchi Volpe"))

    def test_partial_word_overlap_rejected(self):
        self.assertFalse(title_matches_keyword("Specialized Stumpjumper", "Specialized Rockhopper"))


if __name__ == "__main__":
    unittest.main()
