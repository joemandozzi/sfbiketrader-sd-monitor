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

4. Ask me where I saved the Google service-account credentials file
   (something like `service-account.json`) that whoever manages the
   shared spreadsheet sent me -- I'll give you the full path. This is a
   password-like credential for writing to that shared Sheet, so keep it
   out of any commit if you ever touch git status/add, and don't print
   its contents.

5. Create `.env` (copy from `.env.example`) and fill in:
   - APIFY_API_TOKEN = the token from step 3
   - ANTHROPIC_API_KEY = the key from step 3
   - GOOGLE_SERVICE_ACCOUNT_JSON = the path from step 4
   - GOOGLE_SHEET_ID = 1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY

6. Create `config.yaml` (copy from `config.example.yaml`) and set:
   - instagram.profile = "sfbiketrader"
   - san_diego.zip = "92101"
   - san_diego.radius_miles = 50
   - offerup.enabled = true
   - facebook.enabled = false (can be set up later -- it needs its own
     one-time login step, see facebook_login.py)

7. Run `python main.py --only ig` as a test, show me the output, and
   confirm it worked (it should print something like "Fetched N post(s)"
   with no error at the end).

8. Tell me about REFRESH.md in the repo -- that's what I'll use day to
   day after this initial setup.

Ask me questions any time you're unsure rather than assuming. Go.
```
