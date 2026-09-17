# Security Policy

## Supported versions

Security fixes go into the latest release on [PyPI](https://pypi.org/project/slipbox-mcp/). Please upgrade before reporting.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub: open the [Security tab](https://github.com/jamesfishwick/slipbox-mcp/security) and choose **Report a vulnerability**. Please don't open a public issue.

Include the version, how to reproduce it, and what an attacker could do with it.

## Scope

Slipbox runs locally and reads and writes notes under the paths you configure. Reports about these are especially welcome:

- Reading or writing files outside the configured notes directory, for example through a crafted note ID or link
- Exposure of note contents or the SQLite index to other local users
- Anything an MCP client could trigger that goes beyond the documented tools
