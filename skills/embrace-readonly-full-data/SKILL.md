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

## Complete official tool map

Use `embrace_call_readonly` with these remote tool names. For repeatable local smoke tests or when a host has not inherited the environment, use the prebuilt `scripts/embrace_mcp_call.py`; do not generate a new client script. The CLI accepts a tool name and a JSON object via `--arguments` and preserves the proxy's full JSON output.

```bash
zsh -lic 'uv run --project /Users/tamlh/workspaces/self/AI/Tools/embrace-readonly-mcp python /Users/tamlh/workspaces/self/AI/Tools/embrace-readonly-mcp/scripts/embrace_mcp_call.py embrace_list_readonly_tools'
```


### App and sessions

- `list_apps`: discover app IDs, platforms, regions, and latest versions.
- `get_app_details`: sessions, unique users, crash-free rate, and version totals.
- `get_top_versions`: version adoption.
- `get_session_distribution`: session breakdown by app version, OS, country, device, or manufacturer.

### Logs and exceptions

- `list_logs`: find log groups and obtain `group_id` values.
- `get_log_details`: counts, trends, templates, and token analysis for one log group.
- `get_log_distribution`: break a log group down by version, OS, country, device, or environment.
- `list_exceptions`: find web/Unity/Flutter exception groups.
- `get_exception_details`: inspect one exception group.

### Crashes and debug traces

- `list_crashes`: find crash groups and obtain `group_id` values.
- `get_crash_details`: crash impact, versions, foreground rate, and top frame.
- `get_crash_stack_samples`: full representative stack frames, timestamps, devices, and `session_id` values.
- `get_crash_distribution`: crash breakdown by version, OS, country, or device.
- `list_root_spans`: find slow or failing root operations.
- `get_root_span_stats`: timing and outcome statistics for one root span.
- `get_root_span_distribution`: root-span breakdown by version, OS, country, or device.

### Network diagnostics

- `list_network_domains`: domain-level network health.
- `list_network_endpoints`: endpoints ranked by latency, errors, or volume.
- `get_network_endpoint_errors`: HTTP status and connection-error breakdown.
- `get_network_endpoint_latency`: latency percentiles.
- `get_network_endpoint_timeseries`: performance over time.
- `get_network_endpoint_distribution`: endpoint breakdown by version, OS, country, device, status, or connection error.

## Standard debug workflow

1. `list_apps` → `get_app_details`.
2. `list_crashes`, `list_logs`, `list_root_spans`, or `list_network_endpoints`.
3. Follow the returned IDs with the relevant detail/distribution/stack tool.
4. For a crash, always request `get_crash_stack_samples`.
5. For a slow request, use endpoint errors, latency, then timeseries/distribution.

## Dashboard User Timeline support

The official MCP does not publish User Timeline tools, so use the local custom
read-only Dashboard tools when a Dashboard URL, `user_email`, or session IDs are
provided:

- `embrace_dashboard_list_user_sessions`: filter and paginate sessions by app and email.
- `embrace_dashboard_get_session_sequence`: retrieve the sequence between `first` and `last` session IDs.
- `embrace_dashboard_get_session_detail`: retrieve complete events for one session ID.

The Dashboard adapter runs headless Playwright with an authenticated local
browser profile. It allows only the three explicit session routes and only GET
or semantically read-only POST requests. It never returns cookies, auth headers,
or secrets. If browser authentication is unavailable, report that clearly
instead of falling back to undocumented arbitrary requests.

For a Dashboard URL:

1. Parse `app_id`, `user_email`, `first`, and `last`.
2. Call `embrace_dashboard_list_user_sessions` to validate the exact sessions.
3. Call `embrace_dashboard_get_session_sequence` when both boundary IDs exist.
4. Call `embrace_dashboard_get_session_detail` for each relevant session.
5. Preserve event IDs, timestamps, logs, spans, network requests, breadcrumbs,
   taps, and metadata in the investigation report.

For investigations:


1. Start with `list_apps` and `get_app_details`.
2. Use `list_logs`, `list_crashes`, `list_network_endpoints`, or
   `list_root_spans` to find identifiers.
3. Follow up with the corresponding detail, distribution, latency, error, or
   stack-sample tool using the returned IDs.
4. Preserve exact timestamps, versions, counts, and IDs in the report.

Do not expose arbitrary Dashboard endpoints or write methods. Do not ask for
or return `EMBRACE_API_TOKEN`, cookies, authorization headers, or secrets.
