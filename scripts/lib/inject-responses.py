#!/usr/bin/env python3
"""Inject Claude responses into demo.md, replacing <details> blocks.

Finds existing <details><summary>Claude's response</summary>...</details> blocks
and replaces their content with fresh text from /tmp/demo-shot-*.txt files.
Also replaces bare ![...](assets/screenshots/NN-name.png) image references.

Usage:
    python3 inject-responses.py <demo.md path> <text file prefix>

Example:
    python3 inject-responses.py demo.md /tmp/demo-shot
    # Reads /tmp/demo-shot-01-maintenance.txt, /tmp/demo-shot-02-search.txt, etc.
"""
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <demo.md> <text-file-prefix>", file=sys.stderr)
        sys.exit(1)

    demo_path = Path(sys.argv[1])
    prefix = sys.argv[2]
    text = demo_path.read_text()
    count = 0

    # Collect all available response files.
    import glob
    response_files = {}
    for f in glob.glob(f"{prefix}-*.txt"):
        # Extract shot name: /tmp/demo-shot-01-maintenance.txt -> 01-maintenance
        name = Path(f).stem.replace(Path(prefix).stem + "-", "", 1)
        response_files[name] = Path(f)

    # Pattern 1: Replace existing <details> blocks.
    details_pattern = re.compile(
        r'<details>\s*\n<summary>Claude\'s response</summary>\n\n'
        r'(.*?)'
        r'\n</details>',
        re.DOTALL,
    )

    # For each <details> block, find which shot it corresponds to by looking
    # at the preceding context (the section heading or prompt).
    # Strategy: walk through all image refs and details blocks, match by position.

    # Pattern 2: Replace bare image references that haven't been converted yet.
    for name, txt_path in response_files.items():
        content = txt_path.read_text().rstrip()

        # Try replacing image reference first.
        img_pattern = re.compile(
            rf'!\[[^\]]*\]\(assets/screenshots/{re.escape(name)}\.png\)'
        )
        if img_pattern.search(text):
            replacement = f"""<details>
<summary>Claude's response</summary>

{content}

</details>"""
            text = img_pattern.sub(replacement, text)
            count += 1
            print(f"  [inject] {name}: replaced image ref")
            continue

        # Try replacing existing <details> block.
        # Find the block that's closest after a prompt file reference or section marker.
        # Simpler approach: replace the Nth <details> block with the Nth response,
        # but that's fragile. Instead, search for the shot name in nearby context.
        # Most reliable: just replace ALL details blocks sequentially with matching files.

    # Now handle existing <details> blocks by matching them to response files.
    # We scan for each details block, look backwards for clues about which shot it is.
    def replace_details(match):
        nonlocal count
        old_content = match.group(1)
        # Look at first ~100 chars of old content for identifying info
        # and try to match against response files.
        start_pos = match.start()
        # Get preceding 500 chars for context
        preceding = text[max(0, start_pos - 500):start_pos]

        for name, txt_path in list(response_files.items()):
            # Check if this response file's content is already used
            content = txt_path.read_text().rstrip()

            # Match by checking if the old content starts similarly,
            # or if the preceding text contains keywords from the prompt file.
            prompt_file = Path(f"/Users/jamesfishwick/Workspace/slipbox-mcp/scripts/demo-prompts/{name}.txt")
            if prompt_file.exists():
                prompt_keywords = prompt_file.read_text()[:100].lower()
                preceding_lower = preceding.lower()
                # Check for keyword overlap
                keywords = [w for w in prompt_keywords.split() if len(w) > 5]
                matches = sum(1 for kw in keywords if kw in preceding_lower)
                if matches >= 2:
                    del response_files[name]
                    count += 1
                    print(f"  [inject] {name}: replaced details block")
                    return f"""<details>
<summary>Claude's response</summary>

{content}

</details>"""

        # No match found, leave unchanged
        return match.group(0)

    text = details_pattern.sub(replace_details, text)

    demo_path.write_text(text)
    print(f"\n  [inject] Updated {count} response(s) in {demo_path.name}")


if __name__ == "__main__":
    main()
