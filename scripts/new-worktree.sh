#!/usr/bin/env bash
# new-worktree.sh — Create a git worktree under .worktrees/<name> and sync
# its own venv, so each worktree imports its own src/ instead of the main
# checkout's editable install. Works when invoked from any worktree.
#
# Usage: scripts/new-worktree.sh <name> [base-ref]
#   <name>      branch + directory name (e.g. fix/foo -> .worktrees/foo)
#   [base-ref]  ref to branch from (default: origin/main)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <name> [base-ref]" >&2
  exit 2
fi

name="$1"
base_ref="${2:-origin/main}"

# Resolve the MAIN working tree (first entry of `git worktree list`), so
# .worktrees/ always sits beside the primary checkout regardless of cwd.
main_tree="$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')"
if [[ -z "${main_tree}" ]]; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

# Directory name is the last path segment of the branch name.
dir_name="${name##*/}"
dest="${main_tree}/.worktrees/${dir_name}"

if [[ -e "${dest}" ]]; then
  echo "error: ${dest} already exists" >&2
  exit 1
fi

# Find uv even when it isn't on the non-login PATH.
uv_bin="$(command -v uv || true)"
[[ -z "${uv_bin}" && -x "${HOME}/.local/bin/uv" ]] && uv_bin="${HOME}/.local/bin/uv"
if [[ -z "${uv_bin}" ]]; then
  echo "error: uv not found (looked on PATH and ~/.local/bin)" >&2
  exit 1
fi

echo "Creating worktree ${dest} on branch ${name} from ${base_ref}..."
git fetch --quiet origin 2>/dev/null || true

# Reuse the branch if it already exists; otherwise create it from base_ref.
if git show-ref --verify --quiet "refs/heads/${name}"; then
  git worktree add "${dest}" "${name}"
else
  git worktree add -b "${name}" "${dest}" "${base_ref}"
fi

echo "Syncing venv with all extras..."
( cd "${dest}" && "${uv_bin}" sync --all-extras )

echo
echo "Done. Worktree ready:"
echo "  cd ${dest}"
echo "  uv run pytest"
