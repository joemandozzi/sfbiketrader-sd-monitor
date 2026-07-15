# sfbiketrader-sd-monitor

Tracks every bike frame the Instagram account `@sfbiketrader` posts for
sale, then cross-references those frames against Craigslist, Facebook
Marketplace, and OfferUp listings in San Diego. Everything lands in a
Google Sheet with three tabs:

- **SF Bike Trader Frames** -- every frame mention extracted from IG
  captions (brand, model, size, price, condition, post link).
- **San Diego Matches** -- new San Diego listings found for those same
  frames (source, title, price, location, link), sorted newest-first by
  the date this tool found each match. (None of the three sources
  reliably expose the listing's actual posted date in search results, so
  this is "date added," not "date listed.")
- **Frame Counts** -- distinct (brand, model) pairs the account has ever
  posted, ranked by how many times each has appeared, plus the min/max
  asking price seen for that frame. Fully recomputed every run (a derived
  summary, not an append log).

Safe to rerun repeatedly or put on a schedule -- already-processed
Instagram posts and already-logged San Diego listings are always skipped.

## How it works

1. Fetches recent posts from the configured Instagram profile via
   [Apify](https://apify.com)'s hosted `instagram-scraper` actor (Instagram
   has no public API for reading someone else's profile and blocks DIY
   scraping).
2. Extracts structured frame details from each new caption via the
   Anthropic API (captions are free text, so a fixed keyword list would
   miss too much).
3. Logs new frame mentions to the "SF Bike Trader Frames" tab, then
   recomputes the "Frame Counts" leaderboard tab.
4. Searches Craigslist (and Facebook Marketplace / OfferUp, if enabled) in
   San Diego for every distinct brand/model pair ever seen -- not just new
   ones, since a fresh San Diego listing can appear for a frame first seen
   weeks ago.
5. Logs genuinely new matches to the "San Diego Matches" tab.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml   # fill in Instagram profile, SD zip/radius
cp .env.example .env                 # fill in the credentials below
```

All secrets below go in `.env` (gitignored, loaded automatically by
`main.py` -- never pasted into chat or committed).

### Apify (Instagram scraping)

1. Sign up free at [apify.com](https://apify.com) (no credit card needed).
2. Settings -> Integrations/API -> copy your personal API token.
3. Set `APIFY_API_TOKEN` in `.env`.

### Anthropic API (caption parsing)

Set `ANTHROPIC_API_KEY` in `.env` (from [console.anthropic.com](https://console.anthropic.com) -> API Keys).

### Google Sheets (output)

Uses a Google service account, not your personal login, so results always
land in a place the script can write to non-interactively.

1. In the [Google Cloud Console](https://console.cloud.google.com/),
   create/pick a project and enable the **Google Sheets API** and
   **Google Drive API**.
2. Create a **Service Account**, then a JSON key for it, and download the
   file.
3. **Pre-create a spreadsheet yourself** (in your own Google Sheets), share
   it with the service account's email (found in the JSON key as
   `client_email`) with **Editor** access. A plain (non-Workspace) Google
   account's service account has zero personal Drive quota and can't own a
   new file itself -- writing into a spreadsheet you already own and shared
   with it is the reliable path.
4. Set `GOOGLE_SERVICE_ACCOUNT_JSON` (path to the downloaded key file) and
   `GOOGLE_SHEET_ID` (the id in your spreadsheet's URL, between `/d/` and
   `/edit`) in `.env`.

### Facebook Marketplace (optional)

Off by default (`facebook.enabled: false` in `config.yaml`). To enable:

```bash
pip install -r requirements-facebook.txt
playwright install chromium
python3 facebook_login.py
```

`facebook_login.py` opens a real, visible browser for you to log in
yourself (handles any 2FA), then saves a session to `data/fb_session.json`
so scheduled runs can reuse it headlessly.

**That session file is effectively a login credential for that Facebook
account, stored in plaintext on this machine** (gitignored, never
committed, never sent anywhere). Anyone with access to this machine's
filesystem could use it to act as that account without a password or 2FA.
Consider a secondary account rather than your primary one if that's a
concern. Re-run `facebook_login.py` any time the session expires.

Without a session file, Facebook search still runs, but in logged-out mode
-- location then comes from IP-based geolocation, which can resolve
incorrectly.

### OfferUp (optional)

Off by default (`offerup.enabled: false` in `config.yaml`). No login
needed, just Playwright + Chromium:

```bash
pip install -r requirements-offerup.txt
playwright install chromium
```

(If Facebook Marketplace is also enabled, one `playwright install
chromium` covers both -- they share the same browser.) Capped at OfferUp's
own 50-mile max search radius regardless of `san_diego.radius_miles`.

## Usage

```bash
python3 main.py
```

### Manual refresh (one side only)

```bash
python3 main.py --only ig   # just the Instagram scrape + Frame Counts recompute
python3 main.py --only sd   # just the Craigslist/Facebook/OfferUp search
```

There's no live button in the Sheet -- Google Sheets/Apps Script has no
access to a local machine, so a real "click to refresh" would need a
server or tunnel running on your laptop at all times. Simpler for now:
the exact commands above are also written to an "Instructions" tab
created automatically in the Sheet itself.

### Run it on a schedule

```bash
./launchd/install.sh
```

Installs a `launchd` agent (same pattern as
[bike-scraper](https://github.com/joemandozzi/bike-scraper)) that runs
`main.py` once each time you log in / start your laptop -- matching how you
actually use this machine, rather than a fixed background interval. Logs go
to `data/monitor.log`.

**Your laptop needs to be on and awake for a run to fire** -- if it's asleep
or off, that check is simply skipped until next login. If you leave your
laptop logged in and awake for multiple days straight without restarting,
this alone won't re-fire daily; edit the `.plist.template` to add a
`StartCalendarInterval` (an `Hour` key) if you want a guaranteed daily run
regardless of login frequency, then re-run `install.sh`.

To uninstall:

```bash
launchctl unload ~/Library/LaunchAgents/com.sfbiketrader-sd-monitor.plist
rm ~/Library/LaunchAgents/com.sfbiketrader-sd-monitor.plist
```

## Tests

```bash
python -m pytest
```
