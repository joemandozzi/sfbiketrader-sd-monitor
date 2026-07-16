import unittest

from sfmonitor.sheets import compute_frame_counts, frame_keys, sort_match_rows


def _row(brand, model, price=""):
    # Matches FRAMES_HEADER column order: post_timestamp, post_url, brand,
    # model, frame_size, price, condition.
    return ["2026-01-01", "https://example.com/p/1", brand, model, "", price, ""]


def _match_row(date_added, url="https://example.com/x"):
    # Matches MATCHES_HEADER column order: date_added, matched_brand,
    # matched_model, source, title, price, location, url.
    return [date_added, "Trek", "520", "craigslist", "Trek 520", "$300", "San Diego", url]


class TestComputeFrameCounts(unittest.TestCase):
    def test_orders_by_count_descending(self):
        rows = [
            _row("Specialized", "Stumpjumper", "$400"),
            _row("Specialized", "Stumpjumper", "$500"),
            _row("Specialized", "Stumpjumper", "$450"),
            _row("Trek", "520", "$300"),
        ]
        result = compute_frame_counts(rows)
        self.assertEqual(
            result,
            [["Specialized", "Stumpjumper", 3, 400, 500], ["Trek", "520", 1, 300, 300]],
        )

    def test_skips_rows_missing_brand_or_model(self):
        rows = [_row("Trek", "520", "$300"), _row("Trek", None), _row(None, "520"), _row("", "")]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Trek", "520", 1, 300, 300]])

    def test_empty_rows_returns_empty(self):
        self.assertEqual(compute_frame_counts([]), [])

    def test_handles_comma_and_dollar_sign_prices(self):
        rows = [_row("Somec", "Supercorsa", "$1,450"), _row("Somec", "Supercorsa", "1200")]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Somec", "Supercorsa", 2, 1200, 1450]])

    def test_blank_min_max_when_no_parseable_price(self):
        rows = [_row("Trek", "520", ""), _row("Trek", "520", "obo")]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Trek", "520", 2, "", ""]])

    def test_mix_of_priced_and_unpriced_rows(self):
        rows = [_row("Trek", "520", "$300"), _row("Trek", "520", "")]
        result = compute_frame_counts(rows)
        self.assertEqual(result, [["Trek", "520", 2, 300, 300]])


class TestFrameKeys(unittest.TestCase):
    def test_returns_distinct_pairs(self):
        rows = [
            _row("Specialized", "Stumpjumper"),
            _row("Specialized", "Stumpjumper"),
            _row("Trek", "520"),
        ]
        self.assertEqual(frame_keys(rows), {("Specialized", "Stumpjumper"), ("Trek", "520")})

    def test_skips_rows_missing_brand_or_model(self):
        rows = [_row("Trek", "520"), _row("Trek", None), _row(None, "520"), _row("", "")]
        self.assertEqual(frame_keys(rows), {("Trek", "520")})

    def test_empty_rows_returns_empty_set(self):
        self.assertEqual(frame_keys([]), set())


class TestSortMatchRows(unittest.TestCase):
    def test_sorts_newest_first(self):
        rows = [
            _match_row("2026-07-10T00:00:00+00:00", url="oldest"),
            _match_row("2026-07-15T00:00:00+00:00", url="newest"),
            _match_row("2026-07-12T00:00:00+00:00", url="middle"),
        ]
        result = sort_match_rows(rows)
        self.assertEqual([row[-1] for row in result], ["newest", "middle", "oldest"])

    def test_empty_rows_returns_empty(self):
        self.assertEqual(sort_match_rows([]), [])

    def test_does_not_mutate_input(self):
        rows = [_match_row("2026-07-10T00:00:00+00:00"), _match_row("2026-07-15T00:00:00+00:00")]
        original = list(rows)
        sort_match_rows(rows)
        self.assertEqual(rows, original)


if __name__ == "__main__":
    unittest.main()
