"""Tests for configuration path expansion."""

import os
import stat

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
