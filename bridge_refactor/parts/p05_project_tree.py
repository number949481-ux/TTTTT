"""[VERBATIM SLICE] p05_project_tree
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 1484..1728
المحتوى: projects_tree branches + finished flag + random account + detect_response_status (P20: DATA_RETENTION كنفاد رصيد) + P18: activity signature monitor (Deep Thinking / Tasks Remaining وقف فوري) + extract_project_id
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
# ══════════════════════════════════════════════════════════════
# 🌳 [Task-2] شجرة التفريعات وعلم انتهاء المشروع
# ══════════════════════════════════════════════════════════════
def save_project_branch(
    parent_id: str | None,
    child_id: str,
    title: str = "تحديث محادثة",
    model: str = "claude-fable-5",
    status: str = "COMPLETED"
) -> bool:
    """حفظ شجرة تفريع المشروع (parent_pid -> child_pid) في projects_tree.json"""
    tree_data = {}
    if PROJECTS_TREE_FILE.exists():
        try:
            with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
                tree_data = json.load(f)
        except Exception:
            tree_data = {}
    root_key = parent_id or child_id
    if root_key not in tree_data:
        tree_data[root_key] = {
            "root_id": root_key,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "branches": []
        }
    safe_title = summarize_resume_prompt_for_display(title, limit=30)
    branch_entry = {
        "project_id": child_id,
        "parent_id": parent_id,
        "title": safe_title,
        "model": model,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    existing_ids = [b.get("project_id") for b in tree_data[root_key]["branches"]]
    if child_id not in existing_ids:
        tree_data[root_key]["branches"].append(branch_entry)
    try:
        tmp_file = PROJECTS_TREE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(PROJECTS_TREE_FILE)
        return True
    except Exception as err:
        log_event("warning", f"تنبيه أثناء حفظ شجرة التفريع: {err}")
        return False


def get_project_branches(root_id: str) -> list[dict]:
    """استرجاع نقاط الاستئناف والتفريعات لمشروع معين"""
    if not PROJECTS_TREE_FILE.exists():
        return []
    try:
        with open(PROJECTS_TREE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            tree_data = json.load(f)
        return tree_data.get(root_id, {}).get("branches", [])
    except Exception:
        return []


def check_project_finished_flag(status: str, response_text: str | None = None) -> bool:
    """كشف علم اكتمال انتهاء المشروع PROJECT_FINISHED_FLAG"""
    if status == "COMPLETED":
        return True
    if response_text:
        text_lower = response_text.lower()
        if "تم التنفيذ" in text_lower or "جاهزة للعب" in text_lower or "project completed" in text_lower:
            return True
    return False


def get_random_email_from_accounts_genspark(json_path: str | None = None) -> dict | None:
    accounts = read_accounts_safe(json_path)
    active_accounts = [
        acc for acc in accounts
        if isinstance(acc, dict) and acc.get("email") and is_account_ready(acc)
    ]
    if not active_accounts:
        return None
    chosen = random.choice(active_accounts)
    return reactivate_account_if_due(chosen, json_path=json_path)


# ══════════════════════════════════════════════════════════════
# 🧠 كشف حالة الرد — نسخة محصّنة ضد الكلمات العامة
# ══════════════════════════════════════════════════════════════
SESSION_EXPIRED_KEYWORDS = ["401", "unauthorized", "session expired", "session منتهية", "login required", "not logged in"]
FORBIDDEN_KEYWORDS = ["403", "forbidden", "not authorized", "permission denied", "access denied"]
CREDIT_EXHAUSTED_KEYWORDS = [
    "your credit balance is negative", "this run was stopped", "please top up to continue",
    "you've used all your credits", "used all your credits", "credits are insufficient",
    "action_credit_exhausted", "__credit_exhausted__", "upgrade to continue", "out of credits",
    "كريدت منتهية"
]
# علامات التوليد الجزئي — تُستخدم فقط للنصوص القصيرة جداً (أقل من 60 حرفاً)
PARTIAL_GENERATION_MARKERS = ["thinking", "processing", "generating", "بيفكر", "جاري", "جارٍ"]
# 🧬 [P20] خطأ AI Data Retention — يُعامل كحساب منتهي الرصيد (تبريد + انتقال لحساب آخر)
# مع تنبيه مميز + إعادة إرسال «نفس آخر رسالة» المستخدمة في نفس الحساب كما هي.
DATA_RETENTION_KEYWORDS = [
    "ai data retention", "requires ai data retention",
    "data retention to be enabled", "turn on ai data retention",
]


def detect_response_status(response: str | dict | None) -> str:
    """
    كشف واستخراج حالة الرد بدقة بين SESSION_EXPIRED, FORBIDDEN, CREDIT_EXHAUSTED,
    DATA_RETENTION (🧬 P20), RUNNING, COMPLETED.
    ⚠️ الإصلاح: كلمات مثل running/processing/thinking في ردود مكتملة طويلة (مثل: "الموقع شغال running")
    كانت تسبب RUNNING كاذب → تعليق حتى TIMEOUT. الآن RUNNING تُحتسب فقط للنصوص القصيرة جداً
    التي تُمثل مرحلة توليد فعلية، وأي نص غير قصير يعتبر COMPLETED افتراضياً.
    """
    if not response:
        return "EMPTY"

    text = json.dumps(response, ensure_ascii=False) if isinstance(response, dict) else str(response)
    t = text.lower()
    check_text = t[-3500:] if len(t) > 3500 else t

    # 🧬 [P20] فحص Data Retention أولاً — أكثر تحديداً من باقي الفئات
    if any(kw in check_text for kw in DATA_RETENTION_KEYWORDS):
        return "DATA_RETENTION"
    if any(kw in check_text for kw in SESSION_EXPIRED_KEYWORDS):
        return "SESSION_EXPIRED"
    if any(kw in check_text for kw in FORBIDDEN_KEYWORDS):
        return "FORBIDDEN"
    if any(kw in check_text for kw in CREDIT_EXHAUSTED_KEYWORDS):
        return "CREDIT_EXHAUSTED"

    if len(check_text.strip()) < 2:
        return "EMPTY"

    # RUNNING فقط للنصوص القصيرة جداً (<25 حرف) أو التي تبدأ بعلامة توليد فعلية
    # (مثل "thinking..." أو "جاري التوليد") — أي رد مكتمل مهما احتوى على
    # كلمات عامة مثل processing/running/جاري يُعتبر COMPLETED
    stripped = check_text.strip()
    if stripped:
        is_very_short = len(stripped) < 25
        starts_with_marker = any(stripped.startswith(kw) for kw in PARTIAL_GENERATION_MARKERS)
        if (is_very_short or starts_with_marker) and any(kw in stripped for kw in PARTIAL_GENERATION_MARKERS):
            return "RUNNING"

    return "COMPLETED"


# ══════════════════════════════════════════════════════════════
# ⛳ [P18] مراقب مؤشر النشاط الحي (Deep Thinking / Tasks Remaining)
# لو المؤشر اتغيّر أثناء المتابعة → وقف فوري (مفيش أي تكملة على مهام جديدة)
# ══════════════════════════════════════════════════════════════
DEEP_THINKING_MARKERS = ["deep thinking", "deep-thinking", "deepthinking"]
TASKS_REMAINING_PATTERN = re.compile(r"tasks?\s*remaining\D{0,16}?(\d+)|(\d+)\s*tasks?\s*remaining", re.IGNORECASE)
TASKS_REMAINING_TEXT_MARKERS = ["tasks remaining", "task remaining", "tasks left", "task left"]


def extract_activity_signature(page_text: str | None) -> dict:
    """
    ⛳ [P18] يستخرج بصمة مؤشر النشاط من نص صفحة المشروع (/agents?id=PID):
      - deep_thinking: هل مؤشر Deep Thinking ظاهر؟
      - tasks_remaining: عدد المهام المتبقية إن وُجد رقم (وإلا -1 لو النص موجود بدون رقم، None لو غير موجود)
      - active: هل يوجد أي مؤشر توليد حي (Deep Thinking أو Tasks Remaining)؟
    """
    text = str(page_text or "")
    low = text.lower()
    deep = any(m in low for m in DEEP_THINKING_MARKERS)
    tasks = None
    m = TASKS_REMAINING_PATTERN.search(low)
    if m:
        num = m.group(1) or m.group(2)
        try:
            tasks = int(num)
        except (TypeError, ValueError):
            tasks = -1
    elif any(k in low for k in TASKS_REMAINING_TEXT_MARKERS):
        tasks = -1
    return {
        "deep_thinking": deep,
        "tasks_remaining": tasks,
        "active": bool(deep or tasks is not None),
    }


def fetch_project_activity_signature(project_id: str, cookies: dict) -> dict | None:
    """
    ⛳ [P18] يجلب صفحة المشروع الحية ويستخرج بصمة مؤشر Deep Thinking / Tasks Remaining.
    يرجع None عند أي فشل شبكة/HTTP حتى لا يؤثر إطلاقاً على حلقة المتابعة الأساسية.
    """
    if not project_id:
        return None
    try:
        from curl_cffi import requests as cffi
        sess = cffi.Session(impersonate="chrome120")
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Referer": "https://www.genspark.ai/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        for name, val in (cookies or {}).items():
            sess.cookies.set(str(name), str(val), domain="www.genspark.ai")
        r = sess.get(f"https://www.genspark.ai/agents?id={project_id}", timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        return extract_activity_signature(getattr(r, "text", "") or "")
    except Exception:
        return None


def should_stop_on_activity_change(prev: dict | None, curr: dict | None) -> tuple[bool, str]:
    """
    ⛳ [P18] قرار الوقف الفوري: أي تغيّر في مؤشر Deep Thinking / Tasks Remaining = وقف فوراً.
      1. المؤشر كان ظاهراً (active) ثم اختفى تماماً → وقف فوري.
      2. عدد Tasks Remaining اتغيّر بأي شكل (زيادة أو نقصان) → المهام اتغيرت → وقف فوري
         (المطلوب صراحةً: لو المهام اتغيرت مفيش أي تكملة).
      3. مؤشر Deep Thinking اتقلب (ظهر/اختفى مع بقاء النشاط) → وقف فوري.
      4. لو مفيش بصمة سابقة نشطة → لا قرار (لسه بنلتقط الـ baseline).
    ملاحظة صريحة: أي تغيّر في العدد — حتى النقصان — يعني المهام اتغيرت → وقف فوري، مفيش أي تكملة.
    """
    if not prev or not curr:
        return False, ""
    if not prev.get("active"):
        return False, ""
    if not curr.get("active"):
        return True, "activity-indicator-disappeared"
    # ⛳ [P18] المطلوب صراحةً: أي تغيّر في المهام = وقف فوري (زيادة أو نقصان — مفيش تكملة)
    prev_tasks = prev.get("tasks_remaining")
    curr_tasks = curr.get("tasks_remaining")
    if prev_tasks != curr_tasks:
        return True, "tasks-remaining-changed"
    if bool(prev.get("deep_thinking")) != bool(curr.get("deep_thinking")):
        return True, "deep-thinking-changed"
    return False, ""


def extract_project_id(url_or_id: str) -> str:
    if not url_or_id:
        return ""
    url_str = str(url_or_id).strip()
    match = re.search(r"id=([a-f0-9\-]{36})", url_str, re.IGNORECASE)
    if match:
        return match.group(1)
    uuid_match = re.search(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", url_str, re.IGNORECASE)
    if uuid_match:
        return uuid_match.group(1)
    return url_str


