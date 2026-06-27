"""Version single-source-of-truth contract.

`src/slipbox_mcp/__init__.py:__version__` is the only place the version is
written. `pyproject.toml` resolves it dynamically via
`[tool.setuptools.dynamic] version = {attr = "slipbox_mcp.__version__"}`, the
release workflow reads it to gate the publish tag, and `config.server_version`
derives from it. These tests pin that contract so a future divergence fails a
fast unit test instead of a tag push.
"""

import re
from importlib.metadata import PackageNotFoundError, version

import pytest

from slipbox_mcp import __version__


def test_version_is_pep440_shaped():
    # The release workflow strips a leading `v` from the git tag and compares
    # the remainder to __version__; a malformed value would break that compare.
    assert re.match(r"^\d+\.\d+\.\d+([.\-+].*)?$", __version__), __version__


def test_installed_metadata_matches_dunder():
    # Proves the pyproject dynamic-version wiring actually resolves to
    # __version__. CI installs the package (editable), so metadata is present;
    # skip cleanly if the tree was never installed.
    try:
        installed = version("slipbox-mcp")
    except PackageNotFoundError:
        pytest.skip("slipbox-mcp not installed; run `pip install -e .`")
    assert installed == __version__


def test_server_version_derives_from_dunder():
    from slipbox_mcp.config import ZettelkastenConfig

    assert ZettelkastenConfig().server_version == __version__
