# Install via Claude Code

If you have [Claude Code](https://claude.com/product/claude-code)
installed, this is the easiest path -- paste the prompt below into a new
Claude Code session (open Terminal, run `claude`) and it'll walk you
through everything, adjusting how much it explains based on how familiar
you already are with this kind of setup.

Don't have Claude Code yet? See
[claude.com/product/claude-code](https://claude.com/product/claude-code)
to install it first, then come back and paste the prompt below. Or, if
you'd rather do this by hand instead, use `SETUP.md` in this repo.

---

## The prompt (copy everything below)

```
Set up the sfbiketrader-sd-monitor project on this computer for me:
https://github.com/joemandozzi/sfbiketrader-sd-monitor

First, ask me how familiar I am with things like Terminal, git/GitHub,
and installing developer tools. Based on my answer:
- If I'm experienced: move through setup quickly, just flagging each
  step before you run it.
- If I'm new to this: don't assume I know anything. Explain what
  Terminal is and how to open it, what a "repository" is, what a
  Python virtual environment is for, etc., in plain language, before
  each step -- and check in with me before moving on if a step doesn't
  look like what you described.

Here's the situation: this is a personal tool that tracks bikes posted
for sale on an Instagram account and cross-references them against
Craigslist/Facebook/OfferUp listings in San Diego, writing everything to
a shared Google Sheet. I need my own local copy set up so I can trigger
refreshes myself, using the same shared Sheet someone else already set
up.

Please:

1. Check whether I have `git` and `python3` installed (`git --version`,
   `python3 --version`). If not, help me install them (on a Mac: Xcode
   Command Line Tools for git -- running `git --version` with git
   missing triggers a one-click install prompt; python.org's installer
   for Python).

2. Clone the repo above into my home folder, then set up a Python
   virtual environment and install its dependencies (there's a
   requirements.txt).

3. Ask me to go get two things myself (you can't do these steps for me):
   - A free Apify account and API token (apify.com -> sign up -> Settings
     -> Integrations/API -> copy the token). This is what reads the
     Instagram posts.
   - A free Anthropic API key (console.anthropic.com -> sign up -> API
     Keys). This is what reads each caption and figures out the bike
     brand/model/price.
   Wait for me to paste both back to you.

4. Walk me through creating my own Google service account for writing to
   the shared Sheet (don't have me use someone else's credential file --
   a service account I create myself only ever has access to the one
   sheet I explicitly get added to, not anything else the sheet owner
   manages). You can't click through Google Cloud Console for me, so
   narrate each step and wait for me to confirm before moving on:
   a. Go to console.cloud.google.com and create a new project (or pick
      an existing one).
   b. Enable the "Google Sheets API" and "Google Drive API" for it
      (search each by name, click Enable).
   c. Go to IAM & Admin -> Service Accounts -> Create Service Account,
      give it any name, click through without adding any roles.
   d. Open the new service account -> Keys tab -> Add Key -> Create New
      Key -> JSON -> Create. This downloads a JSON file (usually to
      Downloads) -- help me move it somewhere sensible and note the
      full path.
   e. Show me the service account's email (looks like
      something@project-id.iam.gserviceaccount.com -- visible on its
      details page, or as "client_email" inside the downloaded JSON).
      I need to send that email address (not the file -- the file
      never leaves my machine) to whoever manages the shared
      spreadsheet, so they can add it as an Editor via Google Sheets'
      Share dialog. Tell me to do that and wait for their confirmation
      before continuing.

5. Create `.env` (copy from `.env.example`) and fill in:
   - APIFY_API_TOKEN = the token from step 3
   - ANTHROPIC_API_KEY = the key from step 3
   - GOOGLE_SERVICE_ACCOUNT_JSON = the path to the key file from step 4
   - GOOGLE_SHEET_ID = 1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY

6. Create `config.yaml` (copy from `config.example.yaml`) and set:
   - instagram.profile = "sfbiketrader"
   - san_diego.zip = "92101"
   - san_diego.radius_miles = 50
   - offerup.enabled = true
   - facebook.enabled = false (can be set up later -- it needs its own
     one-time login step, see facebook_login.py)

7. Once the sheet owner confirms they've added my service account as an
   Editor, run `python main.py --only ig` as a test, show me the output,
   and confirm it worked (it should print something like "Fetched N
   post(s)" with no error at the end -- a permissions error here usually
   means the sheet owner hasn't finished sharing it with my service
   account's email yet).

8. Tell me about REFRESH.md in the repo -- that's what I'll use day to
   day after this initial setup.

Ask me questions any time you're unsure rather than assuming. Go.
```
