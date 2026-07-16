# Setup guide (for Mac, no coding experience needed)

This walks through getting this tool running on your own Mac, step by
step. It'll take maybe 20-30 minutes the first time. Everything here is
typed into an app called **Terminal** -- it looks intimidating but you're
just copying and pasting each block below, one at a time, and pressing
Return.

If anything doesn't look like what's described here, stop and ask rather
than guessing -- it's easy to fix if we catch it early.

(If you have Claude Code installed, `INSTALL_PROMPT.md` in this repo does
this same setup for you interactively -- you can use that instead and
skip this whole document.)

## 1. Open Terminal

Press `Cmd + Space` to open Spotlight search, type `Terminal`, press
Return. A plain window with white or black background and blinking cursor
opens -- that's it, that's Terminal.

## 2. Check if you have the basics installed

Paste this in and press Return:

```bash
git --version
```

- If you see something like `git version 2.x.x`, you're good, skip to
  step 3.
- If a popup appears asking to install "Command Line Tools," click
  **Install**, wait for it to finish (a few minutes), then run the same
  command again to confirm.

Next, check Python:

```bash
python3 --version
```

You want to see `Python 3.10` or higher. If you get an error instead, go
to [python.org/downloads](https://www.python.org/downloads/), download the
latest macOS installer, run it (click through like any other app
installer), then come back and run `python3 --version` again.

## 3. Download the code

Pick where you want this to live -- your home folder is simplest. Paste:

```bash
cd ~
git clone https://github.com/joemandozzi/sfbiketrader-sd-monitor.git
cd sfbiketrader-sd-monitor
```

This creates a folder called `sfbiketrader-sd-monitor` and moves you into
it. Every command from here on assumes you're still in this folder --
if you ever close Terminal and reopen it later, run `cd
~/sfbiketrader-sd-monitor` first to get back here.

## 4. Set up Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The last command installs everything this tool needs -- it'll print a lot
of text, that's normal. If it ends without a red "error" message, it
worked.

**Every time you reopen Terminal to use this tool later**, you need to run
`source .venv/bin/activate` again first (from inside the
`sfbiketrader-sd-monitor` folder) before the other commands will work.

## 5. Get your own Apify account (free)

This is the service that reads the Instagram posts.

1. Go to [apify.com](https://apify.com) and sign up (Google/GitHub login
   works, no credit card needed).
2. Once logged in, go to **Settings -> Integrations** (or **API**) and
   copy your personal API token -- a long string of letters/numbers.
3. Keep it somewhere safe for a minute, you'll paste it in step 8.

## 6. Get your own Anthropic API key

This is what reads each Instagram caption and figures out the bike
brand/model/price.

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign
   up.
2. Go to **API Keys**, create a new key, and copy it.

## 7. Create your own Google service account

This is what actually writes to the shared Google Sheet. You're creating
your **own** one here rather than receiving someone else's credential
file -- that way your access is scoped to only this one sheet, not
anything else the sheet owner manages.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and
   sign in. Create a new project (top-left project dropdown -> "New
   Project"), name it anything (e.g. "sfbiketrader"), click Create.
2. Once it's created and selected, use the search bar at the top to find
   **Google Sheets API**, open it, click **Enable**. Do the same for
   **Google Drive API**.
3. Go to **IAM & Admin -> Service Accounts** (search bar works here too),
   click **Create Service Account**, give it any name (e.g.
   "sfbiketrader-sheets"), click **Create and Continue**, then **Done**
   (no roles needed).
4. Click into the service account you just created, go to the **Keys**
   tab, click **Add Key -> Create New Key**, choose **JSON**, click
   **Create**. A file downloads (usually to your Downloads folder).
   Move it somewhere you'll remember (e.g. Documents) and note the full
   path.
5. On that same service account's page, copy its **email address** --
   it looks like `something@your-project-id.iam.gserviceaccount.com`.
   **Send this email address (not the JSON file) to whoever manages the
   shared spreadsheet** -- they need to open the Sheet, click **Share**,
   and add that email as an **Editor**. Wait for them to confirm they've
   done this before moving on to step 9.

## 8. Fill in your settings

Paste these to create your own local copies of two settings files:

```bash
cp .env.example .env
cp config.example.yaml config.yaml
```

Now open `.env` in a text editor -- easiest way from Terminal:

```bash
open -e .env
```

Fill in:
- `APIFY_API_TOKEN` -- from step 5
- `ANTHROPIC_API_KEY` -- from step 6
- `GOOGLE_SERVICE_ACCOUNT_JSON` -- the full path to the file from step 7
- `GOOGLE_SHEET_ID` -- `1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY`
  (the shared sheet)

Save and close the file (`Cmd + S`, then close the window).

Now open `config.yaml` the same way:

```bash
open -e config.yaml
```

Set these values to match the shared setup (so you're searching the same
account/area):

```yaml
instagram:
  profile: "sfbiketrader"

san_diego:
  zip: "92101"
  radius_miles: 50

offerup:
  enabled: true

facebook:
  enabled: false
```

Leave `facebook.enabled` as `false` for now -- that one needs an extra
one-time login step you can do later if you want it.

## 9. Run it

Make sure the sheet owner has confirmed they've added your service
account's email as an Editor (step 7.5) before running this -- otherwise
you'll get a permissions error.

Back in Terminal (make sure you did `source .venv/bin/activate` from step
4 if you closed/reopened Terminal since then):

```bash
python main.py --only ig
```

This checks Instagram for new posts and logs them to the shared sheet.
It should finish in well under a minute most days.

```bash
python main.py --only sd
```

This searches Craigslist/OfferUp in San Diego for every bike frame ever
logged. **This one is slow** -- it can take 30-60+ minutes since it checks
every known frame one at a time. That's normal, just let it run; you'll
see it printing progress as it goes.

You can check the [shared Google
Sheet](https://docs.google.com/spreadsheets/d/1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY/edit)
afterward to see anything new that showed up.

## If something goes wrong

Copy the exact error message you see and send it over -- almost
everything here is fixable, it's just easier with the exact wording of
whatever it printed.
