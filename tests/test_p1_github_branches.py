import sys
import pathlib
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

import importlib.util
spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.32_telegram_gen_bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)



class TestGitHubBranchesP1(unittest.TestCase):
    def test_extract_from_raw_list(self):
        raw = [{"name": "main"}, {"name": "dev"}]
        res = bridge._extract_items_from_github_response(raw)
        self.assertEqual(res, raw)

    def test_extract_from_wrapper_json(self):
        wrapped = {"status_code": 200, "json": [{"name": "feat-1"}, {"name": "feat-2"}]}
        res = bridge._extract_items_from_github_response(wrapped)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "feat-1")

    def test_paginate_100_100_37_exactly_3_requests(self):
        call_log = []

        def mock_requester(method, url, headers, params, timeout):
            page = params.get("page", 1) if params else 1
            call_log.append(page)
            if "repos/owner/repo/branches" in url:
                if page == 1:
                    items = [{"name": f"branch_{i}"} for i in range(1, 101)]
                elif page == 2:
                    items = [{"name": f"branch_{i}"} for i in range(101, 201)]
                elif page == 3:
                    items = [{"name": f"branch_{i}"} for i in range(201, 238)]
                else:
                    items = []
                return {"status_code": 200, "json": items, "text": ""}
            else:
                return {"status_code": 200, "json": {"default_branch": "main", "private": False}, "text": ""}

        info = bridge.inspect_github_repository("owner/repo", token="ghp_test123", requester=mock_requester)
        self.assertTrue(info["ok"])
        self.assertEqual(info["default_branch"], "main")
        self.assertIn("main", info["branches"])
        self.assertEqual(info["branches"][0], "main")  # default branch first
        # 1 call for repo info + 3 calls for 3 branch pages
        self.assertEqual(call_log, [1, 1, 2, 3])
        # Total branches = 237 mock branches + "main"
        self.assertEqual(len(info["branches"]), 238)

    def test_default_branch_first(self):
        def mock_requester(method, url, headers, params, timeout):
            if "repos/owner/repo/branches" in url:
                return {"status_code": 200, "json": [{"name": "dev"}, {"name": "main"}, {"name": "feature"}], "text": ""}
            return {"status_code": 200, "json": {"default_branch": "main", "private": False}, "text": ""}

        info = bridge.inspect_github_repository("owner/repo", token="ghp_test123", requester=mock_requester)
        self.assertEqual(info["branches"][0], "main")
        self.assertEqual(info["branches"], ["main", "dev", "feature"])


if __name__ == "__main__":
    unittest.main()
