#!/usr/bin/env bash
# snapshot-fixture.sh — rsync live data/ into a /tmp fixture so demo capture
# runs (especially mutating tier-2 shots) never touch real notes.
#
# The fixture mirrors the repo-root-relative structure: <fixture>/data/notes/, etc.
# SLIPBOX_BASE_DIR should point at the fixture root (not <fixture>/data).
#
# Usage: snapshot-fixture.sh <fixture-dir>
# Prints the fixture root path on stdout when done.

set -euo pipefail

FIXTURE_DIR="${1:?usage: snapshot-fixture.sh <fixture-dir>}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DATA="$REPO_ROOT/data"

# Refuse to write outside /tmp — guards against accidental overwrite of the live vault.
case "$FIXTURE_DIR" in
    /tmp/*|/private/tmp/*) ;;
    *)
        echo "snapshot-fixture: refusing to snapshot to '$FIXTURE_DIR' (must live under /tmp)" >&2
        exit 2
        ;;
esac

if [[ ! -d "$SRC_DATA/notes" ]]; then
    echo "snapshot-fixture: no notes found at $SRC_DATA/notes" >&2
    exit 1
fi

# Mirror repo structure: <fixture>/data/{notes,db}
mkdir -p "$FIXTURE_DIR/data"
rsync -a --delete "$SRC_DATA/" "$FIXTURE_DIR/data/"

# Rebuild the DB and cluster report against the fixture so tier 2 has fresh data.
cd "$REPO_ROOT"
SLIPBOX_BASE_DIR="$FIXTURE_DIR" uv run slipbox --base-dir "$FIXTURE_DIR" rebuild --clusters >&2

echo "$FIXTURE_DIR"
