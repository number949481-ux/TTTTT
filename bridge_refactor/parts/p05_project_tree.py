"""[VERBATIM SLICE] p05_project_tree
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 1661..2115
المحتوى: projects_tree branches + finished flag + random account + detect_response_status (P20: DATA_RETENTION كنفاد رصيد) + P35: MODEL_DECLINE_MARKERS/MODEL_DECLINE_MAX_RESPONSE_CHARS/MODEL_DECLINED_STATUS + is_model_decline_response (كشف رفض الموديل — ردود قصيرة ≤300 حرف فقط منعاً للـ False Positive) + P18: activity signature monitor (Deep Thinking / Tasks Remaining وقف فوري) + P44: compute_reply_fingerprint (بصمة len+hash للاستقرار D7) + fetch_final_reply_text (الجلبة النهائية D8 — FINAL_FETCH_OK/FALLBACK) + P45: clean_assistant_reply (تطهير CoT/وسوم thought دفاعياً SSOT) + تحصين فلترة الجلبة (تخطي tool_calls والفارغ + تمرير clean + Fail-Open لو التنظيف أفرغ الرد) + extract_project_id + P41: parse_project_locator (التصنيف المركزي SSOT: pid/malformed/none) + detect_context_collision (كشف تصادم السياق النشط مع رابط مشروع آخر)
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
# 🚪 [P44] Activity Gate — تغليف detect_response_status (D5+D6+D9+D12)
# «التغليف مسموح، التعديل محظور» — جسم detect_response_status لا يُلمس (R4).
# البوابة تمنع فقط COMPLETED المبكر؛ الإشارات المهيكلة تخترقها فوراً دائماً.
# ══════════════════════════════════════════════════════════════
# الإشارات المهيكلة (تتكشف بدليل لا بالظن — §3.3 وثيقة 18): تمر بلا أي بوابة
P44_STRUCTURED_STATUSES = ("CREDIT_EXHAUSTED", "DATA_RETENTION", "SESSION_EXPIRED", "FORBIDDEN")
# D6: قراءتان متتاليتان بـ active=False مطلوبتان لفتح البوابة
P44_GATE_INACTIVE_READS_REQUIRED = 2
# D8 (يُوصَّل في CP5): قراءتان بمحتوى ثابت (بصمة len+hash) لاعتماد الرد نهائياً
P44_GATE_STABLE_READS_REQUIRED = 2


def detect_response_status_gated(
    raw_status: str,
    activity: dict | None,
    inactive_streak: int = 0,
    stable_streak: int | None = None,
    email: str = "",
) -> str:
    """🚪 [P44-D9] Wrapper حول detect_response_status — بلا لمس جسمها.

    القرار النهائي للحالة داخل حلقة المتابعة (polling):
      - raw_status مهيكلة (CREDIT_EXHAUSTED/DATA_RETENTION/SESSION_EXPIRED/FORBIDDEN)
        → تمر فوراً (تخترق البوابة — صفر تأخير).
      - raw_status ≠ COMPLETED (RUNNING/EMPTY/...) → تمر كما هي (البوابة تمنع
        فقط الاكتمال المبكر الكاذب).
      - activity is None (فشل شبكة P18) → البوابة محايدة تماماً — Fail-Open
        = سلوك اليوم حرفياً (D6: لا يُحتسب قراءة).
      - activity.active=True → RUNNING مهما طال النص (D5: ACTIVITY_GATE_HOLD).
      - inactive_streak < 2 → RUNNING (D6: debounce — قراءة واحدة لا تكفي).
      - stable_streak (D8 — يُمرَّر من CP5): None = غير مقاس (محايد)؛
        قيمة < 2 = محتوى متغير بين قراءتين → RUNNING (REPLY_UNSTABLE_HOLD).
      - D12: سقف session_timeout القائم يعمل فوق كل ذلك في الحلقة نفسها
        (فحص elapsed قبل هذا الاستدعاء) — شبكة أمان محفوظة بلا تغيير.
    """
    if raw_status in P44_STRUCTURED_STATUSES:
        return raw_status
    if raw_status != "COMPLETED":
        return raw_status
    if activity is None:
        return raw_status
    if activity.get("active"):
        log_event("info", "🚪 [P44] ACTIVITY_GATE_HOLD reason=indicator-active", email=email)
        return "RUNNING"
    if inactive_streak < P44_GATE_INACTIVE_READS_REQUIRED:
        log_event("info", f"🚪 [P44] ACTIVITY_GATE_HOLD reason=debounce inactive_streak={inactive_streak}", email=email)
        return "RUNNING"
    if stable_streak is not None and stable_streak < P44_GATE_STABLE_READS_REQUIRED:
        log_event("info", f"🚪 [P44] REPLY_UNSTABLE_HOLD stable_streak={stable_streak}", email=email)
        return "RUNNING"
    log_event("info", f"🚪 [P44] ACTIVITY_GATE_RELEASE inactive_streak={inactive_streak}", email=email)
    return "COMPLETED"


def compute_reply_fingerprint(text) -> tuple[int, str]:
    """🫆 [P44-D7] بصمة الرد len+hash — قراءتان متطابقتان = محتوى مستقر.

    sha256 على البايتات UTF-8 (errors=replace) + الطول — رخيصة ومحلية
    بالكامل (صفر شبكة)، وتكشف أي تغيّر في المحتوى حتى مع ثبات الطول.
    """
    s = str(text or "")
    return (len(s), hashlib.sha256(s.encode("utf-8", "replace")).hexdigest())


def clean_assistant_reply(text) -> str:
    """🧼 [P45] تطهير الرد النهائي من شوائب CoT والوسوم الداخلية (SSOT).

    فلتر دفاعي Post-processing (قرار خطة 09_FINAL_REPLY_CLEANUP_PLAN —
    المعتمد مع الوكيل الخارجي):
      1. إزالة كتل التفكير <thought|thinking|antThinking>...</...>
         (DOTALL + IGNORECASE — تشمل المتعددة الأسطر والمتعددة التكرار).
      2. إزالة بادئات "Assistant:" المتسربة من الـ System Prompt.
    لو النص نظيف أصلاً فالدالة no-op (نفس النص بعد strip) — صفر ضرر.
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = re.sub(
        r"<(?:thought|thinking|antThinking)>.*?</(?:thought|thinking|antThinking)>",
        "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"^(\s*Assistant:\s*)+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def fetch_final_reply_text(mod, pid, cookies, cfg, old_text, email: str = ""):
    """🎣 [P44-D8] الجلبة النهائية بعد خروج حلقة المتابعة بأي سبب (خصوصاً وقف P18).

    آخر رسالة assistant حقيقية = الرد النهائي المعتمد — وقف P18 يكسر الحلقة
    قبل قراءة الرسائل فيبقى last_resp_text على نسخة وسطية قديمة؛ هذه الجلبة
    تصحح ذلك بطلب واحد أخير. أي فشل (شبكة/لا رسائل/محتوى فارغ) →
    FINAL_FETCH_FALLBACK بالنص القديم كما هو — صفر كسر (Fail-Open).

    🧼 [P45] تحصين الفلترة: تخطّي أغلفة الأدوات (assistant بـ tool_calls)
    والرسائل فارغة المحتوى — الحقول الحقيقية من عيّنة الوكيل المعتمدة
    (لا وجود للحقل المتخيَّل في الـ gist) + تمرير الناتج على clean_assistant_reply؛
    لو التنظيف أفرغ الرد بالكامل (رد كله CoT) → Fail-Open بالنص القديم.
    """
    try:
        if not hasattr(mod, "fetch_project_messages"):
            raise RuntimeError("fetch_project_messages غير متاح في المحرك")
        msgs = mod.fetch_project_messages(pid, cookies, cfg)
        # 🧼 [P45] آخر assistant حقيقية = بلا tool_calls وبمحتوى فعلي
        last_asst = next(
            (m for m in reversed(msgs or [])
             if isinstance(m, dict)
             and m.get("role") == "assistant"
             and not m.get("tool_calls")
             and str(m.get("content", "")).strip()),
            None,
        )
        final_c = (last_asst or {}).get("content", "")
        if final_c and str(final_c).strip():
            clean_final = clean_assistant_reply(str(final_c))
            if not clean_final:
                raise RuntimeError("الرد بعد تنظيف CoT فارغ بالكامل")
            log_event("info", f"🎣 [P44] FINAL_FETCH_OK chars={len(clean_final)}", email=email)
            return clean_final
        raise RuntimeError("لا توجد رسالة assistant بمحتوى")
    except Exception as _ff_err:
        log_event("warning", f"🎣 [P44] FINAL_FETCH_FALLBACK reason={_ff_err}", email=email)
        return old_text


# ══════════════════════════════════════════════════════════════
# 🚫 [P35] كشف رفض الموديل (Model Decline Recovery)
# ══════════════════════════════════════════════════════════════
# الرد "The model declined to answer this request..." يصل بطول > 25 حرفاً
# فيُحتسب COMPLETED في detect_response_status — وهذا صحيح تقنياً (المهمة
# انتهت فعلاً) لكنه خاطئ دلالياً: لا يوجد ناتج، والأسوأ أن مؤشر الاستئناف
# كان يتقدم لنقطة "الرفض". فلسفة P35: الرفض يُعامل «كأن الطلب لم يُرسل».
#
# ⚠️ حارس False Positive: الكشف يعمل فقط للردود القصيرة
# (≤ MODEL_DECLINE_MAX_RESPONSE_CHARS) — أي رد طويل شرعي *يقتبس* جملة
# الرفض داخله لا يُحتسب رفضاً أبداً (نفس فلسفة إصلاح RUNNING الكاذب).
MODEL_DECLINE_MARKERS = [
    "the model declined to answer this request",
    "model declined to answer",
    "declined to answer this request",
    "the model declined to respond",
    "model declined this request",
]
MODEL_DECLINE_MAX_RESPONSE_CHARS = 300
MODEL_DECLINED_STATUS = "MODEL_DECLINED"


def is_model_decline_response(response_text: str | None) -> bool:
    """🚫 [P35] هل هذا الرد رفض صريح من الموديل؟

    True فقط إذا: الرد غير فارغ + قصير (≤ 300 حرف بعد strip) + جوهره
    إحدى عبارات الرفض المعتمدة. الردود الطويلة تُستبعد فوراً حتى لو
    احتوت العبارة (اقتباس داخل رد شرعي ≠ رفض).
    """
    text = str(response_text or "").strip()
    if not text:
        return False
    if len(text) > MODEL_DECLINE_MAX_RESPONSE_CHARS:
        return False
    low = text.lower()
    return any(marker in low for marker in MODEL_DECLINE_MARKERS)


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


# ══════════════════════════════════════════════════════════════
# 🧭 [P41] Project Locator Parsing SSOT + Context Collision Guard
# ══════════════════════════════════════════════════════════════
# علاج تداخل الروابط (وثيقة 15_PROJECT_ROUTING_AND_CLEAN_SHUTDOWN.MD):
#   - parse_project_locator: التصنيف المركزي الوحيد (SSOT) لأي نص وارد —
#     "pid" (رابط/UUID صالح) أو "malformed" (يشبه رابط مشروع بلا UUID صالح)
#     أو "none" (برومبت عادي). يُبنى فوق extract_project_id +
#     is_probable_project_id القائمتين بلا أي تعديل عليهما (T3).
#   - detect_context_collision: يُستدعى حصرياً في فرعي البرومبت النشط
#     (AWAITING_NEW_PROMPT / AWAITING_CONT_PROMPT) قبل الجدولة — سياق
#     مشروع (A) نشط + نص يحمل رابط مشروع (B) ➔ يستحيل تنفيذ الرابط
#     كبرومبت على المشروع الخطأ (T1/T2 — منع Cross-Project Context Hijacking).
def parse_project_locator(text) -> dict:
    """التصنيف المركزي (SSOT) لأي نص وارد من Telegram كمحدد مشروع محتمل."""
    raw = str(text or "").strip()
    result = {"kind": "none", "pid": "", "raw": raw}
    if not raw:
        return result
    has_domain = "genspark.ai" in raw.lower()
    has_uuid = bool(re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", raw, re.IGNORECASE))
    if has_uuid:
        pid = extract_project_id(raw)
        if is_probable_project_id(pid):
            result["kind"] = "pid"
            result["pid"] = pid
            return result
    if has_domain:
        result["kind"] = "malformed"
        return result
    return result


def detect_context_collision(state, text):
    """حارس تصادم السياق النشط: None = برومبت عادي (المسار القديم حرفياً)."""
    locator = parse_project_locator(text)
    if locator["kind"] == "none":
        return None
    state = state or {}
    active_url = str(state.get("url") or "")
    active_pid = extract_project_id(active_url) if active_url else ""
    return {
        "kind": locator["kind"],
        "pid": locator["pid"],
        "raw": locator["raw"],
        "active_project_key": str(state.get("project_key") or ""),
        "active_pid": active_pid if is_probable_project_id(active_pid) else "",
    }


