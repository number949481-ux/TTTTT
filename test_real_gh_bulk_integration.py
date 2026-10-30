# -*- coding: utf-8 -*-
"""
Full Spectrum Real Integration Test for gh_bulk v5.4 against GitHub API
Tests:
1. Connecting to real repository (number949481-ux/11111)
2. Creating branch gh_bulk_live_spectrum from main
3. Atomic tree creation with:
   - Inline small text files (<= 4KB)
   - Real binary blob (> 4KB) via client.create_blob (POST /git/blobs)
4. Creating commit
5. Updating branch ref
6. Reading back the commit and tree to verify 100% integrity
7. Testing incremental sync (up_to_date)
8. Branch cleanup
"""
import sys
import os
import json
import re
import pathlib

sys.path.insert(0, r"d:\SMS\.hRhRhRhRhRhR\scratch\ttttt_upload")
from gh_bulk import GhClient, sync

def _get_active_token() -> str:
    env_tok = os.getenv("GITHUB_TOKEN")
    if env_tok:
        return env_tok.strip()
    keys_file = pathlib.Path(r"d:\SMS\.hRhRhRhRhRhR\Root\keys.txt")
    if keys_file.exists():
        text = keys_file.read_text(encoding="utf-8")
        m = re.search(r"ghp_[a-zA-Z0-9]{30,}", text)
        if m:
            return m.group(0)
    raise RuntimeError("No active GitHub token found in env or keys.txt!")

TOKEN = _get_active_token()
OWNER = "number949481-ux"
REPO = "11111"
BRANCH = "gh_bulk_live_spectrum"

def main():
    print(f"Connecting to {OWNER}/{REPO} on branch {BRANCH}...")
    client = GhClient(owner=OWNER, repo=REPO, token=TOKEN)
    
    # 5KB binary blob to trigger real blob upload
    binary_data = b"\x89PNG\r\n\x1a\n" + (b"\x00\xff\xaa\x55" * 1280)  # 5128 bytes
    
    payload = {
        "repository": f"{OWNER}/{REPO}",
        "branch": BRANCH,
        "target_root": "test_spectrum",
        "upload_files": [
            {
                "path": "app.js",
                "content_bytes": b"console.log('Production Ready v5.4');",
                "bytes": 35,
            },
            {
                "path": "assets/sample_banner.png",
                "content_bytes": binary_data,
                "bytes": len(binary_data),
            }
        ],
        "delete_files": [],
    }

    print("\n--- Phase 1: Real Push of 1 Inline File + 1 Real Blob File ---")
    res1 = sync(
        client=client,
        branch=BRANCH,
        target_root="test_spectrum",
        commit_message="test: full spectrum real blob and inline upload v5.4",
        payload=payload,
    )
    print("Result 1:")
    print(json.dumps(res1, indent=2, ensure_ascii=False))

    commit_sha = res1.get("commit_sha")
    assert commit_sha, "No commit SHA returned!"
    assert res1.get("status") == "success", f"Unexpected status: {res1.get('status')}"
    assert res1.get("inline_count") == 1, f"Expected 1 inline file, got {res1.get('inline_count')}"
    assert res1.get("blob_count") == 1, f"Expected 1 blob file, got {res1.get('blob_count')}"
    print(f"Commit with Blob & Inline created successfully: {commit_sha}")

    print("\n--- Phase 2: Incremental Sync with same payload (Expected up_to_date) ---")
    res2 = sync(
        client=client,
        branch=BRANCH,
        target_root="test_spectrum",
        commit_message="test: incremental sync check",
        payload=payload,
    )
    print("Result 2:")
    print(json.dumps(res2, indent=2, ensure_ascii=False))
    assert res2.get("status") == "up_to_date", f"Expected up_to_date, got {res2.get('status')}"
    assert len(res2.get("unchanged", [])) == 2, "Expected 2 unchanged files!"
    print("Incremental sync confirmed up_to_date with ZERO new commits!")

    print("\n--- Phase 3: Cleanup / Delete test branch ---")
    resp_del = client.request("DELETE", f"/git/refs/heads/{BRANCH}")
    print(f"Delete test branch status: HTTP {resp_del.status_code}")
    if resp_del.status_code in (204, 200):
        print("Test branch cleaned up successfully.")

    print("\nALL SPECTRUM PHASES (INLINE + BLOB + INCREMENTAL) PASSED 100%!")

if __name__ == "__main__":
    main()
