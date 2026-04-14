#!/usr/bin/env bash
# tier3-obsidian.sh — Capture a screenshot of a note open in Obsidian.
# Requires macOS GUI, Obsidian installed, vault registered.
#
# Usage: tier3-obsidian.sh <output-dir> [--vault <name>] [--note <filename>]
# Defaults: vault from obsidian-cli print-default, note 20250612T110722584258000

set -euo pipefail

OUTPUT_DIR="${1:?usage: tier3-obsidian.sh <output-dir> [--vault <name>] [--note <filename>]}"
shift

VAULT=""
NOTE_NAME="20250612T110722584258000"  # "Investor-Driven AI Mandates..." — rich frontmatter

while [[ $# -gt 0 ]]; do
    case "$1" in
        --vault) VAULT="$2"; shift 2 ;;
        --note) NOTE_NAME="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

# Auto-detect default vault if not specified.
if [[ -z "$VAULT" ]]; then
    VAULT="$(obsidian-cli print-default 2>/dev/null | head -1 | awk '{print $1}')"
    if [[ -z "$VAULT" ]]; then
        echo "tier3: no vault specified and obsidian-cli has no default set" >&2
        echo "       run: obsidian-cli set-default <vault-name>" >&2
        exit 1
    fi
fi

echo "=== Tier 3: Obsidian screenshot ==="
echo "  Vault: $VAULT"
echo "  Note: $NOTE_NAME"
echo ""

mkdir -p "$OUTPUT_DIR"

# Close Obsidian cleanly if open (prevents stale windows).
if pgrep -q Obsidian; then
    osascript -e 'tell application "Obsidian" to quit' 2>/dev/null || true
    sleep 1
fi

# Open the note via obsidian-cli.
obsidian-cli open -v "$VAULT" "$NOTE_NAME"

# Wait for the window to render.
echo "  [tier3] waiting for Obsidian to open..."
for i in $(seq 1 10); do
    sleep 1
    if pgrep -q Obsidian; then
        break
    fi
done
sleep 2  # extra settle time for rendering

# Get the window ID via AppleScript.
WINDOW_ID=$(osascript -e '
    tell application "System Events"
        tell process "Obsidian"
            set frontWin to front window
            return id of frontWin
        end tell
    end tell
' 2>/dev/null || true)

OUTPUT_FILE="$OUTPUT_DIR/09-raw-markdown.png"

if [[ -n "$WINDOW_ID" ]]; then
    # screencapture with window ID — silent, no shadow.
    screencapture -x -o -l "$WINDOW_ID" "$OUTPUT_FILE"
else
    # Fallback: capture the frontmost window.
    echo "  [tier3] WARN: couldn't get window ID, capturing frontmost window" >&2
    screencapture -x -o -w "$OUTPUT_FILE"
fi

if [[ -s "$OUTPUT_FILE" ]]; then
    echo "  [tier3] 09-raw-markdown -> $OUTPUT_FILE"
else
    echo "  [tier3] ERROR: empty screenshot" >&2
    exit 1
fi

echo ""
echo "=== Tier 3 complete ==="
