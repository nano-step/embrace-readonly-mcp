#!/usr/bin/env python3
"""Capture read-only, authenticated Embrace Dashboard UI traffic.

This uses the visible Dashboard UI and an existing local Brave profile. It never
prints cookies, authorization headers, or request headers. Captured response
bodies remain local and are intended for investigation only.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from playwright.async_api import async_playwright

BRAVE = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
BRAVE_PROFILE = Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser"
HEADLESS = os.environ.get("EMBRACE_DASHBOARD_HEADLESS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    sensitive = ("token", "secret", "authorization", "cookie", "password", "api_key")
    redacted = [
        (key, "<redacted>")
        if any(part in key.lower() for part in sensitive)
        else (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunparse(parsed._replace(query=urlencode(redacted)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, default=Path("/tmp/embrace-dashboard-capture.json"))
    parser.add_argument("--wait-ms", type=int, default=8000)
    parser.add_argument("--profile-directory", default="Default")
    parser.add_argument("--session-id", action="append", default=[])
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme != "https" or parsed.netloc != "dash.embrace.io":
        raise SystemExit("Only https://dash.embrace.io URLs are allowed")
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2 or path_parts[0] != "app":
        raise SystemExit("Dashboard URL must include /app/<app_id>/...")
    app_id = path_parts[1]
    if not Path(BRAVE).exists():
        raise SystemExit(f"Brave executable not found: {BRAVE}")
    if not BRAVE_PROFILE.exists():
        raise SystemExit(f"Brave profile not found: {BRAVE_PROFILE}")

    responses: list[dict[str, object]] = []
    response_bodies: list[dict[str, object]] = []
    dashboard_session_header: str | None = None

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            str(BRAVE_PROFILE),
            executable_path=BRAVE,
            headless=HEADLESS,
            args=[f"--profile-directory={args.profile_directory}"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        async def on_response(response) -> None:
            parsed_response = urlparse(response.url)
            # Capture only same-page API/fetch traffic; never capture request
            # headers, cookies, or authorization. Static assets are omitted.
            if response.request.resource_type not in {"xhr", "fetch"}:
                return
            if parsed_response.scheme != "https":
                return
            if not (
                parsed_response.netloc == "dash.embrace.io"
                or (
                    parsed_response.netloc.startswith("dash-api")
                    and parsed_response.netloc.endswith(".embrace.io")
                )
            ):
                return
            content_type = response.headers.get("content-type", "")
            try:
                post_data = response.request.post_data
            except UnicodeDecodeError:
                post_data = "<binary>"
            record: dict[str, object] = {
                "url": safe_url(response.url),
                "status": response.status,
                "content_type": content_type,
                "resource_type": response.request.resource_type,
                "method": response.request.method,
                "post_data": post_data,
            }
            responses.append(record)
            if "json" in content_type or "javascript" in content_type:
                try:
                    body = await response.json()
                    response_bodies.append({
                        "url": safe_url(response.url),
                        "method": response.request.method,
                        "post_data": post_data,
                        "body": body,
                    })
                except Exception:
                    pass

        async def on_request(request) -> None:
            nonlocal dashboard_session_header
            if dashboard_session_header is not None:
                return
            try:
                headers = await request.all_headers()
            except Exception:
                return
            for name, value in headers.items():
                if name.lower() == "sessionid" and value:
                    # Keep this browser auth value in memory only.
                    dashboard_session_header = value
                    return

        page.on("request", on_request)
        page.on("response", on_response)
        await page.goto(args.url, wait_until="domcontentloaded")
        await page.wait_for_timeout(args.wait_ms)
        # Let pending response handlers finish before serializing.
        await page.wait_for_timeout(500)

        dashboard_api: list[dict[str, object]] = []
        for session_id in args.session_id:
            endpoint = (
                "https://dash-api-us1.embrace.io/v4/app/"
                f"{app_id}/session/detail?session={session_id}"
            )
            api_response = await context.request.get(
                endpoint,
                headers=(
                    {"sessionId": dashboard_session_header}
                    if dashboard_session_header
                    else None
                ),
            )
            record: dict[str, object] = {
                "url": endpoint,
                "status": api_response.status,
            }
            try:
                record["body"] = await api_response.json()
            except Exception:
                record["body"] = (await api_response.text())[:10000]
            dashboard_api.append(record)

        result = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "page": {
                "url": page.url,
                "title": await page.title(),
                "text": (await page.locator("body").inner_text())[:100_000],
                "links": await page.locator("a").evaluate_all(
                    "els => els.map(a => ({text: a.innerText, href: a.href}))"
                ),
            },
            "responses": responses,
            "response_bodies": response_bodies,
            "dashboard_api": dashboard_api,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps({
            "output": str(args.output),
            "page_url": page.url,
            "title": await page.title(),
            "same_origin_responses": len(responses),
        }, ensure_ascii=False))
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
