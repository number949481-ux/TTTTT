#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
🚀 gh_bulk.py — Git Data API Bulk Uploader Engine (v5.4 Implementation Ready)
=============================================================================
محرك الرفع والمزامنة الذري عبر GitHub REST Git Data API:
- Atomic Single Commit (كوميت واحد شامل لكافة التغييرات)
- Inline Content للـ Small Text Files (توفير استدعاءات Blobs للـ Text Files <= 4KB)
- Bootstrap ذكي للمستودع الفارغ (PUT /contents بملف حقيقي ثم إكمال بـ Git Data API)
- تمييز قطعي بين المستودع الفارغ (0 فروع) والفرع غير الموجود في مستودع قائم
- تصنيف مرن ومحكم لنتائج وأخطاء PATCH (Idempotent / Superseded / Conflict 409 / Validation 422)
- معالجة انقطاع الاتصال ومهلات الشبكة بإعادة قراءة HEAD
- سقف زمني إجمالي للمزامنة (MAX_TOTAL_SYNC_SECONDS = 120) لمنع الاستنزاف
- دعم نمط الفحص الجاف (dry_run=True)
- توافق كامل مع بيئة ويندوز والمسارات الطويلة وتطبيع NFC
"""

import base64
import hashlib
import os
import pathlib
import sys
import time
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

# -------------------------------------------------------------
# ⚙️ الثوابت والحدود التشغيلية (Constants & Limits)
# -------------------------------------------------------------
INLINE_CONTENT_MAX_BYTES = 4096      # ملفات النصوص <= 4KB ترسل مباشرة في شجرة الـ Git بدون Blobs
MAX_PATH_LENGTH_WARN = 200          # تنبيه عند اقتراب المسار من 200 حرف
MAX_PATH_LENGTH_HARD = 900          # حد أقصى للمسار لتجنب تجاوزات نظام الملفات
MAX_TOTAL_SYNC_SECONDS = 120        # سقف المهلة الكلية للمزامنة الواحدة لمنع التعليق
DEFAULT_TIMEOUT_SECONDS = 30        # مهلة كل ريكويست عادي
BLOB_TIMEOUT_SECONDS = 60           # مهلة ريكويست رفع الـ Blob الكبير
GITHUB_API_VERSION = "2022-11-28"

# أسماء الملفات التأسيسية المفضلة للـ Bootstrap عند ريبو فارغ
BOOTSTRAP_PREFERENCES = [
    "index.html",
    "main.py",
    "app.py",
    "README.md",
    "package.json",
    ".gitignore",
    "requirements.txt",
]


# -------------------------------------------------------------
# 🚨 فئات الأخطاء والاستثناءات المخصصة (Custom Exceptions)
# -------------------------------------------------------------
class GhBulkError(Exception):
    """الخطأ الأساسي لكافة أخطاء محرك المزامنة gh_bulk."""
    pass


class RepoNotFoundError(GhBulkError):
    """المستودع المطلوب غير موجود على GitHub أو الحساب لا يملك صلاحيات."""
    pass


class EmptyRepoNoBootstrapError(GhBulkError):
    """المستودع فارغ ولا توجد أي ملفات صالحة في الأرشيف لعمل Bootstrap."""
    pass


class ConcurrentPushConflictError(GhBulkError):
    """تعارض حقيقي (409) بسبب دفع متزامن آخر غيّر HEAD الفرع."""
    pass


class ValidationFailedError(GhBulkError):
    """فشل التحقق من مدخلات GitHub API (422)."""
    pass


class SyncTimeoutError(GhBulkError):
    """تجاوزت عملية المزامنة السقف الزمني الإجمالي المحدد (MAX_TOTAL_SYNC_SECONDS)."""
    pass


# -------------------------------------------------------------
# 🛠️ أدوات مساعدة وتطبيع المسارات وتوليد الهاش
# -------------------------------------------------------------
def git_blob_sha(content_bytes: bytes) -> str:
    """حساب SHA-1 القياسي لـ Git Blob بدون الحاجة لأمر git الخارجي."""
    header = f"blob {len(content_bytes)}\0".encode("ascii")
    return hashlib.sha1(header + content_bytes).hexdigest()


def normalize_remote_path(path_str: str, target_root: str = "/") -> str:
    """
    تطبيع المسار البعيد لـ GitHub:
    - توحيد الفواصل إلى /
    - تطبيع الرموز العربية واليونيكود إلى NFC
    - إزالة أي زوائد / أو مسارات خطيرة (..)
    - التحقق من حدود طول المسار
    """
    cleaned = str(path_str or "").replace("\\", "/").strip()
    norm_nfc = unicodedata.normalize("NFC", cleaned)
    pure = pathlib.PurePosixPath(norm_nfc)
    
    parts = [p for p in pure.parts if p not in (".", "/")]
    if any(p == ".." for p in parts):
        raise GhBulkError(f"PATH_TRAVERSAL_DETECTED: مسار غير آمن يحتوي على .. ({path_str})")
    
    rel_path = "/".join(parts)
    if not rel_path:
        raise GhBulkError(f"EMPTY_PATH: مسار غير صالح بعد التطبيع ({path_str})")
    
    root_cleaned = str(target_root or "/").replace("\\", "/").strip("/")
    final_path = f"{root_cleaned}/{rel_path}" if root_cleaned else rel_path
    
    if len(final_path) > MAX_PATH_LENGTH_HARD:
        raise GhBulkError(f"PATH_TOO_LONG: تجاوز المسار الحد الأقصى {MAX_PATH_LENGTH_HARD} حرفاً ({final_path})")
    
    return final_path


def is_text_content(content_bytes: bytes) -> Tuple[bool, str]:
    """فحص ما إذا كان المحتوى نصياً UTF-8 صالحاً وخالياً من الـ null bytes."""
    if b"\x00" in content_bytes:
        return False, ""
    try:
        decoded = content_bytes.decode("utf-8")
        return True, decoded
    except UnicodeDecodeError:
        return False, ""


def find_bootstrap_candidate(files_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    اختيار أفضل ملف حقيقي من الأرشيف لعمل Bootstrap لمستودع فارغ:
    1. يفضل الملفات الشائعة (index.html, README.md, main.py, الخ) بشرط أن تكون نصية.
    2. ثم أي ملف نصي UTF-8 ذو أصغر حجم.
    3. ثم أصغر ملف متاح.
    """
    if not files_list:
        return None
    
    existing_candidates = []
    for item in files_list:
        p = item.get("local_path")
        if p and os.path.isfile(p):
            sz = os.path.getsize(p)
            existing_candidates.append({**item, "_size": sz})
        elif "content_bytes" in item:
            sz = len(item["content_bytes"])
            existing_candidates.append({**item, "_size": sz})

    if not existing_candidates:
        return None

    # 1. البحث في الأسماء المفضلة
    by_name = {os.path.basename(c.get("path", "")).lower(): c for c in existing_candidates}
    for pref in BOOTSTRAP_PREFERENCES:
        pref_lower = pref.lower()
        if pref_lower in by_name:
            cand = by_name[pref_lower]
            data = _read_item_bytes(cand)
            is_txt, _ = is_text_content(data)
            if is_txt:
                return cand

    # 2. أصغر ملف نصي UTF-8
    sorted_by_size = sorted(existing_candidates, key=lambda x: x["_size"])
    for cand in sorted_by_size:
        data = _read_item_bytes(cand)
        is_txt, _ = is_text_content(data)
        if is_txt:
            return cand

    # 3. Fallback: أصغر ملف أياً كان نوعه
    return sorted_by_size[0]


def _read_item_bytes(item: Dict[str, Any]) -> bytes:
    """قراءة محتوى الملف بصيغة bytes سواء كان مساراً محلياً أو محتوى محفوظاً."""
    if "content_bytes" in item:
        return item["content_bytes"]
    local_path = item.get("local_path")
    if local_path and os.path.exists(local_path):
        with open(local_path, "rb") as fh:
            return fh.read()
    return b""


# -------------------------------------------------------------
# 🌐 عميل GitHub API (GhClient)
# -------------------------------------------------------------
class GhClient:
    """عميل GitHub REST API مخصص للتعامل مع Git Data API بأمان ومقاومة للانقطاعات."""

    def __init__(self, owner: str, repo: str, token: str, base_url: str = "https://api.github.com", session: Optional[requests.Session] = None):
        self.owner = owner.strip()
        self.repo = repo.strip()
        self.token = token.strip()
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "Genspark-GhBulk-Sync/5.4",
        }

    def request(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Any] = None, data: Optional[Any] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS, max_retries: int = 3, backoff: float = 1.0) -> requests.Response:
        """تنفيذ طلب HTTP مع إعادة المحاولة التلقائية للأخطاء الشبكية و 5xx و 429."""
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/repos/{self.owner}/{self.repo}{endpoint}"
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                    json=json,
                    data=data,
                    timeout=timeout,
                )
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                return resp
            except (requests.exceptions.RequestException, TimeoutError) as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                else:
                    raise last_exc
        raise last_exc or GhBulkError("HTTP_REQUEST_FAILED")

    def get_repo_info(self) -> Dict[str, Any]:
        """استعلام معلومات المستودع (GET /repos/{owner}/{repo})."""
        resp = self.request("GET", "")
        if resp.status_code == 404:
            raise RepoNotFoundError(f"المستودع {self.owner}/{self.repo} غير موجود أو لا تملك صلاحية الوصول.")
        if resp.status_code != 200:
            raise GhBulkError(f"فشل جلب بيانات المستودع: HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()

    def list_branches(self) -> List[str]:
        """جلب قائمة الفروع الحالية للمستودع."""
        resp = self.request("GET", "/branches", params={"per_page": 100})
        if resp.status_code == 404:
            # في بعض الحالات للمستودعات الفارغة تماماً
            return []
        if resp.status_code != 200:
            raise GhBulkError(f"فشل استعلام الفروع: HTTP_{resp.status_code}")
        items = resp.json()
        if isinstance(items, list):
            return [b["name"] for b in items if isinstance(b, dict) and "name" in b]
        return []

    def get_ref(self, branch: str) -> Optional[Dict[str, Any]]:
        """قراءة مرجع الفرع (GET /git/refs/heads/{branch})."""
        resp = self.request("GET", f"/git/refs/heads/{branch}")
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return None
        raise GhBulkError(f"فشل قراءة مرجع الفرع {branch}: HTTP_{resp.status_code}")

    def create_ref(self, branch: str, commit_sha: str) -> Dict[str, Any]:
        """إنشاء مرجع فرع جديد (POST /git/refs)."""
        body = {"ref": f"refs/heads/{branch}", "sha": commit_sha}
        resp = self.request("POST", "/git/refs", json=body)
        if resp.status_code not in (200, 201):
            raise GhBulkError(f"فشل إنشاء الفرع {branch}: HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()

    def update_ref(self, branch: str, commit_sha: str, force: bool = False) -> requests.Response:
        """تحديث مرجع الفرع (PATCH /git/refs/heads/{branch}). إرجاع الـ Response لفحصه."""
        body = {"sha": commit_sha, "force": force}
        return self.request("PATCH", f"/git/refs/heads/{branch}", json=body)

    def compare_commits(self, base_sha: str, head_sha: str) -> Dict[str, Any]:
        """مقارنة كوميتين لتحديد هل هو سلف (GET /compare/{base}...{head})."""
        resp = self.request("GET", f"/compare/{base_sha}...{head_sha}")
        if resp.status_code == 200:
            return resp.json()
        return {}

    def get_commit(self, commit_sha: str) -> Dict[str, Any]:
        """جلب تفاصيل كوميت ومعرفة شجرته (GET /git/commits/{sha})."""
        resp = self.request("GET", f"/git/commits/{commit_sha}")
        if resp.status_code != 200:
            raise GhBulkError(f"فشل جلب تفاصيل الكوميت {commit_sha}: HTTP_{resp.status_code}")
        return resp.json()

    def get_tree(self, tree_sha: str, recursive: bool = True) -> Dict[str, Any]:
        """جلب الشجرة بالكامل مع شجرة الفروع (GET /git/trees/{sha}?recursive=1)."""
        params = {"recursive": "1"} if recursive else None
        resp = self.request("GET", f"/git/trees/{tree_sha}", params=params)
        if resp.status_code != 200:
            raise GhBulkError(f"فشل جلب شجرة المستودع {tree_sha}: HTTP_{resp.status_code}")
        return resp.json()

    def create_blob(self, content_bytes: bytes) -> str:
        """رفع ملف كبير كـ Blob مشفر Base64 (POST /git/blobs)."""
        b64_content = base64.b64encode(content_bytes).decode("ascii")
        body = {"content": b64_content, "encoding": "base64"}
        resp = self.request("POST", "/git/blobs", json=body, timeout=BLOB_TIMEOUT_SECONDS)
        if resp.status_code not in (200, 201):
            raise GhBulkError(f"فشل رفع الـ Blob: HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()["sha"]

    def create_tree(self, tree_items: List[Dict[str, Any]], base_tree_sha: Optional[str] = None) -> str:
        """إنشاء شجرة جديدة (POST /git/trees)."""
        body: Dict[str, Any] = {"tree": tree_items}
        if base_tree_sha:
            body["base_tree"] = base_tree_sha
        resp = self.request("POST", "/git/trees", json=body)
        if resp.status_code not in (200, 201):
            raise GhBulkError(f"فشل إنشاء شجرة Git: HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()["sha"]

    def create_commit(self, message: str, tree_sha: str, parents: List[str]) -> str:
        """إنشاء الكوميت الذري النهائي (POST /git/commits)."""
        body = {
            "message": message,
            "tree": tree_sha,
            "parents": parents,
        }
        resp = self.request("POST", "/git/commits", json=body)
        if resp.status_code not in (200, 201):
            raise GhBulkError(f"فشل إنشاء الكوميت: HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()["sha"]

    def bootstrap_put_contents(self, file_path: str, content_bytes: bytes, branch: str = "main", message: str = "Initial bootstrap commit") -> Dict[str, Any]:
        """تهيئة المستودع الفارغ عبر PUT /contents بملف تأسيسي حقيقي."""
        b64 = base64.b64encode(content_bytes).decode("ascii")
        body = {
            "message": message,
            "content": b64,
            "branch": branch,
        }
        resp = self.request("PUT", f"/contents/{file_path}", json=body)
        if resp.status_code not in (200, 201):
            raise GhBulkError(f"فشل تهيئة المستودع الفارغ (Bootstrap): HTTP_{resp.status_code} {resp.text[:200]}")
        return resp.json()


# -------------------------------------------------------------
# 🚀 دالة المزامنة المركزية الشاملة (sync)
# -------------------------------------------------------------
def sync(
    client: GhClient,
    workdir: Optional[str] = None,
    branch: str = "main",
    target_root: str = "/",
    commit_message: str = "chore: atomic bulk sync",
    dry_run: bool = False,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    تنفيذ المزامنة الكاملة والذرية عبر Git Data API:
    - فحص الريبو والتفريق بين المستودع الفارغ والفرع غير الموجود
    - بناء الـ Tree بالتتابع وتضمين الملفات الصغيرة مباشرة كـ inline
    - إنشاء كوميت ذري واحد وتحديث الفرع
    - معالجة وإعادة تصنيف أخطاء PATCH والتحقق من حالة HEAD
    """
    start_time = time.time()
    
    def _check_timeout():
        if time.time() - start_time > MAX_TOTAL_SYNC_SECONDS:
            raise SyncTimeoutError(f"تجاوزت المزامنة السقف الزمني الإجمالي ({MAX_TOTAL_SYNC_SECONDS} ثانية).")

    # 1. تجهيز قائمة الملفات
    upload_files: List[Dict[str, Any]] = []
    delete_files: List[str] = []
    skipped: List[str] = []

    if payload:
        upload_files = list(payload.get("upload_files", []))
        delete_files = list(payload.get("delete_files", []))
        skipped = list(payload.get("skipped", []))
        if "target_root" in payload:
            target_root = payload["target_root"]
        if "branch" in payload:
            branch = payload["branch"]
    elif workdir and os.path.exists(workdir):
        for root, dirs, files in os.walk(workdir):
            dirs[:] = [d for d in dirs if d != ".git"]
            for f in files:
                abs_f = os.path.join(root, f)
                rel_f = os.path.relpath(abs_f, workdir)
                sz = os.path.getsize(abs_f)
                upload_files.append({"path": rel_f, "local_path": abs_f, "bytes": sz})

    _check_timeout()

    # 2. فحص المستودع وحالة الفروع
    repo_info = client.get_repo_info()
    default_branch = repo_info.get("default_branch") or "main"
    branches = client.list_branches()
    
    is_truly_empty_repo = (len(branches) == 0)
    target_branch_exists = (branch in branches)
    is_new_branch = False
    head_commit_sha: Optional[str] = None
    bootstrap_done_file: Optional[str] = None

    # 3. معالجة المستودع الفارغ (Bootstrap) أو تحديد الكوميت الأساسي
    if is_truly_empty_repo:
        # المستودع فارغ تماماً: لا يمكن عمل POST /git/refs!
        bootstrap_cand = find_bootstrap_candidate(upload_files)
        if not bootstrap_cand:
            if not upload_files:
                return {
                    "status": "empty_no_files",
                    "scanned": 0,
                    "uploaded": [],
                    "modified": [],
                    "unchanged": [],
                    "deleted": [],
                    "skipped": skipped,
                    "message": "المستودع فارغ ولا توجد أي ملفات للرفع.",
                }
            # Fallback: إنشاء README.md تأسيسي
            bootstrap_cand = {
                "path": "README.md",
                "content_bytes": f"# {client.repo}\n\nInitialized by Genspark Bulk Uploader.\n".encode("utf-8"),
                "bytes": 50,
            }

        cand_rel = normalize_remote_path(bootstrap_cand["path"], target_root)
        cand_bytes = _read_item_bytes(bootstrap_cand)
        bootstrap_done_file = cand_rel

        if dry_run:
            # في الـ dry_run نكتفي بالإحصاء
            head_commit_sha = "0000000000000000000000000000000000000000"
        else:
            boot_resp = client.bootstrap_put_contents(
                file_path=cand_rel,
                content_bytes=cand_bytes,
                branch=branch,
                message=f"Initial bootstrap commit with {bootstrap_cand['path']}",
            )
            head_commit_sha = boot_resp.get("commit", {}).get("sha")
            # الآن أصبح المستودع به فرع صالح
            target_branch_exists = True

    elif target_branch_exists:
        # الفرع المطلوب موجود
        head_ref = client.get_ref(branch)
        if head_ref and "object" in head_ref:
            head_commit_sha = head_ref["object"]["sha"]
        else:
            raise GhBulkError(f"تعذر استخراج SHA للفرع القائم {branch}")

    else:
        # المستودع ليس فارغاً، لكن الفرع المطلوب غير موجود
        # نستند إلى الفرع الافتراضي كأساس للفرع الجديد
        is_new_branch = True
        base_branch = default_branch if default_branch in branches else branches[0]
        base_ref = client.get_ref(base_branch)
        if base_ref and "object" in base_ref:
            head_commit_sha = base_ref["object"]["sha"]
        else:
            raise GhBulkError(f"تعذر استخراج SHA للفرع الافتراضي {base_branch}")

    _check_timeout()

    # 4. جلب الشجرة الأساسية (Base Tree) إن وجدت
    base_tree_sha: Optional[str] = None
    remote_tree_map: Dict[str, str] = {}

    if head_commit_sha and head_commit_sha != "0000000000000000000000000000000000000000":
        try:
            head_commit_obj = client.get_commit(head_commit_sha)
            base_tree_sha = head_commit_obj.get("tree", {}).get("sha")
            if base_tree_sha:
                tree_data = client.get_tree(base_tree_sha, recursive=True)
                for item in tree_data.get("tree", []):
                    if item.get("type") == "blob" and "path" in item and "sha" in item:
                        remote_tree_map[item["path"]] = item["sha"]
        except Exception:
            # لو فشل جلب الشجرة لسبب ما، نبني بدون base_tree
            base_tree_sha = None

    # 5. المقارنة وتجهيز الـ Blobs والـ Tree Items
    tree_items: List[Dict[str, Any]] = []
    uploaded: List[str] = []
    modified: List[str] = []
    unchanged: List[str] = []
    deleted: List[str] = []
    inline_count = 0
    blob_count = 0

    for item in upload_files:
        _check_timeout()
        rel_orig = item.get("path", "")
        remote_rel = normalize_remote_path(rel_orig, target_root)
        content_bytes = _read_item_bytes(item)
        local_sha = git_blob_sha(content_bytes)

        # هل الملف مطابق تماماً للموجود في المستودع؟
        if remote_rel in remote_tree_map and remote_tree_map[remote_rel] == local_sha:
            unchanged.append(rel_orig)
            continue

        # تحديد وضع الرفع: inline أم blob منفصل
        is_modified = (remote_rel in remote_tree_map)
        is_txt, text_str = is_text_content(content_bytes)

        if is_txt and len(content_bytes) <= INLINE_CONTENT_MAX_BYTES:
            inline_count += 1
            if not dry_run:
                tree_items.append({
                    "path": remote_rel,
                    "mode": "100644",
                    "type": "blob",
                    "content": text_str,
                })
        else:
            blob_count += 1
            if not dry_run:
                blob_sha = client.create_blob(content_bytes)
                tree_items.append({
                    "path": remote_rel,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })

        if is_modified:
            modified.append(rel_orig)
        else:
            uploaded.append(rel_orig)

    # 6. معالجة الملفات المحذوفة
    for del_path in delete_files:
        _check_timeout()
        del_remote = normalize_remote_path(del_path, target_root)
        if del_remote in remote_tree_map:
            deleted.append(del_path)
            if not dry_run:
                # حذف الملف في Git Data API يتم بتعيين sha: None مع تمرير base_tree
                tree_items.append({
                    "path": del_remote,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                })

    # 7. نتائج الـ Dry Run
    total_scanned = len(upload_files) + len(delete_files)
    if dry_run:
        return {
            "status": "dry_run",
            "scanned": total_scanned,
            "uploaded": len(uploaded),
            "modified": len(modified),
            "unchanged": len(unchanged),
            "deleted": len(deleted),
            "would_send_inline": inline_count,
            "would_upload_blobs": blob_count,
            "would_delete": len(deleted),
            "is_empty_repo": is_truly_empty_repo,
            "bootstrap_candidate": bootstrap_done_file,
        }

    # 8. فحص هل هناك تغييرات فعلية
    if not tree_items:
        return {
            "status": "up_to_date",
            "scanned": total_scanned,
            "uploaded": [],
            "modified": [],
            "unchanged": unchanged,
            "deleted": [],
            "skipped": skipped,
            "commit_sha": head_commit_sha,
            "inline_count": 0,
            "blob_count": 0,
        }

    _check_timeout()

    # 9. إنشاء الشجرة الجديدة (Create Tree)
    new_tree_sha = client.create_tree(tree_items, base_tree_sha=base_tree_sha)

    # 10. إنشاء الكوميت الذري (Create Commit)
    parents = [head_commit_sha] if head_commit_sha else []
    resolved_commit_message = commit_message() if callable(commit_message) else commit_message
    new_commit_sha = client.create_commit(resolved_commit_message, new_tree_sha, parents=parents)

    _check_timeout()

    # 11. تحديث المرجع (Ref Update) مع الصمود والتصنيف الدقيق
    if is_new_branch:
        client.create_ref(branch, new_commit_sha)
    else:
        try:
            patch_resp = client.update_ref(branch, new_commit_sha, force=False)
            if patch_resp.status_code != 200:
                _handle_patch_error_resilient(client, branch, new_commit_sha, patch_resp)
        except (requests.exceptions.RequestException, TimeoutError) as net_err:
            # انقطاع اتصال أو مهلة أثناء PATCH: إعادة التحقق من HEAD مباشرة
            _verify_head_after_patch_disconnect(client, branch, new_commit_sha, net_err)

    return {
        "status": "success",
        "scanned": total_scanned,
        "uploaded": uploaded,
        "modified": modified,
        "unchanged": unchanged,
        "deleted": deleted,
        "skipped": skipped,
        "commit_sha": new_commit_sha,
        "inline_count": inline_count,
        "blob_count": blob_count,
        "bootstrap_file": bootstrap_done_file,
    }


def _verify_head_after_patch_disconnect(client: GhClient, branch: str, our_commit_sha: str, original_exc: Exception):
    """التحقق الصامد من حالة الفرع عند انقطاع الاتصال أثناء إرسال طلب PATCH."""
    try:
        current_ref = client.get_ref(branch)
        if current_ref and current_ref.get("object", {}).get("sha") == our_commit_sha:
            # نجاح تام غير متأثر بالانقطاع (Idempotent Success)
            return
        # لو اختلف، نفحص المقارنة
        if current_ref and "object" in current_ref:
            current_head = current_ref["object"]["sha"]
            comp = client.compare_commits(our_commit_sha, current_head)
            if comp.get("status") in ("ahead", "identical"):
                return
    except Exception:
        pass
    raise GhBulkError(f"PATCH_DISCONNECT: انقطع الاتصال أثناء تحديث مرجع الفرع ({original_exc})")


def _handle_patch_error_resilient(client: GhClient, branch: str, our_commit_sha: str, resp: requests.Response):
    """
    معالجة أخطاء PATCH (409 / 422) بتصنيف دقيق:
    - فحص هل الكوميت وصل بالفعل لـ HEAD (Idempotent)
    - فحص هل تم دمجه أو تجاوزه (Superseded)
    - تصنيف 409 كتعارض حقيقي فقط إذا اختلف الفرع ولم يكن سلفاً
    - تصنيف 422 كفشل تحقق
    """
    status_code = resp.status_code
    try:
        current_ref = client.get_ref(branch)
        if current_ref and current_ref.get("object", {}).get("sha") == our_commit_sha:
            return  # Idempotent
        if current_ref and "object" in current_ref:
            current_head = current_ref["object"]["sha"]
            comp = client.compare_commits(our_commit_sha, current_head)
            if comp.get("status") in ("ahead", "identical"):
                return  # Superseded
    except Exception:
        pass

    if status_code == 409:
        raise ConcurrentPushConflictError(f"HTTP_409: تعارض في دفع التغييرات على الفرع {branch}.")
    elif status_code == 422:
        raise ValidationFailedError(f"HTTP_422: فشل التحقق من صحة المرجع أو الكوميت: {resp.text[:200]}")
    else:
        raise GhBulkError(f"HTTP_{status_code}: فشل تحديث الفرع {branch}: {resp.text[:200]}")


# -------------------------------------------------------------
# 🔌 واجهة الربط المباشرة مع ProjectRegistry (sync_payload)
# -------------------------------------------------------------
def sync_payload(payload: Dict[str, Any], token: str, commit_message: Optional[str] = None) -> Dict[str, Any]:
    """واجهة التوصيل Drop-in Replacement لـ _default_github_uploader."""
    repo_full = payload["repository"]
    branch = payload.get("branch") or "main"
    target_root = payload.get("target_root") or "/"
    job_id = payload.get("job_id", "sync")
    project_key = payload.get("project_key", "prj")
    
    parts = repo_full.split("/", 1)
    if len(parts) != 2:
        raise GhBulkError(f"INVALID_REPOSITORY_NAME: {repo_full}")
    owner, repo_name = parts[0], parts[1]

    client = GhClient(owner=owner, repo=repo_name, token=token)
    msg = commit_message if callable(commit_message) else (commit_message or f"[{project_key}] sync {job_id}: atomic single commit")

    res = sync(
        client=client,
        branch=branch,
        target_root=target_root,
        commit_message=msg,
        payload=payload,
    )

    return {
        "uploaded": res.get("uploaded", []),
        "modified": res.get("modified", []),
        "unchanged": res.get("unchanged", []),
        "deleted": res.get("deleted", []),
        "skipped": res.get("skipped", []),
        "commit_sha": res.get("commit_sha", ""),
        "inline_count": res.get("inline_count", 0),
        "blob_count": res.get("blob_count", 0),
    }
