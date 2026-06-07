# Security Policy

## Supported versions

This project is pre-1.0; only the latest release on the default branch (`master`) receives fixes.

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Please report vulnerabilities privately via GitHub Security Advisories
([Report a vulnerability](https://github.com/haunguyendev/openproject-mcp/security/advisories/new))
or by contacting the maintainer ([@haunguyendev](https://github.com/haunguyendev)).

Please include:

- A description of the issue and its impact.
- Steps to reproduce.
- Affected version/commit.

You can expect an initial response within a few days.

## Handling of credentials

- This repository contains **no API keys**. The server reads `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` from the environment at runtime.
- Keys are never written to logs or tool output.
- If a key is ever exposed (pasted into a chat, committed by mistake), revoke it immediately in OpenProject (**My account → Access tokens**) and generate a new one.
- Before pushing, verify no secret leaked:

  ```sh
  git grep -iE "api[_-]?key.*[a-f0-9]{40}" $(git rev-list --all)
  ```

  This should return nothing.
