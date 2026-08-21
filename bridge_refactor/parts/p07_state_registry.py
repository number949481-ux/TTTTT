"""[VERBATIM SLICE] p07_state_registry
المصدر: 01.31_telegram_gen_bridge.py — الأسطر 2410..3358
المحتوى: EXECUTOR + user state + upload queue consts + ProjectRegistry (snapshots/checkpoints/github_sync | P20: الرفع REST-Only — إلغاء Git Native Sync نهائياً | P21: تصنيف دقيق جديد/معدل في uploader)
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
# ══════════════════════════════════════════════════════════════
# ⚡ [Task-4] مشغل المهام الموازية للبوت (Concurrent Parallel Queue)
# ══════════════════════════════════════════════════════════════
EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix="genspark_worker")
USER_STATE_STORE = {}
USER_STATE_LOCK = threading.Lock()


def set_user_state(chat_id: int, state: dict):
    with USER_STATE_LOCK:
        state["ts"] = time.time()
        USER_STATE_STORE[chat_id] = state


def get_user_state(chat_id: int) -> dict:
    with USER_STATE_LOCK:
        state = USER_STATE_STORE.get(chat_id, {})
        if not state:
            return {}
        if time.time() - state.get("ts", 0) > 1800:
            del USER_STATE_STORE[chat_id]
            return {}
        return state


UPLOAD_QUEUE_SCHEMA_VERSION = 1
UPLOAD_MAX_INLINE_BYTES = 95 * 1024 * 1024
UPLOAD_RETRY_BASE_SECONDS = 5
UPLOAD_RETRY_MAX_SECONDS = 300


class ProjectRegistry:
    """عزل دائم لكل مشروع: ملفات، checkpoints، manifests وقفل مستقل.

    الأسرار لا تُكتب على القرص ولا تُرسل لتليجرام. GitHub اختياري ويُفعل فقط من
    GITHUB_UPLOAD_TOKEN و GITHUB_UPLOAD_REPOSITORY=owner/repo.
    """
    def __init__(self, project_key: str):
        self.key = re.sub(r"[^A-Za-z0-9_-]", "_", project_key)[:80]
        self.root = PROJECT_REGISTRY_HOME / self.key
        # fallback environment token يبقى احتياطياً فقط؛ الأولوية لاحقاً لتوكن المشروع نفسه.
        self._github_token = get_default_github_token_from_env()
        self._github_repo = os.getenv("GITHUB_UPLOAD_REPOSITORY", "").strip()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = get_project_lock(self.key)
        self.manifest_path = self.root / "manifest.json"

    def remember_identity(self, root_pid: str | None = None, latest_pid: str | None = None,
                          project_name: str | None = None, chat_id: int | None = None,
                          status: str | None = None) -> dict:
        return upsert_project_identity(
            self.key,
            root_pid=root_pid,
            latest_pid=latest_pid,
            project_name=project_name,
            chat_id=chat_id,
            status=status,
        )

    def _manifest_backup_path(self) -> pathlib.Path:
        return self.manifest_path.with_suffix(".bak")

    def _secrets_path(self) -> pathlib.Path:
        return self.root / "secrets.local.json"

    def _secrets_default(self) -> dict:
        return {
            "schema_version": PROJECT_SECRET_SCHEMA_VERSION,
            "github": {"token": ""},
        }

    def _normalize_project_secrets(self, data: dict | None) -> dict:
        base = self._secrets_default()
        if not isinstance(data, dict):
            return base
        github = data.get("github") if isinstance(data.get("github"), dict) else {}
        base["github"] = {"token": str(github.get("token") or "").strip()}
        return base

    def _read_secrets(self) -> dict:
        path = self._secrets_path()
        if not path.exists():
            return self._secrets_default()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self._secrets_default()
        if not isinstance(raw, dict):
            return self._secrets_default()
        if raw.get("schema_version") not in (None, PROJECT_SECRET_SCHEMA_VERSION):
            return self._secrets_default()
        return self._normalize_project_secrets(raw)

    def _write_secrets(self, data: dict):
        normalized = self._normalize_project_secrets(data)
        path = self._secrets_path()
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def _manifest_default(self) -> dict:
        return {
            "project_key": self.key,
            "created_at": _utc(),
            "updated_at": _utc(),
            "schema_version": PROJECT_MANIFEST_SCHEMA_VERSION,
            "updates": [],
            "checkpoints": [],
            "last_three_urls": [],
            "file_index": {},
            "project_settings": default_project_settings(),
        }

    def _normalize_project_settings(self, settings: dict | None) -> dict:
        base = default_project_settings()
        payload = settings if isinstance(settings, dict) else {}
        base["model"] = normalize_project_model(payload.get("model"))
        continuation = payload.get("continuation") if isinstance(payload.get("continuation"), dict) else {}
        prompt = normalize_project_resume_prompt(continuation.get("prompt"))
        base["continuation"] = {
            "prompt": prompt,
            "mode": normalize_project_resume_mode(continuation.get("mode"), prompt=prompt),
        }
        github = payload.get("github") if isinstance(payload.get("github"), dict) else {}
        base["github"] = {
            "configured": bool(github.get("configured", False)),
            "enabled": bool(github.get("enabled", False)),
            "repository": str(github.get("repository") or "").strip(),
            "token_present": bool(github.get("token_present", False)),
            "token_storage": str(github.get("token_storage") or "").strip(),
            "branch": str(github.get("branch") or "").strip(),
            "branch_mode": str(github.get("branch_mode") or ("manual" if github.get("branch") else "disabled")),
            "detected_default_branch": str(github.get("detected_default_branch") or "").strip(),
            "available_branches": [str(x).strip() for x in (github.get("available_branches") or []) if str(x).strip()][:20],
            "last_repo_check_status": str(github.get("last_repo_check_status") or "").strip(),
            "last_repo_check_at": str(github.get("last_repo_check_at") or "").strip(),
        }
        if not base["github"]["enabled"] and base["github"]["configured"] and base["github"]["branch_mode"] == "manual":
            base["github"]["branch_mode"] = "disabled"
        if base["github"]["enabled"] and base["github"]["branch_mode"] == "disabled":
            base["github"]["branch_mode"] = "manual" if base["github"]["branch"] else "auto_default"
        return base

    def _apply_secret_metadata_to_settings(self, settings: dict) -> dict:
        normalized = self._normalize_project_settings(settings)
        token_present = bool(self._read_secrets().get("github", {}).get("token"))
        normalized["github"]["token_present"] = token_present
        normalized["github"]["token_storage"] = "project-local-secret" if token_present else ""
        return normalized

    def _normalize_manifest(self, data: dict | None) -> dict:
        base = self._manifest_default()
        if not isinstance(data, dict):
            return base
        if data.get("project_key"):
            base["project_key"] = self.key
        for field_name in ("created_at", "updated_at"):
            if data.get(field_name):
                base[field_name] = data.get(field_name)
        for list_field in ("updates", "checkpoints", "last_three_urls"):
            if isinstance(data.get(list_field), list):
                base[list_field] = list(data.get(list_field))
        if isinstance(data.get("file_index"), dict):
            normalized_index = {}
            for raw_path, raw_entry in data.get("file_index", {}).items():
                rel_path = pathlib.PurePosixPath(str(raw_path)).as_posix()
                if not rel_path or rel_path == ".":
                    continue
                entry = raw_entry if isinstance(raw_entry, dict) else {}
                normalized_index[rel_path] = {
                    "project_key": self.key,
                    "relative_path": rel_path,
                    "sha256": str(entry.get("sha256") or ""),
                    "bytes": int(entry.get("bytes") or 0),
                    "last_seen_at": str(entry.get("last_seen_at") or ""),
                    "deleted_at": entry.get("deleted_at"),
                }
            base["file_index"] = normalized_index
        base["project_settings"] = self._normalize_project_settings(data.get("project_settings"))
        base["schema_version"] = PROJECT_MANIFEST_SCHEMA_VERSION
        return base

    def _read(self):
        if not self.manifest_path.exists():
            return self._manifest_default()
        try:
            raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception as err:
            log_event("warning", f"تعذر قراءة manifest للمشروع {self.key}; سيتم التعامل fail-closed: {type(err).__name__}")
            return self._manifest_default()
        if not isinstance(raw, dict):
            log_event("warning", f"manifest للمشروع {self.key} ليست JSON object؛ تم التعامل fail-closed")
            return self._manifest_default()
        schema_version = raw.get("schema_version")
        if schema_version not in (None, PROJECT_MANIFEST_SCHEMA_VERSION):
            log_event("warning", f"schema_version غير معروفة في manifest المشروع {self.key}: {schema_version}")
            return self._manifest_default()
        normalized = self._normalize_manifest(raw)
        if schema_version is None:
            try:
                self._write(normalized)
            except Exception:
                pass
        return normalized

    def _write(self, data):
        normalized = self._normalize_manifest(data)
        normalized["updated_at"] = _utc()
        if self.manifest_path.exists():
            self._manifest_backup_path().write_text(self.manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        temp = self.manifest_path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.manifest_path)

    def restore_manifest_from_backup(self) -> bool:
        backup = self._manifest_backup_path()
        if not backup.exists() or not backup.is_file():
            return False
        try:
            raw = json.loads(backup.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(raw, dict):
            return False
        schema_version = raw.get("schema_version")
        if schema_version not in (None, PROJECT_MANIFEST_SCHEMA_VERSION):
            return False
        normalized = self._normalize_manifest(raw)
        temp = self.manifest_path.with_suffix(".restore.tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.manifest_path)
        return True

    def get_project_settings(self) -> dict:
        with self.lock:
            data = self._read()
            return self._apply_secret_metadata_to_settings(data.get("project_settings") or {})

    def update_project_settings(self, settings: dict | None = None) -> dict:
        with self.lock:
            data = self._read()
            current = self._normalize_project_settings(data.get("project_settings"))
            patch = settings if isinstance(settings, dict) else {}
            if "model" in patch:
                current["model"] = normalize_project_model(patch.get("model"))
            if isinstance(patch.get("continuation"), dict):
                continuation_patch = patch.get("continuation") or {}
                prompt = current["continuation"]["prompt"]
                if "prompt" in continuation_patch:
                    prompt = normalize_project_resume_prompt(continuation_patch.get("prompt"))
                    current["continuation"]["prompt"] = prompt
                if "mode" in continuation_patch or "prompt" in continuation_patch:
                    current["continuation"]["mode"] = normalize_project_resume_mode(continuation_patch.get("mode"), prompt=prompt)
            if isinstance(patch.get("github"), dict):
                github_patch = patch.get("github") or {}
                for key, value in github_patch.items():
                    if key == "configured":
                        current["github"][key] = bool(value)
                    elif key == "enabled":
                        current["github"][key] = bool(value)
                    elif key in {"repository", "token_storage", "branch", "branch_mode", "detected_default_branch", "last_repo_check_status", "last_repo_check_at"}:
                        current["github"][key] = str(value or "").strip()
                    elif key == "token_present":
                        current["github"][key] = bool(value)
                    elif key == "available_branches":
                        current["github"][key] = [str(x).strip() for x in (value or []) if str(x).strip()][:20]
                current = self._normalize_project_settings(current)
            data["project_settings"] = current
            self._write(data)
            return self._apply_secret_metadata_to_settings(current)

    def get_project_github_token(self, allow_env_fallback: bool = True) -> str:
        with self.lock:
            token = self._read_secrets().get("github", {}).get("token", "")
        if token:
            return token
        return get_default_github_token_from_env() if allow_env_fallback else ""

    def set_project_github_token(self, token: str | None) -> dict:
        clean = str(token or "").strip()
        with self.lock:
            secrets = self._read_secrets()
            secrets.setdefault("github", {})["token"] = clean
            self._write_secrets(secrets)
        return self.update_project_settings({
            "github": {
                "token_present": bool(clean),
                "token_storage": "project-local-secret" if clean else "",
            }
        })

    def clear_project_github_token(self) -> dict:
        return self.set_project_github_token("")

    def set_project_model(self, model: str | None) -> dict:
        return self.update_project_settings({"model": model})

    def set_project_resume_prompt(self, prompt: str | None) -> dict:
        return self.update_project_settings({"continuation": {"prompt": prompt}})

    def build_effective_resume_prompt(self, include_github_token: bool = False) -> str:
        settings = self.get_project_settings()
        github_token = self.get_project_github_token() if include_github_token else ""
        return compose_runtime_resume_prompt(settings.get("continuation", {}).get("prompt"), github_token=github_token)

    def _hot_checkpoint_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "checkpoints" / "hot" / checkpoint_id

    def _archive_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "archive" / f"{checkpoint_id}.tar.gz"

    def _queue_path(self) -> pathlib.Path:
        return self.root / "queue.json"

    def _queue_default(self) -> dict:
        return {"schema_version": UPLOAD_QUEUE_SCHEMA_VERSION, "jobs": []}

    def _normalize_upload_job(self, job: dict | None) -> dict:
        data = job if isinstance(job, dict) else {}
        destination = data.get("destination") if isinstance(data.get("destination"), dict) else {}
        branch = str(destination.get("branch") or "")
        branch_mode = str(destination.get("branch_mode") or ("manual" if branch else "auto_default"))
        return {
            "job_id": str(data.get("job_id") or uuid.uuid4().hex),
            "project_key": self.key,
            "checkpoint_id": str(data.get("checkpoint_id") or ""),
            "destination": {
                "repository": str(destination.get("repository") or ""),
                "branch": branch,
                "branch_mode": branch_mode,
                "target_root": str(destination.get("target_root") or "/"),
            },
            "idempotency_key": str(data.get("idempotency_key") or ""),
            "attempt_count": int(data.get("attempt_count") or 0),
            "next_retry_at": data.get("next_retry_at"),
            "last_error_code": str(data.get("last_error_code") or ""),
            "state": str(data.get("state") or "pending"),
            "created_at": str(data.get("created_at") or _utc()),
            "updated_at": str(data.get("updated_at") or _utc()),
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
        }

    def _read_queue(self) -> dict:
        path = self._queue_path()
        if not path.exists():
            return self._queue_default()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as err:
            log_event("warning", f"تعذر قراءة queue للمشروع {self.key}; سيتم التعامل fail-closed: {type(err).__name__}")
            return self._queue_default()
        if not isinstance(raw, dict):
            return self._queue_default()
        if raw.get("schema_version") not in (None, UPLOAD_QUEUE_SCHEMA_VERSION):
            return self._queue_default()
        jobs = raw.get("jobs") if isinstance(raw.get("jobs"), list) else []
        return {
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
            "jobs": [self._normalize_upload_job(job) for job in jobs],
        }

    def _write_queue(self, payload: dict):
        normalized = {
            "schema_version": UPLOAD_QUEUE_SCHEMA_VERSION,
            "jobs": [self._normalize_upload_job(job) for job in (payload.get("jobs") or [])],
        }
        path = self._queue_path()
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def _github_destination(self) -> dict | None:
        settings = self.get_project_settings().get("github", {})
        if not settings.get("configured"):
            return None
        if not settings.get("enabled"):
            return None
        repo = str(settings.get("repository") or "").strip()
        if not repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            return None
        branch = str(settings.get("branch") or "").strip()
        branch_mode = str(settings.get("branch_mode") or ("manual" if branch else "auto_default"))
        return {
            "repository": repo,
            "branch": branch,
            "branch_mode": branch_mode,
            "target_root": "/",
        }

    def inspect_github_repository(self, repo_ref: str | None = None, requester=None) -> dict:
        target_repo = str(repo_ref or self.get_project_settings().get("github", {}).get("repository") or self._github_repo or "").strip()
        return inspect_github_repository(target_repo, token=self.get_project_github_token(), requester=requester)

    def enqueue_github_sync(self, update: dict) -> dict:
        destination = self._github_destination()
        if not self.get_project_github_token() or not destination:
            return {"enabled": False, "queued": [], "jobs": [], "uploaded": [], "unchanged": [], "skipped": []}
        queue_data = self._read_queue()
        checkpoint_id = str(update.get("checkpoint") or "")
        checksum = str(update.get("checksum") or "")
        branch_part = destination.get("branch") or destination.get("branch_mode") or "auto"
        idempotency_key = f"{self.key}:{checkpoint_id}:{checksum}:{destination['repository']}:{branch_part}"
        existing = next((job for job in queue_data["jobs"] if job.get("idempotency_key") == idempotency_key), None)
        if existing:
            return {"enabled": True, "queued": [existing["job_id"]], "jobs": [existing], "uploaded": [], "unchanged": [], "skipped": []}
        job = self._normalize_upload_job({
            "job_id": uuid.uuid4().hex,
            "project_key": self.key,
            "checkpoint_id": checkpoint_id,
            "destination": destination,
            "idempotency_key": idempotency_key,
            "attempt_count": 0,
            "next_retry_at": None,
            "last_error_code": "",
            "state": "pending",
            "created_at": _utc(),
            "updated_at": _utc(),
        })
        queue_data["jobs"].append(job)
        self._write_queue(queue_data)
        return {"enabled": True, "queued": [job["job_id"]], "jobs": [job], "uploaded": [], "unchanged": [], "skipped": []}

    def list_upload_jobs(self, state: str | None = None) -> list[dict]:
        jobs = self._read_queue().get("jobs", [])
        if state:
            jobs = [job for job in jobs if job.get("state") == state]
        return [dict(job) for job in jobs]

    def _parse_iso_time(self, value: str | None) -> float | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)).timestamp()
        except Exception:
            return None

    def compute_upload_backoff_seconds(self, attempt_count: int) -> int:
        attempts = max(1, int(attempt_count or 1))
        return min(UPLOAD_RETRY_MAX_SECONDS, UPLOAD_RETRY_BASE_SECONDS * (2 ** (attempts - 1)))

    def claim_next_upload_job(self, now_ts: float | None = None) -> dict | None:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        chosen_idx = None
        chosen_job = None
        for idx, job in enumerate(queue_data.get("jobs", [])):
            state = str(job.get("state") or "")
            if state == "pending":
                chosen_idx, chosen_job = idx, job
                break
            if state == "retrying":
                due_ts = self._parse_iso_time(job.get("next_retry_at"))
                if due_ts is None or due_ts <= now_ts:
                    chosen_idx, chosen_job = idx, job
                    break
        if chosen_job is None:
            return None
        updated = self._normalize_upload_job(chosen_job)
        updated["attempt_count"] = int(updated.get("attempt_count") or 0) + 1
        updated["state"] = "uploading"
        updated["next_retry_at"] = None
        updated["updated_at"] = _utc()
        queue_data["jobs"][chosen_idx] = updated
        self._write_queue(queue_data)
        return dict(updated)

    def claim_upload_job_by_id(self, job_id: str, now_ts: float | None = None) -> dict | None:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if str(job.get("job_id") or "") != str(job_id or ""):
                continue
            state = str(job.get("state") or "")
            if state == "synced":
                return dict(self._normalize_upload_job(job))
            if state == "uploading":
                return None
            if state == "retrying":
                due_ts = self._parse_iso_time(job.get("next_retry_at"))
                if due_ts is not None and due_ts > now_ts:
                    return None
            if state not in {"pending", "retrying"}:
                return None
            updated = self._normalize_upload_job(job)
            updated["attempt_count"] = int(updated.get("attempt_count") or 0) + 1
            updated["state"] = "uploading"
            updated["next_retry_at"] = None
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def update_upload_job_state(self, job_id: str, state: str, last_error_code: str = "", next_retry_at: str | None = None) -> dict | None:
        queue_data = self._read_queue()
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if job.get("job_id") != job_id:
                continue
            updated = self._normalize_upload_job(job)
            updated["state"] = str(state)
            updated["last_error_code"] = str(last_error_code or "")
            updated["next_retry_at"] = next_retry_at
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def mark_upload_job_retrying(self, job_id: str, last_error_code: str, now_ts: float | None = None) -> dict | None:
        queue_data = self._read_queue()
        now_ts = time.time() if now_ts is None else float(now_ts)
        for idx, job in enumerate(queue_data.get("jobs", [])):
            if job.get("job_id") != job_id:
                continue
            updated = self._normalize_upload_job(job)
            backoff = self.compute_upload_backoff_seconds(updated.get("attempt_count") or 1)
            updated["state"] = "retrying"
            updated["last_error_code"] = str(last_error_code or "")
            updated["next_retry_at"] = datetime.fromtimestamp(now_ts + backoff, timezone.utc).isoformat()
            updated["updated_at"] = _utc()
            queue_data["jobs"][idx] = updated
            self._write_queue(queue_data)
            return dict(updated)
        return None

    def build_upload_job_plan(self, job_id: str) -> dict | None:
        job = next((j for j in self.list_upload_jobs() if j.get("job_id") == job_id), None)
        if not job:
            return None
        record = self.load_checkpoint_record(job.get("checkpoint_id"))
        if not record:
            return {
                "job": job,
                "upload_files": [],
                "delete_files": [],
                "skipped": [f"checkpoint:{job.get('checkpoint_id')} (CHECKPOINT_RECORD_MISSING)"],
            }
        checkpoint_dir = self._hot_checkpoint_path(job.get("checkpoint_id"))
        upload_files = []
        skipped = []
        for info in record.get("files", []):
            rel = str(info.get("path") or "")
            size = int(info.get("bytes") or 0)
            if size > UPLOAD_MAX_INLINE_BYTES:
                skipped.append(f"{rel} (FILE_TOO_LARGE_LOCAL_ONLY)")
                continue
            local = checkpoint_dir / rel
            if not local.exists() or not local.is_file():
                skipped.append(f"{rel} (CHECKPOINT_FILE_MISSING)")
                continue
            upload_files.append({"path": rel, "bytes": size, "local_path": str(local)})
        delete_files = [str(info.get("path") or "") for info in record.get("deleted_files", []) if info.get("path")]
        return {
            "job": job,
            "upload_files": upload_files,
            "delete_files": delete_files,
            "skipped": skipped,
        }

    def _normalize_remote_relative_path(self, rel_path: str) -> str:
        rel = pathlib.PurePosixPath(str(rel_path or "").replace("\\", "/")).as_posix()
        if not rel or rel.startswith("/") or ".." in pathlib.PurePosixPath(rel).parts:
            raise ValueError(f"INVALID_REMOTE_PATH:{rel_path}")
        return rel

    def _default_branch_resolver(self, repository: str) -> str:
        if not repository:
            return "main"
        inspection = self.inspect_github_repository(repository)
        branch = str(inspection.get("default_branch") or "").strip()
        return branch or "main"

    @staticmethod
    def _git_blob_sha(local_path: str) -> str:
        """Compute the SHA returned by GitHub Contents API without invoking git."""
        import hashlib
        size = pathlib.Path(local_path).stat().st_size
        digest = hashlib.sha1()
        digest.update(f"blob {size}\0".encode("ascii"))
        with open(local_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _default_github_uploader(self, payload: dict) -> dict:
        repository = payload["repository"]
        branch = payload["branch"]
        target_root = str(payload.get("target_root") or "/").strip("/")
        token = self.get_project_github_token()
        if not token:
            raise RuntimeError("PROJECT_GITHUB_TOKEN_MISSING")

        # 🔧 [P20] قرار المالك: إلغاء مسار Git Native Sync نهائياً (كان يفشل بـ
        # name 'dest_root' is not defined بشكل متكرر) — GitHub Contents REST API
        # هو مسار الرفع الوحيد والمباشر الآن بدون أي محاولة clone/push.
        import base64
        import requests
        headers = build_github_api_headers(token)
        # 🎯 [P21] دقة تصنيف commit: التمييز بين ملف جديد (غير موجود على الريموت
        # → 404 → uploaded) وملف معدل (له remote_sha مختلف → modified) — كان الاثنان
        # يُحسبان "➕ جديد" في الإحصائيات رغم أن remote_sha متاح أصلاً قبل الـ PUT.
        uploaded, modified, unchanged, deleted, skipped = [], [], [], [], list(payload.get("skipped", []))
        for file_info in payload.get("upload_files", []):
            rel = self._normalize_remote_relative_path(file_info["path"])
            if _should_skip_archive_member(rel):
                skipped.append(rel)
                continue
            remote_rel = "/".join(part for part in (target_root, rel) if part)
            api = f"https://api.github.com/repos/{repository}/contents/{remote_rel}"
            remote_sha = None
            got = requests.get(api, headers=headers, params={"ref": branch}, timeout=30)
            if got.status_code == 200:
                remote_sha = str(got.json().get("sha") or "")
            elif got.status_code != 404:
                raise RuntimeError(f"HTTP_{got.status_code}")
            local_sha = self._git_blob_sha(file_info["local_path"])
            if remote_sha and remote_sha == local_sha:
                unchanged.append(rel)
                continue
            with open(file_info["local_path"], "rb") as fh:
                content_b64 = base64.b64encode(fh.read()).decode("ascii")
            body = {"message": f"[{self.key}] sync {payload['job_id']}: {rel}", "content": content_b64, "branch": branch}
            if remote_sha:
                body["sha"] = remote_sha
            put = requests.put(api, headers=headers, json=body, timeout=120)
            if put.status_code in (200, 201):
                # [P21] remote_sha موجود = الملف كان على الريموت واختلف محتواه → معدل ✏️
                (modified if remote_sha else uploaded).append(rel)
            else:
                raise RuntimeError(f"HTTP_{put.status_code}")
        for rel in payload.get("delete_files", []):
            rel = self._normalize_remote_relative_path(rel)
            remote_rel = "/".join(part for part in (target_root, rel) if part)
            api = f"https://api.github.com/repos/{repository}/contents/{remote_rel}"
            got = requests.get(api, headers=headers, params={"ref": branch}, timeout=30)
            if got.status_code == 404:
                continue
            if got.status_code != 200:
                raise RuntimeError(f"HTTP_{got.status_code}")
            sha = got.json().get("sha")
            body = {"message": f"[{self.key}] delete {payload['job_id']}: {rel}", "sha": sha, "branch": branch}
            delete_resp = requests.delete(api, headers=headers, json=body, timeout=120)
            if delete_resp.status_code in (200, 204):
                deleted.append(rel)
            else:
                raise RuntimeError(f"HTTP_{delete_resp.status_code}")
        return {"uploaded": uploaded, "modified": modified, "unchanged": unchanged, "deleted": deleted, "skipped": skipped}

    def recover_upload_queue_after_restart(self, now_ts: float | None = None) -> list[dict]:
        now_ts = time.time() if now_ts is None else float(now_ts)
        queue_data = self._read_queue()
        recovered = []
        changed = False
        for idx, job in enumerate(queue_data.get("jobs", [])):
            state = str(job.get("state") or "")
            attempts = int(job.get("attempt_count") or 0)
            if attempts >= 5 and state != "synced":
                job["state"] = "failed"
                job["last_error_code"] = "MAX_RETRIES_EXCEEDED"
                job["updated_at"] = _utc()
                changed = True
                continue
            if state in {"uploading", "retrying"}:
                updated = self._normalize_upload_job(job)
                updated["state"] = "retrying"
                updated["next_retry_at"] = None  # تصفير الانتظار لإعادة المحاولة الفورية
                updated["updated_at"] = _utc()
                queue_data["jobs"][idx] = updated
                recovered.append(dict(updated))
                changed = True
        if changed:
            self._write_queue(queue_data)
        return recovered

    def _execute_claimed_upload_job(self, job: dict, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        plan = self.build_upload_job_plan(job["job_id"])
        if not plan:
            retry_job = self.mark_upload_job_retrying(job["job_id"], "JOB_PLAN_MISSING", now_ts=now_ts)
            return {"processed": False, "reason": "JOB_PLAN_MISSING", "job": retry_job or job}
        destination = plan["job"].get("destination", {}) if isinstance(plan.get("job"), dict) else {}
        repository = str(destination.get("repository") or "")
        if not repository:
            retry_job = self.mark_upload_job_retrying(job["job_id"], "DESTINATION_MISSING", now_ts=now_ts)
            return {"processed": False, "reason": "DESTINATION_MISSING", "job": retry_job or job}
        branch = str(destination.get("branch") or "")
        if not branch:
            resolver = branch_resolver or self._default_branch_resolver
            branch = resolver(repository)
        payload = {
            "job_id": job["job_id"],
            "project_key": self.key,
            "repository": repository,
            "branch": branch,
            "target_root": str(destination.get("target_root") or "/"),
            "upload_files": plan.get("upload_files", []),
            "delete_files": plan.get("delete_files", []),
            "skipped": list(plan.get("skipped", [])),
        }
        try:
            result = (uploader or self._default_github_uploader)(payload)
        except Exception as err:
            retry_job = self.mark_upload_job_retrying(job["job_id"], type(err).__name__ if type(err).__name__ != "RuntimeError" else str(err), now_ts=now_ts)
            return {"processed": False, "job": retry_job or job, "error": str(err)}
        updated = self.update_upload_job_state(job["job_id"], "synced", last_error_code="", next_retry_at=None)
        return {"processed": True, "job": updated or job, **(result or {})}

    def process_upload_job_by_id(self, job_id: str, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        current = next((j for j in self.list_upload_jobs() if j.get("job_id") == job_id), None)
        if current and str(current.get("state") or "") == "synced":
            return {"processed": True, "already_synced": True, "job": current, "uploaded": [], "deleted": [], "skipped": []}
        job = self.claim_upload_job_by_id(job_id, now_ts=now_ts)
        if not job:
            return {"processed": False, "reason": "JOB_NOT_DUE_OR_MISSING", "job": current}
        if str(job.get("state") or "") == "synced":
            return {"processed": True, "already_synced": True, "job": job, "uploaded": [], "deleted": [], "skipped": []}
        return self._execute_claimed_upload_job(job, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)

    def process_next_upload_job(self, uploader=None, branch_resolver=None, now_ts: float | None = None) -> dict:
        job = self.claim_next_upload_job(now_ts=now_ts)
        if not job:
            return {"processed": False, "reason": "NO_DUE_JOB"}
        return self._execute_claimed_upload_job(job, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)

    def _checkpoint_record_path(self, checkpoint_id: str) -> pathlib.Path:
        return self.root / "reports" / f"{checkpoint_id}.json"

    def _normalize_checkpoint_record(self, record: dict | None) -> dict:
        data = record if isinstance(record, dict) else {}
        checkpoint_id = str(data.get("checkpoint_id") or "")
        return {
            "checkpoint_id": checkpoint_id,
            "project_key": self.key,
            "run_id": str(data.get("run_id") or checkpoint_id),
            "created_at": str(data.get("created_at") or _utc()),
            "artifact_state": str(data.get("artifact_state") or "empty"),
            "manifest_path": str(data.get("manifest_path") or ""),
            "archive_ref": str(data.get("archive_ref") or ""),
            "summary": data.get("summary") if isinstance(data.get("summary"), dict) else {},
            "files": data.get("files") if isinstance(data.get("files"), list) else [],
            "deleted_files": data.get("deleted_files") if isinstance(data.get("deleted_files"), list) else [],
            "status": str(data.get("status") or ""),
            "url": str(data.get("url") or ""),
            "schema_version": CHECKPOINT_RECORD_SCHEMA_VERSION,
            "checksum": str(data.get("checksum") or ""),
        }

    def _checkpoint_record_checksum(self, record: dict) -> str:
        normalized = self._normalize_checkpoint_record(record)
        normalized["checksum"] = ""
        payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _write_checkpoint_archive(self, checkpoint_id: str, checkpoint_dir: pathlib.Path) -> pathlib.Path:
        import tarfile
        archive_path = self._archive_path(checkpoint_id)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        temp = archive_path.with_suffix(".tmp")
        with tarfile.open(temp, mode="w:gz") as tf:
            if checkpoint_dir.exists():
                for item in sorted(checkpoint_dir.rglob("*")):
                    arcname = item.relative_to(checkpoint_dir).as_posix()
                    if item.is_dir() and not arcname:
                        continue
                    tf.add(item, arcname=arcname or ".")
        temp.replace(archive_path)
        return archive_path

    def _write_checkpoint_record(self, record: dict) -> dict:
        normalized = self._normalize_checkpoint_record(record)
        path = self._checkpoint_record_path(normalized["checkpoint_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized["manifest_path"] = path.relative_to(self.root).as_posix()
        normalized["checksum"] = self._checkpoint_record_checksum(normalized)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
        return normalized

    def load_checkpoint_record(self, checkpoint_id: str) -> dict | None:
        path = self._checkpoint_record_path(checkpoint_id)
        if not path.exists() or not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(raw, dict):
            return None
        if raw.get("schema_version") != CHECKPOINT_RECORD_SCHEMA_VERSION:
            return None
        return self._normalize_checkpoint_record(raw)

    def verify_checkpoint_record_checksum(self, checkpoint_id: str) -> bool:
        record = self.load_checkpoint_record(checkpoint_id)
        if not record:
            return False
        expected = str(record.get("checksum") or "")
        return bool(expected) and expected == self._checkpoint_record_checksum(record)

    def snapshot(self, sandbox_dir, public_url, status, message):
        """نسخ streaming إلى hot checkpoint مع تسطيح مسار webapp واستبعاد الأرشيف والملفات السرية."""
        with self.lock:
            data = self._read(); stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            checkpoint = self._hot_checkpoint_path(stamp)
            checkpoint.mkdir(parents=True, exist_ok=True)
            files = []
            deleted_files = []
            raw_src = pathlib.Path(sandbox_dir) if sandbox_dir else None
            src = _resolve_effective_source_root(raw_src) if raw_src else None
            prior_index = data.get("file_index") if isinstance(data.get("file_index"), dict) else {}
            current_seen_at = _utc()
            seen_paths = set()
            if src and src.exists():
                for item in src.rglob("*"):
                    if item.is_file():
                        if _is_never_copy_file(item.name) or _should_skip_archive_member(item.name):
                            continue
                        rel = item.relative_to(src)
                        rel_path = pathlib.PurePosixPath(rel.as_posix()).as_posix()
                        if _should_skip_archive_member(rel_path):
                            continue
                        dest = checkpoint / rel; dest.parent.mkdir(parents=True, exist_ok=True)
                        # copy2 streams internally; لا يحمل الأرشيف الكبير في الذاكرة.
                        shutil.copy2(item, dest)
                        sha256 = _sha256_file(item)
                        files.append({"path": rel_path, "bytes": item.stat().st_size, "sha256": sha256})
                        seen_paths.add(rel_path)
            for item in files:
                previous_entry = prior_index.get(item["path"], {}) if isinstance(prior_index.get(item["path"]), dict) else {}
                if not previous_entry or previous_entry.get("deleted_at"):
                    classification = "ADDED"
                    changed = True
                elif previous_entry.get("sha256") != item["sha256"]:
                    classification = "MODIFIED"
                    changed = True
                else:
                    classification = "UNCHANGED"
                    changed = False
                item["changed"] = changed
                item["classification"] = classification
                prior_index[item["path"]] = {
                    "project_key": self.key,
                    "relative_path": item["path"],
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "last_seen_at": current_seen_at,
                    "deleted_at": None,
                }

            for rel_path, entry_prev in list(prior_index.items()):
                if rel_path in seen_paths or not isinstance(entry_prev, dict):
                    continue
                if entry_prev.get("deleted_at"):
                    continue
                entry_prev["deleted_at"] = current_seen_at
                deleted_files.append({
                    "path": rel_path,
                    "bytes": int(entry_prev.get("bytes") or 0),
                    "sha256": str(entry_prev.get("sha256") or ""),
                    "changed": True,
                    "classification": "DELETED",
                })

            summary = {
                "added": sum(1 for item in files if item.get("classification") == "ADDED"),
                "modified": sum(1 for item in files if item.get("classification") == "MODIFIED"),
                "unchanged": sum(1 for item in files if item.get("classification") == "UNCHANGED"),
                "deleted": len(deleted_files),
            }
            artifact_state = "files_present" if (files or deleted_files) else "empty"
            archive_path = self._write_checkpoint_archive(stamp, checkpoint)
            archive_ref = archive_path.relative_to(self.root).as_posix()
            checkpoint_record = self._write_checkpoint_record({
                "checkpoint_id": stamp,
                "run_id": stamp,
                "created_at": current_seen_at,
                "artifact_state": artifact_state,
                "archive_ref": archive_ref,
                "summary": summary,
                "files": files,
                "deleted_files": deleted_files,
                "status": status,
                "url": public_url or "",
            })
            data["file_index"] = prior_index
            entry = {
                "at": current_seen_at,
                "status": status,
                "url": public_url or "",
                "files": files,
                "deleted_files": deleted_files,
                "summary": summary,
                "artifact_state": artifact_state,
                "archive_ref": archive_ref,
                "manifest_path": checkpoint_record["manifest_path"],
                "checksum": checkpoint_record["checksum"],
                "message_preview": redact_github_secrets(str(message or ""))[:500],
                "checkpoint": stamp,
            }
            data["updates"].append(entry); data["checkpoints"].append(stamp)
            # hot checkpoints فقط آخر 3؛ archive التاريخي الكامل يبقى محفوظاً منفصلاً.
            for old in data["checkpoints"][:-3]:
                shutil.rmtree(self._hot_checkpoint_path(old), ignore_errors=True)
            data["checkpoints"] = data["checkpoints"][-3:]
            data["last_three_urls"] = [u.get("url", "") for u in data["updates"] if u.get("url")][-3:]
            self._write(data)
            return entry

    def github_sync(self, update, uploader=None, branch_resolver=None, now_ts: float | None = None):
        """في 01.19: أنشئ queue job ثم حاول معالجة نفس job فوراً إذا كانت إعدادات المشروع مكتملة."""
        sync = self.enqueue_github_sync(update)
        if not sync.get("enabled"):
            return sync
        job = (sync.get("jobs") or [{}])[0]
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return {**sync, "upload_confirmed": False, "job_state": ""}
        execution = self.process_upload_job_by_id(job_id, uploader=uploader, branch_resolver=branch_resolver, now_ts=now_ts)
        final_job = execution.get("job") or job
        state = str((final_job or {}).get("state") or "")
        uploaded = list(execution.get("uploaded", []) or [])
        modified = list(execution.get("modified", []) or [])
        deleted = list(execution.get("deleted", []) or [])
        skipped = list(execution.get("skipped", []) or [])
        unchanged = list(execution.get("unchanged", []) or [])
        commit_hash = str(execution.get("commit_hash") or "")
        confirmed = bool(execution.get("processed")) and state == "synced"
        return {
            "enabled": True,
            "queued": [] if confirmed else [job_id],
            "jobs": [final_job] if final_job else [],
            "uploaded": uploaded,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
            "skipped": skipped,
            "commit_hash": commit_hash,
            "upload_confirmed": confirmed,
            "job_state": state,
            "upload_error": str(execution.get("error") or execution.get("reason") or ""),
        }

PROJECT_LOCKS = {}; PROJECT_LOCKS_GUARD = threading.Lock()
PROJECT_RUN_OWNERS = {}; PROJECT_RUN_OWNERS_GUARD = threading.Lock()
REGISTRY_INDEX_LOCK = threading.Lock()
PROJECT_MANIFEST_SCHEMA_VERSION = 1
CHECKPOINT_RECORD_SCHEMA_VERSION = 1


