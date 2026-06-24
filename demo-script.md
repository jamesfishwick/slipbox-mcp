# slipbox-mcp Demo Recording Script

**Target length:** ~12 minutes
**Setup:** Three windows ready to switch between: Claude (CLI or Desktop), Obsidian open to the vault, terminal in the slipbox-mcp repo.
**Recording note:** All Claude responses below are pre-captured in `demo.md`. You don't need to wait for fresh responses on camera — talk over them while they stream, or pre-record the streams and narrate.

---

## Pre-flight checklist

**Data freshness (run these in the terminal first — they affect what's on camera):**

```bash
SLIPBOX_BASE_DIR=. slipbox rebuild --clusters    # rebuilds index + refreshes cluster report
SLIPBOX_BASE_DIR=. slipbox status                # confirm "Pending clusters" > 0
SLIPBOX_BASE_DIR=. slipbox clusters | head -5    # confirm top cluster has a clean small note count (~7)
```

If the top cluster has 15+ notes (e.g. "Engineering Philosophy"), the structure-note moment in section 8 will produce a wall-of-text on camera. Two options:

- **Easier:** in Claude during section 8, ask for the *second* highest cluster instead — the prompt is parameterizable.
- **Cleaner:** dismiss the largest one off-camera so #2 becomes #1: `slipbox_dismiss_cluster` via Claude with the cluster ID from `slipbox clusters`. Re-running `slipbox status` should then show one fewer.

**Environment:**

- [ ] Claude session started, MCP server connected (verify with one quick prompt off-camera)
- [ ] Slipbox skills installed in Claude Desktop — run `python scripts/build_skills.py`, then Settings → Skills → Upload skill and add the `dist/*.skill` bundles (§7 needs `slipbox-analyze-note.skill`; §9 shows the full set)
- [ ] Obsidian open to the slipbox vault
- [ ] Obsidian graph view ready (Cmd+G) and a "good" note open in another tab — pick one with rich backlinks (`Contract Testing Knowledge Map` is currently the most connected at 52 links)
- [ ] Terminal in `~/Workspace/personal/slipbox-mcp` with a clean prompt
- [ ] Browser windows hidden / Do Not Disturb on / notifications silenced
- [ ] Mic check, screen recorder confirmed at 1080p+

---

## 1. Cold open — what this is (~45s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Terminal** | "Want to show you slipbox-mcp. A Model Context Protocol server that turns Claude into a working partner in a Zettelkasten. Not just a note-taker; something that finds connections and proposes structure." | Run `SLIPBOX_BASE_DIR=. slipbox status` so the audience sees the real numbers (currently ~554 notes, ~1585 tags, 5 pending clusters — but confirm with the pre-flight). |
| **Terminal** | "Everything you'll see runs against my real notes. More than 550 of them, accumulated over months of daily use. No mocks, no fake data." | Leave the status output on screen for a beat, then transition. |

---

## 2. The notes themselves (~60s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Obsidian** | "Before I show Claude doing anything clever, here's what the data actually is. Plain markdown files with YAML frontmatter. No proprietary format. Readable in any editor." | Open one note in source mode for 2-3 seconds — let viewers see the frontmatter (`references`, `tags`, `type`). |
| **Obsidian** | "The reason I'm using Obsidian here is the graph view and backlinks panel — they map directly onto the typed-link structure the slipbox uses. But I could be in VS Code, Logseq, or vim. The MCP server doesn't care." | Switch to reading mode. Point at the `## Links` section showing typed relationships (`supports`, `extends`, etc). |
| **Obsidian** | "Each note has a unique timestamp ID, a type — fleeting, literature, permanent, or structure — and typed links to other notes. The links are the whole game." | Open the backlinks panel briefly to show incoming references. |

---

## 3. Session start: proactive maintenance (~75s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Here's the first thing I want Claude doing every session — telling me what needs attention" | Paste the prompt: `Use the slipbox://maintenance-status resource and tell me if there's anything that needs attention.` |
| **Claude** | "What it's reading is an MCP resource: a live endpoint the server exposes, not a tool it's calling. It audits the whole vault and ranks what needs attention. This is the first prompt I run every session." | Let the response stream. Highlight the cluster table when it lands. |
| **Claude** | "Five pending clusters, ranked by urgency. The top one is the highest-leverage thing I could do in this vault right now. At the end I'll come back and actually do it. One question, and it surfaces structural work I'd never spot browsing note by note." | Point at the top cluster row. (Adapt the talk to whichever cluster is actually #1 on the day — Prompt Engineering Knowledge Map at the time of writing.) |

---

## 4. Search across 550+ notes (~45s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Hold that thought on the clusters — at the end I'll turn one into a structure note. First, the primitives underneath it. Simplest one: search. Not grep. BM25-ranked full-text search across every note, in milliseconds." | Paste: `Search my notes for "zettelkasten workflow" and show me the most relevant results.` |
| **Claude** | "Top result is a note about slipbox-mcp itself: meta. Next two are workflow patterns. Below that, related but less central. That's the FTS5 index ranking by relevance, not keyword match." | Point at the score ordering as the table renders. |

---

## 5. The graph: hubs and orphans (~120s) *— the Obsidian bridge*

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Two questions that only make sense if your notes are a graph: which ones are central, and which ones are isolated?" | Paste: `Which notes are the most connected in my Zettelkasten? Show me the top 10.` |
| **Claude** | "Top of the list: Contract Testing Knowledge Map, with 52 connections. That's a structure note: a hub. Below it, you can see what I actually think about: contract testing, software craft, poetry, consciousness. The graph reveals my preoccupations." | Let the table render. Briefly run a finger down the list. |
| **Obsidian** | "Let me show you what 'central' actually looks like." | Switch to Obsidian. Open the global graph view (Cmd+G). |
| **Obsidian** | "Five hundred and fifty-four nodes. The bright clusters are the hubs: those are the structure notes from Claude's list. The thin tendrils between them are typed links. The empty space at the edges? That's where the orphans live." | Let the graph spin / zoom out so the topology is visible. |
| **Obsidian** | "Here's the local graph for Contract Testing Knowledge Map." | Open the central note, switch to local graph. |
| **Obsidian** | "You can see how a structure note works — it's a small constellation. The structure note is the center, member notes orbit it, and each member note has its own connections branching outward." | Hover over a couple of edges to show the typed relationships. |
| **Claude** | "Now the inverse — what's *not* connected." | Switch back to Claude. Paste: `Find all my orphaned notes — the ones with no connections to anything else.` |
| **Claude** | "Fifty-eight orphans. That's about 10% of the vault. These are notes I captured but never integrated. They're not bad. They're debt. And the system makes them visible so I can pay it down." | Let the response render. |

---

## 6. Direct capture: rough idea → atomic note (~120s)

**Prompt to paste:**

```text
I've been thinking about something. Here's my rough idea:

"When I read technical books, I tend to extract too many notes at once.
I end up with 30 fleeting notes from a single chapter and never process them.
Getting them down is easy; connecting them is where I stall. Maybe I should
limit myself to 3-5 notes per reading session and link each one before moving on."

Capture this as a permanent note and find related notes to link it to.
```

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Here's the workflow I use most. I have a rough thought. I want it in the slipbox, properly formed, properly linked. I don't want to do the formatting work myself." | Paste the prompt above. |
| **Claude** | "Claude doesn't generate the idea. The idea is mine. It formats that into an atomic note, infers tags, preferring my existing taxonomy where they fit, and links it to related notes that already exist." | Let the response stream. |
| **Claude** | "Look at the link types. *Extends*: building in the same direction. *Refines*: tightening a previous claim. They encode argumentative structure. Future-me can traverse this graph by argument, not just by topic." | Point at the link-types table when it renders. |
| **Claude** | "Claude is a *formatting and integration layer*. The thinking stays mine." | Brief pause. |

---

## 7. Quality gate: analyze a note (~90s)

**Prompt to paste:**

```text
Analyze this note for my slipbox:

"Luhmann's slip-box worked because the constraints forced understanding.
You can't write an atomic note without decomposing what you read. You
can't link it without understanding how it relates to what you already know.
The method is a thinking tool disguised as a filing system. But most digital
implementations miss this — they optimize for capture speed when the hard
part was always integration."
```

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Capture is one half. The other half is checking what you just captured against the rest of your knowledge. That's the analyze workflow." | Paste the prompt above. |
| **Claude** | "Five dimensions. Atomicity — is this one idea or four? Connectivity — what does it link to in *my actual graph*, not in the abstract? Tag suggestions, preferring my existing taxonomy. A clarity rewrite. And emergent insights." | Let the response stream. Pause at the atomicity table. |
| **Claude** | "It spots near-duplicates of notes I already have — and tells me *before* I add a new one, so I can merge, split, or skip. That's the difference between a search index and a thinking partner." | Scroll to whatever the connectivity / near-duplicate callout is in the live response. |

---

## 8. The big one: cluster → structure note (~90s)

**Prompt to paste:**

```text
Take the highest-scoring cluster and create a structure note for it.
Link it to all the member notes.
```

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Remember the maintenance status from the start — five pending clusters, ranked? Let's close the loop. This one ranked first because it had the most orphaned notes and the loosest internal linking. So a structure note here buys the most connectivity per minute spent. I'm going to take it and have Claude build that note." | Paste the prompt. |
| **Claude** | "Claude creates the structure note, writes a synthesis stub, builds bidirectional `reference` links to every member note, and dismisses the cluster from future maintenance reports. One prompt, full scaffolding." | Let the response complete. |
| **Obsidian** | "And here's the result in Obsidian." | Switch to Obsidian. Open the new structure note (search by title or paste the ID Claude returned). |
| **Obsidian** | "Fresh backlinks. Open the local graph and you can see the new constellation that didn't exist 30 seconds ago." | Cmd+G or local graph view on the new note. |
| **Claude** | "Next time I run the maintenance check, this cluster won't appear. It's been promoted from emergent to organized. That's the loop: emergent → organized → forgotten about, repeated as the vault grows." | Brief pause for the punchline. |

---

## 9. The skills library (~60s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude** | "Everything I just showed you is one command away. Each workflow is installed as a skill — so it's a slash command, or I can trigger it in plain language like I did with analyze." | Type `/` to bring up the installed slipbox skills and let the list show. |
| **Claude** | "Knowledge creation, knowledge exploration, knowledge synthesis, batch creation for book chapters, analyze-note, cluster maintenance. Each one is a structured workflow that encodes the Zettelkasten method so I don't re-explain it every session." | Let viewers see the list. Don't run one — just show they exist. |
| **Claude** | "The synthesis workflow is the one I use least often and value most. It looks for connections I haven't drawn yet: bridges between clusters that developed independently. That's where the real thinking work gets done." | Optional: briefly mention without running. |

---

## 10. Lock-in story (~30s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Terminal** | "One last thing. Everything you saw — the search, the graph, the clusters — comes from a SQLite index. But the source of truth is the markdown files." | Run `ls -lh data/db/` to show `zettelkasten.db` (~5 MB) exists. |
| **Terminal** | "I can blow this index away and rebuild it from the markdown files in seconds. The notes are never locked into this tool. They're plain text. They'll outlive any software I'm using to view them." | Run `SLIPBOX_BASE_DIR=. slipbox rebuild` — completes in a couple of seconds against 554 notes. (Don't actually `rm` the DB on camera; the rebuild rewrites it in place, which makes the same point without the suspense.) |

---

## 11. Close (~30s)

| SCREEN | What you say | What you do |
|---|---|---|
| **Claude or Obsidian** | "That's slipbox-mcp. Atomic notes, typed links, an active agent that processes my content rather than generating it, and zero lock-in. Repo's linked below. Build something with it." | Hold on a closing frame. The graph view is the strongest visual. |

---

## Section-by-section mapping (back to demo.md)

| Recording section | demo.md section(s) | Notes |
|---|---|---|
| 1. Cold open | Stats block (line 75-88) | Use real terminal, not screenshot |
| 2. Notes | Note Format (line 9-56), Browsing (line 58-72) | Obsidian only, no Claude needed |
| 3. Maintenance | §1 (line 244-279) | The proactive hook |
| 4. Search | §2 (line 283-316) | Quick win, sets expectations |
| 5. Graph | §3 + §4 (line 320-385) bridged with Obsidian | Combined for one strong narrative |
| 6. Capture | §5 (line 389-431) | Highest-frequency workflow |
| 7. Analyze | §6 (line 435-560) | The quality gate |
| 8. Cluster→Structure | §11 (line 743-770) | Closes the loop on §3 |
| 9. Skills | §14 (line 872-1164) | Brief — they're aware of the surface area, that's enough |
| 10. Lock-in | §15 (line 1169-1183) | The trust statement |
| 11. Close | Talking Points (line 1187-1195) | Don't recap. Let the demo speak. |

---

## Sections deliberately cut

These are in `demo.md` but skipped for the 12-min cut. Add them if you want to extend:

- §7 Source Decomposition — overlaps with §5 capture; the prompt is the same shape
- §8 Conversation Distillation — hard to demo without setting up a fake conversation first
- §9 Find Similar Notes — interesting but slightly redundant with §5 (graph)
- §10 Cluster Detection — already covered implicitly by §3 (maintenance status)
- §12 Browse by Date — utility, not a story
- §13 Tag Taxonomy — ends on a typo dedup finding (`ai-adoption` vs `AI-adoption`), which is honest but anti-climactic for a sales-y demo

---

## Recording tips

- **Don't read this verbatim.** Hit the talking points; the camera will catch you reading and it shows.
- **Pre-run every prompt** the day-of so you know the responses won't surprise you mid-recording.
- **Talk over the streaming text** — viewers don't want silence while Claude types. The talk track above is timed roughly to the response length.
- **One take per section** is fine. Edit the seams in post.
- **B-roll** of the Obsidian graph rotating slowly is great filler if you need to cover a slow Claude response.
