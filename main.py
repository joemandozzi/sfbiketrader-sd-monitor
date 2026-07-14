#!/usr/bin/env python3
"""Entry point: pull new frame-for-sale posts from an Instagram marketplace
account, log them to a Google Sheet, then search San Diego Craigslist (and
Facebook Marketplace, if a login session exists) for every distinct frame
ever seen, logging new matches to a second tab.

Run manually with `python3 main.py`, or schedule it (see README.md).
"""
import sys
import time
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import yaml

from sfmonitor import apify_client, extract, ig_state, known_frames, matcher, sd_state, sheets
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
    full set of distinct (brand, model) pairs seen across all runs."""
    profile_url = f"https://www.instagram.com/{config['instagram']['profile']}/"
    limit = config["instagram"].get("fetch_limit", 25)

    print(f"Fetching up to {limit} recent posts from {profile_url}...")
    posts = apify_client.fetch_posts(profile_url, limit)
    print(f"Fetched {len(posts)} post(s).")

    seen = ig_state.load_seen()
    new_posts = [p for p in posts if p.post_id not in seen]
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

    if new_posts:
        ig_state.mark_seen([p.post_id for p in new_posts])

    known_frames.add_known_frames(new_frames)
    all_frames = known_frames.load_known_frames()
    print(f"{len(new_frames)} new distinct frame(s) this run, {len(all_frames)} known in total.")
    return all_frames


def search_san_diego(frames, config, sheet: sheets.SheetHandles):
    zip_code = config["san_diego"]["zip"]
    radius = config["san_diego"]["radius_miles"]
    facebook_enabled = config.get("facebook", {}).get("enabled", False)

    with ExitStack() as stack:
        fb_session = None
        if facebook_enabled:
            from playwright.sync_api import sync_playwright

            from sfmonitor.facebook import FacebookSession

            playwright = stack.enter_context(sync_playwright())
            fb_session = stack.enter_context(FacebookSession(playwright))

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

            candidates = [c for c in candidates if matcher.title_matches_keyword(c["title"], keyword)]
            unseen = sd_state.filter_unseen(candidates)
            print(f"  {keyword!r}: {len(candidates)} candidate(s), {len(unseen)} new")

            for item in unseen:
                sheet.append_match_row(
                    brand, model, item["source"], item["title"], item.get("price"), item.get("location"), item["url"]
                )
            sd_state.mark_seen(unseen)
            total_new += len(unseen)
            time.sleep(SD_SEARCH_DELAY_SECONDS)

    return total_new


def main() -> int:
    run_started = datetime.now()
    print(f"=== run started {run_started.isoformat(timespec='seconds')} ===")

    config = load_config()
    try:
        sheet = sheets.SheetHandles()
    except sheets.SheetsConfigError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Google Sheet: {sheet.url}")

    try:
        all_frames = collect_ig_frames(config, sheet)
    except (apify_client.ApifyConfigError, extract.ExtractConfigError) as exc:
        print(f"Error: {exc}")
        return 1

    if all_frames:
        print(f"Searching San Diego for {len(all_frames)} known frame(s)...")
        total_new = search_san_diego(all_frames, config, sheet)
        print(f"{total_new} new San Diego match(es) logged.")
    else:
        print("No known frames yet -- nothing to search San Diego for.")

    print(f"=== run finished {datetime.now().isoformat(timespec='seconds')} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
