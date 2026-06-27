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

# Distribution name on PyPI (note: differs from the import name slipbox_mcp).
DIST_NAME = "slipbox-mcp"
# Simple PEP 440 release shape: N.N.N with an optional pre/post/dev suffix.
PEP440_RELEASE_RE = r"^\d+\.\d+\.\d+([.\-+].*)?$"


def test_version_is_pep440_shaped():
    # The release workflow strips a leading `v` from the git tag and compares
    # the remainder to __version__; a malformed value would break that compare.
    assert re.match(PEP440_RELEASE_RE, __version__), (
        f"__version__ {__version__!r} is not a PEP 440 release string"
    )


def test_installed_metadata_matches_dunder():
    # Proves the pyproject dynamic-version wiring actually resolves to
    # __version__. CI installs the package (editable), so metadata is present;
    # skip cleanly if the tree was never installed.
    try:
        installed = version(DIST_NAME)
    except PackageNotFoundError:
        pytest.skip(f"{DIST_NAME} not installed; run `pip install -e .`")
    assert installed == __version__, (
        f"built metadata {installed!r} != __version__ {__version__!r}; "
        "dynamic-version wiring is out of sync"
    )


def test_server_version_derives_from_dunder():
    from slipbox_mcp.config import ZettelkastenConfig

    assert ZettelkastenConfig().server_version == __version__
