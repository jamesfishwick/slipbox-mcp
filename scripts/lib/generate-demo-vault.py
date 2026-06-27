#!/usr/bin/env python3
"""Generate the curated demo vault for slipbox-mcp asciinema recordings.

Creates 41 notes under scripts/demo-vault/notes/ with a link topology
engineered to produce compelling responses for every demo prompt:

  Cluster scores (approximate, based on formula in cluster_service.py):
    cognitive-load/code-review   : ~1.00  (4/6 orphans, low density)
    zettelkasten/knowledge-mgmt  : ~0.74  (2/10 orphans, hub-spoked)
    team-comm/software-teams     : ~0.57  (1/5 orphans)
    api-design/software-arch     : ~0.58  (1/6 orphans)

  Global orphans: ~21 notes (15 standalone + ZK5, ZK7, CL5, CL6, API3, TC4)

Usage:
    python scripts/lib/generate-demo-vault.py [--output-dir PATH]
    python scripts/lib/generate-demo-vault.py --dry-run
"""

import argparse
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "scripts" / "demo-vault" / "notes"


# ─── Note definitions ────────────────────────────────────────────────────────
# Each entry: (id, title, type, tags, references, body, links)
# links = list of (link_type, target_id, description)

NOTES = [
    # ── Hub note ────────────────────────────────────────────────────────────
    (
        "20240101T100000000000000",
        "The Zettelkasten as a Thinking Partner, Not a Filing System",
        "permanent",
        ["zettelkasten", "knowledge-management", "note-taking"],
        [],
        dedent("""\
            Most digital note-taking tools are optimised for retrieval, not for thinking.
            The Zettelkasten does the opposite: its constraints — one idea per note, mandatory
            linking, no hierarchical folders — force you to think before you file. You cannot
            write an atomic note without decomposing what you understood. You cannot link it
            without deciding how it relates to what you already know.

            The result is not a filing system you consult after thinking; it is a thinking
            apparatus you operate *while* thinking. Luhmann described his slip-box as a
            conversation partner, not an archive. That distinction collapses the difference
            between input (reading, capturing) and output (thinking, writing): the linking
            work *is* the thinking work.

            The bottleneck in most knowledge workflows is not capture — it is integration.
            Digital tools that make capture frictionless inadvertently remove the constraint
            that makes integration happen."""),
        [
            (
                "reference",
                "20240101T110000000000000",
                "Luhmann's original formulation of constraints as thinking apparatus",
            ),
            (
                "reference",
                "20240101T120000000000000",
                "Atomic notes as the decomposition constraint in action",
            ),
            (
                "extends",
                "20240101T130000000000000",
                "Hub extends the linking-as-learning claim to the conversation metaphor",
            ),
            (
                "extends",
                "20240101T140000000000000",
                "Hub extends the analysis of why digital tools fail at integration depth",
            ),
            (
                "supports",
                "20240101T160000000000000",
                "Both argue integration is the real bottleneck, not capture",
            ),
            (
                "supports",
                "20240101T180000000000000",
                "Both support distinguishing ZK from reference management",
            ),
            (
                "contradicts",
                "20240104T140000000000000",
                "Fatigue is a symptom; the real constraint is integration discipline",
            ),
            (
                "questions",
                "20240104T130000000000000",
                "Questions whether working-memory limits are the right frame for ZK's value",
            ),
            (
                "related",
                "20240104T110000000000000",
                "Both concern the mental work required in knowledge tasks",
            ),
            (
                "related",
                "20240103T110000000000000",
                "Shared vocabulary is the linking requirement applied to team communication",
            ),
            (
                "refines",
                "20240101T130000000000000",
                "Refines the linking claim: linking creates a thinking partner, not just a graph",
            ),
        ],
    ),
    # ── Zettelkasten cluster (ZK1–ZK8) ─────────────────────────────────────
    (
        "20240101T110000000000000",
        "Luhmann's Slip-Box: Constraints as Thinking Apparatus",
        "permanent",
        ["zettelkasten", "knowledge-management", "constraints"],
        [],
        dedent("""\
            Niklas Luhmann produced over 70 books and 400 articles in 30 years using a
            physical slip-box of 90,000 index cards. The system's power was not its size but
            its constraints: one idea per card, every card assigned a branching numeric ID,
            no thematic folders. These constraints prevented the accumulation of half-processed
            thoughts and forced decomposition at the moment of capture.

            A card that cannot be written without referencing another card is evidence of
            understanding, not just transcription. The ID system, which allows a new card to
            be inserted *between* two existing cards, mirrors the way ideas relate — not in
            linear sequence but in associative branches. The constraint is the method."""),
        [
            (
                "supports",
                "20240101T100000000000000",
                "Luhmann's system is the primary evidence for constraint-driven thinking",
            ),
        ],
    ),
    (
        "20240101T120000000000000",
        "Atomic Notes Require Decomposition Before Writing",
        "permanent",
        ["zettelkasten", "atomic-notes", "knowledge-management"],
        [],
        dedent("""\
            An atomic note contains exactly one idea. This sounds simple until you try to
            write one and discover you cannot isolate the idea without first understanding it
            well enough to separate it from adjacent ideas. The atomicity constraint is a
            comprehension test in disguise.

            Most notes that feel atomic are actually bundles: "X causes Y, which leads to Z"
            is three notes compressed into one sentence. Decomposing them forces you to ask
            what the evidence is for each claim independently, whether Y is always entailed by
            X or only sometimes, and what the boundaries of Z actually are. The writing of the
            note *is* the understanding."""),
        [
            (
                "supports",
                "20240101T160000000000000",
                "Decomposition at the note level is the mechanism that prevents the integration bottleneck",
            ),
        ],
    ),
    (
        "20240101T130000000000000",
        "The Linking Requirement Is Where Learning Happens",
        "permanent",
        ["zettelkasten", "linking", "knowledge-management"],
        [],
        dedent("""\
            Highlighting and re-reading feel like learning because they are familiar and
            comfortable. The linking requirement feels effortful because it *is* effortful —
            and that effort is the learning.

            When you link a new note to an existing one, you must answer: in what way does
            this new idea relate to that older one? Does it support it, contradict it, extend
            it, or refine it? That question cannot be answered by passive exposure. It requires
            activating and interrogating your existing knowledge, which is exactly what cognitive
            science means by 'retrieval practice.' The Zettelkasten method is retrieval practice
            in a form that also produces a knowledge artefact."""),
        [
            (
                "supports",
                "20240101T100000000000000",
                "The linking claim directly supports the thinking-partner thesis",
            ),
            (
                "related",
                "20240101T120000000000000",
                "Linking and atomic notes are two sides of the same constraint",
            ),
        ],
    ),
    (
        "20240101T140000000000000",
        "Why Digital Zettelkasten Fail at Integration Depth",
        "permanent",
        ["zettelkasten", "knowledge-management", "note-taking"],
        [],
        dedent("""\
            Digital tools reduce capture friction to near zero: select text, press Ctrl+C,
            paste into a note. This feels like productivity. The problem is that capture
            without integration produces a searchable archive of half-understood material,
            not a knowledge graph.

            Physical systems imposed friction at capture: you had to write by hand, which
            slowed you down enough to process what you were writing. Digital systems moved
            the friction to integration — which users then skip. The result is tens of
            thousands of notes with weak or no links, a pile of raw material that never
            becomes knowledge. Tools optimised for fast capture are systematically optimised
            against deep integration."""),
        [
            (
                "extends",
                "20240101T160000000000000",
                "The failure mode is a direct consequence of the integration bottleneck",
            ),
        ],
    ),
    (
        "20240101T150000000000000",
        "Fleeting Notes as Raw Input, Not Finished Output",
        "permanent",
        ["zettelkasten", "note-taking", "atomic-notes"],
        [],
        dedent("""\
            A fleeting note is a trigger, not a note. Its purpose is to capture a signal
            before it disappears — a phrase that struck you, a question that arose while
            reading, a half-formed connection. It is the raw material that you will later
            process into a permanent note, not the permanent note itself.

            The confusion between fleeting notes and permanent notes is a primary cause of
            bloated note systems. When fleeting notes are kept indefinitely without processing,
            the inbox grows without the knowledge graph growing. The inbox is not the system;
            it is the queue feeding the system. Empty it regularly or it defeats its purpose."""),
        # No links — orphan in ZK cluster (ZK5)
        [],
    ),
    (
        "20240101T160000000000000",
        "The Bottleneck Is Integration, Not Capture",
        "permanent",
        ["zettelkasten", "knowledge-management", "note-taking"],
        [],
        dedent("""\
            Most people who struggle with knowledge management do not have a capture problem.
            They can highlight, screenshot, clip, and export with great efficiency. Their
            inboxes are full. Their archives are enormous. Their knowledge graph is empty.

            The constraint is integration: the deliberate work of placing a new idea in
            relation to existing ideas, asking how it changes what you already know, and
            writing that relationship as an explicit link. This work is cognitively expensive
            and does not feel immediately productive, which is why it is systematically skipped.
            Every tool that makes capture faster without making integration easier widens this
            gap."""),
        [
            (
                "supports",
                "20240101T140000000000000",
                "The integration bottleneck explains why digital capture-optimised tools produce weak knowledge graphs",
            ),
        ],
    ),
    (
        "20240101T170000000000000",
        "Read to Extract, Not to Annotate",
        "permanent",
        ["zettelkasten", "note-taking", "reading"],
        [],
        dedent("""\
            Annotation keeps the note in the source. You underline a sentence in the book,
            which means the insight lives in the margin of the book, indexed to the book's
            structure. When you later want that insight, you must remember which book it was
            in, which chapter, which page.

            Extraction moves the note to your system, indexed to your own ideas. You write the
            insight in your own words, which requires understanding it, and you place it where
            it relates to other ideas you have, not where it appeared in the source. Annotation
            is the author's indexing system. Extraction builds your own."""),
        # No links — orphan in ZK cluster (ZK7)
        [],
    ),
    (
        "20240101T180000000000000",
        "Zettelkasten vs Reference Management: Different Problems",
        "permanent",
        ["zettelkasten", "knowledge-management", "references"],
        [],
        dedent("""\
            Reference managers (Zotero, Mendeley, Papers) solve a bibliographic problem:
            how do I track what I have read, cite it correctly, and find it again? The unit
            of organisation is the source — the paper, book, or article.

            The Zettelkasten solves a thinking problem: how do I develop ideas over time by
            connecting new ideas to old ones? The unit of organisation is the idea. These are
            different problems, and tools optimised for one perform poorly at the other. A
            reference manager full of PDFs is not a Zettelkasten. A Zettelkasten without
            source attribution is not a reference manager. Using one as a substitute for the
            other produces neither."""),
        # No outgoing links — targeted by hub (supports), so not globally orphaned
        [],
    ),
    # ── API design cluster (API1–API6) ───────────────────────────────────────
    (
        "20240102T110000000000000",
        "API Contracts as Promises to Consumers",
        "permanent",
        ["api-design", "software-architecture", "contracts"],
        [],
        dedent("""\
            An API is a promise: given these inputs, in this form, you will receive this
            output, within these error conditions. That promise is the contract between the
            provider and every consumer who builds on it.

            Breaking the contract — changing a field name, removing an endpoint, altering
            error shapes — breaks every consumer simultaneously. The contract is not a
            convenience; it is a structural dependency. Good API design treats contract
            maintenance as a first-class obligation: you do not remove a promise, you
            deprecate it, then version past it, with enough warning for consumers to migrate.
            The contract is the product, not the implementation behind it."""),
        [
            (
                "extends",
                "20240102T120000000000000",
                "Versioning strategy is how you manage the evolution of promises over time",
            ),
        ],
    ),
    (
        "20240102T120000000000000",
        "Versioning Strategy: Additive Changes Only",
        "permanent",
        ["api-design", "software-architecture", "versioning"],
        [],
        dedent("""\
            The safest versioning strategy for a public API is additive-only changes within
            a major version: new fields, new endpoints, new optional parameters are allowed;
            removing or renaming existing fields requires a major version bump and a
            deprecation period.

            This constraint forces API designers to think carefully before adding fields —
            everything added becomes permanent or requires a breaking change to remove. It
            also gives consumers a reliable guarantee: if they pin to v2, a v2.3 release
            will not break their integration. Additive-only versioning is a promise about
            the promise: the contract will only grow, never shrink, until the next major
            version is declared."""),
        [
            (
                "extends",
                "20240102T140000000000000",
                "Versioning strategy is implemented through schema evolution disciplines",
            ),
        ],
    ),
    (
        "20240102T130000000000000",
        "The Leaky Abstraction Problem in REST",
        "permanent",
        ["api-design", "software-architecture", "rest"],
        [],
        dedent("""\
            REST APIs frequently leak implementation details through their surface: database
            primary keys as resource IDs, query parameters that mirror SQL WHERE clauses,
            endpoint paths that follow database table names, error messages that include
            stack traces. Each leak couples the consumer to the provider's internal structure.

            When the database schema changes, the API breaks — not because the API's contract
            changed intentionally but because the implementation leaked. The fix is a
            separation layer: the API surface should represent domain concepts, not storage
            concepts. Resource IDs should be opaque handles, not database keys. Queries should
            express intent, not database structure."""),
        # No links — orphan in API cluster (API3)
        [],
    ),
    (
        "20240102T140000000000000",
        "Schema Evolution and Backward Compatibility",
        "permanent",
        ["api-design", "software-architecture", "schema"],
        [],
        dedent("""\
            Schema evolution is the art of changing data formats without breaking existing
            consumers. The core techniques are: making new fields optional with sensible
            defaults; never removing required fields in a minor version; using explicit
            nullable rather than field absence to signal missing data; and providing
            deprecation notices before removal.

            The hardest case is renaming: a renamed field is simultaneously a new field and
            a removed field. The least disruptive path is to support both names in parallel
            during a transition period, with the old name marked deprecated. Consumers can
            migrate at their own pace. This requires more provider work but respects the
            contractual nature of the API surface."""),
        [
            (
                "supports",
                "20240102T120000000000000",
                "Schema evolution discipline is how versioning promises are kept in practice",
            ),
        ],
    ),
    (
        "20240102T150000000000000",
        "Consumer-Driven Contract Testing",
        "permanent",
        ["api-design", "software-architecture", "testing"],
        [],
        dedent("""\
            Consumer-driven contract testing (Pact, Spring Cloud Contract) inverts the
            traditional testing direction: instead of the provider defining what the API
            returns and consumers hoping it matches their expectations, consumers publish
            their expectations as machine-readable contracts that providers must satisfy.

            Each consumer says: 'I expect this endpoint to return at least these fields in
            this shape.' The provider's CI runs all consumer contracts as tests. If a
            proposed change would break any consumer's contract, it fails before deployment.
            This makes implicit contracts explicit, and breaking changes visible before they
            cause production incidents."""),
        [
            (
                "extends",
                "20240102T110000000000000",
                "Contract testing is how you verify API promises are being kept",
            ),
        ],
    ),
    (
        "20240102T160000000000000",
        "API Design as Organizational Boundary Signal",
        "permanent",
        ["api-design", "software-architecture", "organization"],
        [],
        dedent("""\
            Conway's Law states that organisations produce systems that mirror their
            communication structures. Applied to APIs: the boundaries between your APIs
            reflect the boundaries between your teams. A monolithic API with no internal
            seams usually means a team with no clear ownership boundaries. An API with
            clean domain separations usually means teams organised around those domains.

            This has a practical implication: if you want to change your API architecture,
            you may need to change your team structure first. The API is not just a technical
            artefact; it is a record of organisational decisions. Refactoring it without
            changing the underlying team structure typically produces the old structure again
            within months."""),
        [
            (
                "related",
                "20240102T110000000000000",
                "Organisational boundaries define what promises cross team lines",
            ),
        ],
    ),
    # ── Team communication cluster (TC1–TC5) ─────────────────────────────────
    (
        "20240103T110000000000000",
        "Shared Vocabulary Reduces Coordination Cost",
        "permanent",
        ["team-communication", "software-teams", "coordination"],
        [],
        dedent("""\
            When two engineers use the same word to mean different things, every conversation
            about that concept requires implicit negotiation about meaning before content can
            be discussed. The overhead is small per exchange but compounds across a year of
            collaboration. Shared vocabulary eliminates this tax.

            Building shared vocabulary is not just writing a glossary. It requires the team
            to notice when a term is being used ambiguously, agree on a definition, and then
            use the agreed definition consistently. Code reviews and design documents are
            vocabulary-building opportunities: when a term is unclear, defining it in the
            document is as important as clarifying the logic."""),
        [
            (
                "extends",
                "20240103T120000000000000",
                "Documentation is how shared vocabulary is formalised and transmitted across time and onboarding",
            ),
        ],
    ),
    (
        "20240103T120000000000000",
        "Documentation as Asynchronous Team Communication",
        "permanent",
        ["team-communication", "software-teams", "documentation"],
        [],
        dedent("""\
            A meeting is synchronous communication: it requires all participants to be present
            at the same time, and its output (decisions, shared understanding) exists only in
            the minds of attendees. Documentation is asynchronous: it can be consumed at any
            time, by people who were not present, including future team members who have not
            yet joined.

            Good documentation is not a meeting transcript; it is a distillation of the
            decisions and their rationale, written for a reader who lacks the context of the
            meeting. Teams that default to documentation over meetings scale their coordination
            without scaling their meeting load. Documentation is also searchable and linkable
            in ways that meeting recordings are not."""),
        [
            (
                "supports",
                "20240103T130000000000000",
                "Async documentation enables feedback loops that would otherwise require synchronous meetings",
            ),
        ],
    ),
    (
        "20240103T130000000000000",
        "Feedback Loops in Engineering Teams",
        "permanent",
        ["team-communication", "software-teams", "feedback"],
        [],
        dedent("""\
            Feedback loops in engineering exist at multiple timescales: the millisecond loop
            of a unit test, the hour loop of a code review, the week loop of a sprint
            retrospective, the quarter loop of a team health survey. Each loop catches
            different categories of error.

            The most valuable investment is usually in shortening the highest-impact loop
            that is currently too slow. A team with fast CI but no retrospective process
            catches individual bugs quickly but accumulates team dysfunction slowly. A team
            with excellent retrospectives but slow CI catches team problems but ships broken
            code frequently. Mapping which loops exist and how fast they are reveals where
            the bottlenecks in quality and alignment actually sit."""),
        [
            (
                "related",
                "20240103T110000000000000",
                "Feedback loops require shared vocabulary to be actionable — vague feedback is friction",
            ),
        ],
    ),
    (
        "20240103T140000000000000",
        "Conway's Law and System Design Alignment",
        "permanent",
        ["team-communication", "software-teams", "architecture"],
        [],
        dedent("""\
            Conway's Law — 'organisations design systems that mirror their own communication
            structure' — is usually cited as a warning, but it can be used as a design tool.
            If you want a particular system architecture, design the team structure that would
            naturally produce it. This is the 'inverse Conway manoeuvre': restructure teams
            to produce the system boundaries you want, rather than trying to impose boundaries
            on teams that are not organised to maintain them.

            The law's mechanism is simple: people build interfaces along the lines of least
            resistance in communication. Teams that talk frequently produce tightly coupled
            systems. Teams that communicate only through formal interfaces produce loosely
            coupled systems. Team topology is system topology."""),
        # No links — orphan in TC cluster (TC4)
        [],
    ),
    (
        "20240103T150000000000000",
        "The Cost of Implicit Assumptions in Specifications",
        "permanent",
        ["team-communication", "software-teams", "requirements"],
        [],
        dedent("""\
            Every specification contains unstated assumptions: facts the author considered
            obvious and therefore did not write down. The problem is that 'obvious' is
            relative to the author's context, which the implementer does not share. An
            assumption that is invisible to the author is invisible in the spec, but very
            visible — as a bug — in the implementation.

            The cheapest way to surface implicit assumptions is to have someone outside the
            authoring team attempt to implement from the spec before implementation begins.
            Every question they ask is an implicit assumption made explicit. Specification
            reviews are not editing exercises; they are assumption-excavation exercises.
            The goal is not a beautiful document but a document with no invisible load-bearing
            assumptions."""),
        [
            (
                "related",
                "20240103T120000000000000",
                "Documentation that makes assumptions explicit reduces the coordination cost of implicit vocabulary",
            ),
        ],
    ),
    # ── Cognitive-load cluster (CL1–CL6) ─────────────────────────────────────
    (
        "20240104T110000000000000",
        "Cognitive Load Theory Applied to Code Review",
        "permanent",
        ["cognitive-load", "code-review", "software-development"],
        [],
        dedent("""\
            Cognitive Load Theory (Sweller, 1988) distinguishes three types of load:
            intrinsic (the inherent complexity of the material), extraneous (complexity
            introduced by poor presentation), and germane (the effort of building new
            mental schemas). Code review involves all three.

            Intrinsic load varies with code complexity — a 10-line function with clear
            naming has low intrinsic load; a 400-line function with implicit state has high.
            Extraneous load is introduced by poor formatting, inconsistent naming, and
            missing context. Germane load is incurred when the reviewer must build a new
            mental model of an unfamiliar subsystem. Reviewers cannot reduce intrinsic load,
            but authors can reduce extraneous load through clarity, and both can manage
            germane load by limiting PR scope."""),
        [
            (
                "related",
                "20240104T120000000000000",
                "Chunking is the primary mechanism for reducing intrinsic cognitive load in review",
            ),
        ],
    ),
    (
        "20240104T120000000000000",
        "Chunking and Code Readability",
        "permanent",
        ["cognitive-load", "code-review", "mental-models"],
        [],
        dedent("""\
            Miller's chunking principle: working memory holds 7±2 chunks, but a 'chunk' can
            be a single digit or an entire familiar pattern. Expert programmers read
            'for i in range(len(xs))' as a single chunk (indexed loop); novices parse it
            token by token. Readability, then, is not about simplicity in absolute terms
            but about alignment with the reader's chunk library.

            Code that uses idiomatic patterns is more readable to experienced reviewers
            because those patterns are pre-chunked. Code that invents non-standard patterns
            forces decomposition of every expression. This is why code style guides and
            linters matter beyond aesthetic preference: they define the shared chunk library
            that makes review efficient for the whole team."""),
        [
            (
                "related",
                "20240104T110000000000000",
                "Chunking theory explains why cognitive load varies by reviewer expertise",
            ),
        ],
    ),
    (
        "20240104T130000000000000",
        "Working Memory Limits in Debugging",
        "permanent",
        ["cognitive-load", "code-review", "debugging"],
        [],
        dedent("""\
            Debugging requires holding multiple hypotheses simultaneously while tracing
            execution paths. Each active hypothesis consumes working-memory capacity.
            When hypotheses exceed capacity — typically when a bug requires tracing through
            more than three or four call frames simultaneously — recall becomes unreliable
            and hypotheses get silently dropped.

            External scaffolding (print statements, breakpoints, diagrams, rubber-duck
            narration) externalises the hypothesis queue, freeing WM for evaluation rather
            than storage. Expert debuggers are not faster because they have more WM capacity;
            they are faster because they have learned to externalise earlier and more
            systematically. Debugging is a memory-management problem as much as a
            logic problem."""),
        # No links — orphan in CL cluster (CL3)
        # (targeted by hub's 'questions' link, but that's cross-cluster — not counted)
        [],
    ),
    (
        "20240104T140000000000000",
        "Code Review Fatigue and Decision Quality",
        "permanent",
        ["cognitive-load", "code-review", "decision-making"],
        [],
        dedent("""\
            Decision fatigue research (Baumeister et al.) shows that decision quality
            degrades after sustained decision-making. Code review is decision-intensive:
            every line prompts micro-decisions about correctness, clarity, style, and risk.
            Review quality degrades across the day as decision resources deplete.

            The practical implication is that review quality is highest in the first two
            reviews of the day and degrades thereafter — not because of distraction but
            because of resource depletion. Teams that batch reviews into long sessions
            produce more approvals-without-scrutiny than teams that spread reviews through
            the day with breaks. Review culture should treat attention as a limited resource,
            not an infinite one."""),
        # No links — orphan in CL cluster (CL4)
        # (targeted by hub's 'contradicts' link, but cross-cluster — not counted)
        [],
    ),
    (
        "20240104T150000000000000",
        "The Seven Plus or Minus Two Rule for PR Size",
        "permanent",
        ["cognitive-load", "code-review", "process"],
        [],
        dedent("""\
            Miller's Law (7±2 items in working memory) provides a principled basis for PR
            size limits. A PR that changes 7 logical units — functions, classes, config
            sections — is at the edge of a reviewer's ability to hold the whole change in
            mind simultaneously. A PR that changes 20 logical units exceeds it.

            The corollary is that large PRs do not receive thorough review; they receive the
            appearance of review. A reviewer who cannot hold the full context approves
            implicitly, not explicitly. Keeping PRs small is not a courtesy; it is a
            structural prerequisite for the review process to function as intended. The
            constraint on PR size is a constraint on review quality."""),
        # No links — orphan in CL cluster (CL5)
        [],
    ),
    (
        "20240104T160000000000000",
        "Mental Models and Code Navigation",
        "permanent",
        ["cognitive-load", "code-review", "mental-models"],
        [],
        dedent("""\
            Navigating an unfamiliar codebase requires building a mental model: which
            components exist, what they do, how they interact. Each navigation action
            (jump to definition, trace a call stack, find usages) updates and refines the
            model. The cost of navigation is not in the keystrokes but in the cognitive
            overhead of keeping the developing model coherent.

            Developers with accurate mental models navigate in straight lines: they predict
            where a function is defined and are right. Developers building their first model
            navigate in spirals: each find triggers two more finds. Code that makes its
            structure visible — through naming, module boundaries, and consistent patterns —
            accelerates model-building. Opaque code forces spiral navigation indefinitely."""),
        # No links — orphan in CL cluster (CL6)
        [],
    ),
    # ── Orphan notes (O1–O15) ────────────────────────────────────────────────
    (
        "20240105T110000000000000",
        "Spaced Repetition and Long-Term Retention",
        "permanent",
        ["spaced-repetition", "memory-systems", "retention"],
        [],
        dedent("""\
            Spaced repetition exploits the spacing effect: memories are strengthened more by
            reviews spread across time than by massed practice in a single session. The
            forgetting curve (Ebbinghaus) shows that retention decays exponentially after
            learning, but each review resets the decay at a lower rate. Optimal review
            timing is just before the point of forgetting.

            SRS (Spaced Repetition Software) systems like Anki automate the scheduling,
            presenting cards at intervals calculated to maximise retention per unit of
            review time. The system is most effective for discrete facts and procedures,
            less so for complex reasoning chains that require construction rather than
            retrieval."""),
        [],
    ),
    (
        "20240105T120000000000000",
        "The Feynman Technique as Compression Test",
        "permanent",
        ["explanation-techniques", "teaching", "understanding"],
        [],
        dedent("""\
            The Feynman Technique: explain a concept as if teaching it to someone who knows
            nothing about it. Where you stumble — where you reach for jargon, or glide past
            a transition with 'and so therefore' — is exactly where your understanding has
            gaps. The technique works because explanation requires compression: you must
            identify what is essential versus incidental.

            The test is not whether you can produce words about the topic but whether you can
            produce a coherent causal chain without technical crutches. Understanding is the
            ability to rebuild the argument from first principles, not the ability to
            reproduce memorised sentences."""),
        [],
    ),
    (
        "20240105T130000000000000",
        "Why We Over-Highlight",
        "permanent",
        ["reading-habits", "passive-learning", "highlighting"],
        [],
        dedent("""\
            Studies consistently show that students highlight 20–50% of text they read,
            despite this having little effect on recall compared to active retrieval
            strategies. The explanation is fluency illusion: highlighted text feels more
            familiar on re-reading, which the reader interprets as understanding.

            Highlighting is also cognitively cheap. It requires recognising that something
            seems important without requiring you to articulate why or connect it to
            anything else you know. It provides the feeling of engagement without the cost
            of engagement. The marker in the margin is the productivity-theatre equivalent
            of copy-pasting code without understanding it."""),
        [],
    ),
    (
        "20240105T140000000000000",
        "Tool Fetishism in Productivity Culture",
        "permanent",
        ["productivity", "tool-overload", "distraction"],
        [],
        dedent("""\
            Productivity culture has a recurring pathology: belief that the right tool will
            solve the underlying problem of not doing work. New task managers, new note-taking
            apps, new calendar systems are adopted, configured elaborately, and eventually
            abandoned — not because they were bad tools but because the problem was not
            a tool problem.

            Tool switching is a form of procrastination that resembles productivity. It
            produces artefacts (configured systems, colour-coded tags) that look like output
            but substitute for actual output. The question 'what tool should I use?' is often
            a displacement of the question 'why am I not doing the thing?'"""),
        [],
    ),
    (
        "20240105T150000000000000",
        "The Map Is Not the Territory",
        "permanent",
        ["epistemology", "mental-models", "semantics"],
        [],
        dedent("""\
            Korzybski's aphorism names a persistent epistemic error: confusing the
            representation of a thing with the thing itself. A model is always a
            simplification; every model omits features of the territory it represents.
            The question is not whether the map is perfect but whether it is useful for
            the purpose at hand.

            Problems arise when the map is mistaken for reality: when a business model is
            treated as a guarantee, when a scientific theory is treated as final, when a
            word is treated as capturing everything about the thing it names. Intellectual
            honesty requires holding models lightly — using them as tools while remaining
            alert to where they diverge from the territory."""),
        [],
    ),
    (
        "20240105T160000000000000",
        "Interleaving Beats Massed Practice",
        "permanent",
        ["practice-science", "interleaving", "retention-strategies"],
        [],
        dedent("""\
            Interleaved practice — alternating between different problem types — produces
            better long-term retention than blocked practice (mastering one type before
            moving to the next), even though it feels harder and produces worse performance
            during the practice session itself. This is the 'desirable difficulty' principle.

            The mechanism: interleaving forces the learner to identify which strategy applies
            to each problem, not just execute a recently-primed strategy. This discrimination
            practice strengthens the retrieval cue for each strategy independently. Massed
            practice produces fluency within a session; interleaving produces durability
            across sessions."""),
        [],
    ),
    (
        "20240105T170000000000000",
        "The Generation Effect in Learning",
        "permanent",
        ["active-recall", "generation-effect", "memory-encoding"],
        [],
        dedent("""\
            The generation effect: words that learners generate themselves (by completing
            word fragments, answering questions, or reconstructing from partial cues) are
            remembered better than words presented for passive reading. The effect is robust
            across material types and age groups.

            The mechanism is encoding specificity: generating an item requires constructing
            a retrieval path to it, which makes that path available for later retrieval.
            Reading provides the item without requiring construction of a retrieval path.
            Active generation is not just more effortful; it is structurally different in
            what it builds. This is why writing notes in your own words produces better
            recall than copy-pasting source text."""),
        [],
    ),
    (
        "20240105T180000000000000",
        "Deliberate Practice Requires Feedback Cycles",
        "permanent",
        ["deliberate-practice", "skill-acquisition", "performance"],
        [],
        dedent("""\
            Ericsson's deliberate practice framework specifies that expertise requires not
            just time-on-task but practice structured around feedback: perform, observe
            outcome, compare to goal, adjust. Without a feedback mechanism, practice
            reinforces current patterns rather than correcting errors.

            The implication is that naive repetition does not produce expertise; it produces
            automated mediocrity. A programmer who writes code for 10 years without systematic
            code review, without studying others' code, and without measuring outcomes against
            goals does not become an expert; they become fluent at whatever they were doing
            from the start. Expertise is shaped by feedback, not time."""),
        [],
    ),
    (
        "20240105T190000000000000",
        "Retrieval Practice Strengthens Memory More Than Re-reading",
        "permanent",
        ["retrieval-practice", "memory-consolidation", "testing-effect"],
        [],
        dedent("""\
            The testing effect (Roediger & Karpicke, 2006): recalling information from
            memory produces stronger retention than re-studying the same material for an
            equal amount of time. The act of retrieval — not just the re-exposure — is what
            strengthens memory.

            The mechanism is reconstruction: each retrieval partially reconstructs the
            memory trace, making it more robust. Re-reading provides recognition cues that
            feel like retrieval but do not require reconstruction. Flashcards, practice
            problems, and recall-then-check study methods outperform re-reading because they
            force retrieval rather than recognition. This is the empirical basis for the
            advice to 'quiz yourself' rather than review your notes."""),
        [],
    ),
    (
        "20240106T110000000000000",
        "Expert Blind Spot in Teaching",
        "permanent",
        ["expertise", "teaching-gap", "instructional-design"],
        [],
        dedent("""\
            The expert blind spot (Nathan & Petrosino, 2003): domain experts systematically
            underestimate the difficulty of material for novices because experts have
            automated the component skills that novices must consciously apply. What is
            effortless for the expert — pattern recognition, chunk retrieval, implicit
            inference — is effortful for the novice.

            The practical failure mode: expert instructors skip steps they no longer
            consciously notice, use jargon they have forgotten is jargon, and pace
            explanations at the rate of their own understanding rather than the student's
            acquisition rate. The gap produces confusion that experts interpret as student
            deficiency when it is actually instructor omission."""),
        [],
    ),
    (
        "20240106T120000000000000",
        "The Curse of Knowledge",
        "permanent",
        ["cognitive-bias", "communication-failure", "perspective-taking"],
        [],
        dedent("""\
            The curse of knowledge (Heath & Heath): once you know something, it is very
            hard to imagine not knowing it. This makes it difficult to communicate with
            people who lack your knowledge, because you cannot easily simulate their
            ignorance. You reach for analogies that assume background knowledge your
            audience does not have.

            The bias is structural, not intentional. The expert is not condescending; they
            have genuinely lost access to the experience of not-knowing. The fix is not
            effort but calibration: testing explanations on actual novices, tracking where
            they lose the thread, and revising. The feedback loop that the curse of
            knowledge severs must be reinstated deliberately."""),
        [],
    ),
    (
        "20240106T130000000000000",
        "Semantic Satiation and Familiarity Traps",
        "permanent",
        ["perception", "language", "habituation"],
        [],
        dedent("""\
            Semantic satiation: repeat a word often enough and it temporarily loses its
            meaning — the sounds detach from the concept. The effect is a microcosm of a
            broader habituation phenomenon: frequent exposure reduces signal. Words,
            warnings, and patterns that once carried information become background noise.

            In engineering, this manifests as ignored lint warnings (because there are
            always 400 of them), unread TODOs, boilerplate README sections that are never
            updated. High-frequency, low-information stimuli train people to stop reading.
            The implication for code reviews, documentation, and monitoring alerts: signal
            should be reserved for signal. Noise in the channel degrades everything."""),
        [],
    ),
    (
        "20240106T140000000000000",
        "Note-Taking Is Not Learning",
        "permanent",
        ["study-myths", "passive-processing", "active-learning"],
        [],
        dedent("""\
            A common misconception: thorough notes demonstrate understanding. They demonstrate
            attendance, not comprehension. Transcribing a lecture or copying source material
            into a notebook is encoding without retrieval — it produces a record, not a
            memory.

            Learning requires the construction of retrievable mental representations, which
            requires active processing: predicting, questioning, connecting, explaining.
            Passive transcription does none of these. The notes may be comprehensive and
            useless. The test of note quality is not how much they contain but how well they
            support retrieval and reasoning when the source is no longer available."""),
        [],
    ),
    (
        "20240106T150000000000000",
        "The Illusion of Explanatory Depth",
        "permanent",
        ["metacognition", "self-assessment", "knowledge-gaps"],
        [],
        dedent("""\
            Rozenblit & Keil (2002): people consistently overestimate how well they can
            explain mechanical and causal processes. Ask someone to rate their understanding
            of how a toilet flush works, then ask them to actually explain it step by step.
            Their rating drops significantly after the attempt. The illusion is not about
            facts but about causal models.

            This matters because we use subjective confidence as a proxy for actual
            understanding, and this proxy is unreliable for complex systems. The fix is
            the same as for the Feynman technique: attempt explanation before assuming
            you have understanding. The stumbling reveals what the confidence rating conceals."""),
        [],
    ),
    (
        "20240106T160000000000000",
        "Survivorship Bias in Productivity Advice",
        "permanent",
        ["cognitive-bias", "productivity-culture", "selection-effects"],
        [],
        dedent("""\
            Productivity advice is dominated by the successful: people who write books and
            give talks about their system are, by selection, people whose system worked
            for them. We do not hear from the equal number of people who tried the same
            system and found it useless or harmful. The visible sample is massively biased
            toward the system's successes.

            The result: systems that worked for a specific combination of person, task
            type, and life context are marketed as universal methods. The listener's job is
            not to adopt the method but to extract the underlying principle and test whether
            it applies to their own context. No-one's productivity system is portable
            intact."""),
        [],
    ),
]


# ─── Renderer ────────────────────────────────────────────────────────────────


def render_note(
    note_id: str,
    title: str,
    note_type: str,
    tags: list[str],
    references: list[str],
    body: str,
    links: list[tuple[str, str, str]],
) -> str:
    """Render a note as a markdown file with YAML frontmatter."""
    # Fixed timestamp derived from ID for reproducibility
    ts = (
        f"{note_id[:4]}-{note_id[4:6]}-{note_id[6:8]}"
        f"T{note_id[9:11]}:{note_id[11:13]}:{note_id[13:15]}.000000"
    )

    lines = ["---"]
    lines.append(f"created: '{ts}'")
    lines.append(f"id: {note_id}")
    if references:
        lines.append("references:")
        for ref in references:
            lines.append(f"- '{ref}'")
    lines.append("tags:")
    for tag in tags:
        lines.append(f"- {tag}")
    # YAML single-quoted strings escape ' by doubling it.
    safe_title = title.replace("'", "''")
    lines.append(f"title: '{safe_title}'")
    lines.append(f"type: {note_type}")
    lines.append(f"updated: '{ts}'")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(body.strip())

    if links:
        lines.append("")
        lines.append("## Links")
        lines.append("")
        for link_type, target_id, description in links:
            lines.append(f"- {link_type} [[{target_id}]] {description}")

    lines.append("")
    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate demo vault notes")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory for note files (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print paths without writing"
    )
    args = parser.parse_args()

    out = args.output_dir
    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)

    written = 0
    for note in NOTES:
        note_id = note[0]
        filename = f"{note_id}.md"
        content = render_note(*note)
        path = out / filename

        if args.dry_run:
            print(f"  {path}")
        else:
            path.write_text(content)
            written += 1

    if args.dry_run:
        print(f"\n{len(NOTES)} notes would be written to {out}")
    else:
        print(f"Generated {written} notes in {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
