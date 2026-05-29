#!/usr/bin/env bash
# build-demo-fixture.sh — Populate a /tmp fixture from the curated demo vault.
#
# Copies scripts/demo-vault/notes/ to <fixture-dir>/data/notes/, then rebuilds
# the SQLite index and cluster report. This is the fixture used by tier4
# recordings; it replaces snapshot-fixture.sh (which copies the live vault).
#
# Usage: build-demo-fixture.sh <fixture-dir>
# Requires: uv

set -euo pipefail

FIXTURE_DIR="${1:?usage: build-demo-fixture.sh <fixture-dir>}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
VAULT_NOTES="$SCRIPTS_DIR/demo-vault/notes"

# Safety: refuse to write outside /tmp.
case "$FIXTURE_DIR" in
    /tmp/*|/private/tmp/*) ;;
    *)
        echo "build-demo-fixture: refusing to write to '$FIXTURE_DIR' (must be under /tmp)" >&2
        exit 2
        ;;
esac

if [[ ! -d "$VAULT_NOTES" ]]; then
    echo "build-demo-fixture: demo vault notes not found at $VAULT_NOTES" >&2
    echo "  Run: uv run python scripts/lib/generate-demo-vault.py" >&2
    exit 1
fi

NOTE_COUNT=$(find "$VAULT_NOTES" -name "*.md" | wc -l | tr -d ' ')
if [[ "$NOTE_COUNT" -lt 40 ]]; then
    echo "build-demo-fixture: expected ≥40 notes, found $NOTE_COUNT in $VAULT_NOTES" >&2
    exit 1
fi

echo "  [fixture] Copying $NOTE_COUNT notes to $FIXTURE_DIR ..."
mkdir -p "$FIXTURE_DIR/data/notes"
rsync -a --delete "$VAULT_NOTES/" "$FIXTURE_DIR/data/notes/"

echo "  [fixture] Rebuilding index and cluster report ..."
cd "$REPO_ROOT"
SLIPBOX_BASE_DIR="$FIXTURE_DIR" uv run slipbox --base-dir "$FIXTURE_DIR" rebuild --clusters 2>&1 \
    | sed 's/^/    /'

echo "  [fixture] Done: $FIXTURE_DIR"
echo "$FIXTURE_DIR"
