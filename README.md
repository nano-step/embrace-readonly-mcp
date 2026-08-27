# Embrace read-only full-data MCP

This local stdio MCP preserves the official Embrace MCP response, including
`structuredContent`, instead of returning only the gateway summary.

It uses a separate, headless Playwright Dashboard adapter for the read-only
User Timeline actions that the official MCP does not expose. The adapter uses an
authenticated local browser profile, an explicit endpoint allowlist, and never
returns cookies or authorization headers. It does not expose arbitrary methods
or paths.

The official Embrace MCP currently exposes aggregate session tools, plus detailed
log/crash/network/span results. The local adapter adds read-only Dashboard
session listing, sequence, and detail retrieval.

## Run

The parent MCP process must inherit the service-account token:

```sh
export EMBRACE_API_TOKEN='...'
uv run server.py
```

Do not pass the token as a tool argument or commit it to a file.

## Tools

- `embrace_list_readonly_tools` returns the remote tool schemas.
- `embrace_call_readonly(tool_name, arguments)` forwards one allowlisted tool
  and returns the complete JSON-RPC response.

The server has an explicit allowlist of the 22 published Embrace tools and
rejects anything else. Dashboard requests are separately restricted to GET or
semantically read-only POST requests for the session sequence, session list,
and session detail routes.

## Headless Dashboard setup

Authenticate once with a dedicated profile using `EMBRACE_DASHBOARD_HEADLESS=false`,
then use that profile headlessly:

```sh
export EMBRACE_DASHBOARD_PROFILE_DIR="$HOME/.config/embrace-dashboard-profile"
export EMBRACE_DASHBOARD_PROFILE_DIRECTORY=Default
export EMBRACE_DASHBOARD_HEADLESS=true
```

Do not use a profile concurrently in another browser process. The Dashboard
adapter requires browser OAuth/session authentication; `EMBRACE_API_TOKEN` only
authenticates the official MCP proxy.

## Skill

The workflow skill is at
[`skills/embrace-readonly-full-data/SKILL.md`](skills/embrace-readonly-full-data/SKILL.md).
Install or copy that directory into the skill directory used by your agent.
The skill instructs agents to discover schemas, preserve structured responses,
chain detail tools, and avoid undocumented Dashboard endpoints.

## MCP client configuration

For a client that supports stdio MCP servers:

```json
{
  "mcpServers": {
    "embrace-raw-readonly": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/embrace-readonly-mcp", "server.py"]
    }
  }
}
```

The client process must inherit `EMBRACE_API_TOKEN`. See
[`docs/SECURITY.md`](docs/SECURITY.md) for credential handling.
