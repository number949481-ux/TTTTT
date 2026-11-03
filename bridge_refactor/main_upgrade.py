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
  4. مكتبات قياسية فقط (LIMITS): subprocess, sys, time, signal, pathlib, atexit, logging. يعمل على Windows وLinux
     (sys.executable + pathlib؛ المسارات مطلقة ومحسومة من __file__ مهما كان مجلد التشغيل).

أعلام اختيارية:  --run-now sweep|revive  (تشغيل مهمة فوراً عند الإقلاع ثم متابعة الجدول)   --no-bot  (المجدول فقط)
                 --help
"""
from __future__ import annotations

import atexit
import logging
import pathlib
import signal
import subprocess
import sys
import time

# ── المسارات المطلقة (D51) ─────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent          # bridge_refactor/
ROOT_DIR = SCRIPT_DIR.parent                                   # جذر المشروع
BOT_MAIN_PY = SCRIPT_DIR / "main.py"
ENGINE_0502 = ROOT_DIR / "05.02_genspark_delayed_gifts_manager.py"
ACCOUNTS_FILE = ROOT_DIR / "accounts_genspark.json"
COOLDOWN_VAULT = ROOT_DIR / "accounts_cooldown.json"          # D33: بجوار الأساسي
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


class Supervisor:
    def __init__(self, with_bot: bool = True):
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

    def tick(self, lt: time.struct_time | None = None) -> None:
        """دورة واحدة: حصد المنتهي ثم إطلاق المستحق (مرة واحدة لكل موعد في اليوم)."""
        self.reap_job()
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
    return Supervisor(with_bot=opts["with_bot"]).run(run_now=opts["run_now"])


if __name__ == "__main__":
    sys.exit(main())
