# Changelog

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
