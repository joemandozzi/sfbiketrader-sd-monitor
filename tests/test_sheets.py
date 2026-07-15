import unittest

from sfmonitor.sheets import compute_frame_counts


def _row(brand, model):
    # Matches FRAMES_HEADER column order: post_timestamp, post_url, brand,
    # model, frame_size, price, condition -- only brand/model matter here.
    return ["2026-01-01", "https://example.com/p/1", brand, model, "", "", ""]


class TestComputeFrameCounts(unittest.TestCase):
    def test_orders_by_count_descending(self):
        rows = [
            _row("Specialized", "Stumpjumper"),
            _row("Specialized", "Stumpjumper"),
            _row("Specialized", "Stumpjumper"),
            _row("Trek", "520"),
        ]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Specialized", "Stumpjumper", 3], ["Trek", "520", 1]])

    def test_skips_rows_missing_brand_or_model(self):
        rows = [_row("Trek", "520"), _row("Trek", None), _row(None, "520"), _row("", "")]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Trek", "520", 1]])

    def test_empty_rows_returns_empty(self):
        self.assertEqual(compute_frame_counts([]), [])


if __name__ == "__main__":
    unittest.main()
