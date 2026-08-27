"""Full-fidelity, read-only proxy for the published Embrace MCP tools."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from typing import Any

from mcp.server.fastmcp import FastMCP

REMOTE_URL = "https://mcp.embrace.io/mcp"
REQUEST_TIMEOUT_SECONDS = 60

# Keep this explicit so a future remote write tool cannot be reached accidentally.
READ_ONLY_TOOLS = frozenset(
    {
        "get_app_details",
        "get_crash_details",
        "get_crash_distribution",
        "get_crash_stack_samples",
        "get_exception_details",
        "get_log_details",
        "get_log_distribution",
        "get_network_endpoint_distribution",
        "get_network_endpoint_errors",
        "get_network_endpoint_latency",
        "get_network_endpoint_timeseries",
        "get_root_span_distribution",
        "get_root_span_stats",
        "get_session_distribution",
        "get_top_versions",
        "list_apps",
        "list_crashes",
        "list_exceptions",
        "list_logs",
        "list_network_domains",
        "list_network_endpoints",
        "list_root_spans",
    }
)

mcp = FastMCP(
    "embrace-readonly-full-data",
    instructions=(
        "Proxy for Embrace's published read-only tools. "
        "Responses are returned as full JSON, including structuredContent. "
        "The official API does not expose arbitrary User Timeline retrieval."
    ),
)


def _token() -> str:
    token = os.environ.get("EMBRACE_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("EMBRACE_API_TOKEN is not configured")
    return token


def _decode_response(body: bytes) -> dict[str, Any]:
    text = body.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Streamable HTTP may use an SSE response. Preserve the last JSON data
        # event, without attempting to interpret or expose headers/cookies.
        events = [
            line.removeprefix("data: ").strip()
            for line in text.splitlines()
            if line.startswith("data: ")
        ]
        for event in reversed(events):
            try:
                value = json.loads(event)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise RuntimeError("Embrace MCP returned a non-JSON response")


def _remote_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode("utf-8")
    request = urllib.request.Request(
        REMOTE_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return _decode_response(response.read())
    except urllib.error.HTTPError as error:
        # Do not include request headers or the token in the diagnostic.
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Embrace MCP HTTP {error.code}: {body[:1000]}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Embrace MCP connection failed: {error.reason}") from error


async def _call_remote(method: str, params: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_remote_request, method, params)


@mcp.tool()
async def embrace_list_readonly_tools() -> str:
    """Return the official Embrace read-only tool schemas as full JSON."""
    response = await _call_remote("tools/list", {})
    result = response.get("result", {})
    tools = result.get("tools", []) if isinstance(result, dict) else []
    filtered = [
        tool for tool in tools if isinstance(tool, dict) and tool.get("name") in READ_ONLY_TOOLS
    ]
    return json.dumps(
        {"jsonrpc": "2.0", "result": {"tools": filtered}},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def embrace_call_readonly(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> str:
    """Call one published Embrace tool and return its complete JSON-RPC result.

    This intentionally accepts arbitrary JSON arguments because the remote tool
    schemas evolve independently. Use embrace_list_readonly_tools first when the
    required arguments are unknown.
    """
    if tool_name not in READ_ONLY_TOOLS:
        raise ValueError(f"Tool is not in the read-only allowlist: {tool_name}")

    response = await _call_remote(
        "tools/call",
        {"name": tool_name, "arguments": arguments or {}},
    )
    return json.dumps(response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
