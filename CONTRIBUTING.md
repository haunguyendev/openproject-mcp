# Contributing

Thanks for your interest in improving **OpenProject MCP**! Contributions of all kinds are welcome — bug reports, feature requests, docs, and code.

## Development setup

This project has no build step. The server is a single Python file with dependencies declared inline ([PEP 723](https://peps.python.org/pep-0723/)) and run by [`uv`](https://docs.astral.sh/uv/).

```sh
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the server locally
export OPENPROJECT_URL="https://your-openproject.example.com"
export OPENPROJECT_API_KEY="your-api-token"
uv run --script server/server.py
```

## Before opening a pull request

1. **Lint and format** with [ruff](https://docs.astral.sh/ruff/):

   ```sh
   uvx ruff check server/
   uvx ruff format server/
   ```

2. **Check syntax**: `python -m py_compile server/server.py`
3. Keep the server a **single, dependency-light file**. New runtime dependencies should be justified and added to the PEP 723 header in `server/server.py`.
4. Describe which **OpenProject API v3** endpoints your change touches.

## Tool design conventions

- Clear verb names (`create_work_package`, `report_overdue`).
- Docstrings describe **every** parameter — Claude reads them to learn how to call the tool.
- Return trimmed JSON with only useful fields, plus a `url` for direct access.
- Read operations are freely callable; write operations are confirmed by the skill before executing.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, etc. Keep commits focused.

## Reporting bugs / requesting features

Open an issue using the provided templates. For security issues, see [SECURITY.md](SECURITY.md) instead of filing a public issue.
