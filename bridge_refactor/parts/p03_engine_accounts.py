"""[VERBATIM SLICE] p03_engine_accounts
المصدر: 01.33_telegram_gen_bridge.py — الأسطر 488..1136
المحتوى: Engine loader + account locks/claims + fingerprint + BridgeConfig (P25: cancel_event/cancel_token | P29: account_journey + record_account_journey/format_account_journey_line + Immutable Event Snapshots | P30: account_journey_spans + open/close_account_timing_span + format_arabic_duration + P40: format_compact_duration (المدة المضغوطة 45s/12m 17s/1h 5m — الكتلة تستخدمها في المواضع الثلاثة والقديمة باقية) + aggregate_journey_spans_per_email | P39: PRODUCTIVE_SPAN_MIN_SECONDS=60 + filter_productive_account_entries (فلترة الحسابات المنتجة: عتبة الدقيقة + تحصين الحساب المُنجِز + Fail-Open عند إفراغ القائمة) + format_account_timing_block المطوَّرة (عنوان الحسابات الفعلية عند الفلترة/عنوان P30 عند Fail-Open + أدوار البداية/استئناف k/🌟 الحساب المنجز + السطر المدمج ⏱️ إجمالي زمن التوليد (N حسابات منتجة | 🔁 M استئناف) + 🕒 الزمن الكلي — التوقيع لم يتغير)) + accounts I/O + readiness + cooldown + refresh_cookies_on_401
⚠️ ممنوع التعديل اليدوي — يُعاد توليده عبر scripts/rebuild_refactor.py
"""
_ENGINE_CACHE = {"mod": None, "path": None}
_ENGINE_LOCK = threading.Lock()


def get_genspark_engine():
    """استيراد وتخزين محرك Genspark مرة واحدة فقط لتوحيد دوال الدخول والتوليد"""
    with _ENGINE_LOCK:
        if _ENGINE_CACHE["mod"] is not None:
            return _ENGINE_CACHE["mod"]

        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))

        # البحث فقط داخل مجلد W___webapp واستخدام المحرك المحلي المدمج 01.02
        search_order = [
            "01.03Genspark_claude-opus-5-code.py",
        ]
        search_dirs = [SCRIPT_DIR]

        for script_name in search_order:
            for search_dir in search_dirs:
                file_path = search_dir / script_name
                if file_path.exists():
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("genspark_engine", file_path)
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "send_chat"):
                            _ENGINE_CACHE["mod"] = mod
                            _ENGINE_CACHE["path"] = str(file_path)
                            log_event("success", f"تم استيراد المحرك بنجاح: {script_name}")
                            return mod
                    except Exception as e:
                        log_event("error", f"فشل استيراد المحرك {script_name}: {e}")

        log_event("error", "لم يُعثر على أي محرك Genspark متوافق!")
        return None


def get_account_lock(email: str) -> threading.Lock:
    """قفل خاص بكل إيميل لمنع تضارب الثريدات الموازية لنفس الحساب"""
    key = (email or "").strip().lower()
    with ACCOUNT_LOCKS_GUARD:
        if key not in ACCOUNT_LOCKS:
            ACCOUNT_LOCKS[key] = threading.Lock()
        return ACCOUNT_LOCKS[key]


def _normalize_account_claim_key(email: str | None) -> str:
    return str(email or "").strip().lower()


def get_account_selection_claim(email: str | None) -> dict | None:
    key = _normalize_account_claim_key(email)
    if not key:
        return None
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        claim = ACCOUNT_SELECTION_CLAIMS.get(key)
        return dict(claim) if isinstance(claim, dict) else None


def claim_account_selection(email: str | None, owner_token: str, project_key: str = "", attempt_number: int = 0) -> bool:
    key = _normalize_account_claim_key(email)
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        existing = ACCOUNT_SELECTION_CLAIMS.get(key)
        if isinstance(existing, dict) and existing.get("owner_token") and existing.get("owner_token") != token:
            return False
        ACCOUNT_SELECTION_CLAIMS[key] = {
            "owner_token": token,
            "project_key": str(project_key or ""),
            "attempt_number": int(attempt_number or 0),
            "claimed_at": time.time(),
        }
        return True


def release_account_selection(email: str | None, owner_token: str) -> bool:
    key = _normalize_account_claim_key(email)
    token = str(owner_token or "").strip()
    if not key or not token:
        return False
    with ACCOUNT_SELECTION_CLAIMS_GUARD:
        existing = ACCOUNT_SELECTION_CLAIMS.get(key)
        if not isinstance(existing, dict) or existing.get("owner_token") != token:
            return False
        del ACCOUNT_SELECTION_CLAIMS[key]
        return True


def claim_eligible_account_for_owner(
    all_accounts: list,
    tried_emails: set,
    owner_token: str,
    project_key: str = "",
    attempt_number: int = 0,
) -> tuple[dict | None, list[dict], str]:
    ready_accounts = get_eligible_accounts(all_accounts, tried_emails)
    if not ready_accounts:
        return None, [], "no-eligible"
    candidate_pool = list(ready_accounts[:5] if len(ready_accounts) > 5 else ready_accounts)
    while candidate_pool:
        curr_acc = random.choice(candidate_pool)
        curr_email = curr_acc.get("email") if isinstance(curr_acc, dict) else ""
        if claim_account_selection(curr_email, owner_token, project_key=project_key, attempt_number=attempt_number):
            return curr_acc, ready_accounts, "claimed"
        candidate_pool = [acc for acc in candidate_pool if acc is not curr_acc]
    return None, ready_accounts, "busy"


def record_account_journey(bridge_cfg, email: str) -> list:
    """يسجل الحساب في مسار رحلة المهمة على bridge_cfg مع منع التكرار المتتالي (A→A تبقى A).

    يُستدعى فقط لحظة الـ claim الفعلي (لا Email وهمي من الـ Pool)، ويُرجع القائمة الحية.
    """
    if bridge_cfg is None:
        return []
    email_clean = str(email or "").strip()
    journey = getattr(bridge_cfg, "account_journey", None)
    if not isinstance(journey, list):
        journey = []
        bridge_cfg.account_journey = journey
    if email_clean and (not journey or journey[-1] != email_clean):
        journey.append(email_clean)
    return journey


def format_account_journey_line(journey) -> str:
    """يبني سطر «مسار الحسابات» للرسالة النهائية — يظهر فقط عند تعدد الحسابات الفعلية."""
    emails = [str(item).strip() for item in (journey or []) if str(item or "").strip()]
    if len(emails) < 2:
        return ""
    return "🧾 <b>مسار الحسابات:</b> " + " ← ".join(f"<code>{html_escape(item)}</code>" for item in emails)


# ══════════════════════════════════════════════════════════════
# ⏱️ [P30] المحاسبة الزمنية الجنائية للحسابات (Forensic Time Accounting)
# spans حية على bridge_cfg — تُفتح لحظة الـ claim الفعلي وتُغلق حتماً
# في finally (نجاح/فشل/إلغاء/استثناء). monotonic للمدة + wall للعرض.
# ══════════════════════════════════════════════════════════════
def open_account_timing_span(bridge_cfg, email: str, attempt_number: int = 0) -> dict | None:
    """يفتح span زمني لحساب لحظة الـ claim الفعلي فقط (لا Email وهمي من الـ Pool).

    المدة تُقاس بـ time.monotonic() (محصّنة ضد قفزات ساعة النظام داخل نفس البروسيس)،
    و time.time() يُسجَّل للعرض/التدقيق فقط. يُرجع الـ span الحي أو None.
    """
    if bridge_cfg is None:
        return None
    email_clean = str(email or "").strip()
    if not email_clean:
        return None
    spans = getattr(bridge_cfg, "account_journey_spans", None)
    if not isinstance(spans, list):
        spans = []
        bridge_cfg.account_journey_spans = spans
    span = {
        "email": email_clean,
        "attempt_number": int(attempt_number or 0),
        "started_monotonic": time.monotonic(),
        "started_wall": time.time(),
        "ended_monotonic": None,
        "ended_wall": None,
        "duration_seconds": None,
        "closed": False,
    }
    spans.append(span)
    return span


def close_account_timing_span(bridge_cfg, email: str | None = None) -> dict | None:
    """يغلق آخر span مفتوح (idempotent — الإغلاق المزدوج لا يغيّر المدة المسجلة).

    يُستدعى من finally حصراً فيُنفَّذ حتماً في كل المسارات. لو مرّر email
    يُغلق آخر span مفتوح لنفس الحساب؛ وإلا آخر span مفتوح أياً كان.
    """
    if bridge_cfg is None:
        return None
    spans = getattr(bridge_cfg, "account_journey_spans", None)
    if not isinstance(spans, list) or not spans:
        return None
    email_clean = str(email or "").strip()
    for span in reversed(spans):
        if not isinstance(span, dict) or span.get("closed"):
            continue
        if email_clean and str(span.get("email") or "") != email_clean:
            continue
        span["ended_monotonic"] = time.monotonic()
        span["ended_wall"] = time.time()
        span["duration_seconds"] = max(0.0, float(span["ended_monotonic"]) - float(span.get("started_monotonic") or 0.0))
        span["closed"] = True
        return span
    return None


def format_arabic_duration(seconds) -> str:
    """صياغة مدة زمنية بالعربية: «45 ثانية» / «3 دقائق و12 ثانية» / «1 ساعة و5 دقائق».

    القيم السالبة/غير الصالحة تُعامل كصفر (لا Crash أبداً في مسار الرسالة النهائية).
    """
    try:
        total = int(max(0.0, float(seconds or 0)))
    except (TypeError, ValueError):
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours} ساعة")
    if minutes:
        parts.append(f"{minutes} دقيقة" if hours else f"{minutes} دقائق" if minutes > 2 else f"{minutes} دقيقة")
    if secs or not parts:
        parts.append(f"{secs} ثانية")
    return " و".join(parts)


def format_compact_duration(seconds) -> str:
    """⏱️ [P40] صياغة مدة مضغوطة: «45s» / «12m 17s» / «1h 5m».

    قاعدة العرض (نفس فلسفة format_arabic_duration — لا مكوّن صفري مع مكوّن أكبر):
    مع الساعات ➔ Xh (+ Ym إن > 0) بلا ثوانٍ؛ دقائق فقط ➔ Xm (+ Zs إن > 0)؛ وإلا Zs.
    القيم السالبة/غير الصالحة تُعامل كصفر «0s» (لا Crash أبداً في مسار الرسالة النهائية).
    الدالة القديمة format_arabic_duration باقية بلا مساس (عقد 14_DECLINE_FAST_PATH_LATENCY.MD).
    """
    try:
        total = int(max(0.0, float(seconds or 0)))
    except (TypeError, ValueError):
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    return f"{secs}s"


def aggregate_journey_spans_per_email(spans) -> list[dict]:
    """يجمع الـ spans لكل حساب بترتيب أول ظهور: [{email, total_seconds, spans_count}].

    A→B→A تُنتج مدخلاً واحداً لـ A بمجموع فترتيه — بدون فقدان أي فترة.
    الـ spans المفتوحة (لم تُغلق بعد) تُحتسب حتى اللحظة الحالية (best-effort).
    """
    order: list[str] = []
    totals: dict[str, dict] = {}
    now_mono = time.monotonic()
    for span in (spans or []):
        if not isinstance(span, dict):
            continue
        email = str(span.get("email") or "").strip()
        if not email:
            continue
        dur = span.get("duration_seconds")
        if dur is None:
            start = span.get("started_monotonic")
            dur = max(0.0, now_mono - float(start)) if start is not None else 0.0
        if email not in totals:
            order.append(email)
            totals[email] = {"email": email, "total_seconds": 0.0, "spans_count": 0}
        totals[email]["total_seconds"] += max(0.0, float(dur or 0.0))
        totals[email]["spans_count"] += 1
    return [totals[e] for e in order]


# 🧹 [P39] عتبة الإنتاجية المركزية: الحساب الذي لم يتجاوز مجموع فتراته هذه
# الثواني لم يولّد شيئاً فعلياً (نفاد رصيد فوري/pre-flight skip) — يُخفى من
# بطاقة الاكتمال (الشات نظيف) ويبقى كاملاً في اللوج الجنائي. تعريف وحيد —
# ممنوع أي hardcoding متناثر (نمط P32/P34).
PRODUCTIVE_SPAN_MIN_SECONDS = 60


def filter_productive_account_entries(aggregated, last_email=None) -> tuple[list[dict], bool]:
    """🧹 [P39] فلترة الحسابات المنتجة فقط من القائمة المجمَّعة (نقية قابلة للاختبار).

    القواعد: (1) العتبة PRODUCTIVE_SPAN_MIN_SECONDS على مجموع الفترات المجمَّع
    (A→B→A يُقيَّم بمجموع فترتي A لا بالفترة المفردة). (2) الحساب المُنجِز
    (last_email = صاحب آخر span خام) محصَّن دائماً حتى لو مدته < العتبة —
    هو من سلّم النتيجة النهائية. (3) Fail-Open: لو الفلترة أفرغت القائمة
    كلها تُعاد القائمة الكاملة بلا فلترة («الفلترة تنظيف لا إخفاء»).
    تُرجع (القائمة المعروضة, علم Fail-Open).
    """
    entries = [
        item for item in (aggregated or [])
        if isinstance(item, dict) and str(item.get("email") or "").strip()
    ]
    if not entries:
        return [], False
    last_clean = str(last_email or "").strip()
    filtered = []
    for item in entries:
        email = str(item.get("email") or "").strip()
        try:
            total = max(0.0, float(item.get("total_seconds") or 0.0))
        except (TypeError, ValueError):
            total = 0.0
        if total >= PRODUCTIVE_SPAN_MIN_SECONDS or (last_clean and email == last_clean):
            filtered.append(item)
    if not filtered:
        return list(entries), True
    return filtered, False


def format_account_timing_block(bridge_cfg, task_total_seconds=None) -> str:
    """يبني كتلة إحصائيات الحسابات للرسالة النهائية (P30 + فلترة P39 الذكية).

    P39: تُعرض الحسابات المنتجة فقط (عتبة PRODUCTIVE_SPAN_MIN_SECONDS) بأدوار
    واضحة — (البداية) / (استئناف k) / (🌟 الحساب المنجز) — وإجمالي زمن التوليد
    يُحسب من المفلتَر حصراً، بينما «الزمن الكلي للمهمة» (wall clock) مستقل.
    Fail-Open: لو كل الحسابات دون العتبة تُعرض القائمة الكاملة بالعنوان القديم.
    عداد الاستئنافات مصدره الوحيد last_credit_continuations (عقد P30 —
    لا يُشتق أبداً من عدد الحسابات). إيميلات كاملة مهرَّبة بلا masking (P29).
    تُرجع "" فقط لو لا توجد spans إطلاقاً. التوقيع ثابت (عقد P30 محفوظ).
    """
    spans = getattr(bridge_cfg, "account_journey_spans", None) if bridge_cfg is not None else None
    aggregated = aggregate_journey_spans_per_email(spans)
    if not aggregated:
        return ""
    continuations = int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0)
    last_email = ""
    raw_spans = [s for s in (spans or []) if isinstance(s, dict) and str(s.get("email") or "").strip()]
    if raw_spans:
        last_email = str(raw_spans[-1].get("email") or "").strip()
    # 🧹 [P39] الفلترة الذكية: منتجون فقط + تحصين المُنجِز + Fail-Open
    display_entries, fail_open = filter_productive_account_entries(aggregated, last_email)
    productive_total = sum(max(0.0, float(item.get("total_seconds") or 0.0)) for item in display_entries)
    header = (
        "📊 <b>إحصائيات الحسابات وزمن التشغيل:</b>"
        if fail_open
        else "📊 <b>الحسابات الفعلية التي قامت بالتوليد والاستئناف:</b>"
    )
    lines = [header]
    resume_counter = 0
    shown_count = len(display_entries)
    for idx, item in enumerate(display_entries, start=1):
        email = str(item.get("email") or "").strip()
        # 🎭 [P39] الأدوار: المُنجِز الحقيقي (آخر span خام) يتغلب دائماً — حتى لو كان الأول
        if last_email and email == last_email:
            role = " <b>(🌟 الحساب المنجز)</b>"
        elif idx == 1:
            role = " <b>(البداية)</b>"
        else:
            resume_counter += 1
            role = f" <b>(استئناف {resume_counter})</b>"
        multi = f" ×{item.get('spans_count')}" if int(item.get("spans_count") or 0) > 1 else ""
        lines.append(
            f"  {idx}. <code>{html_escape(email)}</code> — "
            f"⏱ {format_compact_duration(item.get('total_seconds'))}{multi}{role}"  # ⏱️ [P40] مدة مضغوطة
        )
    # ⏱️ [P39] السطر المدمج: إجمالي التوليد (من المفلتَر فقط) + عدد المنتجين + عداد الاستئنافات المستقل
    accounts_word = "حساب منتج" if shown_count == 1 else "حسابات منتجة"
    lines.append(
        f"⏱️ <b>إجمالي زمن التوليد:</b> {format_compact_duration(productive_total)} "  # ⏱️ [P40]
        f"({shown_count} {accounts_word} | 🔁 {continuations} استئناف)"
    )
    if task_total_seconds is not None:
        lines.append(f"🕒 <b>الزمن الكلي للمهمة:</b> {format_compact_duration(task_total_seconds)}")  # ⏱️ [P40]
    return "\n".join(lines)


def notify_account_selection_observer(bridge_cfg, event_type: str, **payload) -> bool:
    observer = getattr(bridge_cfg, "account_selection_observer", None) if bridge_cfg is not None else None
    if not callable(observer):
        return False
    event = {
        "event": str(event_type or ""),
        "project_key": str(getattr(bridge_cfg, "selection_project_key", "") or "") if bridge_cfg is not None else "",
        "attempt_number": int(getattr(bridge_cfg, "selection_attempt_number", 0) or 0) if bridge_cfg is not None else 0,
        "selected_account_email": str(getattr(bridge_cfg, "selected_account_email", "") or "") if bridge_cfg is not None else "",
        "selected_account_claim_state": str(getattr(bridge_cfg, "selected_account_claim_state", "") or "") if bridge_cfg is not None else "",
        "credit_continuations": int(getattr(bridge_cfg, "last_credit_continuations", 0) or 0) if bridge_cfg is not None else 0,
        "max_credit_continuations": get_credit_continuation_limit(bridge_cfg),
        "continuation_prompt_public": summarize_resume_prompt_for_display(get_bridge_cfg_public_resume_prompt(bridge_cfg)) if bridge_cfg is not None else DEFAULT_PROJECT_RESUME_PROMPT,
        "runtime_binding_source": str(getattr(bridge_cfg, "project_runtime_binding_source", "") or "") if bridge_cfg is not None else "",
        # 📸 [P29] snapshot غير قابل للتغيير لمسار الحسابات لحظة إنشاء الحدث (Immutable Event Snapshot)
        "account_journey": [str(item) for item in (getattr(bridge_cfg, "account_journey", []) or [])] if bridge_cfg is not None else [],
        **payload,
    }
    try:
        observer(event)
        return True
    except Exception as obs_err:
        log_event("warning", f"فشل observer اختياري بدون إيقاف selection: {obs_err}", email=event.get("selected_account_email", ""))
        return False


def is_valid_email(email: str) -> bool:
    """التحقق من صحة صيغة الإيميل واستبعاد الإيميلات الفاسدة"""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email or "").strip()))


def get_account_fingerprint(email: str) -> dict:
    """بصمة رقمية ثابتة ومتسقة لكل حساب (UA + Browser Profile) لمنع 401"""
    if not email:
        return {"user_agent": USER_AGENTS[0], "browser": BROWSER_PROFILES[0]}
    seed = int(hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest(), 16)
    return {
        "user_agent": USER_AGENTS[seed % len(USER_AGENTS)],
        "browser": BROWSER_PROFILES[seed % len(BROWSER_PROFILES)]
    }


def needs_web_search(query: str) -> bool:
    """تحديد ما إذا كان السؤال يتطلب البحث في الويب لتوفير الكريدت"""
    web_indicators = [
        "ابحث", "search", "آخر أخبار", "latest", "موقع", "website",
        "رابط", "link", "api", "documentation", "docs", "2025", "2026", "حالياً"
    ]
    q_lower = (query or "").lower()
    return any(ind in q_lower for ind in web_indicators)


# ══════════════════════════════════════════════════════════════
# ⚙️ كلاس الإعدادات الرئيسي (BridgeConfig) - SSOT & Config-Driven
# ══════════════════════════════════════════════════════════════
@dataclass
class BridgeConfig:
    model: str = "claude-fable-5"
    agent_type: str = "code_sandbox"
    session_timeout: int = 1000          # ⏱️ المهلة القصوى لانتظار الجلسة الواحدة (1000 ثانية)
    max_timeout_retries: int = 2         # 🔄 عدد محاولات إعادة الطلب تلقائياً عند التايم أوت
    max_account_attempts: int = 50       # 🛡️ حد أقصى للمحاولات لمنع الحلقات المفرغة
    max_credit_continuations: int = 10   # عدد مرات نقل الاستئناف عند نفاد الرصيد
    cooldown_hours: float = 29.0         # ⏱️ مهلة الـ 29 ساعة للحسابات المنتهية بـ cooldown_until
    min_preflight_balance: int = 100     # 💰 [P13] الحد الأدنى للرصيد قبل أي إرسال — أقل منه = تبريد 29h وتخطٍ صامت
    user_agent: str = USER_AGENTS[0]
    current_browser: str = "chrome120"   # 🌐 يُحدث ديناميكياً لكل حساب
    extracted_webapp_dir: pathlib.Path = field(default_factory=lambda: SCRIPT_DIR / "extracted_webapp")
    run_started_at: float | None = None
    last_credit_continuations: int = 0
    last_credit_checkpoint_state: str = ""
    last_credit_checkpoint_note: str = ""
    last_credit_checkpoint_id: str = ""
    last_credit_resume_target_url: str = ""
    last_credit_resume_project_id: str = ""
    credit_handoff_callback: object | None = None
    selection_owner_token: str = ""
    selection_project_key: str = ""
    selection_attempt_number: int = 0
    selected_account_email: str = ""
    selected_account_claim_state: str = ""
    # 🧾 [P29] مسار رحلة الحسابات الفعلية للمهمة (لحظة الـ claim فقط — لا Email وهمي)
    account_journey: list = field(default_factory=list)
    # ⏱️ [P30] spans المحاسبة الزمنية لكل claim: فتح عند الـ claim، إغلاق حتمي في finally
    account_journey_spans: list = field(default_factory=list)
    project_resume_prompt_public: str = DEFAULT_PROJECT_RESUME_PROMPT
    project_resume_prompt_runtime: str = DEFAULT_PROJECT_RESUME_PROMPT
    project_runtime_binding_source: str = ""
    # ⚡ [P43] Fast Lean Mode (DEC-039): محسوم عند apply_project_runtime_binding
    # فقط (الحدية 1) — الافتراضي False = المسار الكامل حرفياً (G3 Zero Regression).
    project_fast_lean_skip: bool = False
    account_selection_observer: object | None = None
    # 🛑 [P25] حدث الإلغاء التفاعلي — يُحقن من الـ worker ويُمرَّر لمحرك التوليد
    # (cfg.cancel_event) لقطع بث ask_proxy فوراً + وقف حلقات المتابعة (polling).
    cancel_event: object | None = None
    cancel_token: str = ""


# ══════════════════════════════════════════════════════════════
# 🛠️ إدارة الحسابات الآمنة وتحديث البيانات (Thread-Safe JSON)
# ══════════════════════════════════════════════════════════════
def get_accounts_file_path(json_path: str | None = None) -> pathlib.Path | None:
    """تحديد مسار ملف accounts_genspark.json تلقائياً"""
    possible_paths = []
    if json_path:
        possible_paths.append(pathlib.Path(json_path))
    possible_paths.extend([
        resolve_shared_path("accounts_genspark.json"),  # 🔎 [P23] محلي ثم الأب (موحّد)
        SCRIPT_DIR.parent / "accounts_genspark.json",
        pathlib.Path("accounts_genspark.json"),
    ])
    for p in possible_paths:
        if p.exists() and p.is_file():
            return p
    return None


def read_accounts_safe(json_path: str | None = None) -> list[dict]:
    """قراءة آمنة لملف الحسابات بـ FILE_LOCK لمنع التعارض مع ثريدات التحديث"""
    target_file = get_accounts_file_path(json_path)
    if not target_file or not target_file.exists():
        return []
    with FILE_LOCK:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception as e:
            log_event("error", f"خطأ في قراءة ملف الحسابات: {e}")
    return []


def update_account_data(email: str, updates: dict, json_path: str | None = None) -> bool:
    """تحديث حقول محددة لحساب في accounts_genspark.json بأمان ذري (Thread-Safe)"""
    target_file = get_accounts_file_path(json_path)
    if not target_file or not target_file.exists():
        return False
    with FILE_LOCK:
        try:
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                accounts = json.load(f)
            if not isinstance(accounts, list):
                return False
            found = False
            for acc in accounts:
                if isinstance(acc, dict) and acc.get("email") == email:
                    acc.update(updates)
                    acc["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    found = True
                    break
            if not found:
                return False
            tmp = target_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(accounts, f, ensure_ascii=False, indent=2)
            tmp.replace(target_file)
            return True
        except Exception as e:
            log_event("error", f"فشل تحديث بيانات الحساب {email}: {e}")
            return False


def is_account_ready(acc: dict) -> bool:
    """
    فحص جاهزية الحساب (نقي 100% بدون أي كتابة على القرص):
    - status == 'cooldown' → جاهز فقط إذا انقضت مدة cooldown_until
    - status في (auth_failed, disabled) → جاهز فقط إذا كان له cooldown_until منتهي
      (أي أن الحظر مؤقت وله موعد إعادة تفعيل) — بدون موعد = رفض دائم حتى تدخل يدوي
    - status في (banned, blocked) → رفض دائم
    """
    if not isinstance(acc, dict):
        return False

    email = acc.get("email")
    if email and not is_valid_email(email):
        return False

    status = str(acc.get("status", "active")).lower().strip()
    now = time.time()

    if status in ("banned", "blocked"):
        return False

    cooldown_until = 0
    try:
        cooldown_until = float(acc.get("cooldown_until") or 0)
    except Exception:
        cooldown_until = 0

    # لسه في تبريد فعلي
    if cooldown_until > now:
        return False

    # تبريد منتهي (cooldown أو auth_failed/disabled مؤقتة) → جاهز للاستخدام
    if status == "cooldown":
        return True
    if status in ("auth_failed", "disabled"):
        # مؤقت فقط إذا كان له موعد إعادة تفعيل (cooldown_until غير صفر ومنتهي)
        return cooldown_until > 0

    if acc.get("active", True) is False:
        return False

    return True


def reactivate_account_if_due(acc: dict, json_path: str | None = None) -> dict:
    """إعادة تفعيل الحساب في الملف إذا انقضت مدة التبريد (تُستدعى عند الاستخدام الفعلي فقط)"""
    if not isinstance(acc, dict):
        return acc
    email = acc.get("email")
    if not email or not is_account_ready(acc):
        return acc
    status = str(acc.get("status", "active")).lower().strip()
    if status in ("cooldown", "auth_failed", "disabled"):
        update_account_data(email, {
            "status": "active",
            "active": True,
            "cooldown_until": 0,
            "cooldown_released_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, json_path=json_path)
        acc = dict(acc)
        acc["status"] = "active"
        acc["active"] = True
        acc["cooldown_until"] = 0
    return acc


def get_eligible_accounts(all_accounts: list, tried_emails: set) -> list:
    """يرجع الحسابات المؤهلة فقط (خرجت من التبريد + إيميل صحيح + لم تُجرب) مرتبة بالأقدم"""
    eligible = []
    for acc in all_accounts:
        if not isinstance(acc, dict):
            continue
        em = acc.get("email")
        if not em or em in tried_emails or not is_valid_email(em):
            continue
        if not is_account_ready(acc):
            continue
        eligible.append(acc)
    eligible.sort(key=lambda x: x.get("last_used", 0) if isinstance(x.get("last_used"), (int, float)) else 0)
    return eligible


def mark_account_cooldown(email: str, cooldown_hours: float = 29.0, json_path: str | None = None) -> bool:
    """تسجيل نفاد الكريدت وتعيين cooldown_until = الآن + 29h مع active=False، وتستعاد تلقائياً بـ is_account_ready"""
    now = time.time()
    cd_until_ts = now + (cooldown_hours * 3600)
    return update_account_data(email, {
        "cooldown_until": cd_until_ts,
        "last_used": now,
        "last_credit_exhausted": now,
        "last_credit_exhausted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "cooldown",
        "active": False
    }, json_path=json_path)


def refresh_cookies_on_401(mod, email: str, password: str, json_path: str | None = None) -> dict | None:
    """تجديد الكوكيز بقفل محكوم منفرد لكل إيميل يمنع التضارب بين الثريدات الموازية"""
    lock = get_account_lock(email)
    with lock:
        try:
            log_event("warning", "جاري تجديد كوكيز الجلسة...", email=email)
            new_cookies = mod.do_login(email, password) if hasattr(mod, "do_login") else None
            if new_cookies and isinstance(new_cookies, dict) and len(new_cookies) > 0:
                update_account_data(email, {
                    "cookies": new_cookies,
                    "status": "active",
                    "active": True,
                    "last_refresh": time.time(),
                    "last_refresh_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                log_event("success", "تم تجديد الكوكيز والجلسة بنجاح!", email=email)
                return new_cookies
        except Exception as e:
            log_event("error", f"فشل تجديد كوكيز الجلسة: {e}", email=email)
            update_account_data(email, {
                "status": "auth_failed",
                "active": False,
                "cooldown_until": time.time() + 1800,  # حظر مؤقت 30 دقيقة فقط ثم يُعاد تلقائياً
                "last_auth_error": str(e),
                "last_auth_error_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }, json_path=json_path)
        return None


