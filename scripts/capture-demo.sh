#!/usr/bin/env bash
# capture-demo.sh — Automated screenshot pipeline for slipbox-mcp README.
#
# Produces 17 screenshots demonstrating every differentiating MCP tool and prompt.
# Three tiers:
#   1. Deterministic (slipbox CLI + freeze) — no network/GUI needed
#   2. Claude subprocess (claude -p + MCP + freeze) — needs API key
#   3. Obsidian window capture (obsidian-cli + screencapture) — needs macOS GUI
#
# Usage:
#   ./scripts/capture-demo.sh                        # all tiers (skip obsidian)
#   ./scripts/capture-demo.sh --tier 1               # deterministic only
#   ./scripts/capture-demo.sh --tier 2               # claude shots only
#   ./scripts/capture-demo.sh --with-obsidian        # include tier 3
#   ./scripts/capture-demo.sh --update-demo-md       # also refresh demo.md output blocks
#   ./scripts/capture-demo.sh --fixture-dir /tmp/x   # custom fixture location

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LIB_DIR="$SCRIPTS_DIR/lib"
OUTPUT_DIR="$REPO_ROOT/assets/screenshots"

TIER="all"
WITH_OBSIDIAN=false
UPDATE_DEMO_MD=false
FIXTURE_DIR="/tmp/slipbox-demo-fixture"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tier) TIER="$2"; shift 2 ;;
        --with-obsidian) WITH_OBSIDIAN=true; shift ;;
        --update-demo-md) UPDATE_DEMO_MD=true; shift ;;
        --fixture-dir) FIXTURE_DIR="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            head -16 "$0" | tail -14
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

# ── Preflight checks ────────────────────────────────────────────
check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "ERROR: '$1' not found. Install it first." >&2
        return 1
    fi
}

check_cmd freeze
check_cmd uv

run_tier1=false
run_tier2=false

case "$TIER" in
    1)   run_tier1=true ;;
    2)   run_tier2=true ;;
    3)
        if ! $WITH_OBSIDIAN; then
            echo "Tier 3 requires --with-obsidian flag" >&2
            exit 1
        fi
        ;;
    all) run_tier1=true; run_tier2=true ;;
    *)   echo "Unknown tier: $TIER (expected 1, 2, 3, or all)" >&2; exit 1 ;;
esac

if $run_tier2; then
    check_cmd claude
fi

if $WITH_OBSIDIAN; then
    check_cmd obsidian-cli
    check_cmd screencapture
fi

# ── Setup ────────────────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

# Fixture is needed by tier 2 (mutating shots). Tier 1 reads live data directly.
FIXTURE_READY=false
ensure_fixture() {
    if ! $FIXTURE_READY; then
        echo "Snapshotting fixture..."
        bash "$LIB_DIR/snapshot-fixture.sh" "$FIXTURE_DIR"
        FIXTURE_READY=true
    fi
}

# Cleanup fixture on exit (only if we created it).
cleanup() {
    if $FIXTURE_READY; then
        echo "Cleaning up fixture at $FIXTURE_DIR"
        rm -rf "$FIXTURE_DIR"
    fi
}
trap cleanup EXIT

# ── Tier 1: Deterministic ──────────────────────────────────────
if $run_tier1; then
    bash "$LIB_DIR/tier1-deterministic.sh" "$OUTPUT_DIR"
fi

# ── Tier 2: Claude subprocess ──────────────────────────────────
if $run_tier2; then
    ensure_fixture
    bash "$LIB_DIR/tier2-claude.sh" "$FIXTURE_DIR" "$OUTPUT_DIR"
fi

# ── Tier 3: Obsidian ──────────────────────────────────────────
if $WITH_OBSIDIAN; then
    bash "$LIB_DIR/tier3-obsidian.sh" "$OUTPUT_DIR"
fi

# ── Showboat block refresh ─────────────────────────────────────
if $UPDATE_DEMO_MD; then
    echo ""
    echo "=== Refreshing demo.md output blocks ==="
    uv run python "$LIB_DIR/update-demo-blocks.py"
fi

# ── Coverage assertion ─────────────────────────────────────────
echo ""
echo "=== Coverage check ==="

# Coverage map: tool_name:screenshot_name (one per line).
# We maintain an explicit map because tier 1 uses the slipbox CLI (wraps tools)
# and tier 2 prompts describe operations in natural language.
COVERAGE_MAP="
slipbox_search_notes:02-search
slipbox_find_central_notes:03-central-notes
slipbox_get_cluster_report:07-cluster-report
slipbox_find_orphaned_notes:10-orphans
slipbox_find_similar_notes:11-similar-notes
slipbox_get_linked_notes:12-linked-notes
slipbox_get_all_tags:13-tag-taxonomy
slipbox_list_notes_by_date:14-date-browsing
slipbox_rebuild_index:16-index-rebuild
slipbox_create_note:04-idea-capture
slipbox_create_link:04-idea-capture
slipbox_create_structure_from_cluster:08-structure-note
"

# Tools intentionally not covered (mechanical CRUD / housekeeping).
SKIP_TOOLS="slipbox_update_note slipbox_delete_note slipbox_remove_link slipbox_refresh_clusters slipbox_dismiss_cluster slipbox_get_note"

# Extract all tool names from server code.
TOOL_DIR="$REPO_ROOT/src/slipbox_mcp/server/tools"
ALL_TOOLS=$(grep -ohE 'name="(slipbox_\w+)"' "$TOOL_DIR"/*.py | sed 's/name="//;s/"//' | sort)

missing_count=0
for tool in $ALL_TOOLS; do
    # Skip intentionally excluded tools.
    skip=false
    for st in $SKIP_TOOLS; do
        if [[ "$tool" == "$st" ]]; then skip=true; break; fi
    done
    $skip && continue

    # Look up in coverage map.
    shot=$(echo "$COVERAGE_MAP" | grep "^${tool}:" | head -1 | cut -d: -f2)
    if [[ -z "$shot" ]]; then
        echo "  WARN: $tool not covered by any screenshot" >&2
        missing_count=$((missing_count + 1))
    elif [[ ! -f "$OUTPUT_DIR/${shot}.png" ]]; then
        echo "  NOTE: $tool -> ${shot}.png (not yet generated)"
    fi
done

if [[ $missing_count -eq 0 ]]; then
    echo "  All differentiating tools are covered."
fi

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "=== Summary ==="
COUNT=$(find "$OUTPUT_DIR" -name '*.png' -type f | wc -l | tr -d ' ')
echo "  Screenshots: $COUNT in $OUTPUT_DIR"
echo ""
find "$OUTPUT_DIR" -name '*.png' -type f | sort | while read -r f; do
    SIZE=$(du -h "$f" | cut -f1)
    echo "  $SIZE  $(basename "$f")"
done
echo ""

# Verify fixture isolation — live data/ must be unchanged.
if ! git -C "$REPO_ROOT" diff --quiet data/ 2>/dev/null; then
    echo "  WARNING: data/ directory was modified! Fixture isolation may have failed." >&2
    exit 1
fi

echo "Done."
