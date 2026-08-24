"""find_similar_notes must pre-filter candidates instead of scanning the corpus.

A note that shares no tag or link with the source always scores 0, so scoring it
is wasted work. The service restricts scoring to candidates from the repository
for threshold > 0, and falls back to the full corpus only at threshold 0 (where
0-similarity notes are still wanted).
"""

from unittest.mock import patch

from slipbox_mcp.models.schema import LinkType


def test_find_similarity_candidates_includes_sharers_excludes_disconnected(
    zettel_service,
):
    repo = zettel_service.repository
    source = zettel_service.create_note("Source", "content", tags=["alpha"])
    shared_tag = zettel_service.create_note("SharedTag", "content", tags=["alpha"])
    target = zettel_service.create_note("Target", "content", tags=[])
    disconnected = zettel_service.create_note("Disc", "content", tags=["zzz"])
    zettel_service.create_link(source.id, target.id, LinkType.REFERENCE)

    candidate_ids = {n.id for n in repo.find_similarity_candidates(source.id)}

    assert shared_tag.id in candidate_ids  # shares a tag
    assert target.id in candidate_ids  # outgoing link target
    assert source.id not in candidate_ids  # excludes self
    assert disconnected.id not in candidate_ids  # no shared tag or link


def test_find_similar_notes_prefilters_instead_of_full_scan(zettel_service):
    source = zettel_service.create_note("Source", "shared body", tags=["alpha"])
    similar = zettel_service.create_note("Similar", "shared body", tags=["alpha"])
    for i in range(3):
        zettel_service.create_note(f"Disc {i}", "unrelated", tags=[f"tag{i}"])

    repo = zettel_service.repository
    with patch.object(repo, "get_all", wraps=repo.get_all) as spy_get_all:
        results = zettel_service.find_similar_notes(source.id, threshold=0.1)

    spy_get_all.assert_not_called()  # no full-corpus scan
    result_ids = {n.id for n, _ in results}
    assert similar.id in result_ids
    assert all("Disc" not in n.title for n, _ in results)


def test_find_similar_notes_threshold_zero_uses_full_corpus(zettel_service):
    source = zettel_service.create_note("Source", "content", tags=["alpha"])
    disconnected = zettel_service.create_note("Disc", "content", tags=["zzz"])

    repo = zettel_service.repository
    with patch.object(repo, "get_all", wraps=repo.get_all) as spy_get_all:
        results = zettel_service.find_similar_notes(source.id, threshold=0.0)

    spy_get_all.assert_called()  # fallback preserves full-corpus behavior
    result_ids = {n.id for n, _ in results}
    assert disconnected.id in result_ids  # 0-similarity note still returned at t=0
