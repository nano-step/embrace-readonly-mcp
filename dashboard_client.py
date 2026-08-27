"""Read-only Embrace Dashboard UI adapter.

The Dashboard does not expose these actions through the official MCP. This
adapter uses an authenticated, visible browser profile and the same
Dashboard-origin requests made by the UI. It never prints or returns browser
cookies or request headers.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator
from urllib.parse import urlencode, urlsplit

from playwright.async_api import BrowserContext, Page, async_playwright

READ_ONLY_DASHBOARD_METHODS = frozenset({"GET", "POST"})
READ_ONLY_DASHBOARD_PATHS = (
    "/v3/app/{app_id}/session/sequence",
    "/v4/app/{app_id}/session/stitch_list",
    "/v4/app/{app_id}/session/detail",
)

BRAVE = os.environ.get(
    "EMBRACE_DASHBOARD_BROWSER",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
PROFILE = os.environ.get(
    "EMBRACE_DASHBOARD_PROFILE_DIR",
    str(Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser"),
)
PROFILE_DIRECTORY = os.environ.get("EMBRACE_DASHBOARD_PROFILE_DIRECTORY", "Default")
DASHBOARD_API = os.environ.get("EMBRACE_DASHBOARD_API", "https://dash-api-us1.embrace.io")
HEADLESS = os.environ.get("EMBRACE_DASHBOARD_HEADLESS", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


class DashboardAuthError(RuntimeError):
    pass


def dashboard_url(app_id: str, user_email: str | None = None) -> str:
    base = f"https://dash.embrace.io/app/{app_id}/grouped_sessions/day"
    if not user_email:
        return base
    params = {
        "filters[0][op]": "eq",
        "filters[0][name]": "user_email",
        "filters[0][values][0]": user_email,
    }
    return f"{base}?{urlencode(params)}"


@asynccontextmanager
async def authenticated_page(app_id: str, user_email: str | None = None) -> AsyncIterator[tuple[BrowserContext, Page, str]]:
    if not Path(BRAVE).exists():
        raise DashboardAuthError(f"Dashboard browser not found: {BRAVE}")
    if not Path(PROFILE).exists():
        raise DashboardAuthError(f"Dashboard browser profile not found: {PROFILE}")

    session_header: str | None = None
    async with async_playwright() as playwright:
        try:
            context = await playwright.chromium.launch_persistent_context(
                PROFILE,
                executable_path=BRAVE,
                headless=HEADLESS,
                args=[f"--profile-directory={PROFILE_DIRECTORY}"],
            )
        except Exception as error:
            raise DashboardAuthError(
                "Could not open the Dashboard browser profile. Close Brave or "
                "set EMBRACE_DASHBOARD_PROFILE_DIR to a dedicated profile."
            ) from error

        page = context.pages[0] if context.pages else await context.new_page()

        async def capture_session_header(request) -> None:
            nonlocal session_header
            if session_header:
                return
            try:
                headers = await request.all_headers()
            except Exception:
                return
            for name, value in headers.items():
                if name.lower() == "sessionid" and value:
                    session_header = value
                    return

        page.on("request", capture_session_header)
        await page.goto(dashboard_url(app_id, user_email), wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if not session_header:
            await context.close()
            raise DashboardAuthError(
                "Dashboard did not provide an authenticated session. Log in with "
                "the configured browser profile and try again."
            )
        try:
            yield context, page, session_header
        finally:
            await context.close()


def _assert_read_only_request(method: str, path: str) -> None:
    if method.upper() not in READ_ONLY_DASHBOARD_METHODS:
        raise PermissionError(f"Dashboard method is not read-only: {method}")
    pathname = urlsplit(path).path
    if not re.fullmatch(
        r"/v[34]/app/[A-Za-z0-9]{5}/session/(sequence|stitch_list|detail)",
        pathname,
    ):
        raise PermissionError(f"Dashboard path is not allowlisted: {pathname}")


async def _request(
    context: BrowserContext,
    session_header: str,
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    method = method.upper()
    _assert_read_only_request(method, path)
    request_headers = {"sessionId": session_header, **kwargs.pop("headers", {})}
    response = await context.request.fetch(
        f"{DASHBOARD_API}{path}",
        method=method,
        headers=request_headers,
        **kwargs,
    )
    try:
        body = await response.json()
    except Exception:
        body = (await response.text())[:10000]
    return {"status": response.status, "body": body}


async def list_user_sessions(
    app_id: str,
    user_email: str,
    resolution: str = "day",
    max_pages: int = 20,
) -> dict[str, Any]:
    pages = []
    next_cursor: str | None = None
    async with authenticated_page(app_id, user_email) as (context, _page, header):
        for _ in range(max(1, min(max_pages, 100))):
            body: dict[str, Any] = {
                "resolution": resolution,
                "filters": {
                    "op": "and",
                    "children": [
                        {"key": "user_email", "field_op": "eq", "val": user_email}
                    ],
                },
            }
            if next_cursor:
                body["next"] = next_cursor
            page = await _request(
                context,
                header,
                "POST",
                f"/v4/app/{app_id}/session/stitch_list",
                data=json.dumps(body),
                headers={"Content-Type": "application/json", "sessionId": header},
            )
            pages.append(page)
            response_body = page["body"]
            if not isinstance(response_body, dict) or not response_body.get("next"):
                break
            next_cursor = response_body["next"]
    return {"app_id": app_id, "user_email": user_email, "resolution": resolution, "pages": pages}


async def session_detail(
    app_id: str,
    session_id: str,
    user_email: str | None = None,
) -> dict[str, Any]:
    async with authenticated_page(app_id, user_email) as (context, _page, header):
        return await _request(
            context,
            header,
            "GET",
            f"/v4/app/{app_id}/session/detail?{urlencode({'session': session_id})}",
        )


async def session_sequence(
    app_id: str,
    first_id: str,
    last_id: str,
    user_email: str | None = None,
) -> dict[str, Any]:
    params = urlencode({"first_id": first_id, "last_id": last_id})
    async with authenticated_page(app_id, user_email) as (context, _page, header):
        return await _request(
            context,
            header,
            "GET",
            f"/v3/app/{app_id}/session/sequence?{params}",
        )
