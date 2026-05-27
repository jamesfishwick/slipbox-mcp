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

# Use full path — shell alias 'agg' may shadow the binary.
AGG=/opt/homebrew/bin/agg

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
# --idle-time-limit 3: cap pauses at 3s so long MCP calls don't stall the GIF
# --last-frame-duration 5: pause 5s on final frame so the output is readable
AGG_FLAGS=(
    --theme dracula
    --font-size 14
    --speed 1.5
    --idle-time-limit 3
    --last-frame-duration 5
    --cols 100
    --rows 30
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
        --idle-time-limit 3 \
        --window-size "100x30" \
        --title "$title" \
        --command "bash $wrapper" \
        "$cast_file"

    echo "  [tier4] converting $(basename "$cast_file") -> $(basename "$gif_file") ..."
    "$AGG" "${AGG_FLAGS[@]}" "$cast_file" "$gif_file"

    if [[ -s "$gif_file" ]]; then
        local size
        size=$(du -h "$gif_file" | cut -f1)
        echo "  [tier4] done: $(basename "$gif_file") ($size)"
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

    # 16-index-rebuild
    cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
SLIPBOX_BASE_DIR='$base_dir' uv run --project '$REPO_ROOT' slipbox --base-dir '$base_dir' rebuild
SCRIPT
    record_shot \
        "/tmp/tier4-16-index-rebuild.cast" \
        "$OUTPUT_DIR/16-index-rebuild.gif" \
        "$wrapper" \
        "Index Rebuild"

    # 00-status
    cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
SLIPBOX_BASE_DIR='$base_dir' uv run --project '$REPO_ROOT' slipbox --base-dir '$base_dir' status
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
        # Note: --bare is intentionally omitted; it breaks auth when claude is called
        # as a subprocess (e.g. from asciinema). The plain output format records fine.
        # --model: Sonnet has a more generous rate limit than Opus for batch runs
        # and produces equivalent quality for these demo prompts.
        cat > "$wrapper" <<SCRIPT
#!/usr/bin/env bash
claude -p "\$(cat '$prompt_file')" \\
    --model claude-sonnet-4-6 \\
    --strict-mcp-config \\
    --mcp-config '$mcp_config' \\
    --allowedTools 'mcp__slipbox-mcp__*' \\
    --output-format text
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
