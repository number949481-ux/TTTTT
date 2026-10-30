import os
import pathlib
import shutil
import sys
import tempfile
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

import bridge_refactor.runtime as runtime

ns = runtime.ns


class TestWinLongPath360(unittest.TestCase):
    def test_to_win_long_path_idempotence_and_format(self):
        to_long = ns._to_win_long_path
        self.assertIsNone(to_long(None))

        sample = pathlib.Path("C:/test/some/path")
        res = to_long(sample)
        self.assertIsNotNone(res)
        res_str = str(res)
        if os.name == "nt":
            self.assertTrue(res_str.startswith("\\\\?\\"))
            self.assertNotIn("/", res_str)
            # Idempotence: calling again shouldn't double prepend
            res_again = to_long(res)
            self.assertEqual(str(res_again), res_str)

    def test_sha256_and_git_blob_sha_on_long_path(self):
        to_long = ns._to_win_long_path
        with tempfile.TemporaryDirectory() as td:
            base = to_long(pathlib.Path(td))
            # Build a very deep directory exceeding 260 chars
            deep = base
            for i in range(10):
                deep = deep / f"subdir_layer_{i}_with_long_name_padding"
            deep.mkdir(parents=True, exist_ok=True)
            test_file = deep / "payload_verification_test_file.txt"
            test_file.write_text("Hello Windows Long Path Protection!", encoding="utf-8")

            full_path_len = len(str(test_file))
            self.assertGreater(full_path_len, 260, f"Path length {full_path_len} should exceed 260")

            # _sha256_file
            sha = ns._sha256_file(test_file)
            self.assertEqual(len(sha), 64)

            # _git_blob_sha
            blob_sha = ns.ProjectRegistry._git_blob_sha(str(test_file))
            self.assertEqual(len(blob_sha), 40)

            # Manual rmtree using to_long to avoid WinError 145 in tempfile cleanup on Windows
            if os.name == "nt":
                shutil.rmtree(str(to_long(td)), ignore_errors=True)

    def test_snapshot_and_upload_plan_on_live_project(self):
        """Test on the actual extracted_webapp of project 23cba224-c6e8-4454-99c2-917d2a8f33bd."""
        sandbox_path = ns.SCRIPT_DIR / "extracted_webapp" / "23cba224-c6e8-4454-99c2-917d2a8f33bd"
        if not sandbox_path.exists():
            self.skipTest("Sandbox dir not present locally")

        resolved_src = ns._resolve_effective_source_root(sandbox_path)
        self.assertIsNotNone(resolved_src)
        all_files = [p for p in resolved_src.rglob("*") if p.is_file()]

        # The project must discover all 200+ files, NOT just 22
        self.assertGreaterEqual(len(all_files), 200)

        # GITHUB_SYNC_25424TEST.md must be discovered
        file_names = {p.name for p in all_files}
        self.assertIn("GITHUB_SYNC_25424TEST.md", file_names)

        # Test snapshot into a temporary isolated registry
        reg = ns.ProjectRegistry("test_prj_long_path_verification")
        try:
            reg.update_project_settings({
                "github": {
                    "configured": True,
                    "enabled": True,
                    "repository": "number949481-ux/TTTTT",
                    "branch": "genspark_ai_developer"
                }
            })
            reg.set_project_github_token("ghp_fake_test_token")

            update = reg.snapshot(str(sandbox_path), "https://genspark.ai/test", "COMPLETED", "test long path")
            self.assertIn("checkpoint", update)

            sync_res = reg.enqueue_github_sync(update)
            self.assertTrue(sync_res["enabled"])
            self.assertGreater(len(sync_res["jobs"]), 0)
            job = sync_res["jobs"][0]

            plan = reg.build_upload_job_plan(job["job_id"])

            # None of the upload files should be marked CHECKPOINT_FILE_MISSING
            missing_skips = [s for s in plan.get("skipped", []) if "CHECKPOINT_FILE_MISSING" in s]
            self.assertEqual(missing_skips, [], f"Found checkpoint missing files: {missing_skips}")

            # GITHUB_SYNC_25424TEST.md must be in upload_files
            plan_file_paths = {f["path"] for f in plan["upload_files"]}
            self.assertIn("GITHUB_SYNC_25424TEST.md", plan_file_paths)
            print(f"\n[SUCCESS] Planned {len(plan['upload_files'])} files for upload with zero missing!")
        finally:
            # Clean up test registry
            ns.delete_project_atomically("test_prj_long_path_verification")


if __name__ == "__main__":
    unittest.main()
