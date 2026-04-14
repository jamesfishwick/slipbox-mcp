#!/usr/bin/env bash
# tier1-deterministic.sh — Capture mechanical demo screenshots that don't need
# Claude or the MCP server. Currently just the index rebuild shot.
#
# Usage: tier1-deterministic.sh <output-dir> [--base-dir <path>]
# Requires: uv, freeze

set -euo pipefail

OUTPUT_DIR="${1:?usage: tier1-deterministic.sh <output-dir> [--base-dir <path>]}"
shift
BASE_DIR=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --base-dir) BASE_DIR="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_DIR="${BASE_DIR:-$REPO_ROOT}"

export SLIPBOX_BASE_DIR="$BASE_DIR"
cd "$REPO_ROOT"

mkdir -p "$OUTPUT_DIR"

# Freeze styling — consistent across all shots.
FREEZE_OPTS=(
    --window
    --padding "20,40"
    --margin "0"
    --border.radius "8"
    --font.size "14"
    --width "800"
    --theme "dracula"
)

capture() {
    local name="$1"
    local cmd="$2"
    local output_file="$OUTPUT_DIR/$name.png"

    echo "  [tier1] $name ..."
    freeze -x "$cmd" "${FREEZE_OPTS[@]}" -o "$output_file"
    if [[ -s "$output_file" ]]; then
        echo "  [tier1] $name -> $output_file"
    else
        echo "  [tier1] ERROR: empty PNG for $name" >&2
        return 1
    fi
}

echo "=== Tier 1: Deterministic shots ==="
echo "  Base dir: $BASE_DIR"
echo ""

# --- #16: Index Rebuild ---
# Proves the safety guarantee: the SQLite index is always derivable from flat files.
capture "16-index-rebuild" "uv run slipbox --base-dir '$BASE_DIR' rebuild"

echo ""
echo "=== Tier 1 complete ==="
