"""Google Sheets output via a service account (gspread).

Two persistent tabs are appended to over time (not recreated each run):
"SF Bike Trader Frames" and "San Diego Matches". See README.md for how to
create a service account, enable the Sheets + Drive APIs, and share your
sheet with the service account's email.
"""
import os
import time

import gspread
import requests
from google.oauth2.service_account import Credentials

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
MATCHES_HEADER = ["matched_brand", "matched_model", "source", "title", "price", "location", "url"]


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


def _append_with_retry(worksheet, row: list) -> None:
    """A run appending hundreds of rows will eventually hit a transient
    network blip or a Sheets API rate-limit response -- retry with backoff
    rather than letting one flaky request kill an hours-long backfill.
    """
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            worksheet.append_row(row)
            return
        except (requests.exceptions.ConnectionError, gspread.exceptions.APIError):
            if attempt == RETRY_ATTEMPTS:
                raise
            time.sleep(RETRY_BASE_DELAY_SECONDS * attempt)


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

    @property
    def url(self) -> str:
        return self.spreadsheet.url

    def append_frame_row(self, post_timestamp, post_url, brand, model, frame_size, price, condition) -> None:
        _append_with_retry(self.frames_ws, [post_timestamp, post_url, brand, model, frame_size, price, condition])

    def append_match_row(self, matched_brand, matched_model, source, title, price, location, url) -> None:
        _append_with_retry(self.matches_ws, [matched_brand, matched_model, source, title, price, location, url])
