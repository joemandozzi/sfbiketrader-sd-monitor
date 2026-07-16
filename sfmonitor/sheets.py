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

INSTALL_TAB = "First Time Install"
INSTALL_ROWS = [
    ["First-time setup"],
    [""],
    ["This Sheet is updated by whoever has this project set up on their own"],
    ["computer -- there's no button in the Sheet itself. To set it up on"],
    ["your own computer, copy the block below and paste it as a message to"],
    ["Claude Code (https://claude.com/product/claude-code). It'll ask what"],
    ["you already know and walk you through the rest either way."],
    [""],
    ["Don't have Claude Code? See SETUP.md in the GitHub repo instead:"],
    ["https://github.com/joemandozzi/sfbiketrader-sd-monitor"],
    [""],
    ["--- copy everything below this line ---"],
    [""],
    ["Set up the sfbiketrader-sd-monitor project on this computer for me:"],
    ["https://github.com/joemandozzi/sfbiketrader-sd-monitor"],
    [""],
    ["First, ask me how familiar I am with things like Terminal, git/GitHub,"],
    ["and installing developer tools. Based on my answer:"],
    ["- If I'm experienced: move through setup quickly, just flagging each"],
    ["  step before you run it."],
    ["- If I'm new to this: don't assume I know anything. Explain what"],
    ["  Terminal is and how to open it, what a \"repository\" is, what a"],
    ["  Python virtual environment is for, etc., in plain language, before"],
    ["  each step -- and check in with me before moving on if a step"],
    ["  doesn't look like what you described."],
    [""],
    ["Here's the situation: this is a personal tool that tracks bikes"],
    ["posted for sale on an Instagram account and cross-references them"],
    ["against Craigslist/Facebook/OfferUp listings in San Diego, writing"],
    ["everything to a shared Google Sheet. I need my own local copy set up"],
    ["so I can trigger refreshes myself, using the same shared Sheet"],
    ["someone else already set up."],
    [""],
    ["Please:"],
    [""],
    ["1. Check whether I have git and python3 installed (git --version,"],
    ["   python3 --version). If not, help me install them (on a Mac: Xcode"],
    ["   Command Line Tools for git -- running git --version with git"],
    ["   missing triggers a one-click install prompt; python.org's"],
    ["   installer for Python)."],
    [""],
    ["2. Clone the repo above into my home folder, then set up a Python"],
    ["   virtual environment and install its dependencies (there's a"],
    ["   requirements.txt)."],
    [""],
    ["3. Ask me to go get two things myself (you can't do these steps for"],
    ["   me):"],
    ["   - A free Apify account and API token (apify.com -> sign up ->"],
    ["     Settings -> Integrations/API -> copy the token). This is what"],
    ["     reads the Instagram posts."],
    ["   - A free Anthropic API key (console.anthropic.com -> sign up ->"],
    ["     API Keys). This is what reads each caption and figures out the"],
    ["     bike brand/model/price."],
    ["   Wait for me to paste both back to you."],
    [""],
    ["4. Walk me through creating my own Google service account for"],
    ["   writing to the shared Sheet (don't have me use someone else's"],
    ["   credential file -- a service account I create myself only ever"],
    ["   has access to the one sheet I get added to, not anything else"],
    ["   the sheet owner manages). You can't click through Google Cloud"],
    ["   Console for me, so narrate each step and wait for me to confirm:"],
    ["   a. Go to console.cloud.google.com, create a new project (or"],
    ["      pick an existing one)."],
    ["   b. Enable the \"Google Sheets API\" and \"Google Drive API\" for"],
    ["      it (search each by name, click Enable)."],
    ["   c. IAM & Admin -> Service Accounts -> Create Service Account,"],
    ["      any name, click through without adding any roles."],
    ["   d. Open it -> Keys tab -> Add Key -> Create New Key -> JSON ->"],
    ["      Create. This downloads a JSON file -- help me move it"],
    ["      somewhere sensible and note the full path."],
    ["   e. Show me the service account's email (looks like"],
    ["      something@project-id.iam.gserviceaccount.com -- on its"],
    ["      details page, or \"client_email\" inside the JSON). I need to"],
    ["      send that email (not the file) to whoever manages the shared"],
    ["      spreadsheet so they can add it as an Editor via Share. Tell"],
    ["      me to do that and wait for their confirmation before"],
    ["      continuing."],
    [""],
    ["5. Create .env (copy from .env.example) and fill in:"],
    ["   - APIFY_API_TOKEN = the token from step 3"],
    ["   - ANTHROPIC_API_KEY = the key from step 3"],
    ["   - GOOGLE_SERVICE_ACCOUNT_JSON = the path to the key file from"],
    ["     step 4"],
    ["   - GOOGLE_SHEET_ID = 1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY"],
    [""],
    ["6. Create config.yaml (copy from config.example.yaml) and set:"],
    ["   - instagram.profile = \"sfbiketrader\""],
    ["   - san_diego.zip = \"92101\""],
    ["   - san_diego.radius_miles = 50"],
    ["   - offerup.enabled = true"],
    ["   - facebook.enabled = false (can be set up later -- it needs its"],
    ["     own one-time login step, see facebook_login.py)"],
    [""],
    ["7. Once the sheet owner confirms they've added my service account"],
    ["   as an Editor, run python main.py --only ig as a test, show me"],
    ["   the output, and confirm it worked (it should print something"],
    ["   like \"Fetched N post(s)\" with no error -- a permissions error"],
    ["   here usually means the sharing step above isn't done yet)."],
    [""],
    ["8. Tell me about REFRESH.md in the repo -- that's what I'll use day"],
    ["   to day after this initial setup."],
    [""],
    ["Ask me questions any time you're unsure rather than assuming. Go."],
    [""],
    ["--- copy everything above this line ---"],
]

REFRESH_TAB = "Refresh Instructions"
REFRESH_ROWS = [
    ["Refresh instructions"],
    [""],
    ["Already set up? Run these in Terminal. (First time? See the"],
    ["\"First Time Install\" tab instead.)"],
    [""],
    ["These are two completely independent refreshes -- each one works"],
    ["fine without the other, in any order, on any schedule."],
    [""],
    ["1) Instagram scrape -- needs Apify"],
    ["cd ~/sfbiketrader-sd-monitor && source .venv/bin/activate && python main.py --only ig"],
    ["Checks the Instagram account for new posts and logs new bike frames"],
    ["to the Frames tab. Usually under a minute. This is the only one of"],
    ["the two that calls Apify -- if your Apify account/credit has an"],
    ["issue, this command will fail, but that has no effect on (2) below."],
    [""],
    ["2) San Diego resale search -- no Apify needed"],
    ["cd ~/sfbiketrader-sd-monitor && source .venv/bin/activate && python main.py --only sd"],
    ["Searches Craigslist/Facebook/OfferUp in San Diego for every bike"],
    ["frame already sitting in the Frames tab. Doesn't touch Instagram or"],
    ["Apify at all -- it just works off whatever frames are already"],
    ["logged, so it runs fine even if (1) is broken or hasn't been run in"],
    ["a while. Takes 30-60+ minutes, that's normal, it prints progress as"],
    ["it goes."],
    [""],
    ["Neither of these deletes or overwrites existing rows in the Frames or"],
    ["Matches tabs -- they only add rows for things not already logged."],
    ["(The Frame Counts tab is the one exception: it's a live leaderboard"],
    ["recomputed fresh from the Frames tab every run, not an append log.)"],
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


def sort_match_rows(match_rows: list) -> list:
    """Sort matches-tab data rows by date_added (index 0), newest first."""
    return sorted(match_rows, key=lambda row: row[0], reverse=True)


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
        self._ensure_static_tab(INSTALL_TAB, INSTALL_ROWS)
        self._ensure_static_tab(REFRESH_TAB, REFRESH_ROWS)

    def _ensure_static_tab(self, title: str, rows: list) -> None:
        """Create a static-content tab (install/refresh instructions) the
        first time only -- never touches it again, so it's safe for a user
        to add their own notes below it.
        """
        if any(ws.title == title for ws in self.spreadsheet.worksheets()):
            return
        ws = self.spreadsheet.add_worksheet(title=title, rows=str(len(rows) + 5), cols="1")
        _with_retry(ws.update, rows)

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

    def sort_matches_by_date_added(self) -> None:
        """Re-sort the whole matches tab newest-first. New matches are
        appended to the bottom during a run (cheap, one row at a time), so
        this re-sort happens once at the end rather than re-sorting after
        every single append.
        """
        rows = self.matches_ws.get_all_values()[1:]
        sorted_rows = sort_match_rows(rows)
        _with_retry(self.matches_ws.clear)
        _with_retry(self.matches_ws.update, [MATCHES_HEADER] + sorted_rows)

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
