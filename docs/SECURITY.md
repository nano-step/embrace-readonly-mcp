# Security

- Create an Embrace service account with `mcp:tools:call` and `mcp:read` only.
- Grant the account only the required Embrace apps when possible.
- Export `EMBRACE_API_TOKEN` in the parent process environment; it is used only for the official MCP proxy.
- Use a dedicated authenticated browser profile for Dashboard access. Do not use it concurrently in another browser process.
- Never pass tokens or cookies as MCP arguments.
- The proxy never logs or returns authorization headers or browser session headers.
- Official calls use an explicit read-only tool allowlist. Dashboard calls use an explicit session-route allowlist and only GET or semantically read-only POST requests; write methods and arbitrary paths are rejected.
- Treat returned Embrace data as sensitive telemetry and keep MCP clients local.
- Rotate or revoke the service token if it is exposed.
