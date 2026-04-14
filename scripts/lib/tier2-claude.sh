#!/usr/bin/env bash
# tier2-claude.sh — Run Claude subprocess against slipbox-mcp fixture to capture
# demo responses. Saves raw text for injection into demo.md and renders PNGs
# for the README "In Action" section.
#
# Usage: tier2-claude.sh <fixture-dir> <output-dir>
# Requires: claude CLI, freeze, uv

set -euo pipefail

FIXTURE_DIR="${1:?usage: tier2-claude.sh <fixture-dir> <output-dir>}"
OUTPUT_DIR="${2:?usage: tier2-claude.sh <fixture-dir> <output-dir>}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
PROMPTS_DIR="$SCRIPTS_DIR/demo-prompts"

# Safety: refuse to run unless fixture is under /tmp.
case "$FIXTURE_DIR" in
    /tmp/*|/private/tmp/*) ;;
    *)
        echo "tier2: refusing to run against '$FIXTURE_DIR' (must be under /tmp)" >&2
        exit 2
        ;;
esac

# Generate a live MCP config from template with real paths.
MCP_CONFIG="/tmp/demo-mcp-$$.json"
trap 'rm -f "$MCP_CONFIG"' EXIT

python3 -c "
import sys
with open('$SCRIPTS_DIR/demo-mcp.json.template') as f:
    c = f.read()
c = c.replace('REPO_ROOT_PLACEHOLDER', '$REPO_ROOT')
c = c.replace('FIXTURE_DIR_PLACEHOLDER', '$FIXTURE_DIR')
with open('$MCP_CONFIG', 'w') as f:
    f.write(c)
"

mkdir -p "$OUTPUT_DIR"

# Shots that need PNGs for README (the rest are inline-only in demo.md).
README_SHOTS="01-maintenance 02-search 03-central-notes 04-idea-capture 05-analyze-note 06-source-decomposition 07-cluster-report 08-structure-note 10-orphans 11-similar-notes 12-linked-notes 17-knowledge-synthesis"

# Freeze styling for README PNGs.
FREEZE_FLAGS=(
    --window
    --padding "20,40"
    --margin "0"
    --border.radius "8"
    --font.size "14"
    --width "800"
    --theme "dracula"
)

run_shot() {
    local prompt_file="$1"
    local shot_name="$2"
    local text_file="/tmp/demo-shot-${shot_name}.txt"

    echo "  [tier2] $shot_name ..."

    # Invoke Claude in non-interactive mode with strict MCP config.
    if ! claude -p "$(cat "$prompt_file")" \
        --bare \
        --strict-mcp-config \
        --mcp-config "$MCP_CONFIG" \
        --allowedTools "mcp__slipbox-mcp__*" \
        --output-format text \
        > "$text_file" 2>/dev/null; then
        echo "  [tier2] WARN: claude returned non-zero for $shot_name" >&2
    fi

    # Sanity check: is the output non-trivial?
    local char_count
    char_count=$(wc -c < "$text_file" | tr -d ' ')
    if [[ "$char_count" -lt 100 ]]; then
        echo "  [tier2] WARN: suspiciously short output for $shot_name ($char_count bytes)" >&2
    fi

    echo "  [tier2] $shot_name -> $text_file"

    # Render PNG only for shots referenced in README.
    if echo "$README_SHOTS" | grep -qw "$shot_name"; then
        local output_file="$OUTPUT_DIR/$shot_name.png"
        freeze "$text_file" "${FREEZE_FLAGS[@]}" --language "md" -o "$output_file"
        if [[ -s "$output_file" ]]; then
            echo "  [tier2] $shot_name -> $output_file (README)"
        fi
    fi
}

echo "=== Tier 2: Claude MCP shots ==="
echo "  Fixture: $FIXTURE_DIR"
echo "  MCP config: $MCP_CONFIG"
echo ""

# Process each prompt file.
for prompt_file in "$PROMPTS_DIR"/*.txt; do
    basename="$(basename "$prompt_file" .txt)"
    run_shot "$prompt_file" "$basename"
done

# Inject responses into demo.md as <details> blocks.
echo ""
echo "  [tier2] Injecting responses into demo.md ..."
python3 "$SCRIPTS_DIR/lib/inject-responses.py" "$REPO_ROOT/demo.md" /tmp/demo-shot

echo ""
echo "=== Tier 2 complete ==="
