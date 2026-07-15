"""Google Sheets output via a service account (gspread).

Two persistent tabs are appended to over time (not recreated each run):
"SF Bike Trader Frames" and "San Diego Matches". See README.md for how to
create a service account, enable the Sheets + Drive APIs, and share your
sheet with the service account's email.
"""
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

import gspread
import requests
from google.oauth2.service_account import Credentials

_PRICE_RE = re.compile(r"[\d,]+")

RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY_SECONDS = 2

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CREDS_ENV_VAR = "GOOGLE_SERVICE_ACCOUNT_JSON"
SHEET_ID_ENV_VAR = "GOOGLE_SHEET_ID"

FRAMES_TAB = "SF Bike Trader Frames"
FRAMES_HEADER = ["post_timestamp", "post_url", "brand", "model", "frame_size", "price", "condition"]

MATCHES_TAB = "San Diego Matches"
MATCHES_HEADER = ["date_added", "matched_brand", "matched_model", "source", "title", "price", "location", "url"]

FRAME_COUNTS_TAB = "Frame Counts"
FRAME_COUNTS_HEADER = ["brand", "model", "count", "min_price", "max_price"]

INSTRUCTIONS_TAB = "Instructions"
INSTRUCTIONS_ROWS = [
    ["How this sheet updates"],
    [""],
    ["This updates from whoever's computer has it set up (currently Joe's"],
    ["and his brother-in-law's) -- there's no button in the Sheet itself."],
    [""],
    ["First-time setup: see SETUP.md in the GitHub repo --"],
    ["https://github.com/joemandozzi/sfbiketrader-sd-monitor"],
    [""],
    ["Once set up, run these two commands in Terminal to refresh each tab:"],
    ["cd ~/sfbiketrader-sd-monitor && source .venv/bin/activate && python main.py --only ig"],
    ["cd ~/sfbiketrader-sd-monitor && source .venv/bin/activate && python main.py --only sd"],
    ["(The second one takes 30-60+ minutes -- that's normal.)"],
]


class SheetsConfigError(RuntimeError):
    """Raised when the service-account credentials or sheet aren't configured."""


def get_client() -> gspread.Client:
    creds_path = os.environ.get(CREDS_ENV_VAR)
    if not creds_path:
        raise SheetsConfigError(
            f"Set {CREDS_ENV_VAR} to the path of your Google service-account JSON key "
            "(see README.md for setup steps)."
        )
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_spreadsheet(client: gspread.Client):
    sheet_id = os.environ.get(SHEET_ID_ENV_VAR)
    if not sheet_id:
        raise SheetsConfigError(
            f"Set {SHEET_ID_ENV_VAR} to the id of a spreadsheet you've already created and "
            "shared with the service account's email (Editor access). See README.md."
        )
    return client.open_by_key(sheet_id)


def _get_or_create_worksheet(spreadsheet, title: str, header: list):
    for ws in spreadsheet.worksheets():
        if ws.title == title:
            return ws
    ws = spreadsheet.add_worksheet(title=title, rows="1000", cols=str(len(header)))
    ws.append_row(header)
    return ws


def _with_retry(fn, *args, **kwargs):
    """A run making hundreds of Sheets API calls will eventually hit a
    transient network blip or a rate-limit response -- retry with backoff
    rather than letting one flaky request kill an hours-long backfill.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except (requests.exceptions.ConnectionError, gspread.exceptions.APIError):
            if attempt == RETRY_ATTEMPTS:
                raise
            time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)


def _append_with_retry(worksheet, row: list) -> None:
    _with_retry(worksheet.append_row, row)


def _parse_price(raw: str) -> Optional[int]:
    """Frame-tab prices are Claude's free-text extraction (e.g. "$450",
    "450", "$1,200") -- pull out the first number, ignore anything
    unparseable rather than erroring.
    """
    if not raw:
        return None
    m = _PRICE_RE.search(raw)
    if not m:
        return None
    return int(m.group(0).replace(",", ""))


def frame_keys(frame_rows: list) -> set:
    """Distinct (brand, model) pairs across all logged frame mentions.

    This -- not a local cache file -- is the source of truth for "which
    frames are known so far," since it's derived fresh from the shared
    spreadsheet and so stays correct no matter which machine last wrote to
    it.
    """
    return {(row[2], row[3]) for row in frame_rows if row[2] and row[3]}


def compute_frame_counts(frame_rows: list) -> list:
    """Given data rows from the frames tab (brand at index 2, model at
    index 3, price at index 5), return [brand, model, count, min_price,
    max_price] rows ordered by count desc. min/max are blank when no
    listing for that frame had a parseable price.
    """
    counts: dict = {}
    prices: dict = {}
    for row in frame_rows:
        brand, model, price_raw = row[2], row[3], row[5]
        if not (brand and model):
            continue
        key = (brand, model)
        counts[key] = counts.get(key, 0) + 1
        price = _parse_price(price_raw)
        if price is not None:
            prices.setdefault(key, []).append(price)

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    rows = []
    for key, count in ranked:
        key_prices = prices.get(key)
        min_price = min(key_prices) if key_prices else ""
        max_price = max(key_prices) if key_prices else ""
        rows.append([key[0], key[1], count, min_price, max_price])
    return rows


class SheetHandles:
    """Holds one open spreadsheet + both worksheets for the duration of a
    run, so a run with many rows to append doesn't re-open the spreadsheet
    and re-list its tabs on every single row.
    """

    def __init__(self):
        client = get_client()
        self.spreadsheet = _open_spreadsheet(client)
        self.frames_ws = _get_or_create_worksheet(self.spreadsheet, FRAMES_TAB, FRAMES_HEADER)
        self.matches_ws = _get_or_create_worksheet(self.spreadsheet, MATCHES_TAB, MATCHES_HEADER)
        self.frame_counts_ws = _get_or_create_worksheet(self.spreadsheet, FRAME_COUNTS_TAB, FRAME_COUNTS_HEADER)
        self._ensure_instructions_tab()

    def _ensure_instructions_tab(self) -> None:
        """Create the Instructions tab with its static content the first
        time only -- never touches it again, so it's safe for a user to
        add their own notes below it.
        """
        if any(ws.title == INSTRUCTIONS_TAB for ws in self.spreadsheet.worksheets()):
            return
        ws = self.spreadsheet.add_worksheet(title=INSTRUCTIONS_TAB, rows="20", cols="1")
        _with_retry(ws.update, INSTRUCTIONS_ROWS)

    @property
    def url(self) -> str:
        return self.spreadsheet.url

    def get_frame_rows(self) -> list:
        """Raw data rows (no header) from the frames tab -- the shared
        source of truth for which posts/frames have already been logged.
        Multiple machines can write to the same spreadsheet, so dedup is
        always derived from its current contents rather than any local
        per-machine file.
        """
        return self.frames_ws.get_all_values()[1:]

    def get_match_urls(self) -> set:
        """URLs already logged in the San Diego Matches tab (last column),
        same shared-source-of-truth reasoning as get_frame_rows().
        """
        rows = self.matches_ws.get_all_values()[1:]
        return {row[-1] for row in rows if row[-1]}

    def append_frame_row(self, post_timestamp, post_url, brand, model, frame_size, price, condition) -> None:
        _append_with_retry(self.frames_ws, [post_timestamp, post_url, brand, model, frame_size, price, condition])

    def append_match_row(self, matched_brand, matched_model, source, title, price, location, url) -> None:
        # None of the three sources reliably expose a real "listed" date in
        # their search results (Facebook/OfferUp don't have one at all;
        # Craigslist only on the per-listing detail page), so this stamps
        # when *this tool* first found the match instead -- consistent
        # across all sources, no extra per-listing requests needed.
        date_added = datetime.now(timezone.utc).isoformat()
        _append_with_retry(
            self.matches_ws, [date_added, matched_brand, matched_model, source, title, price, location, url]
        )

    def write_frame_counts(self) -> None:
        """Recompute the distinct-frame leaderboard from scratch, ordered by
        how many times each (brand, model) appears in the frames log. This
        tab is a derived summary, not an append-only log -- it's fully
        overwritten every run rather than incrementally appended to.
        """
        rows = self.frames_ws.get_all_values()[1:]  # skip header
        values = [FRAME_COUNTS_HEADER] + compute_frame_counts(rows)
        _with_retry(self.frame_counts_ws.clear)
        _with_retry(self.frame_counts_ws.update, values)
