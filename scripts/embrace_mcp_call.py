#!/usr/bin/env python3
"""Call a local read-only Embrace proxy tool with JSON arguments."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
PROXY = ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("tool_name")
    parser.add_argument("--arguments", default="{}", help="JSON object")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    arguments = json.loads(args.arguments)
    if not isinstance(arguments, dict):
        raise SystemExit("--arguments must be a JSON object")

    params = StdioServerParameters(
        command="uv",
        args=["run", "server.py"],
        cwd=str(PROXY),
        env=os.environ.copy(),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(args.tool_name, arguments)
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(json.dumps(content.model_dump(), ensure_ascii=False))
            if result.isError:
                raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
