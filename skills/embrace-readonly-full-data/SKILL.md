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

Use `embrace_call_readonly` with these remote tool names:

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

## Dashboard and session limitation

This skill can inspect official Embrace analytics, crash stacks, root-span traces,
and network diagnostics. It cannot open the Dashboard User Timeline or retrieve
arbitrary session events by email/session ID because the official MCP does not
publish that capability. A supplied Dashboard URL is useful context, but it is
not fetched through cookies or undocumented Dashboard APIs.

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
