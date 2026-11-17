# AGENTS.md

Instructions for AI agents working on **acodo**: utilidades puras de Python (validación,
conversión, parseo y logger) sin dependencias.

The shared sections below are the same in every project. Project-specific rules are at the
end, under **Project rules**, and take precedence when they differ.

<!-- shared:start — managed by assistant-skills/new-python-project (scaffold.py sync). Edit there, not here. -->
## Shared rules

**Language.** Code and identifiers in English. Docstrings, comments, README, `docs/`,
CHANGELOG, commits and user-facing messages in Spanish. This file stays in English.

**Tools.** `uv` only, never `pip install`; run everything from the project root.
Quality gate: `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`,
`uv run pytest`. The same gate as `poe check`, if Poe the Poet is installed globally; poe is
never a project dependency, and everything must also work with plain `uv run`.

**Workflow.**

1. Read `README.md`, `pyproject.toml`, this file and the related tests before changing code.
2. Make the smallest change that solves the task: no unrelated refactors, no formatting of
   untouched files, no new dependency without a reason (prefer the standard library).
3. Don't change CI, tool configuration or project structure unless the task needs it.
4. Don't run a failing command more than twice: stop, give the root cause and the exact error,
   propose the minimal fix and ask.
5. Don't run state-changing git commands (commit, push, tag, reset, rebase) unless the user
   asks or the commit policy in **Project rules** allows it. Never `--no-verify`.
6. Leave no secrets, temporary files or TODOs without context. Never hand-edit `uv.lock`.

**Code.** Strict type hints on every signature. Google-style docstrings: complete for public
identifiers, one line for private ones; a public docstring's `Raises` also lists the
exceptions raised by the private functions it calls. Comments explain the *why*. Prefer
simple, explicit code; `pathlib` over `os.path`. Ruff and ty enforce the rest; don't fight
them with ignores.

**Tests.** `pytest` in `tests/`. Cover relevant logic and every fixed bug; they must pass on
Linux and Windows.

**Commits.** Conventional Commits in Spanish (`feat:`, `fix:`, `docs:`, `test:`,
`refactor:`, `chore:`), one intent per commit, explaining the *why*.

**Releases.** Only for versioned projects (a real version and `CHANGELOG.md`). Before
pushing changes to the package, use the `python-release` skill. Without it: SemVer bump,
`## [Unreleased]` → `## [X.Y.Z] - YYYY-MM-DD` in `CHANGELOG.md`, `uv lock`, then
`chore: bump versión a X.Y.Z`. Never tag without confirmation.

**Done** when the quality gate and any extra gate in **Project rules** pass, and the README
and docs reflect any change in usage.

Project rules below take precedence over these. Shared rules change in assistant-skills
(`scaffold.py sync`), not by hand here.
<!-- shared:end -->

## Project rules

### What acodo is

A utility library published on PyPI as `acodo` (formerly `acodo-framework`). Python 3.13+,
**no runtime dependencies**: standard library only. Keep it that way; a runtime dependency
needs the user's explicit approval.

```
src/acodo/
├── utils/      # pure functions grouped by prefix: get_*, has_*, parse_*, to_*, valid_*
│               # (+ the SocialLink type); conventions and errors in the package docstring
└── logger/     # Logger: console and/or file with daily rotation
tests/          # pytest, one file per utils module plus logger and package
docs/           # Zensical site; API reference generated from the docstrings
```

- `acodo.logger` may import from `acodo.utils`, never the other way round.
- New functions go in the module of their prefix and follow the conventions in
  `acodo/utils/__init__.py`; export them from the package `__init__.py`.
- Every `__init__.py` has a docstring. `README.md` stays minimal (it is also the PyPI page).
- Don't modify `AGENTS.md` unless the user asks.

### Docstrings are the API docs

The API reference (`docs/` → API, via `mkdocstrings` and `api-autonav`, custom templates in
`docs_templates/`) is built from the docstrings. Public docstrings are complete and in Spanish,
with an `Examples` section when it shows behaviour that is not obvious.

### Extra quality gates

- `ty` must pass with `--error-on-warning` (as in CI).
- Documentation builds: `uv run zensical build` (`poe docs-build`; preview with `poe docs`).
  Zensical only, configured in `zensical.toml`; no MkDocs-only plugins or hooks.
- Coverage report: `poe cov` (CI uploads it to Codecov). Useful tests over a percentage.
- CI (`.github/workflows/ci.yaml`): `uv sync --locked`, ruff format/check, `ty check
  --error-on-warning`, pytest with coverage, on ubuntu and windows.

### Commit policy

Never commit automatically: report the result and wait for confirmation.

### Publishing

`publish.yml` publishes to PyPI on every push to `main` that touches `src/`,
`pyproject.toml`, `README.md` or `LICENSE`, unless the tag `vX.Y.Z` of the current version
already exists; it then creates the tag and a GitHub release. So a push that changes the
package **must** bump the version (shared **Releases** rules), or nothing is published.
`docs.yml` deploys the site to GitHub Pages on every push to `main`.
