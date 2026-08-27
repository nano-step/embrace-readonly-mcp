# Architecture

```text
MCP client -> local stdio proxy -> Embrace Streamable HTTP MCP
                         \-> EMBRACE_API_TOKEN (environment only)
```

The proxy exposes two local tools:

- `embrace_list_readonly_tools`: returns the published remote schemas.
- `embrace_call_readonly`: forwards one allowlisted remote tool and returns the complete JSON-RPC result.

The allowlist is explicit and currently contains the 22 published Embrace
read-only tools. The proxy does not use Dashboard cookies or private Dashboard
endpoints. Individual User Timeline retrieval is not available through the
published Embrace MCP and remains a Dashboard capability.
