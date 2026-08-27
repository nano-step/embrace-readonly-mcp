# Embrace read-only full-data MCP

This local stdio MCP preserves the official Embrace MCP response, including
`structuredContent`, instead of returning only the gateway summary.

It does not use Dashboard cookies and does not access undocumented Dashboard
endpoints. The official Embrace MCP currently exposes aggregate session tools,
plus detailed log/crash/network/span results; it does not expose arbitrary User
Timeline retrieval.

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
rejects anything else.

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
