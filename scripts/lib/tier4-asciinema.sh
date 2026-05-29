#!/usr/bin/env bash
# tier4-asciinema.sh — Record animated GIF demos of slipbox-mcp tools.
#
# Records tier1 (deterministic CLI) and tier2 (Claude MCP) shots as .cast files,
# then converts to .gif via agg. Uses the curated demo vault fixture so every
# recording produces a compelling, full-throated example.
#
# Usage: tier4-asciinema.sh <fixture-dir> <output-dir>
# Requires: asciinema, agg, uv, claude

set -euo pipefail

FIXTURE_DIR="${1:?usage: tier4-asciinema.sh <fixture-dir> <output-dir>}"
OUTPUT_DIR="${2:?usage: tier4-asciinema.sh <fixture-dir> <output-dir>}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
PROMPTS_DIR="$SCRIPTS_DIR/demo-prompts"

# Use full paths — shell aliases may shadow these binaries.
AGG=/opt/homebrew/bin/agg
GIFSICLE=/opt/homebrew/bin/gifsicle

# Safety: refuse to run against live data.
case "$FIXTURE_DIR" in
    /tmp/*|/private/tmp/*) ;;
    *)
        echo "tier4: refusing to run against '$FIXTURE_DIR' (must be under /tmp)" >&2
        exit 2
        ;;
esac

mkdir -p "$OUTPUT_DIR"

# Shared agg flags — matches freeze/dracula styling used for PNGs.
# --speed 1.0: real-time playback so the slow-print reveal in the wrapper
#   scripts isn't re-accelerated.
# --idle-time-limit 1: cap pauses at 1s (the wrappers fill dead time with
#   a "thinking" indicator).
# --last-frame-duration 5: pause 5s on final frame so the viewer can read.
# --font-size 11 / cols 88 / rows 32: smaller cell size keeps GIFs slim
#   (~70% size reduction vs 14pt/100x40, ~30% vs 12pt/96x36) while staying
#   readable. For the worst-case 70+ line response this is the difference
#   between a 5.1MB and a 1.6MB GIF.
AGG_FLAGS=(
    --theme dracula
    --font-size 11
    --speed 1.0
    --idle-time-limit 1
    --last-frame-duration 5
    --cols 88
    --rows 32
)

# ── record_shot <cast> <gif> <wrapper-script> [title] ──────────
# Runs <wrapper-script> under asciinema, then converts to GIF.
# Using a wrapper script avoids quoting issues with prompts that contain
# newlines, single quotes, and other special characters.
record_shot() {
    local cast_file="$1"
    local gif_file="$2"
    local wrapper="$3"
    local title="${4:-$(basename "$gif_file" .gif)}"

    echo "  [tier4] recording $title ..."
    asciinema rec \
        --overwrite \
        --quiet \
        --output-format asciicast-v2 \
        --idle-time-limit 1 \
        --window-size "88x32" \
        --title "$title" \
        --command "bash $wrapper" \
        "$cast_file"

    echo "  [tier4] converting $(basename "$cast_file") -> $(basename "$gif_file") ..."
    "$AGG" "${AGG_FLAGS[@]}" "$cast_file" "$gif_file"

    # gifsicle -O3 deduplicates frames and tightens encoding (~19% savings).
    # --lossy is omitted intentionally: agg emits local colormaps per frame,
    # which prevents lossy color reduction from helping (often INCREASES size).
    local before_size
    before_size=$(du -k "$gif_file" | cut -f1)
    "$GIFSICLE" -O3 --batch "$gif_file"

    if [[ -s "$gif_file" ]]; then
        local size
        size=$(du -h "$gif_file" | cut -f1)
        local after_size
        after_size=$(du -k "$gif_file" | cut -f1)
        local pct=$(( 100 * (before_size - after_size) / (before_size > 0 ? before_size : 1) ))
        echo "  [tier4] done: $(basename "$gif_file") ($size, ${pct}% smaller after gifsicle)"
    else
        echo "  [tier4] ERROR: empty GIF for $(basename "$gif_file")" >&2
        return 1
    fi
}

# ── Tier 1: Deterministic CLI shots ────────────────────────────
record_tier1() {
    local base_dir="$FIXTURE_DIR"
    cd "$REPO_ROOT"

    echo "=== Tier 4 / CLI shots ==="
    echo "  Base dir: $base_dir"
    echo ""

    local wrapper
    wrapper="$(mktemp /tmp/tier4-wrapper-XXXXXX.sh)"
    trap 'rm -f "$wrapper"' RETURN

    # 16-index-rebuild — show the command being typed, then run it
    cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
B_CYAN=\$'\e[1;36m'
RESET=\$'\e[0m'
printf '%s\$ slipbox rebuild%s\n' "\$B_CYAN" "\$RESET"
echo
sleep 0.6
SLIPBOX_BASE_DIR='$base_dir' uv run --project '$REPO_ROOT' slipbox --base-dir '$base_dir' rebuild
echo
SCRIPT
    record_shot \
        "/tmp/tier4-16-index-rebuild.cast" \
        "$OUTPUT_DIR/16-index-rebuild.gif" \
        "$wrapper" \
        "Index Rebuild"

    # 00-status — same pattern
    cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
B_CYAN=\$'\e[1;36m'
RESET=\$'\e[0m'
printf '%s\$ slipbox status%s\n' "\$B_CYAN" "\$RESET"
echo
sleep 0.6
SLIPBOX_BASE_DIR='$base_dir' uv run --project '$REPO_ROOT' slipbox --base-dir '$base_dir' status
echo
SCRIPT
    record_shot \
        "/tmp/tier4-00-status.cast" \
        "$OUTPUT_DIR/00-status.gif" \
        "$wrapper" \
        "Status"

    echo ""
}

# ── Tier 2: Claude MCP shots ────────────────────────────────────
record_tier2() {
    # Generate a live MCP config from template with real paths.
    local mcp_config
    mcp_config="$(mktemp /tmp/demo-mcp-tier4-XXXXXX.json)"
    trap 'rm -f "$mcp_config"' RETURN

    python3 - <<PYEOF
with open('$SCRIPTS_DIR/demo-mcp.json.template') as f:
    c = f.read()
c = c.replace('REPO_ROOT_PLACEHOLDER', '$REPO_ROOT')
c = c.replace('FIXTURE_DIR_PLACEHOLDER', '$FIXTURE_DIR')
with open('$mcp_config', 'w') as f:
    f.write(c)
PYEOF

    # Only these shots get GIFs for the README.
    local readme_shots="01-maintenance 02-search 03-central-notes 04-idea-capture
                        05-analyze-note 06-source-decomposition 07-cluster-report
                        08-structure-note 10-orphans 11-similar-notes
                        12-linked-notes 17-knowledge-synthesis"

    echo "=== Tier 4 / Claude MCP shots ==="
    echo "  Fixture:    $FIXTURE_DIR"
    echo "  MCP config: $mcp_config"
    echo ""

    local wrapper
    wrapper="$(mktemp /tmp/tier4-wrapper-XXXXXX.sh)"
    trap 'rm -f "$wrapper"' RETURN

    for prompt_file in "$PROMPTS_DIR"/*.txt; do
        local shot_name
        shot_name="$(basename "$prompt_file" .txt)"

        if ! echo "$readme_shots" | grep -qw "$shot_name"; then
            continue
        fi

        # Write a per-shot wrapper so prompt content never needs shell-escaping.
        # The wrapper shows the prompt to the viewer, then slow-prints claude's
        # response line by line so the recording reveals content progressively
        # instead of dumping it all in one frame.
        # Notes on flag choices:
        #   --bare:  intentionally omitted; breaks auth when claude runs as a
        #            subprocess (e.g. from asciinema).
        #   --model: Sonnet has more generous rate limits than Opus for batch
        #            runs and produces equivalent quality for these prompts.
        cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
B_CYAN=\$'\e[1;36m'
DIM=\$'\e[2m'
RESET=\$'\e[0m'

# Show what the user is asking
printf '%s\$ slipbox-mcp%s %s(claude -p, headless mode)%s\n' "\$B_CYAN" "\$RESET" "\$DIM" "\$RESET"
echo
printf '%s> %s%s\n' "\$B_CYAN" "\$RESET" "\$(cat '$prompt_file' | fold -s -w 90 | sed '2,\$s/^/  /')"
echo
sleep 1.0
printf '%s... thinking ...%s\n' "\$DIM" "\$RESET"
echo

# Slow-print the response so the GIF reveals content progressively
claude -p "\$(cat '$prompt_file')" \\
    --model claude-sonnet-4-6 \\
    --strict-mcp-config \\
    --mcp-config '$mcp_config' \\
    --allowedTools 'mcp__slipbox-mcp__*' \\
    --output-format text 2>/dev/null \\
| while IFS= read -r line; do
    printf '%s\n' "\$line"
    sleep 0.03
  done
echo
SCRIPT

        record_shot \
            "/tmp/tier4-${shot_name}.cast" \
            "$OUTPUT_DIR/${shot_name}.gif" \
            "$wrapper" \
            "$shot_name"
    done

    echo ""
    echo "=== Tier 4 complete ==="
}

# ── Main ────────────────────────────────────────────────────────
record_tier1
record_tier2
