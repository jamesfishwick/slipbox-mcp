# Zettelkasten MCP Server

A Model Context Protocol server for managing a Zettelkasten knowledge system with automatic cluster detection.

## Features

- **Atomic Notes**: Create, update, and link notes following Zettelkasten principles
- **Semantic Links**: Seven link types (reference, extends, refines, contradicts, questions, supports, related)
- **Full-Text Search**: Search across titles, content, and tags
- **Graph Analysis**: Find central notes, orphans, and similar notes
- **Cluster Detection**: Automatic identification of emergent knowledge clusters
- **Structure Note Generation**: Create structure notes from detected clusters

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/zettelkasten-mcp.git
cd zettelkasten-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

Create a `.env` file or set environment variables:

```bash
# Required: Where notes are stored as markdown files
export ZETTELKASTEN_NOTES_DIR="~/.local/share/mcp/zettelkasten/notes"

# Required: SQLite database path
export ZETTELKASTEN_DATABASE_PATH="~/.local/share/mcp/zettelkasten/data/zettelkasten.db"

# Optional: Log level (DEBUG, INFO, WARNING, ERROR)
export ZETTELKASTEN_LOG_LEVEL="INFO"
```

Or copy the example env file:

```bash
cp .env.example .env
# Edit .env with your preferred paths
```

### 3. Initialize Data Directories

```bash
# Create directories (the server does this automatically, but good to verify)
mkdir -p ~/.local/share/mcp/zettelkasten/notes
mkdir -p ~/.local/share/mcp/zettelkasten/data
```

### 4. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent on your platform:

```json
{
  "mcpServers": {
    "zettelkasten": {
      "command": "/absolute/path/to/zettelkasten-mcp/.venv/bin/python",
      "args": ["-m", "zettelkasten_mcp"],
      "env": {
        "ZETTELKASTEN_NOTES_DIR": "~/.local/share/mcp/zettelkasten/notes",
        "ZETTELKASTEN_DATABASE_PATH": "~/.local/share/mcp/zettelkasten/data/zettelkasten.db"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/` with your actual path.

### 5. Restart Claude Desktop

Quit and reopen Claude Desktop to load the MCP server.

### 6. Verify Installation

In Claude, try:
- "Create a test note about something"
- "Search my zettelkasten for test"
- "Find orphaned notes"

---

## Optional: Automatic Cluster Detection

### What It Does

As your Zettelkasten grows, notes naturally cluster around themes—groups of notes sharing tags but lacking a structure note to organize them. Cluster detection identifies these emergent patterns so you can formalize them.

**Why schedule it?** Cluster analysis scans all notes and computes similarity scores. Running it in the background (daily at 6am) means results are pre-computed when you start a Claude conversation. Without scheduling, `zk_get_cluster_report()` computes on-demand, which is slower for large collections.

**When to run manually?** After bulk imports, major reorganization, or when you want immediate results without waiting for the next scheduled run.

### Quick Install (macOS)

```bash
# Make installer executable and run it
chmod +x scripts/install-cluster-detection.sh
./scripts/install-cluster-detection.sh
```

The installer automatically:
- Detects your Python/venv path
- Generates the LaunchAgent plist with correct paths
- Installs and loads the LaunchAgent

### Manual Test

```bash
source .venv/bin/activate
python scripts/detect_clusters.py
```

Output shows detected clusters and saves a report to `~/.local/share/mcp/zettelkasten/cluster-analysis.json`.

### Uninstall

```bash
./scripts/install-cluster-detection.sh --uninstall
```

---

## Optional: File Watcher for Auto-Indexing

### What It Does

The MCP server maintains a database index for fast searching. When you edit notes directly in Obsidian (or any editor), the database becomes stale until manually rebuilt with `zk_rebuild_index`.

The file watcher solves this by running as a background daemon that monitors your notes directory and automatically rebuilds the index when `.md` files change.

**When to use it?** If you frequently edit notes in Obsidian while also using Claude, the file watcher ensures both see the same data without manual rebuilds.

### Quick Install (macOS)

```bash
chmod +x scripts/install-file-watcher.sh
./scripts/install-file-watcher.sh
```

The installer:
- Detects your Python/venv path
- Installs `watchdog` if needed
- Generates and loads the LaunchAgent
- Starts automatically on login and restarts if it crashes

### Manual Test

```bash
source .venv/bin/activate
python scripts/watch_notes.py
```

Then edit a note file in another terminal—you should see "rebuilding index..." in the watcher output.

### Check Status

```bash
# Is it running?
launchctl list | grep zettelkasten.watcher

# View logs
tail -f ~/.local/share/mcp/zettelkasten/watcher.log
```

### Uninstall

```bash
./scripts/install-file-watcher.sh --uninstall
```

---

## Recommended System Prompt

For best results, add the system prompt from `docs/SYSTEM_PROMPT.md` to your Claude preferences. This enables:

- Automatic knowledge capture during conversations
- Cluster emergence detection at conversation start
- Proper Zettelkasten workflows (search before create, link immediately)

---

## Tools Reference

### Core Note Operations
| Tool | Description |
|------|-------------|
| `zk_create_note` | Create atomic notes (fleeting/literature/permanent/structure/hub) |
| `zk_get_note` | Retrieve note by ID or title |
| `zk_update_note` | Update existing notes |
| `zk_delete_note` | Delete notes |

### Linking
| Tool | Description |
|------|-------------|
| `zk_create_link` | Create semantic links between notes |
| `zk_remove_link` | Remove links |
| `zk_get_linked_notes` | Get notes linked to/from a note |

### Search & Discovery
| Tool | Description |
|------|-------------|
| `zk_search_notes` | Search by text, tags, or type |
| `zk_find_similar_notes` | Find notes similar to a given note |
| `zk_find_central_notes` | Find most connected notes |
| `zk_find_orphaned_notes` | Find unconnected notes |
| `zk_list_notes_by_date` | List notes by date range |
| `zk_get_all_tags` | List all tags |

### Cluster Analysis
| Tool | Description |
|------|-------------|
| `zk_get_cluster_report` | Get pending clusters needing structure notes |
| `zk_create_structure_from_cluster` | Create structure note from cluster |
| `zk_refresh_clusters` | Regenerate cluster analysis |

### Maintenance
| Tool | Description |
|------|-------------|
| `zk_rebuild_index` | Rebuild database index from files |

---

## Prompts Reference

MCP prompts are workflow templates accessible via Claude's prompt picker. They guide you through common Zettelkasten workflows.

| Prompt | Description | Use When |
|--------|-------------|----------|
| `knowledge_creation` | Process information into 3-5 atomic notes | Adding articles, ideas, or notes |
| `knowledge_creation_batch` | Process larger volumes into 5-10 notes | Processing books or long-form content |
| `knowledge_exploration` | Map connections to existing knowledge | Exploring how topics relate |
| `knowledge_synthesis` | Create higher-order insights | Finding bridges between ideas |

### Example Usage

In Claude Desktop, select a prompt from the prompt picker, then provide the required input:

**knowledge_creation**: Paste an article or your notes, get atomic notes with links.

**knowledge_exploration**: Enter a topic to map its connections in your Zettelkasten.

**knowledge_synthesis**: Provide context to spark connections between unrelated areas.

---

## Link Types

| Type | Use When | Inverse |
|------|----------|---------|
| `reference` | Generic "see also" connection | reference |
| `extends` | Building on another idea | extended_by |
| `refines` | Clarifying or improving | refined_by |
| `contradicts` | Opposing view | contradicted_by |
| `questions` | Raising questions about | questioned_by |
| `supports` | Providing evidence for | supported_by |
| `related` | Loose thematic connection | related |

---

## Note Types

| Type | Purpose |
|------|---------|
| `fleeting` | Quick captures, unprocessed thoughts |
| `literature` | Ideas from sources with citation |
| `permanent` | Refined ideas in your own words |
| `structure` | Maps organizing 7-15 related notes |
| `hub` | Entry points into major domains |

---

## File Format

Notes are stored as Markdown files with YAML frontmatter:

```markdown
---
id: "20251217T172432480464000"
title: "Poetry Revision Principles"
type: structure
tags:
  - poetry
  - revision
  - craft
created: "2025-12-17T17:24:32"
updated: "2025-12-17T17:24:32"
---

# Poetry Revision Principles

Content here...

## Links
- reference [[20250728T125429845760000]] Member of structure
```

You can edit these files directly in any text editor or Obsidian. Run `zk_rebuild_index` after external edits.

---

## Troubleshooting

### Server not loading in Claude Desktop

1. Check the path in `claude_desktop_config.json` is absolute (not relative)
2. Verify the venv python exists: `ls -la /path/to/.venv/bin/python`
3. Check Claude Desktop logs for errors

### Database out of sync

If notes were edited outside the MCP server:

```
zk_rebuild_index
```

### Cluster detection not running

```bash
launchctl list | grep zettelkasten.cluster-detection
# Should show: - 0 com.zettelkasten.cluster-detection

# Check logs
cat /tmp/zettelkasten-clusters.log

# Reinstall if needed
./scripts/install-cluster-detection.sh --uninstall
./scripts/install-cluster-detection.sh
```

### File watcher not running

```bash
launchctl list | grep zettelkasten.watcher
# Should show: - 0 com.zettelkasten.watcher

# Check logs
cat ~/.local/share/mcp/zettelkasten/watcher.log

# Reinstall if needed
./scripts/install-file-watcher.sh --uninstall
./scripts/install-file-watcher.sh
```

---

## Development

```bash
# Run tests
pytest

# Run with debug logging
ZETTELKASTEN_LOG_LEVEL=DEBUG python -m zettelkasten_mcp

# Run cluster detection manually
python scripts/detect_clusters.py
```

---

## License

MIT
