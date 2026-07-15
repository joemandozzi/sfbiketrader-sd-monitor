# Refresh instructions

Once set up (see `SETUP.md` or `INSTALL_PROMPT.md` if you haven't done
that yet), refreshing the shared Google Sheet is two commands in Terminal.

Open Terminal, then every time:

```bash
cd ~/sfbiketrader-sd-monitor
source .venv/bin/activate
```

Then run either or both of:

```bash
python main.py --only ig
```
Checks Instagram for new posts from `@sfbiketrader` and logs them to the
"SF Bike Trader Frames" tab. Usually finishes in under a minute.

```bash
python main.py --only sd
```
Searches Craigslist/Facebook/OfferUp in San Diego for every bike frame
ever logged, and adds anything new to the "San Diego Matches" tab.
**This one is slow -- 30-60+ minutes is normal.** It prints progress as it
goes, so it's not stuck even if it looks quiet for a bit.

Check the [shared Google
Sheet](https://docs.google.com/spreadsheets/d/1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY/edit)
afterward for anything new.
