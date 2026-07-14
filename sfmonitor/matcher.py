"""Title matching for San Diego search candidates.

Ported from joemandozzi/bike-scraper's bikescraper/matcher.py (trimmed to
just the title filter -- this project doesn't do size-target filtering the
way bike-scraper does).
"""


def title_matches_keyword(title, keyword):
    """Craigslist/Facebook search both fall back to loosely-related or even
    cross-category results when a query has few exact hits. Require the
    literal keyword phrase to appear in the title so that noise gets
    dropped before a listing is recorded as a match.
    """
    return keyword.strip().lower() in title.lower()
