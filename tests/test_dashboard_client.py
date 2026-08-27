import unittest

from dashboard_client import _assert_read_only_request


class DashboardReadonlyPolicyTest(unittest.TestCase):
    def test_allows_list_and_detail_requests(self):
        _assert_read_only_request("POST", "/v4/app/jnE5L/session/stitch_list")
        _assert_read_only_request(
            "GET", "/v4/app/jnE5L/session/detail?session=example"
        )
        _assert_read_only_request(
            "GET",
            "/v3/app/jnE5L/session/sequence?first_id=first&last_id=last",
        )

    def test_rejects_write_methods(self):
        with self.assertRaises(PermissionError):
            _assert_read_only_request("DELETE", "/v4/app/jnE5L/session/detail")
        with self.assertRaises(PermissionError):
            _assert_read_only_request("PATCH", "/v4/app/jnE5L/session/detail")
        with self.assertRaises(PermissionError):
            _assert_read_only_request("PUT", "/v4/app/jnE5L/session/detail")

    def test_rejects_non_allowlisted_paths(self):
        with self.assertRaises(PermissionError):
            _assert_read_only_request("GET", "/v4/app/jnE5L/user/delete")
        with self.assertRaises(PermissionError):
            _assert_read_only_request("POST", "/v4/app/jnE5L/session/update")


if __name__ == "__main__":
    unittest.main()
