"""Seed data for eval tests -- builds a realistic slipbox state."""
from slipbox_mcp.models.schema import LinkType, NoteType


def populate_slipbox(zettel_service) -> dict[str, str]:
    """Build a 14-note slipbox with links and return ID reference dict.

    Returns dict mapping descriptive keys to note IDs, e.g.:
        {"hub_philosophy_of_mind": "20260403...", "permanent_spinoza": "20260403...", ...}
    """
    # -- Hub (1) --
    hub = zettel_service.create_note(
        title="Philosophy of Mind",
        content=(
            "Philosophy of mind investigates the nature of consciousness, mental "
            "states, and their relation to the physical world. Central questions "
            "include the hard problem of consciousness, the explanatory gap, and "
            "whether mind is fundamental or emergent."
        ),
        note_type=NoteType.HUB,
        tags=["philosophy-of-mind", "consciousness"],
    )

    # -- Structure (2) --
    panpsychism = zettel_service.create_note(
        title="Panpsychism Overview",
        content=(
            "Panpsychism is the view that consciousness or mentality is a "
            "fundamental and ubiquitous feature of reality. Variants range from "
            "constitutive panpsychism (micro-level experience combines into "
            "macro-level consciousness) to cosmopsychism (the universe itself "
            "is conscious). This note organizes the main panpsychist positions "
            "explored in this slipbox."
        ),
        note_type=NoteType.STRUCTURE,
        tags=["panpsychism", "consciousness", "philosophy-of-mind"],
    )

    wittgenstein = zettel_service.create_note(
        title="Wittgenstein's Philosophy",
        content=(
            "Ludwig Wittgenstein's work divides into early (Tractatus) and late "
            "(Philosophical Investigations) periods. The early work presents a "
            "picture theory of language; the later work replaces it with language "
            "games and forms of life. This structure note organizes Wittgenstein's "
            "key ideas as they relate to philosophy of mind."
        ),
        note_type=NoteType.STRUCTURE,
        tags=["wittgenstein", "language", "philosophy-of-mind"],
    )

    # -- Permanent (6) --
    spinoza = zettel_service.create_note(
        title="Spinoza's Substance Monism",
        content=(
            "Spinoza argues in the Ethics that there is only one substance, which "
            "he identifies with God or Nature (Deus sive Natura). Thought and "
            "extension are two attributes of this single substance, not separate "
            "realms. This dissolves the mind-body problem by denying dualism at "
            "the ontological level."
        ),
        note_type=NoteType.PERMANENT,
        tags=["spinoza", "monism", "metaphysics"],
    )

    hard_problem = zettel_service.create_note(
        title="The Hard Problem of Consciousness",
        content=(
            "David Chalmers formulated the hard problem: why and how do physical "
            "processes give rise to subjective experience? Even a complete "
            "functional account of the brain would leave unexplained why there is "
            "something it is like to be conscious. The hard problem motivates "
            "both panpsychism and property dualism."
        ),
        note_type=NoteType.PERMANENT,
        tags=["consciousness", "hard-problem", "qualia"],
    )

    faggin = zettel_service.create_note(
        title="Faggin's Quantum Information Panpsychism",
        content=(
            "Federico Faggin proposes that consciousness is intrinsic to "
            "information processing at the quantum level. In his view, quantum "
            "fields possess an inner experiential aspect that classical physics "
            "cannot capture. This positions consciousness not as an emergent "
            "byproduct but as fundamental to the fabric of reality."
        ),
        note_type=NoteType.PERMANENT,
        tags=["panpsychism", "quantum", "faggin", "information"],
    )

    private_language = zettel_service.create_note(
        title="Wittgenstein's Private Language Argument",
        content=(
            "Wittgenstein argues in the Investigations that a purely private "
            "language -- one whose words refer to the speaker's immediate private "
            "sensations and nothing else -- is impossible. Language requires "
            "public criteria for correctness. If there is no way to check whether "
            "a word is used consistently, it has no meaning."
        ),
        note_type=NoteType.PERMANENT,
        tags=["wittgenstein", "language", "private-language"],
    )

    iit = zettel_service.create_note(
        title="Integrated Information Theory (IIT)",
        content=(
            "Giulio Tononi's IIT proposes that consciousness corresponds to "
            "integrated information, measured by phi. A system is conscious to "
            "the degree that it is both differentiated (many possible states) and "
            "integrated (cannot be reduced to independent parts). IIT implies "
            "that consciousness is graded and widespread in nature."
        ),
        note_type=NoteType.PERMANENT,
        tags=["consciousness", "iit", "tononi", "information"],
    )

    russellian = zettel_service.create_note(
        title="Russellian Monism",
        content=(
            "Russellian monism holds that physics describes the relational and "
            "structural properties of matter but is silent about its intrinsic "
            "nature. The intrinsic properties grounding physical structure may be "
            "experiential or proto-experiential, offering a middle path between "
            "physicalism and dualism."
        ),
        note_type=NoteType.PERMANENT,
        tags=["panpsychism", "russellian-monism", "physics"],
    )

    # -- Literature (2) --
    lit_faggin = zettel_service.create_note(
        title="Notes on Faggin's Irreducible",
        content=(
            "Reading notes from Federico Faggin's Irreducible. Key themes: "
            "consciousness as fundamental, the limits of classical computation, "
            "quantum information as the seat of experience, and the irreducibility "
            "of first-person awareness to algorithmic processes."
        ),
        note_type=NoteType.LITERATURE,
        tags=["faggin", "panpsychism", "quantum"],
        references=["Faggin, F. (2022). Irreducible: Consciousness, Life, Computers, and Human Nature."],
    )

    lit_investigations = zettel_service.create_note(
        title="Notes on Wittgenstein's Philosophical Investigations",
        content=(
            "Reading notes from the Philosophical Investigations. Key themes: "
            "language games replace the picture theory, meaning is use, forms of "
            "life ground linguistic practice, the beetle-in-a-box thought "
            "experiment undermines private ostensive definition."
        ),
        note_type=NoteType.LITERATURE,
        tags=["wittgenstein", "language-games"],
        references=["Wittgenstein, L. (1953). Philosophical Investigations. Blackwell."],
    )

    # -- Fleeting (2) --
    iit_question = zettel_service.create_note(
        title="Is IIT just mathematical panpsychism?",
        content=(
            "IIT's phi measure assigns some degree of consciousness to any "
            "system with integrated information. Doesn't this collapse into "
            "panpsychism by another name? Need to compare IIT's axioms with "
            "constitutive panpsychism more carefully."
        ),
        note_type=NoteType.FLEETING,
        tags=["iit", "panpsychism", "question"],
    )

    spinoza_faggin = zettel_service.create_note(
        title="Explore connection between Spinoza and Faggin",
        content=(
            "Both Spinoza and Faggin treat consciousness as fundamental rather "
            "than emergent. Spinoza's dual-aspect monism (thought and extension "
            "as attributes of one substance) resonates with Faggin's view that "
            "quantum information has an experiential inner aspect. Worth tracing "
            "the lineage more carefully."
        ),
        note_type=NoteType.FLEETING,
        tags=["spinoza", "faggin", "reading-list"],
    )

    # -- Orphan (1) --
    pasta = zettel_service.create_note(
        title="Best Pasta Recipes",
        content=(
            "Cacio e pepe: pecorino, black pepper, pasta water. The key is "
            "emulsifying the cheese with starchy water off heat. Carbonara: "
            "guanciale, egg yolks, pecorino, black pepper -- never cream."
        ),
        note_type=NoteType.PERMANENT,
        tags=["cooking", "recipes"],
    )

    # -- Links (12) --
    # Hub -> Structure
    zettel_service.create_link(hub.id, panpsychism.id, LinkType.REFERENCE)
    zettel_service.create_link(hub.id, wittgenstein.id, LinkType.REFERENCE)

    # Structure -> Permanent (panpsychism branch)
    zettel_service.create_link(panpsychism.id, spinoza.id, LinkType.REFERENCE)
    zettel_service.create_link(panpsychism.id, hard_problem.id, LinkType.REFERENCE)
    zettel_service.create_link(panpsychism.id, faggin.id, LinkType.REFERENCE)

    # Permanent <-> Permanent
    zettel_service.create_link(spinoza.id, hard_problem.id, LinkType.EXTENDS)  # substance monism addresses the hard problem
    zettel_service.create_link(iit.id, faggin.id, LinkType.SUPPORTS)  # both link consciousness to information

    # Structure -> Permanent (wittgenstein branch)
    zettel_service.create_link(wittgenstein.id, private_language.id, LinkType.REFERENCE)
    zettel_service.create_link(wittgenstein.id, russellian.id, LinkType.REFERENCE)  # later work connects to intrinsic natures

    # Permanent <-> Permanent (cross-branch)
    zettel_service.create_link(private_language.id, hard_problem.id, LinkType.CONTRADICTS)  # if no private language, qualia are suspect

    # Literature -> Permanent
    zettel_service.create_link(lit_faggin.id, faggin.id, LinkType.SUPPORTS)

    # Fleeting -> Permanent
    zettel_service.create_link(iit_question.id, iit.id, LinkType.RELATED)

    return {
        "hub_philosophy_of_mind": hub.id,
        "structure_panpsychism": panpsychism.id,
        "structure_wittgenstein": wittgenstein.id,
        "permanent_spinoza": spinoza.id,
        "permanent_hard_problem": hard_problem.id,
        "permanent_faggin": faggin.id,
        "permanent_private_language": private_language.id,
        "permanent_iit": iit.id,
        "permanent_russellian": russellian.id,
        "literature_faggin_book": lit_faggin.id,
        "literature_investigations": lit_investigations.id,
        "fleeting_iit_question": iit_question.id,
        "fleeting_spinoza_faggin": spinoza_faggin.id,
        "orphan_pasta": pasta.id,
    }
