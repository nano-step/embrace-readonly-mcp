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

### Official Embrace MCP passthrough

- `embrace_list_readonly_tools` returns the remote tool schemas.
- `embrace_call_readonly(tool_name, arguments)` forwards one allowlisted tool
  and returns the complete JSON-RPC response.

The server has an explicit allowlist of the 22 published Embrace read-only tools
and rejects anything else.

### Dashboard User Timeline adapter

These custom tools fill the User Timeline gap in the official MCP:

- `embrace_dashboard_list_user_sessions(app_id, user_email, resolution, max_pages)`
- `embrace_dashboard_get_session_sequence(app_id, first_id, last_id, user_email)`
- `embrace_dashboard_get_session_detail(app_id, session_id, user_email)`

They return the Dashboard session data, including logs, spans, network requests,
breadcrumbs, taps, views, IDs, timestamps, and metadata. Dashboard requests are
restricted to the three session routes and only GET or semantically read-only
POST requests. Write methods and arbitrary paths are rejected.

## Headless Dashboard setup

The Dashboard adapter uses Playwright with a persistent, authenticated browser
profile. Authenticate that profile once in Brave/Chromium, close the browser,
then run the MCP headlessly:

```sh
export EMBRACE_DASHBOARD_PROFILE_DIR="$HOME/.config/embrace-dashboard-profile"
export EMBRACE_DASHBOARD_PROFILE_DIRECTORY=Default
export EMBRACE_DASHBOARD_HEADLESS=true
```

Use `EMBRACE_DASHBOARD_HEADLESS=false` for an interactive re-authentication.
Do not use the profile concurrently in another browser process. Dashboard OAuth
is separate from `EMBRACE_API_TOKEN`, which only authenticates the official MCP
proxy. The adapter uses only the allowlisted Dashboard session routes and never
returns browser cookies or session headers.

## Skill

The workflow skill is at
[`skills/embrace-readonly-full-data/SKILL.md`](skills/embrace-readonly-full-data/SKILL.md).
Install or copy that directory into the skill directory used by your agent.
The skill routes Dashboard URLs to the custom Timeline tools and official
analytics/crash/network questions to the official passthrough tools.

## MCP client configuration

For a client that supports stdio MCP servers:

```json
{
  "mcpServers": {
    "embrace-raw-readonly": {
      "command": "zsh",
      "args": ["-lic", "exec uv run --project /path/to/embrace-readonly-mcp /path/to/embrace-readonly-mcp/server.py"],
      "env": {
        "EMBRACE_DASHBOARD_HEADLESS": "true",
        "EMBRACE_DASHBOARD_PROFILE_DIR": "/path/to/dashboard-profile",
        "EMBRACE_DASHBOARD_PROFILE_DIRECTORY": "Default"
      }
    }
  }
}
```

The parent shell must inherit `EMBRACE_API_TOKEN` for official tools. The
Dashboard adapter additionally requires an authenticated local browser profile.
See
[`docs/SECURITY.md`](docs/SECURITY.md) for credential handling.
