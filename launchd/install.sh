#!/bin/bash
# Installs this monitor as a macOS launchd job that runs once each time you
# log in / start your laptop (see the .plist.template's RunAtLoad comment).
# Safe to re-run after editing the .plist.template.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$REPO_DIR/.venv/bin/python3"
LABEL="com.sfbiketrader-sd-monitor"
PLIST_DEST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "No virtualenv found at $PYTHON_BIN"
    echo "Run this first: cd $REPO_DIR && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "$REPO_DIR/config.yaml" ]; then
    echo "Missing config.yaml in $REPO_DIR"
    echo "Copy config.example.yaml -> config.yaml and fill it in."
    exit 1
fi

sed -e "s#__PYTHON_BIN__#$PYTHON_BIN#g" -e "s#__REPO_DIR__#$REPO_DIR#g" \
    "$REPO_DIR/launchd/com.sfbiketrader-sd-monitor.plist.template" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Installed and loaded $LABEL."
echo "Logs: $REPO_DIR/data/monitor.log"
echo "To uninstall: launchctl unload $PLIST_DEST && rm $PLIST_DEST"
