# Install via Claude Code

If you have [Claude Code](https://claude.com/product/claude-code)
installed, this is the easiest path -- paste the prompt below into a new
Claude Code session (in Terminal, run `claude` in your home folder first)
and it'll walk you through everything, asking you for anything it needs
along the way. You don't need to know what any of the commands mean.

Don't have Claude Code yet? Ask Joe, or see
[claude.com/product/claude-code](https://claude.com/product/claude-code)
to install it first -- then come back and paste the prompt below.

If you'd rather do it by hand instead, use `SETUP.md` in this repo.

---

## The prompt (copy everything below)

```
Set up the sfbiketrader-sd-monitor project on this Mac for me. I'm not
familiar with the command line, so explain each step in plain language
before running it, and pause to ask me for anything you need rather than
guessing.

Here's the situation: this is a personal tool (not mine, a family
member's -- Joe's) that tracks bikes posted for sale on an Instagram
account and cross-references them against Craigslist/Facebook/OfferUp
listings in San Diego, writing everything to a Google Sheet that Joe and
I both use. I need my own local copy running so I can trigger refreshes
myself.

Please:

1. Check I have `git` and `python3` installed (`git --version`,
   `python3 --version`). If not, help me install them (Xcode Command Line
   Tools for git; python.org's installer for Python) before continuing.

2. Clone https://github.com/joemandozzi/sfbiketrader-sd-monitor into my
   home folder, then set up a Python virtual environment and install its
   dependencies (there's a requirements.txt).

3. Ask me to go get two things myself (you can't do these steps for me):
   - A free Apify account and API token (apify.com -> sign up -> Settings
     -> Integrations/API -> copy the token). This is what reads the
     Instagram posts.
   - A free Anthropic API key (console.anthropic.com -> sign up -> API
     Keys). This is what reads each caption and figures out the bike
     brand/model/price.
   Wait for me to paste both back to you.

4. Ask me where I saved the `service-account.json` (or similarly named)
   file Joe sent me -- I'll give you the full path. This is a shared
   credential for writing to our Google Sheet, so keep it out of any
   commit if you ever touch git status/add.

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
   - facebook.enabled = false (I'll set this up later myself if I want it --
     it needs its own one-time login step)

7. Run `python main.py --only ig` as a test, show me the output, and
   confirm it worked (it should print something like "Fetched N post(s)"
   with no error at the end).

8. Tell me about REFRESH.md in the repo -- that's what I'll use day to
   day after this initial setup.

Ask me questions any time you're unsure rather than assuming. Go.
```
