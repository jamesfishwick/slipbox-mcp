"""Tests for ClusterService pure functions."""

from unittest.mock import MagicMock

from helpers import make_note

from slipbox_mcp.models.schema import LinkType, NoteType
from slipbox_mcp.services.cluster_service import (
    CO_OCCURRENCE_THRESHOLD,
    MIN_CLUSTER_SIZE,
    ClusterCandidate,
    ClusterReport,
    ClusterService,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TAG_PYTHON = "python"
TAG_TESTING = "testing"
TAG_ASYNC = "async"
TAG_DESIGN = "design"
TAG_ARCHITECTURE = "architecture"
TAG_DATABASES = "databases"
TAG_MACHINE_LEARNING = "machine-learning"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_tagged_notes(tag_pairs: list[tuple[str, ...]], count: int) -> list:
    """Create *count* notes for each tag combination in *tag_pairs*."""
    notes = []
    for tags in tag_pairs:
        for i in range(count):
            notes.append(make_note(title=f"Note {tags} #{i}", tags=list(tags)))
    return notes


def _make_cluster_notes(n: int, tags: list[str] | None = None) -> list:
    """Create *n* notes each carrying at least two shared tags."""
    tags = tags or [TAG_PYTHON, TAG_TESTING]
    return [make_note(title=f"Cluster note {i}", tags=tags) for i in range(n)]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestBuildTagCooccurrence:
    """build_tag_cooccurrence computes tag pair frequencies above threshold."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_pair_above_threshold_is_included(self):
        # Arrange
        notes = _make_tagged_notes(
            [(TAG_PYTHON, TAG_TESTING)], count=CO_OCCURRENCE_THRESHOLD
        )

        # Act
        result = self.svc.build_tag_cooccurrence(notes)

        # Assert
        key = (TAG_PYTHON, TAG_TESTING)
        assert key in result, (
            f"Expected {key} in cooccurrence at threshold {CO_OCCURRENCE_THRESHOLD}"
        )
        assert result[key] == CO_OCCURRENCE_THRESHOLD, (
            f"Expected count {CO_OCCURRENCE_THRESHOLD}, got {result[key]}"
        )

    def test_pair_below_threshold_is_excluded(self):
        # Arrange
        notes = _make_tagged_notes(
            [(TAG_PYTHON, TAG_TESTING)], count=CO_OCCURRENCE_THRESHOLD - 1
        )

        # Act
        result = self.svc.build_tag_cooccurrence(notes)

        # Assert
        assert len(result) == 0, "Pairs below threshold must be excluded"

    def test_tags_are_sorted_alphabetically_in_keys(self):
        # Arrange -- "testing" > "python" alphabetically, so key should be (python, testing)
        notes = _make_tagged_notes(
            [(TAG_TESTING, TAG_PYTHON)], count=CO_OCCURRENCE_THRESHOLD
        )

        # Act
        result = self.svc.build_tag_cooccurrence(notes)

        # Assert
        assert (TAG_PYTHON, TAG_TESTING) in result, (
            "Tag pair keys must be alphabetically sorted"
        )
        assert (TAG_TESTING, TAG_PYTHON) not in result, "Reverse order must not appear"


class TestFindTagClusters:
    """find_tag_clusters uses union-find to group co-occurring tags."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_single_pair_forms_a_cluster(self):
        # Arrange
        cooccurrence = {(TAG_PYTHON, TAG_TESTING): 5}

        # Act
        clusters = self.svc.find_tag_clusters(cooccurrence)

        # Assert
        assert len(clusters) == 1, "Single pair should produce exactly one cluster"
        assert clusters[0] == {TAG_PYTHON, TAG_TESTING}, (
            f"Expected {{python, testing}}, got {clusters[0]}"
        )

    def test_overlapping_pairs_merge_into_one_cluster(self):
        # Arrange
        cooccurrence = {
            (TAG_PYTHON, TAG_TESTING): 5,
            (TAG_PYTHON, TAG_ASYNC): 4,
        }

        # Act
        clusters = self.svc.find_tag_clusters(cooccurrence)

        # Assert
        assert len(clusters) == 1, "Overlapping pairs must merge into a single cluster"
        assert clusters[0] == {TAG_PYTHON, TAG_TESTING, TAG_ASYNC}, (
            f"Expected {{python, testing, async}}, got {clusters[0]}"
        )

    def test_disjoint_pairs_form_separate_clusters(self):
        # Arrange
        cooccurrence = {
            (TAG_PYTHON, TAG_TESTING): 5,
            (TAG_DESIGN, TAG_ARCHITECTURE): 4,
        }

        # Act
        clusters = self.svc.find_tag_clusters(cooccurrence)

        # Assert
        assert len(clusters) == 2, "Disjoint pairs must produce two separate clusters"
        cluster_sets = [frozenset(c) for c in clusters]
        assert frozenset({TAG_PYTHON, TAG_TESTING}) in cluster_sets, (
            "python/testing cluster not found"
        )
        assert frozenset({TAG_DESIGN, TAG_ARCHITECTURE}) in cluster_sets, (
            "design/architecture cluster not found"
        )

    def test_empty_input_returns_empty(self):
        # Arrange
        cooccurrence = {}

        # Act
        clusters = self.svc.find_tag_clusters(cooccurrence)

        # Assert
        assert clusters == [], "Empty cooccurrence must yield empty cluster list"


class TestGetClusterNotes:
    """get_cluster_notes filters notes by tag overlap with cluster tags."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_note_with_two_matching_tags_is_included(self):
        # Arrange
        cluster_tags = {TAG_PYTHON, TAG_TESTING, TAG_ASYNC}
        note = make_note(tags=[TAG_PYTHON, TAG_TESTING])

        # Act
        result = self.svc.get_cluster_notes([note], cluster_tags)

        # Assert
        assert len(result) == 1, "Note with >= 2 matching tags must be included"
        assert result[0] is note, "Returned note should be the same object"

    def test_note_with_one_matching_tag_is_excluded(self):
        # Arrange
        cluster_tags = {TAG_PYTHON, TAG_TESTING, TAG_ASYNC}
        note = make_note(tags=[TAG_PYTHON, TAG_DATABASES])

        # Act
        result = self.svc.get_cluster_notes([note], cluster_tags)

        # Assert
        assert len(result) == 0, "Note with only 1 matching tag must be excluded"


class TestHasStructureNote:
    """has_structure_note checks for existing structure notes covering a tag set."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_structure_note_with_two_overlapping_tags_returns_true(self):
        # Arrange
        cluster_tags = {TAG_PYTHON, TAG_TESTING, TAG_ASYNC}
        structure = make_note(
            note_type=NoteType.STRUCTURE,
            tags=[TAG_PYTHON, TAG_TESTING],
        )

        # Act
        result = self.svc.has_structure_note([structure], cluster_tags)

        # Assert
        assert result is True, (
            "Structure note with >= 2 overlapping tags should return True"
        )

    def test_permanent_note_with_matching_tags_returns_false(self):
        # Arrange
        cluster_tags = {TAG_PYTHON, TAG_TESTING}
        permanent = make_note(
            note_type=NoteType.PERMANENT,
            tags=[TAG_PYTHON, TAG_TESTING],
        )

        # Act
        result = self.svc.has_structure_note([permanent], cluster_tags)

        # Assert
        assert result is False, "Permanent note must not count as structure note"

    def test_structure_note_with_one_overlap_returns_false(self):
        # Arrange
        cluster_tags = {TAG_PYTHON, TAG_TESTING}
        structure = make_note(
            note_type=NoteType.STRUCTURE,
            tags=[TAG_PYTHON, TAG_DATABASES],
        )

        # Act
        result = self.svc.has_structure_note([structure], cluster_tags)

        # Assert
        assert result is False, "Structure note with only 1 overlap must return False"


class TestCountInternalLinks:
    """count_internal_links counts links whose target is within the cluster."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_links_between_cluster_members_are_counted(self):
        # Arrange
        note_a = make_note(title="A")
        note_b = make_note(title="B")
        note_a.add_link(note_b.id, LinkType.REFERENCE)

        # Act
        count = self.svc.count_internal_links([note_a, note_b])

        # Assert
        assert count == 1, "Link from A to B (both in cluster) should be counted"

    def test_links_to_external_notes_are_not_counted(self):
        # Arrange
        note_a = make_note(title="A")
        external_id = "external-note-id-999"
        note_a.add_link(external_id, LinkType.REFERENCE)

        # Act
        count = self.svc.count_internal_links([note_a])

        # Assert
        assert count == 0, "Link to note outside cluster must not be counted"


class TestCountOrphans:
    """count_orphans identifies notes with no links and not targeted by others."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_note_with_no_links_and_not_targeted_is_orphan(self):
        # Arrange
        orphan = make_note(title="Orphan")

        # Act
        count = self.svc.count_orphans([orphan])

        # Assert
        assert count == 1, "Isolated note must be counted as orphan"

    def test_note_targeted_by_another_is_not_orphan(self):
        # Arrange
        target = make_note(title="Target")
        source = make_note(title="Source")
        source.add_link(target.id, LinkType.REFERENCE)

        # Act
        count = self.svc.count_orphans([source, target])

        # Assert -- target has no outgoing links but IS targeted, so not orphan
        #        -- source has outgoing links so not orphan either
        assert count == 0, "Note targeted by another must not be counted as orphan"


class TestScoreCluster:
    """score_cluster computes a composite health score for a note cluster."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_below_min_cluster_size_returns_none(self):
        # Arrange
        notes = _make_cluster_notes(MIN_CLUSTER_SIZE - 1)

        # Act
        result = self.svc.score_cluster(notes)

        # Assert
        assert result is None, (
            f"Cluster with {MIN_CLUSTER_SIZE - 1} notes must return None"
        )

    def test_at_min_cluster_size_returns_dict_with_expected_keys(self):
        # Arrange
        notes = _make_cluster_notes(MIN_CLUSTER_SIZE)

        # Act
        result = self.svc.score_cluster(notes)

        # Assert
        assert result is not None, (
            f"Cluster with {MIN_CLUSTER_SIZE} notes must return a dict"
        )
        expected_keys = {
            "note_count",
            "orphan_count",
            "internal_links",
            "density",
            "score",
            "newest_date",
        }
        assert set(result.keys()) == expected_keys, (
            f"Result keys mismatch: {set(result.keys())}"
        )
        assert result["note_count"] == MIN_CLUSTER_SIZE, (
            f"Expected note_count {MIN_CLUSTER_SIZE}, got {result['note_count']}"
        )

    def test_score_is_clamped_to_one(self):
        # Arrange -- all orphans, high urgency => could push score > 1.0
        notes = _make_cluster_notes(20)

        # Act
        result = self.svc.score_cluster(notes)

        # Assert
        assert result is not None, "Score result should not be None for 20 notes"
        assert result["score"] <= 1.0, f"Score {result['score']} exceeds 1.0 clamp"

    def test_density_is_zero_when_no_internal_links(self):
        # Arrange
        notes = _make_cluster_notes(MIN_CLUSTER_SIZE)

        # Act
        result = self.svc.score_cluster(notes)

        # Assert
        assert result is not None, "Score result should not be None at min cluster size"
        assert result["density"] == 0.0, (
            f"Density should be 0.0 with no links, got {result['density']}"
        )
        assert result["internal_links"] == 0, (
            f"Expected 0 internal links, got {result['internal_links']}"
        )


class TestReportPath:
    """ClusterService should support configurable report paths."""

    def test_save_report_to_custom_path(self, tmp_path):
        """save_report should use the configured report path."""
        from datetime import datetime

        service = ClusterService(report_path=tmp_path / "report.json")
        report = ClusterReport(
            generated_at=datetime.now(),
            clusters=[],
            stats={},
            dismissed_cluster_ids=[],
        )
        path = service.save_report(report)
        assert path == tmp_path / "report.json"
        assert path.exists()

    def test_load_report_from_custom_path(self, tmp_path):
        """load_report should read from the configured report path."""
        from datetime import datetime

        service = ClusterService(report_path=tmp_path / "report.json")
        report = ClusterReport(
            generated_at=datetime.now(),
            clusters=[],
            stats={"total_notes": 0},
            dismissed_cluster_ids=[],
        )
        service.save_report(report)
        loaded = service.load_report()
        assert loaded is not None
        assert loaded.stats == {"total_notes": 0}

    def test_load_tolerates_unknown_candidate_key(self, tmp_path):
        """A report written by a future version (extra candidate field) still
        loads: the unknown key is dropped rather than crashing the constructor."""
        import json
        from datetime import datetime

        from slipbox_mcp.models.cluster_models import ClusterCandidate

        path = tmp_path / "report.json"
        service = ClusterService(report_path=path)
        report = ClusterReport(
            generated_at=datetime.now(),
            clusters=[
                ClusterCandidate(
                    id="c1",
                    suggested_title="C1",
                    tags=["alpha"],
                    notes=[{"id": "n1", "title": "N1"}],
                    note_count=1,
                    orphan_count=0,
                    internal_links=0,
                    density=0.0,
                    score=0.5,
                    newest_date=datetime.now(),
                )
            ],
            stats={"total_notes": 1},
            dismissed_cluster_ids=[],
        )
        service.save_report(report)

        # Simulate a newer schema by injecting an unknown candidate field.
        data = json.loads(path.read_text())
        data["clusters"][0]["future_field"] = "ignore me"
        path.write_text(json.dumps(data))

        loaded = service.load_report()
        assert loaded is not None, "unknown key must not fail the whole load"
        assert len(loaded.clusters) == 1
        assert loaded.clusters[0].id == "c1"
        assert not hasattr(loaded.clusters[0], "future_field")


class TestDetectClusters:
    """detect_clusters runs the full cluster detection pipeline."""

    def test_detect_clusters_accepts_notes_directly(self):
        """detect_clusters should work with a plain note list."""
        from slipbox_mcp.models.schema import Note, NoteType, Tag

        service = ClusterService()
        # Create enough notes with shared tags to form a cluster
        notes = []
        for i in range(6):
            notes.append(
                Note(
                    title=f"Test Note {i}",
                    content=f"Content {i}",
                    note_type=NoteType.PERMANENT,
                    tags=[Tag(name="alpha"), Tag(name="beta")],
                )
            )
        report = service.detect_clusters(notes=notes)

        # 6 notes all sharing alpha+beta form exactly one cluster. The previous
        # isinstance-only assertion passed even if the pipeline found nothing.
        assert isinstance(report, ClusterReport)
        assert report.stats["total_notes"] == 6
        assert len(report.clusters) == 1, (
            f"expected one cluster, got {len(report.clusters)}"
        )
        cluster = report.clusters[0]
        assert cluster.note_count == 6
        assert set(cluster.tags) == {"alpha", "beta"}


class TestSuggestTitle:
    """suggest_title builds a human-readable cluster title from tags."""

    def setup_method(self):
        self.svc = ClusterService(zettel_service=MagicMock())

    def test_longest_tag_becomes_primary_titlecased(self):
        # Arrange
        tags = {TAG_PYTHON, TAG_TESTING}  # "testing" is longer

        # Act
        title = self.svc.suggest_title(tags)

        # Assert
        assert title == "Testing Knowledge Map", (
            f"Expected 'Testing Knowledge Map', got '{title}'"
        )

    def test_hyphens_replaced_with_spaces(self):
        # Arrange
        tags = {TAG_MACHINE_LEARNING, TAG_PYTHON}

        # Act
        title = self.svc.suggest_title(tags)

        # Assert
        assert title == "Machine Learning Knowledge Map", (
            f"Hyphens must be replaced with spaces, got '{title}'"
        )


# ---------------------------------------------------------------------------
# create_structure_note (domain logic moved out of the MCP tool handler)
# ---------------------------------------------------------------------------


class TestCreateStructureNote:
    """create_structure_note owns the structure-note domain logic."""

    def _cluster(self, note_infos):
        return ClusterCandidate(
            id="c1",
            suggested_title="Alpha Knowledge Map",
            tags=["alpha", "beta"],
            notes=note_infos,
            note_count=len(note_infos),
            orphan_count=0,
            internal_links=0,
            density=0.0,
            score=0.8,
        )

    def _service(self, tmp_path):
        zettel = MagicMock()
        created = MagicMock()
        created.id = "struct1"
        created.title = "Alpha Knowledge Map"
        zettel.create_note.return_value = created
        zettel.create_link.return_value = (MagicMock(), MagicMock())
        service = ClusterService(zettel_service=zettel, report_path=tmp_path / "r.json")
        return service, zettel, created

    def test_creates_structure_note_and_links_each_member(self, tmp_path):
        service, zettel, created = self._service(tmp_path)
        cluster = self._cluster(
            [{"id": "n1", "title": "N1"}, {"id": "n2", "title": "N2"}]
        )

        note, links = service.create_structure_note(cluster)

        assert note is created
        assert links == 2
        kwargs = zettel.create_note.call_args.kwargs
        assert kwargs["note_type"] == NoteType.STRUCTURE
        assert kwargs["tags"] == ["alpha", "beta"]
        assert "[[n1]] N1" in kwargs["content"]
        assert "## Synthesis" in kwargs["content"]
        assert zettel.create_link.call_count == 2
        link_kwargs = zettel.create_link.call_args.kwargs
        assert link_kwargs["link_type"] == LinkType.REFERENCE
        assert link_kwargs["bidirectional"] is True

    def test_title_override_and_create_links_false(self, tmp_path):
        service, zettel, _ = self._service(tmp_path)
        cluster = self._cluster([{"id": "n1", "title": "N1"}])

        _, links = service.create_structure_note(
            cluster, title="Custom Title", create_links=False
        )

        assert links == 0
        zettel.create_link.assert_not_called()
        assert zettel.create_note.call_args.kwargs["title"] == "Custom Title"

    def test_a_failed_member_link_does_not_abort_the_rest(self, tmp_path):
        service, zettel, _ = self._service(tmp_path)
        zettel.create_link.side_effect = [
            Exception("boom"),
            (MagicMock(), MagicMock()),
        ]
        cluster = self._cluster(
            [{"id": "n1", "title": "N1"}, {"id": "n2", "title": "N2"}]
        )

        _, links = service.create_structure_note(cluster)

        assert links == 1, "a failed member link must not abort the others"
