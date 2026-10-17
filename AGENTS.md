# AGENTS.md

## Language

- **Code and identifiers in English**: variables, functions, constants, classes, methods,
  parameters, modules, and tests.
- **Documentation in Spanish**: docstrings, comments, error messages, README, docs, and commits.
- User-facing error messages must be in Spanish. Exception names and internal identifiers must
  be in English.
- This file, `AGENTS.md`, is written in English so the agent does not need to translate
  instructions.

## Expected structure (uv workspace monorepo)

```bash
.
├── .github/                # Automated config for GitHub
├── .local/                 # Private local files, not tracked by git
├── docs/                   # Zensical documentation source (not a workspace member)
├── packages/
│   ├── acodo-framework/    # Core package (zero deps, pure utilities)
│   │   ├── src/acodo/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── acodo-cli/          # Typer CLI (depends on acodo-framework at runtime)
│   │   ├── src/acodo_cli/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── acodo-template/     # Project scaffold (depends on acodo-framework, use acodo-cli in dev)
│       ├── pyproject.toml
│       └── README.md
├── .gitattributes
├── .gitignore
├── .python-version
├── AGENTS.md
├── pyproject.toml          # Workspace root ([tool.uv.workspace] only)
├── uv.lock                 # Single lockfile for the whole workspace
└── README.md               # Minimal informative project overview
```

- Every `__init__.py` must include a short docstring describing the module or package.
- Every workspace member must have its own `README.md`. Read it before changing that member.
- The root `README.md` must be informative and minimal: what it is, installation, basic usage,
  and quality commands. Do not turn it into an extensive manual.
- Do not modify this file (`AGENTS.md`) under any circumstance. If a task appears to require
  changing it, ask developer.

## Workspace rules (load-bearing)

- **One `uv.lock` and one virtualenv at the root serve every member.** A member is not a
  separate environment to activate; it is a package in the same resolution.
- **Use `uv sync --all-packages`**, not a bare `uv sync`. A bare sync resolves only the root
  project and its dev group; every other member is absent and imports fail with
  `ModuleNotFoundError`.
- **Run tools from the root** so one pass covers every member. A lint or type check run inside
  a single package sees a subset of the code and config.
- To run a command against a specific member from any workspace directory:
  `uv run --package <member-name> <command>`.
- A member's dependency belongs in that member's `pyproject.toml`, **not** the root's. The root
  pins the workspace and dev tooling; a dependency added there is invisible to the package that
  actually needs it when installed standalone.
- Inter-member dependencies are declared with `[tool.uv.sources]` and `workspace = true`:
  ```toml
  [tool.uv.sources]
  acodo-framework = { workspace = true }
  ```

## Tools and canonical commands

Do not use `pip install` directly.

From the workspace root:

```bash
uv sync --all-packages
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

Documentation (Zensical, not MkDocs commands):

```bash
uv run zensical build       # build the site
uv run zensical serve       # local preview
```

If a tool is missing, ask the developer:

```bash
uv add --dev <tool>          # workspace dev tooling (root)
uv add --package <member> <dependency>  # member runtime dependency
```

## Documentation with Zensical

- Documentation lives in `docs/` at the repository root. It is **not** a uv workspace member.
- Zensical reads either `mkdocs.yml` or `zensical.toml`. New configuration should use
  `zensical.toml` when possible; `mkdocs.yml` remains supported for compatibility.
- Use `uv run zensical build` and `uv run zensical serve` instead of `mkdocs build` /
  `mkdocs serve`.
- When adding settings during the transition, prefer `mkdocs.yml` examples from the Zensical
  configuration reference so the project remains compatible with both builders until a full
  migration to `zensical.toml` is decided.
- Do not add MkDocs-only plugins or build hooks; verify plugin compatibility before adopting one.
- Generated output goes to `site_dir`. Do not commit it.

## Agent workflow

1. Before changing anything, read the root `README.md`, root `pyproject.toml`, the target
   member's `README.md`, its `pyproject.toml`, and the related tests.
2. Make the smallest necessary change. Do not refactor unrelated code.
3. If you need a new dependency, justify it. If the standard library can solve it, do not add it.
   Add member dependencies to that member's `pyproject.toml`, not the root.
4. Do not modify CI, global configuration, or project structure unless the task requires it.
5. Before finishing, run the quality commands from the root and fix until they pass.
6. If something fails and you cannot resolve it, show the exact error and propose the minimal fix.
7. Do not leave secrets, temporary files, or TODOs without context.

## Code rules

- Follow PEP 8 and Pythonic style with strict type annotations.
- Use `acodo-framework` (module `acodo`) as the utility library.
- Use Google-style docstrings for public identifiers: complete, with examples when they add value.
- For private identifiers, use brief docstrings.
- Do not repeat obvious things in docstrings or add unnecessary examples.
- Avoid overengineering. Prefer simple and explicit solutions.
- Keep functions and classes small, with clear English names.
- Workspace members must not introduce dependency cycles. `acodo-framework` must never import
  from `acodo-cli` or `acodo-template`.

Example of a public docstring:

```python
def sum_numbers(a: int, b: int) -> int:
    """Suma dos números enteros.

    Args:
        a: Primer número.
        b: Segundo número.

    Returns:
        La suma de ``a`` y ``b``.

    Examples:
        >>> sum_numbers(2, 3)
        5
    """
    return a + b
```

## Tests

- Use `pytest`.
- Cover relevant logic and fixed bugs.
- Do not chase 100% coverage. Prioritize useful and readable tests.
- Tests must run on Linux and Windows.
- Test files live in each member's `tests/` directory. Run `uv run pytest` from the root to
  cover all members.

## CI

- GitHub Actions must work on `ubuntu-latest` and `windows-latest`.
- Minimum steps, run from the workspace root:
    - `uv sync --all-packages`
    - `uv run ruff format --check .`
    - `uv run ruff check .`
    - `uv run ty check`
    - `uv run pytest`
- Use a supported Python version declared in the root `pyproject.toml`.
- You may use `astral-sh/setup-uv` to install `uv`.

## Commits

- Never commit automatically; always report task success and wait for confirmation.
- Use Conventional Commits in Spanish.
- Examples:
    - `feat: añade cálculo de totales`
    - `fix: corrige validación de entrada`
    - `docs: actualiza ejemplos de uso`
    - `test: cubre casos límite`
    - `chore: renombrado de ficheros`
- A commit must be atomic and explain the why, not only the what.
- Do not mix unrelated changes.
- Prefix a commit that touches a single member with the member name when it adds clarity:
  `feat(cli): añade subcomando de sincronización`.

## Definition of done

A task is done when:

- `uv run python dev.py check` passes without errors (run from the workspace root).
- Documentation and README are updated if the API or usage changes.
- Zensical still builds: `uv run zensical build` passes.
- The commit is atomic and in Spanish.

## Limits

- Do not modify `AGENTS.md` under any circumstance.
- Do not use `pip install` directly.
- Do not use a bare `uv sync` when the task depends on other members; use `uv sync --all-packages`.
- Do not add unnecessary dependencies.
- Do not change CI, Ruff, ty, pytest, or Zensical configuration without justification.
- Do not format unrelated files.
- Do not rewrite code that is not necessary for the task.
- If you cannot ask, choose the minimal change and document the assumption in the commit or PR.
