# Security

- Create an Embrace service account with `mcp:tools:call` and `mcp:read` only.
- Grant the account only the required Embrace apps when possible.
- Export `EMBRACE_API_TOKEN` in the parent process environment.
- Never pass tokens or cookies as MCP arguments.
- The proxy never logs or returns authorization headers.
- Treat returned Embrace data as sensitive telemetry and keep MCP clients local.
- Rotate or revoke the service token if it is exposed.
