#!/usr/bin/env python3
"""Re-execute each ```bash block in demo.md and overwrite the following ```output block.

This keeps the Showboat-generated demo.md in sync with the live codebase.
Safe: if no output block follows a bash block, it's left alone.

Usage:
    python scripts/lib/update-demo-blocks.py [--dry-run]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_MD = REPO_ROOT / "demo.md"

# Regex: a fenced bash block followed by a fenced output block.
# Captures: (1) the bash fence + code, (2) the command content, (3) the output fence.
BLOCK_PATTERN = re.compile(
    r"(```bash\n(.*?)```)\n\n```output\n(.*?)```",
    re.DOTALL,
)


def execute_block(cmd: str, cwd: Path, env: dict) -> str:
    """Execute a shell command block and return stdout."""
    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=60,
    )
    # Combine stdout (primary) — stderr is suppressed unless the command
    # explicitly redirects it (e.g. 2>&1 in the demo blocks).
    return result.stdout


def update_demo(dry_run: bool = False) -> int:
    """Update all output blocks. Returns count of blocks changed."""
    text = DEMO_MD.read_text()
    env = {**os.environ, "SLIPBOX_BASE_DIR": str(REPO_ROOT)}
    changed = 0

    def replacer(match: re.Match) -> str:
        nonlocal changed
        bash_fence = match.group(1)
        cmd = match.group(2)
        old_output = match.group(3)

        new_output = execute_block(cmd, cwd=REPO_ROOT, env=env)

        # Normalize: strip trailing whitespace per line, ensure ends with \n
        new_output = "\n".join(
            line.rstrip() for line in new_output.rstrip("\n").split("\n")
        ) + "\n"

        if new_output != old_output:
            changed += 1
            if dry_run:
                print(f"[dry-run] block changed: {cmd[:60].strip()!r}")

        return f"{bash_fence}\n\n```output\n{new_output}```"

    updated_text = BLOCK_PATTERN.sub(replacer, text)

    if not dry_run and changed > 0:
        DEMO_MD.write_text(updated_text)

    return changed


def main():
    parser = argparse.ArgumentParser(description="Refresh demo.md output blocks")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    args = parser.parse_args()

    n = update_demo(dry_run=args.dry_run)
    verb = "would update" if args.dry_run else "updated"
    print(f"{verb} {n} output block(s)")
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
