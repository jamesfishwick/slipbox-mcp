"""Tests for configuration path expansion."""

import os
import stat
from pathlib import Path

import pytest

from slipbox_mcp.config import _expand_path, ensure_private_dir

_POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix", reason="POSIX file-mode semantics required"
)


def test_expand_path_tilde_expands_to_absolute():
    result = _expand_path("~/notes")
    assert result.is_absolute(), f"Expected absolute path, got {result}"
    assert not str(result).startswith("~"), f"Tilde should be expanded, got {result}"


def test_expand_path_plain_relative_unchanged():
    result = _expand_path("data/notes")
    assert str(result) == "data/notes", (
        f"Relative path should be unchanged, got {result}"
    )


def test_expand_path_absolute_passthrough():
    result = _expand_path("/absolute/path")
    assert str(result) == "/absolute/path", (
        f"Absolute path should pass through, got {result}"
    )


def test_expand_path_nonexistent_user_raises():
    with pytest.raises(ValueError, match="could not be expanded"):
        _expand_path("~nonexistentuser_xyzzy/notes")


def test_expand_path_dot_unchanged():
    result = _expand_path(".")
    assert str(result) == ".", f"Dot should be unchanged, got {result}"


# ---------------------------------------------------------------------------
# ensure_private_dir: data dirs must be owner-only regardless of umask
# ---------------------------------------------------------------------------


@_POSIX_ONLY
def test_ensure_private_dir_creates_owner_only(tmp_path):
    """A freshly created data dir is 0o700 even under a permissive umask."""
    target = tmp_path / "data" / "notes"
    old_umask = os.umask(0o000)  # most permissive umask, to prove mode is enforced
    try:
        returned = ensure_private_dir(target)
    finally:
        os.umask(old_umask)

    assert returned == target, "ensure_private_dir should return the created path"
    assert target.is_dir(), f"Expected {target} to be created"
    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode == 0o700, f"Expected 0o700, got {oct(mode)}"


@_POSIX_ONLY
def test_ensure_private_dir_tightens_existing_loose_dir(tmp_path):
    """A pre-existing world-readable dir is re-tightened to 0o700."""
    target = tmp_path / "loose"
    target.mkdir(mode=0o755)
    os.chmod(target, 0o777)  # explicitly loosen past any umask masking

    ensure_private_dir(target)

    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode == 0o700, f"Expected 0o700 after tightening, got {oct(mode)}"


def test_ensure_private_dir_is_idempotent(tmp_path):
    """Calling twice on the same path does not raise and keeps the dir."""
    target = tmp_path / "d"
    ensure_private_dir(target)
    ensure_private_dir(target)
    assert target.is_dir()


# ---------------------------------------------------------------------------
# Cluster report path
# ---------------------------------------------------------------------------


def _config(**overrides):
    from slipbox_mcp.config import ZettelkastenConfig

    fields = {"base_dir": "/vault", "cluster_report_path": None}
    fields.update(overrides)
    return ZettelkastenConfig(**fields)


def test_cluster_report_defaults_next_to_relative_database():
    cfg = _config(database_path="data/db/zettelkasten.db")
    assert cfg.get_cluster_report_path() == (
        Path("/vault/data/db/cluster-analysis.json")
    )


def test_cluster_report_follows_absolute_database_path():
    """Two vaults with different databases never share a report."""
    a = _config(database_path="/a/db/z.db").get_cluster_report_path()
    b = _config(database_path="/b/db/z.db").get_cluster_report_path()
    assert a == Path("/a/db/cluster-analysis.json")
    assert b == Path("/b/db/cluster-analysis.json")


def test_cluster_report_override_absolute():
    cfg = _config(database_path="data/db/z.db", cluster_report_path="/elsewhere/r.json")
    assert cfg.get_cluster_report_path() == Path("/elsewhere/r.json")


def test_cluster_report_override_relative_resolves_against_base_dir():
    cfg = _config(cluster_report_path="reports/r.json")
    assert cfg.get_cluster_report_path() == Path("/vault/reports/r.json")


@pytest.mark.parametrize("raw", [None, ""])
def test_cluster_report_env_unset_or_empty_means_default(monkeypatch, raw):
    from slipbox_mcp.config import ZettelkastenConfig

    if raw is None:
        monkeypatch.delenv("SLIPBOX_CLUSTER_REPORT_PATH", raising=False)
    else:
        monkeypatch.setenv("SLIPBOX_CLUSTER_REPORT_PATH", raw)
    assert ZettelkastenConfig().cluster_report_path is None


def test_cluster_report_env_var_is_read(monkeypatch, tmp_path):
    from slipbox_mcp.config import ZettelkastenConfig

    monkeypatch.setenv("SLIPBOX_CLUSTER_REPORT_PATH", str(tmp_path / "r.json"))
    assert ZettelkastenConfig().get_cluster_report_path() == tmp_path / "r.json"
