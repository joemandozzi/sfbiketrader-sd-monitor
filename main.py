#!/usr/bin/env python3
"""Entry point: pull new frame-for-sale posts from an Instagram marketplace
account, log them to a Google Sheet, then search San Diego Craigslist,
Facebook Marketplace, and OfferUp (the latter two if enabled in
config.yaml) for every distinct frame ever seen, logging new matches to a
second tab.

Run manually with `python3 main.py`, schedule it (see README.md), or run
just one half with `--only ig` / `--only sd` (see the "Instructions" tab
in the Sheet for the exact commands to trigger a manual refresh).
"""
import argparse
import sys
import time
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from sfmonitor import apify_client, extract, matcher, sheets
from sfmonitor.craigslist import search_craigslist

ROOT = Path(__file__).resolve().parent
SD_SEARCH_DELAY_SECONDS = 1.5


def load_config():
    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        sys.exit("config.yaml not found. Copy config.example.yaml to config.yaml and fill it in.")
    with open(config_path) as f:
        return yaml.safe_load(f)


def collect_ig_frames(config, sheet: sheets.SheetHandles):
    """Fetch new IG posts, extract frame mentions, log them, and return the
    full set of distinct (brand, model) pairs seen across all runs.

    "Already processed" is derived from the frames tab itself (not a local
    file), since this Sheet can be shared across multiple machines -- the
    Sheet's current contents are the only source of truth both machines
    agree on. One accepted tradeoff: a caption with zero extractable
    frames never gets a row here, so it has no URL to dedupe against and
    will be re-fetched/re-sent through extraction every run it's still
    within `fetch_limit`'s recent window. Bounded, cheap cost -- not worth
    a second shared "processed post IDs" tracking mechanism just to skip
    a minority case.
    """
    profile_url = f"https://www.instagram.com/{config['instagram']['profile']}/"
    limit = config["instagram"].get("fetch_limit", 25)

    print(f"Fetching up to {limit} recent posts from {profile_url}...")
    posts = apify_client.fetch_posts(profile_url, limit)
    print(f"Fetched {len(posts)} post(s).")

    seen_urls = {row[1] for row in sheet.get_frame_rows() if row[1]}
    new_posts = [p for p in posts if p.url not in seen_urls]
    print(f"{len(new_posts)} new post(s) to process ({len(posts) - len(new_posts)} already seen).")

    new_frames = set()
    for post in new_posts:
        frames = extract.extract_frame_info(post.caption)
        for frame in frames:
            sheet.append_frame_row(
                post.timestamp, post.url, frame.brand, frame.model, frame.frame_size, frame.price, frame.condition
            )
            if frame.brand and frame.model:
                new_frames.add((frame.brand, frame.model))

    all_frames = sheets.frame_keys(sheet.get_frame_rows())
    print(f"{len(new_frames)} new distinct frame(s) this run, {len(all_frames)} known in total.")
    return all_frames


def search_san_diego(frames, config, sheet: sheets.SheetHandles):
    zip_code = config["san_diego"]["zip"]
    radius = config["san_diego"]["radius_miles"]
    facebook_enabled = config.get("facebook", {}).get("enabled", False)
    offerup_enabled = config.get("offerup", {}).get("enabled", False)

    # Read once up front rather than per-frame -- same shared-source-of-truth
    # reasoning as collect_ig_frames: this Sheet can be written to by more
    # than one machine, so "already seen" always comes from its current
    # contents, not a local file. Updated in-memory as we go so two
    # different frame keywords matching the same listing in one run don't
    # double-log it.
    seen_urls = sheet.get_match_urls()

    with ExitStack() as stack:
        fb_session = None
        offerup_session = None
        if facebook_enabled or offerup_enabled:
            # Playwright's sync API only supports one active driver per
            # thread, so Facebook and OfferUp (both Playwright-based) share
            # a single instance rather than each starting their own.
            from playwright.sync_api import sync_playwright

            playwright = stack.enter_context(sync_playwright())

            if facebook_enabled:
                from sfmonitor.facebook import FacebookLoginRequiredError, FacebookSession

                try:
                    fb_session = stack.enter_context(FacebookSession(playwright))
                except FacebookLoginRequiredError as exc:
                    print(f"  [warn] skipping facebook this run: {exc}", file=sys.stderr)
            if offerup_enabled:
                from sfmonitor.offerup import OfferUpSession

                offerup_session = stack.enter_context(OfferUpSession(playwright, zip_code))

        total_new = 0
        for brand, model in sorted(frames):
            keyword = f"{brand} {model}"
            candidates = []

            try:
                candidates += search_craigslist(keyword, zip_code, radius)
            except Exception as exc:
                print(f"  [warn] craigslist search failed for {keyword!r}: {exc}", file=sys.stderr)

            if fb_session is not None:
                try:
                    candidates += fb_session.search(keyword, radius)
                except Exception as exc:
                    print(f"  [warn] facebook search failed for {keyword!r}: {exc}", file=sys.stderr)

            if offerup_session is not None:
                try:
                    candidates += offerup_session.search(keyword, radius)
                except Exception as exc:
                    print(f"  [warn] offerup search failed for {keyword!r}: {exc}", file=sys.stderr)

            candidates = [c for c in candidates if matcher.title_matches_keyword(c["title"], keyword)]
            unseen = [c for c in candidates if c["url"] not in seen_urls]
            print(f"  {keyword!r}: {len(candidates)} candidate(s), {len(unseen)} new")

            for item in unseen:
                sheet.append_match_row(
                    brand, model, item["source"], item["title"], item.get("price"), item.get("location"), item["url"]
                )
                seen_urls.add(item["url"])
            total_new += len(unseen)
            time.sleep(SD_SEARCH_DELAY_SECONDS)

    if total_new:
        sheet.sort_matches_by_date_added()

    return total_new


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh the SF Bike Trader / San Diego monitor Google Sheet."
    )
    parser.add_argument(
        "--only",
        choices=["ig", "sd"],
        help='Run only the Instagram scrape ("ig") or only the San Diego '
        'search ("sd") instead of both. Omit to run the full pipeline.',
    )
    return parser


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    run_ig = args.only in (None, "ig")
    run_sd = args.only in (None, "sd")

    run_started = datetime.now()
    print(f"=== run started {run_started.isoformat(timespec='seconds')} ===")

    config = load_config()
    try:
        sheet = sheets.SheetHandles()
    except sheets.SheetsConfigError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Google Sheet: {sheet.url}")

    if run_ig:
        try:
            all_frames = collect_ig_frames(config, sheet)
        except (apify_client.ApifyConfigError, extract.ExtractConfigError) as exc:
            print(f"Error: {exc}")
            return 1
        sheet.write_frame_counts()
    else:
        all_frames = sheets.frame_keys(sheet.get_frame_rows())

    if run_sd:
        if all_frames:
            print(f"Searching San Diego for {len(all_frames)} known frame(s)...")
            total_new = search_san_diego(all_frames, config, sheet)
            print(f"{total_new} new San Diego match(es) logged.")
        else:
            print("No known frames yet -- nothing to search San Diego for.")

    print(f"=== run finished {datetime.now().isoformat(timespec='seconds')} ===")
    return 0


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    sys.exit(main())
