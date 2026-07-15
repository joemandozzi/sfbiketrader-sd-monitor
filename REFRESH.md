# Refresh instructions

Once set up (see `SETUP.md` or `INSTALL_PROMPT.md` if you haven't done
that yet), refreshing the shared Google Sheet is two **completely
independent** commands in Terminal -- each one works fine without the
other, in any order, on any schedule.

Open Terminal, then every time:

```bash
cd ~/sfbiketrader-sd-monitor
source .venv/bin/activate
```

## 1) Instagram scrape -- needs Apify

```bash
python main.py --only ig
```
Checks Instagram for new posts from `@sfbiketrader` and logs new bike
frames to the "SF Bike Trader Frames" tab. Usually finishes in under a
minute. **This is the only one of the two that calls Apify** -- if your
Apify account or credit has an issue, this command will fail, but that
has no effect on the San Diego search below.

## 2) San Diego resale search -- no Apify needed

```bash
python main.py --only sd
```
Searches Craigslist/Facebook/OfferUp in San Diego for every bike frame
*already sitting in the Frames tab*, and adds anything new to the "San
Diego Matches" tab. Doesn't touch Instagram or Apify at all -- it just
works off whatever frames are already logged, so it runs fine even if the
Instagram side above is broken or hasn't been run in a while.
**This one is slow -- 30-60+ minutes is normal.** It prints progress as it
goes, so it's not stuck even if it looks quiet for a bit.

---

Neither command deletes or overwrites existing rows in the Frames or
Matches tabs -- they only add rows for things not already logged. (The
Frame Counts tab is the one exception: it's a live leaderboard recomputed
fresh from the Frames tab every run, not an append log.)

Check the [shared Google
Sheet](https://docs.google.com/spreadsheets/d/1_F4eCWdlerA0RN4FlhEsAHNzBDsmZ-Q5pmfwnBEmbtY/edit)
afterward for anything new.
