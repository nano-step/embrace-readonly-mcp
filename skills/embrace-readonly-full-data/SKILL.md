---
name: embrace-readonly-full-data
description: Use the local read-only Embrace MCP proxy when investigating Embrace app health, logs, crashes, network spans, or full structured tool results.
compatibility: "MCP client with embrace-raw-readonly configured and EMBRACE_API_TOKEN inherited"
metadata:
  version: "1.0.0"
  author: "kokorolx"
  read_only: "true"
triggers:
  - "investigate Embrace"
  - "investigate app crash"
  - "find session logs"
  - "debug mobile performance"
  - "analyze photo picker"
---

# Embrace read-only full data

Use `embrace_list_readonly_tools` to inspect the published tool schemas, then use
`embrace_call_readonly` with the exact remote tool name and JSON arguments.

The proxy preserves the complete official response, including `structuredContent`,
metadata, group IDs, and crash sample session IDs. Prefer a narrow time window,
app version, message filter, and limit when possible; expand only when needed.

For investigations:

1. Start with `list_apps` and `get_app_details`.
2. Use `list_logs`, `list_crashes`, `list_network_endpoints`, or
   `list_root_spans` to find identifiers.
3. Follow up with the corresponding detail, distribution, latency, error, or
   stack-sample tool using the returned IDs.
4. Preserve exact timestamps, versions, counts, and IDs in the report.

The official Embrace MCP does not currently expose arbitrary User Timeline
retrieval. Do not invent or call undocumented Dashboard endpoints. Do not ask
for or return `EMBRACE_API_TOKEN`, cookies, authorization headers, or secrets.
