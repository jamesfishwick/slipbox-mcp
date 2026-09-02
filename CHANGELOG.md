# Changelog

## [1.5.2](https://github.com/jamesfishwick/slipbox-mcp/compare/v1.5.1...v1.5.2) (2026-09-02)


### Bug Fixes

* **deps:** pin mcp to &lt;2 for v1 fastmcp API ([c4c9d22](https://github.com/jamesfishwick/slipbox-mcp/commit/c4c9d225971f618d64ff610a6413bd7608a5ae4b))

## [1.5.1](https://github.com/jamesfishwick/slipbox-mcp/compare/v1.5.0...v1.5.1) (2026-08-24)


### Performance Improvements

* add missing SQLite indexes on link and tag FK columns ([#76](https://github.com/jamesfishwick/slipbox-mcp/issues/76)) ([8db6674](https://github.com/jamesfishwick/slipbox-mcp/commit/8db6674c51faee028e51685162d36d21883669ed))
* pre-filter find_similar_notes candidates instead of scanning the corpus ([#77](https://github.com/jamesfishwick/slipbox-mcp/issues/77)) ([3bd4699](https://github.com/jamesfishwick/slipbox-mcp/commit/3bd469966d912734f565401c542adf9221af273a))
* remove per-hit N+1 in search_by_text ([#70](https://github.com/jamesfishwick/slipbox-mcp/issues/70)) ([dab26ed](https://github.com/jamesfishwick/slipbox-mcp/commit/dab26ed11c20a6b70bb536f6758041ad25b79ebd))

## [1.5.0](https://github.com/jamesfishwick/slipbox-mcp/compare/v1.4.0...v1.5.0) (2026-06-28)


### Miscellaneous Chores

* release 1.5.0 ([#51](https://github.com/jamesfishwick/slipbox-mcp/issues/51)) ([05798c5](https://github.com/jamesfishwick/slipbox-mcp/commit/05798c58eee7be0aaddc0cf029e98cf4f506f21b))

## [1.4.0](https://github.com/jamesfishwick/slipbox-mcp/compare/v1.3.0...v1.4.0) (2026-06-27)


### Features

* PyPI-first install docs + release-please autoversioning ([#37](https://github.com/jamesfishwick/slipbox-mcp/issues/37)) ([5d00a1c](https://github.com/jamesfishwick/slipbox-mcp/commit/5d00a1cfe0a4f907d74d799e960df41bebaa0ba9))


### Bug Fixes

* harden note storage writes and indexing count ([#47](https://github.com/jamesfishwick/slipbox-mcp/issues/47)) ([03f725d](https://github.com/jamesfishwick/slipbox-mcp/commit/03f725d9508fa8e61ffa5b62b213fff87fa453a2))


### Performance Improvements

* fetch the hub note once in `slipbox_get_linked_notes` instead of per row ([#44](https://github.com/jamesfishwick/slipbox-mcp/issues/44))


### Maintenance

This release also folds in substantial housekeeping (no behavior change):

* consolidate linting and formatting on Ruff, enforced across the whole repo ([#42](https://github.com/jamesfishwick/slipbox-mcp/issues/42))
* make the LLM eval suite opt-in (label / manual) instead of path-triggered ([#43](https://github.com/jamesfishwick/slipbox-mcp/issues/43))
* extract a shared `parse_enum` helper and remove dead code ([#41](https://github.com/jamesfishwick/slipbox-mcp/issues/41), [#44](https://github.com/jamesfishwick/slipbox-mcp/issues/44), [#45](https://github.com/jamesfishwick/slipbox-mcp/issues/45))
* type cluster report stats with a `TypedDict` ([#46](https://github.com/jamesfishwick/slipbox-mcp/issues/46))
* add atomic-write failure coverage and refine tests ([#48](https://github.com/jamesfishwick/slipbox-mcp/issues/48))

## 1.3.0 (2026-06-27)

First release on PyPI. Install with `pipx install slipbox-mcp` or `uvx slipbox-mcp`.

### Features

* Simplify install and add a PyPI publishing pipeline ([#34](https://github.com/jamesfishwick/slipbox-mcp/pull/34)) — a `slipbox-mcp` console-script entry point and single `SLIPBOX_BASE_DIR` config collapse client setup to one command.

_Releases from here on are managed automatically by [release-please](https://github.com/googleapis/release-please) from Conventional Commit messages; entries below this line are appended by the bot._
