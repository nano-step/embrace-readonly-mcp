import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch

import server


class ReadonlyProxyTest(unittest.TestCase):
    def test_forwards_and_preserves_structured_content(self):
        remote = AsyncMock(
            return_value={
                "result": {
                    "structuredContent": {
                        "object": "log.list",
                        "items": [{"group_id": "example"}],
                    }
                }
            }
        )
        with patch.object(server, "_call_remote", remote), patch.dict(
            os.environ, {"EMBRACE_API_TOKEN": "test-token"}
        ):
            result = asyncio.run(
                server.embrace_call_readonly(
                    "list_logs", {"app_id": "jnE5L"}
                )
            )

        self.assertEqual(json.loads(result)["result"]["structuredContent"]["items"][0]["group_id"], "example")
        remote.assert_awaited_once()

    def test_rejects_unknown_tools(self):
        with self.assertRaises(ValueError):
            asyncio.run(server.embrace_call_readonly("delete_sessions", {}))

    def test_requires_token_before_remote_call(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "EMBRACE_API_TOKEN"):
                asyncio.run(server.embrace_call_readonly("list_apps", {}))


if __name__ == "__main__":
    unittest.main()
