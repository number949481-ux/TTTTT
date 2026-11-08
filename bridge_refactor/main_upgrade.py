#!/usr/bin/env python3
"""  
bridge_refactor/main_upgrade.py — المشغل الموحد المطور (MAINT-7 / D49–D54)
==========================================================================
نقطة انطلاق واحدة بجوار main.py (عادة المالك — فويس 137):

    cd bridge_refactor && python main_upgrade.py        أو        python bridge_refactor/main_upgrade.py

ما يفعله (Process Supervisor إضافي فقط — D50: main.py و01.33 وكل ملف قائم في bridge_refactor/ لا يُلمس):
  1. يشغّل البوت 31 كعملية ابن:   [sys.executable, SCRIPT_DIR/main.py]  cwd=SCRIPT_DIR  (الشاشة للبوت وحده)
  2. يشغّل ماكينة 05.02 في مواعيد ثابتة بتوقيت الجهاز (D54) كعملية ابن منفصلة cwd=ROOT_DIR،
     ومخرجاتها كلها إلى logs/scheduler_0502.log (D52 — لا تلويث لشاشة التيليجرام):
        06:00 و 18:00  →  --sweep  -f accounts_genspark.json -l 10                      (MAINT-6/D48)
        00:00 و 12:00  →  --revive -q accounts_cooldown.json -f accounts_genspark.json -l 0   (D16/D17/7.11 + Q-15)
     ⚠️ `-q accounts_cooldown.json` إلزامي دستورياً: بدونه يفحص 05.02 معزل الهدية (الافتراضي) وهو ممنوع (7.11/D23).
  3. إغلاق رشيق (D53): SIGINT/SIGTERM (+SIGBREAK على ويندوز) ⇒ إنهاء الأبناء (terminate ثم kill بعد مهلة) + atexit
     كشبكة أمان ⇒ صفر Zombie. خروج البوت (لأي سبب) ⇒ إيقاف أي مهمة جارية والخروج بنفس كود البوت.
  4. مكتبات قياسية فقط (LIMITS): subprocess, sys, time, signal, pathlib, atexit, logging, os, shutil. يعمل على Windows وLinux
     (sys.executable + pathlib؛ المسارات مطلقة ومحسومة من __file__ مهما كان مجلد التشغيل).
  5. منظومة النظافة الشاملة (MAINT-8 / D55–D61 — فويسات 143–147): `clean_disk_garbage()` عند الإقلاع (D58 تطهير استرجاعي)
     ثم كل 60 دقيقة داخل tick — قانون الـ60 دقيقة بلا استثناء (فويس 144: «رفع ما رفعش.. طالما عدت ساعة يتمسح»):
        • ثالوث كل مشروع في project_registry/<key>/ (المحلي ثم الأب — نفس resolve_shared_path في 01.33 L140–157):
          archive/*.tar.gz (+ *.tar.tmp اليتيمة) — D55 | checkpoints/hot/<id>/ عبر rmtree — D56 | reports/<id>.json — D57
        • extracted_webapp/* و extracted_push_temp/* + webapp*.tar.gz في مجلد البوت (نمط مقيّد لا `*.tar.gz` عام) — D60
        • bridge_bot.log و logs/*.log: قصّ في المكان عند >10MB مع إبقاء آخر 2MB (لا حذف ⇒ لا كسر لقفل ويندوز) — D59؛
          لوجات logs/*.log الخاملة >30 يوماً تُحذف (فويس 145)
        • محرَّم اللمس (D61): manifest.json / manifest.bak / queue.json / secrets.local.json / registry.json — المنظّف لا يدخل
          جذر المشروع أصلاً، وكل حذف داخل try/except OSError (أقفال ويندوز ⇒ تخطٍّ وتسجيل، لا انهيار).
        العمر = الأقدم بين الطابع الزمني في الاسم (معرّفات الثالوث UTC `%Y%m%dT%H%M%S%fZ`) وmtime (فويس 143: «حتى لو ملوش تاريخ»).

أعلام اختيارية:  --run-now sweep|revive  (تشغيل مهمة فوراً عند الإقلاع ثم متابعة الجدول)   --no-bot  (المجدول فقط)
                 --help
"""
from __future__ import annotations

import atexit
import logging
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import time

# ── المسارات المطلقة (D51) ─────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent          # bridge_refactor/
ROOT_DIR = SCRIPT_DIR.parent                                   # جذر المشروع
BOT_MAIN_PY = SCRIPT_DIR / "main.py"
ENGINE_0502 = ROOT_DIR / "05.02_genspark_delayed_gifts_manager.py"


def resolve_shared_path(name: str) -> pathlib.Path:
    """مسار مشترك ذكي عاكس لـ 01.33 P23:
    لو الملف/المجلد موجود محلياً جنب البوت (ROOT_DIR) يستخدمه (أولوية محلية)،
    وإلا يلقطه من الفولدر الأب المركزي (ROOT_DIR.parent) — ولو غير موجود في الاثنين يرجع الأب (للإنشاء والتوافق مع الـ Vaults المركزية).
    """
    local = ROOT_DIR / name
    parent = ROOT_DIR.parent / name
    if local.exists():
        return local
    if parent.exists():
        return parent
    return parent


ACCOUNTS_FILE = resolve_shared_path("accounts_genspark.json")
COOLDOWN_VAULT = ACCOUNTS_FILE.parent / "accounts_cooldown.json"          # D33: بجوار الأساسي دائماً
LOGS_DIR = ROOT_DIR / "logs"
ENGINE_LOG_NAME = "scheduler_0502.log"
SUPERVISOR_LOG_NAME = "main_upgrade.log"

# ── الجدول الثابت (D54) — بتوقيت الجهاز المحلي (جهاز المالك = توقيت مصر) ─────────
SCHEDULE = (
    (0, 0, "revive"),
    (6, 0, "sweep"),
    (12, 0, "revive"),
    (18, 0, "sweep"),
)
SWEEP_BATCH = 10            # D54 (≤ SWEEP_MAX_BATCH=20 في 05.02 — Q-24)
TICK_SECONDS = 20.0         # دقة الجدول: أقل من دقيقة ⇒ لا تفويت لدقيقة الموعد
TERMINATE_GRACE_S = 10.0    # مهلة terminate قبل kill (D53)
# ── [MAINT-9/S5+Q-GO-3] علامة «مشغول» للفحص اللايف (bridge_refactor/live_account_checker.py) ──
# وجودها بعمر حديث ⇒ تأجيل --sweep و--revive المجدولين (لا تضارب على الأساسي/الخزنة/الشبكة)؛
# أقدم من LIVE_BUSY_ORPHAN_S = يتيمة (قتل عنيف/انقطاع كهرباء) ⇒ تحذير ومتابعة الجدول.
LIVE_BUSY_FILE = ACCOUNTS_FILE.parent / "live_check.busy"
LIVE_BUSY_ORPHAN_S = 900.0  # الحساب الواحد ≤ ~5.5 دقيقة (45s×2 login + 25s×5 + فاصل 300s) ⇒ 15 دقيقة هامش

# ── منظومة النظافة الشاملة (MAINT-8 / D55–D61) ───────────────────────────────
GARBAGE_MAX_AGE_S = 60 * 60            # D55/D56/D57/D60: ما تجاوز 60 دقيقة يُمسح — بلا استثناء (فويس 144)
GARBAGE_INTERVAL_S = 60 * 60           # دورة التنظيف داخل tick (إضافة إلى التطهير الكامل عند الإقلاع — D58)
LOG_TRUNCATE_AT = 10 * 1024 * 1024     # D59: اللوج فوق 10MB يُقصّ في مكانه…
LOG_KEEP_TAIL = 2 * 1024 * 1024        # D59: …مع الاحتفاظ بآخر 2MB (بلا حذف/إعادة تسمية ⇒ آمن مع FileHandler المفتوح)
LOG_MAX_AGE_DAYS = 30                  # فويس 145: لوجات logs/*.log الخاملة 30 يوماً تُحذف
BOT_LOG_NAME = "bridge_bot.log"        # 01.33 L69: SCRIPT_DIR / "bridge_bot.log"
REGISTRY_DIR_NAME = "project_registry"  # 01.33 L261: resolve_shared_path("project_registry")
TEMP_DIR_NAMES = ("extracted_webapp", "extracted_push_temp")  # D60 (الثاني لا يظهر في أي كود — احتياطي لا-ضرر)
ROOT_ARCHIVE_GLOB = "webapp*.tar.gz*"  # D55 «الروت»: نمط مقيّد (01.33 L2872 webapp.tar.gz/.tmp) — لا `*.tar.gz` عام
PROTECTED_NAMES = frozenset({"manifest.json", "manifest.bak", "queue.json", "secrets.local.json", "registry.json"})  # D61

log = logging.getLogger("main_upgrade")


def build_job_cmd(kind: str) -> list[str]:
    """أمر 05.02 الحرفي لكل نوع (قابل للاختبار بلا تشغيل)."""
    base = [sys.executable, str(ENGINE_0502)]
    if kind == "sweep":
        return base + ["--sweep", "-f", str(ACCOUNTS_FILE), "-l", str(SWEEP_BATCH)]
    if kind == "revive":
        return base + ["--revive", "-q", str(COOLDOWN_VAULT), "-f", str(ACCOUNTS_FILE), "-l", "0"]
    raise ValueError(f"unknown job kind: {kind!r}")


def due_slot(lt: time.struct_time, fired: set) -> tuple:
    """(key, kind) للموعد المستحق في هذه الدقيقة ولم يُطلق اليوم؛ وإلا (None, None). دالة نقية."""
    for hh, mm, kind in SCHEDULE:
        if lt.tm_hour == hh and lt.tm_min == mm:
            key = (lt.tm_year, lt.tm_yday, hh, mm)
            if key not in fired:
                return key, kind
    return None, None


def live_check_busy(now: float | None = None, path: pathlib.Path | None = None) -> tuple[bool, str]:
    """[MAINT-9/S5] (مشغول؟, وصف): True فقط إذا كانت العلامة موجودة وعمر mtime < LIVE_BUSY_ORPHAN_S.
    علامة يتيمة ⇒ (False, "orphan …") — المستدعي يسجّل تحذيراً ويكمل. لا كتابة ولا حذف هنا (المشغّل وحده يملك الملف)."""
    p = LIVE_BUSY_FILE if path is None else path
    try:
        st = p.stat()
    except OSError:
        return False, ""
    age = (time.time() if now is None else now) - st.st_mtime
    if age < LIVE_BUSY_ORPHAN_S:
        return True, f"live_check.busy عمرها {age / 60:.1f} دقيقة"
    return False, f"orphan live_check.busy عمرها {age / 60:.0f} دقيقة (> {LIVE_BUSY_ORPHAN_S / 60:.0f}) — تُتجاهَل"


def _terminate(proc, name: str, grace: float = TERMINATE_GRACE_S) -> None:
    """إنهاء رشيق: terminate ⇒ انتظار ⇒ kill؛ ثم wait لحصد العملية (لا Zombie)."""
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            log.warning("%s لم يستجب خلال %.0fs — kill", name, grace)
            proc.kill()
            proc.wait(timeout=5)
    except Exception as e:  # pragma: no cover — شبكة أمان
        log.error("تعذر إنهاء %s: %s", name, e)


# ── منظومة النظافة الشاملة (MAINT-8 / D55–D61) ───────────────────────────────
def bot_homes() -> list[pathlib.Path]:
    """مجلدات عمل البوت 31 (= SCRIPT_DIR داخل 01.33): BRIDGE_HOME إن ضُبط (runtime.py L26/L36) ثم ROOT_DIR."""
    homes: list[pathlib.Path] = []
    for cand in (os.environ.get("BRIDGE_HOME") or "", ROOT_DIR):
        if not cand:
            continue
        p = pathlib.Path(cand).resolve()
        if p not in homes:
            homes.append(p)
    return homes


def registry_homes() -> list[pathlib.Path]:
    """يعكس resolve_shared_path("project_registry") في 01.33 L140–157 (المحلي ثم الأب) — ويُنظَّف كلاهما إن وُجد
    (فويس 141: «لو مش موجود جوة بيشوفه من الأب» + فويس 143: مشاريع قديمة/أجهزة أخرى تُمسح كذلك)."""
    out: list[pathlib.Path] = []
    for h in bot_homes():
        for cand in (h / REGISTRY_DIR_NAME, h.parent / REGISTRY_DIR_NAME):
            if cand.is_dir() and cand not in out:
                out.append(cand)
    return out


def _long_path(p: pathlib.Path | str) -> str:
    """تحويل ديناميكي للمسار على ويندوز لتجاوز حاجز MAX_PATH (260 حرفاً) حتى 32,767 حرفاً عبر بادئة \\?\\.
    على لينكس/ماك أو إذا كان المسار بادئاً بالفعل بـ \\?\\ يُترك كما هو دون تغيير."""
    try:
        s = str(pathlib.Path(p).resolve())
    except OSError:
        s = str(p)
    if sys.platform == "win32" and not s.startswith(("\\\\?\\", "\\\\.\\")):
        return "\\\\?\\" + s
    return s


def _listdir(path: pathlib.Path) -> list[pathlib.Path]:
    try:
        return list(path.iterdir())
    except OSError:
        try:
            target = _long_path(path)
            return [path / entry for entry in os.listdir(target)]
        except OSError:
            return []


def _stamp_is_old(name: str, cutoff_stamp: str):
    """معرّفات الثالوث تبدأ بـ YYYYMMDDTHHMMSS (UTC — 01.33 L5340)؛ مقارنة نصية ثابتة العرض. None إن لم يكن الاسم طابعاً."""
    s = name[:15]
    if len(s) == 15 and s[8] == "T" and s[:8].isdigit() and s[9:].isdigit():
        return s < cutoff_stamp
    return None


def _newest_mtime(path: pathlib.Path):
    """mtime العنصر، وللمجلد الأحدث بينه وبين أبنائه المباشرين (تنزيل جارٍ داخل extracted_webapp/<pid>/ يبقى طازجاً)."""
    target = _long_path(path)
    try:
        newest = os.lstat(target).st_mtime
    except OSError:
        return None
    if os.path.isdir(target) and not os.path.islink(target):
        for child in _listdir(path):
            try:
                newest = max(newest, os.lstat(_long_path(child)).st_mtime)
            except OSError:
                pass
    return newest


def is_garbage(path: pathlib.Path, now: float, max_age_s: float = GARBAGE_MAX_AGE_S) -> bool:
    """قديم إذا قال الطابع الزمني في الاسم **أو** mtime إنه تجاوز max_age_s — أيهما (فويس 143: «حتى لو ملوش تاريخ»)."""
    cutoff = time.strftime("%Y%m%dT%H%M%S", time.gmtime(now - max_age_s))
    if _stamp_is_old(path.name, cutoff):
        return True
    mtime = _newest_mtime(path)
    if mtime is None:
        return False
    return (now - mtime) > max_age_s


def _tree_bytes(path: pathlib.Path) -> int:
    target = _long_path(path)
    try:
        if not os.path.isdir(target) or os.path.islink(target):
            return os.lstat(target).st_size
    except OSError:
        return 0
    total = 0
    for root, _dirs, files in os.walk(target):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def _remove(path: pathlib.Path, stats: dict, why: str) -> bool:
    """حذف واحد محصّن: D61 (الأسماء المحرّمة لا تُلمس) + تخطي MAX_PATH ديناميكياً عبر _long_path + try/except OSError (أقفال ويندوز WinError 32 ⇒ تخطٍّ، لا انهيار)."""
    if path.name in PROTECTED_NAMES:
        stats["protected"] += 1
        return False
    size = _tree_bytes(path)
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(_long_path(path))
        else:
            path.unlink()
    except OSError as e:
        remaining = _tree_bytes(path) if os.path.exists(_long_path(path)) else 0
        stats["errors"] += 1
        stats["freed_bytes"] += max(0, size - remaining)
        log.warning("🧹 تعذر حذف %s (%s): %s", path, why, e)
        return False
    stats["removed"] += 1
    stats["freed_bytes"] += size
    log.info("🧹 حُذف [%s] %s (%.1f MB)", why, path, size / 1048576)
    return True


def _purge_entries(entries, now: float, stats: dict, why: str, max_age_s: float = GARBAGE_MAX_AGE_S) -> None:
    for p in entries:
        if p.name in PROTECTED_NAMES:
            stats["protected"] += 1
            continue
        if is_garbage(p, now, max_age_s):
            _remove(p, stats, why)
        else:
            stats["kept_fresh"] += 1


def clean_project_triad(project_dir: pathlib.Path, now: float, stats: dict) -> None:
    """D55/D56/D57 لمشروع واحد — ثلاثة مسارات فرعية فقط؛ جذر المشروع (manifest/queue/secrets) لا يُدخَل أصلاً."""
    archive = project_dir / "archive"
    if archive.is_dir():
        _purge_entries([p for p in _listdir(archive) if p.name.endswith((".tar.gz", ".tar.tmp"))], now, stats, "archive")
    hot = project_dir / "checkpoints" / "hot"
    if hot.is_dir():
        _purge_entries(_listdir(hot), now, stats, "checkpoints/hot")
    reports = project_dir / "reports"
    if reports.is_dir():
        _purge_entries([p for p in _listdir(reports) if p.suffix == ".json"], now, stats, "reports")


def clean_temp_dirs(now: float, stats: dict) -> None:
    """D60: بقايا extracted_webapp/<pid>/ (01.33 L997/L6768) و extracted_push_temp/ + webapp*.tar.gz في مجلد البوت."""
    for home in bot_homes():
        for name in TEMP_DIR_NAMES:
            d = home / name
            if d.is_dir():
                _purge_entries(_listdir(d), now, stats, name)
        try:
            root_archives = [p for p in home.glob(ROOT_ARCHIVE_GLOB) if p.is_file()]
        except OSError:
            root_archives = []
        _purge_entries(root_archives, now, stats, "root-webapp-archive")


def truncate_log_in_place(path: pathlib.Path, stats: dict,
                          max_bytes: int | None = None, keep_bytes: int | None = None) -> bool:
    """D59: >max_bytes ⇒ يُعاد كتابة آخر keep_bytes (من أول سطر كامل) في نفس الملف ثم truncate.
    لا حذف ولا إعادة تسمية ⇒ FileHandler المفتوح (01.33 L76 وضع append) يكمل الكتابة في النهاية الجديدة على ويندوز ولينكس."""
    max_bytes = LOG_TRUNCATE_AT if max_bytes is None else max_bytes
    keep_bytes = LOG_KEEP_TAIL if keep_bytes is None else keep_bytes
    try:
        size = path.stat().st_size
        if size <= max_bytes:
            return False
        with open(path, "r+b") as fh:
            fh.seek(max(0, size - keep_bytes))
            tail = fh.read()
            nl = tail.find(b"\n")
            if 0 <= nl < len(tail) - 1:
                tail = tail[nl + 1:]
            fh.seek(0)
            fh.write(tail)
            fh.truncate()
    except OSError as e:
        stats["errors"] += 1
        log.warning("🧹 تعذر قصّ اللوج %s: %s", path, e)
        return False
    stats["truncated"] += 1
    stats["freed_bytes"] += max(0, size - len(tail))
    log.info("🧹 قُصّ اللوج %s: %.1f MB → %.1f MB", path, size / 1048576, len(tail) / 1048576)
    return True


def clean_logs(now: float, stats: dict) -> None:
    """D59 + فويس 145: bridge_bot.log (قصّ فقط — ملف البوت الحي لا يُحذف أبداً) و logs/*.log (قصّ، والخامل >30 يوماً يُحذف)."""
    seen: set = set()
    for home in bot_homes():
        p = home / BOT_LOG_NAME
        if p.is_file() and p not in seen:
            seen.add(p)
            truncate_log_in_place(p, stats)
    if LOGS_DIR.is_dir():
        logs = [p for p in _listdir(LOGS_DIR) if p.suffix == ".log" and p.is_file()]
        for p in logs:
            truncate_log_in_place(p, stats)
        _purge_entries(logs, now, stats, "logs-idle-30d", max_age_s=LOG_MAX_AGE_DAYS * 86400.0)


def clean_disk_garbage(now: float | None = None) -> dict:
    """المنظّف الموحد (D55–D61). يعيد إحصاءات: removed/truncated/freed_bytes/errors/kept_fresh/protected/projects."""
    now = time.time() if now is None else float(now)
    stats = {"removed": 0, "truncated": 0, "freed_bytes": 0, "errors": 0, "kept_fresh": 0, "protected": 0, "projects": 0}
    for home in registry_homes():
        for project_dir in _listdir(home):
            if project_dir.is_dir() and not project_dir.is_symlink():
                stats["projects"] += 1
                clean_project_triad(project_dir, now, stats)
    clean_temp_dirs(now, stats)
    clean_logs(now, stats)
    log.info("🧹 clean_disk_garbage: حُذف %d | قُصّ %d لوج | حُرّر %.1f MB | طازج %d | محمي %d | أخطاء %d | مشاريع %d",
             stats["removed"], stats["truncated"], stats["freed_bytes"] / 1048576,
             stats["kept_fresh"], stats["protected"], stats["errors"], stats["projects"])
    return stats


class Supervisor:
    def __init__(self, with_bot: bool = True):
        self.last_clean = 0.0
        self.with_bot = with_bot
        self.bot = None
        self.job = None
        self.job_kind = None
        self.job_log = None
        self.job_started = 0.0
        self.fired: set = set()
        self.stop_requested = False
        self.stop_reason = ""
        self._closed = False

    # ── البوت 31 ──
    def start_bot(self):
        self.bot = subprocess.Popen([sys.executable, str(BOT_MAIN_PY)], cwd=str(SCRIPT_DIR))
        log.info("البوت 31 انطلق (pid %s): %s", self.bot.pid, BOT_MAIN_PY.name)
        return self.bot

    # ── ماكينة 05.02 ──
    def start_job(self, kind: str) -> bool:
        if self.job is not None and self.job.poll() is None:
            log.warning("تخطي مهمة %s: مهمة %s (pid %s) ما زالت تعمل منذ %.0f دقيقة",
                        kind, self.job_kind, self.job.pid, (time.time() - self.job_started) / 60)
            return False
        busy, why = live_check_busy()
        if busy:
            log.warning("تخطي مهمة %s: فحص لايف يعمل (%s) — [MAINT-9/S5] يُعاد في الموعد التالي", kind, why)
            return False
        if why:
            log.warning("%s", why)
        self.reap_job()
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.job_log = open(LOGS_DIR / ENGINE_LOG_NAME, "a", encoding="utf-8")
        self.job_log.write(f"\n===== [{time.strftime('%Y-%m-%d %H:%M:%S')}] START {kind} =====\n")
        self.job_log.flush()
        self.job = subprocess.Popen(build_job_cmd(kind), cwd=str(ROOT_DIR),
                                    stdout=self.job_log, stderr=subprocess.STDOUT)
        self.job_kind, self.job_started = kind, time.time()
        log.info("مهمة 05.02 %s انطلقت (pid %s) → logs/%s", kind, self.job.pid, ENGINE_LOG_NAME)
        return True

    def reap_job(self) -> None:
        """حصد مهمة انتهت + إغلاق ملف اللوج + تسجيل كود الخروج."""
        if self.job is None or self.job.poll() is None:
            return
        rc = self.job.returncode
        if self.job_log is not None:
            try:
                self.job_log.write(f"===== [{time.strftime('%Y-%m-%d %H:%M:%S')}] END {self.job_kind} exit={rc} =====\n")
                self.job_log.close()
            except Exception:  # pragma: no cover
                pass
            self.job_log = None
        (log.info if rc == 0 else log.warning)("مهمة 05.02 %s انتهت exit=%s بعد %.0f ثانية",
                                               self.job_kind, rc, time.time() - self.job_started)
        self.job = None
        self.job_kind = None

    # ── النظافة (MAINT-8) ──
    def clean(self, why: str, now: float | None = None) -> dict | None:
        """تشغيل المنظّف؛ أي استثناء غير متوقع يُسجَّل ولا يُسقط المشغل أبداً (شبكة أمان فوق OSError الداخلية)."""
        now = time.time() if now is None else now
        self.last_clean = now
        try:
            return clean_disk_garbage(now=now)
        except Exception as e:  # pragma: no cover — شبكة أمان
            log.error("🧹 clean_disk_garbage (%s) فشل: %s", why, e)
            return None

    def tick(self, lt: time.struct_time | None = None, now: float | None = None) -> None:
        """دورة واحدة: حصد المنتهي ثم إطلاق المستحق (مرة واحدة لكل موعد في اليوم) + تنظيف كل GARBAGE_INTERVAL_S."""
        self.reap_job()
        now = time.time() if now is None else now
        if now - self.last_clean >= GARBAGE_INTERVAL_S:
            self.clean("hourly", now)
        key, kind = due_slot(lt or time.localtime(), self.fired)
        if key is not None:
            self.fired.add(key)
            self.start_job(kind)

    # ── الإغلاق (D53) ──
    def request_stop(self, reason: str) -> None:
        self.stop_requested = True
        self.stop_reason = self.stop_reason or reason

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        _terminate(self.job, "05.02")
        self.reap_job()
        _terminate(self.bot, "البوت 31")
        if self.bot is not None and self.bot.poll() is not None:
            log.info("البوت 31 أُغلق exit=%s", self.bot.returncode)

    def _on_signal(self, signum, frame) -> None:
        self.request_stop(f"signal {signum}")

    def install_signal_handlers(self) -> None:
        for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
            sig = getattr(signal, name, None)
            if sig is not None:
                try:
                    signal.signal(sig, self._on_signal)
                except (ValueError, OSError):  # pragma: no cover — ليس الخيط الرئيسي
                    pass
        atexit.register(self.shutdown)

    # ── الحلقة الرئيسية ──
    def run(self, run_now: str | None = None, tick_seconds: float = TICK_SECONDS) -> int:
        self.install_signal_handlers()
        self.clean("startup")          # D58: تطهير استرجاعي كامل قبل انطلاق البوت
        if self.with_bot:
            self.start_bot()
        if run_now:
            self.start_job(run_now)
        rc = 0
        try:
            while not self.stop_requested:
                if self.with_bot and self.bot.poll() is not None:
                    rc = self.bot.returncode
                    self.request_stop(f"bot exited rc={rc}")
                    break
                self.tick()
                time.sleep(tick_seconds)
        except KeyboardInterrupt:
            self.request_stop("KeyboardInterrupt")
        log.info("إيقاف: %s", self.stop_reason)
        self.shutdown()
        return rc


def _setup_logging() -> None:
    if sys.platform.startswith("win"):
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [main_upgrade] %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handlers = [logging.StreamHandler(sys.stderr), logging.FileHandler(LOGS_DIR / SUPERVISOR_LOG_NAME, encoding="utf-8")]
    for h in handlers:
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)


def parse_args(argv: list[str]) -> dict:
    opts = {"run_now": None, "with_bot": True, "help": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--run-now" and i + 1 < len(argv) and argv[i + 1] in ("sweep", "revive"):
            opts["run_now"] = argv[i + 1]
            i += 1
        elif a == "--no-bot":
            opts["with_bot"] = False
        elif a in ("-h", "--help"):
            opts["help"] = True
        else:
            raise SystemExit(f"خيار غير معروف: {a}  (المتاح: --run-now sweep|revive, --no-bot, --help)")
        i += 1
    return opts


def main(argv: list[str] | None = None) -> int:
    opts = parse_args(sys.argv[1:] if argv is None else argv)
    if opts["help"]:
        print(__doc__)
        return 0
    _setup_logging()
    for p, what in ((BOT_MAIN_PY, "main.py"), (ENGINE_0502, ENGINE_0502.name)):
        if not p.exists() and not (what == "main.py" and not opts["with_bot"]):
            log.error("ملف مفقود: %s", p)
            return 2
    log.info("SCRIPT_DIR=%s | ROOT_DIR=%s | الجدول: %s", SCRIPT_DIR, ROOT_DIR,
             ", ".join(f"{hh:02d}:{mm:02d} {k}" for hh, mm, k in SCHEDULE))
    log.info("🧹 النظافة: registry=%s | تنظيف عند الإقلاع ثم كل %d دقيقة | عمر الحذف %d دقيقة",
             [str(p) for p in registry_homes()] or "—", GARBAGE_INTERVAL_S // 60, GARBAGE_MAX_AGE_S // 60)
    return Supervisor(with_bot=opts["with_bot"]).run(run_now=opts["run_now"])


if __name__ == "__main__":
    sys.exit(main())
