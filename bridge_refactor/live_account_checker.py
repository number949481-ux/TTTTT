#!/usr/bin/env python3
"""
bridge_refactor/live_account_checker.py — مشغّل الفحص والتنشيط اللايف (MAINT-9 / D62–D70)
=========================================================================================
يُطلقه البوت 31 (01.33) كعملية مستقلة عند ضغط «🔍 فحص وتنشيط الحسابات لايف ⚡» بعد تأكيد أخضر:

    python bridge_refactor/live_account_checker.py --chat-id <id> --message-id <id> --mode fresh|resume

ما يفعله (DRY — عضلات 05.02 حصراً، لا منطق فحص هنا):
  1. يحجز علامة «مشغول» live_check.busy (O_CREAT|O_EXCL) بجوار الأساسي — Supervisor يؤجّل --sweep/--revive (Q-GO-3).
  2. mode=fresh ⇒ شيك بوينت دوار جديد (RotationCheckpoint._fresh)؛ resume ⇒ يكمل من آخر بصمة (Q-GO-1 البديل ب).
  3. يكتب طابور البصمات live_check_queue.json (sha256 فقط — بلا أسرار) ثم يستدعي
     MasterDelayedGiftsManager.run_quarantine(rotation=…, on_account=…, stop_flag=…) على الأساسي في مكانه
     (نسخ لا قص — فويس 181): السليم يبقى ويُنشَّط للبوت 31، المتأخر → المعزل، الميت → الفاشل، خطأ الشبكة يبقى.
  4. بعد كل حساب: عدادات live_check_state.json + heartbeat للـ busy + تعديل رسالة اللايف (كم من كم — فويس 173)
     + رسالة صيد مستقلة بصوت عند HEALTHY ورصيد ≥ 100 (فويس 170) + سطر JSON في account_log.jsonl لخطأ الشبكة.
  5. الإيقاف بملف راية live_check.stop (ويندوز بلا إشارات) — يتوقف بعد الحساب الجاري (≤ 5.5 دقيقة).
  6. قاطع شبكة (Q-GO-4): 5 AUTH_FAILED متتالية ⇒ توقف 10 دقائق + تنبيه؛ 3 مرات ⇒ إيقاف ذاتي + إشعار.
  7. مكتبات قياسية فقط + importlib لتحميل 05.02 (اسمه يبدأ برقم). لا يستورد 01.33 إطلاقاً.

أكواد الخروج: 0 مكتمل | 1 خطأ | 2 فحص آخر يعمل | 3 أُوقف بالملف | 4 إيقاف ذاتي بالقاطع
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html
import importlib.util
import json
import os
import pathlib
import sys
import time
import traceback
import urllib.error
import urllib.request

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
ENGINE_0502_NAME = "05.02_genspark_delayed_gifts_manager.py"

QUEUE_FILE_NAME = "live_check_queue.json"
STATE_FILE_NAME = "live_check_state.json"
BUSY_FILE_NAME = "live_check.busy"
STOP_FILE_NAME = "live_check.stop"
ACCOUNT_LOG_NAME = "account_log.jsonl"
BUSY_ORPHAN_S = 900.0            # نفس LIVE_BUSY_ORPHAN_S في main_upgrade.py و01.33
HUNT_MIN_BALANCE = 100           # فويس 170: رسالة صيد عند حساب نشط برصيد ≥ 100
LIVE_TEXT_MAX = 3900             # سقف تيليجرام 4096 مع هامش
BREAKER_CONSECUTIVE = 5          # Q-GO-4
BREAKER_PAUSE_S = 600.0
BREAKER_MAX_TRIPS = 3
TELEGRAM_TIMEOUT_S = 20

EXIT_OK, EXIT_ERROR, EXIT_BUSY, EXIT_STOPPED, EXIT_BREAKER = 0, 1, 2, 3, 4


# ── أدوات عامة ───────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(f"[{_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [live_check] {msg}", flush=True)


def email_key(email: str) -> str:
    """بصمة البريد — مطابقة حرفياً لـ RotationCheckpoint.key (lower/strip) ولا تُسرِّب شيئاً"""
    return hashlib.sha256((email or "").strip().lower().encode("utf-8")).hexdigest()


def atomic_write_json(path: pathlib.Path, data) -> bool:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError as e:
        log(f"⚠️ تعذر كتابة {path.name}: {type(e).__name__}")
        try:
            tmp.unlink()
        except OSError:
            pass
        return False


def load_gifts_manager(root: pathlib.Path):
    """تحميل 05.02 بالمسار (الاسم يبدأ برقم ⇒ importlib). يرفع ImportError لو الماستر مانجر غائب (R3)."""
    engine = root / ENGINE_0502_NAME
    if not engine.exists():
        raise FileNotFoundError(f"{ENGINE_0502_NAME} غير موجود بجوار {root.name}")
    spec = importlib.util.spec_from_file_location("gifts_manager_live", engine)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_bot_token(root: pathlib.Path, token_file: str | None = None) -> str:
    """TELEGRAM_BOT_TOKEN ← --token-file ← telegram_bot_token.txt (محلي ثم الأب) — نفس ترتيب 01.33؛ لا يُطبع أبداً"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    candidates = []
    if token_file:
        candidates.append(pathlib.Path(token_file))
    candidates += [root / "telegram_bot_token.txt", root.parent / "telegram_bot_token.txt"]
    for p in candidates:
        try:
            if p.exists():
                token = p.read_text(encoding="utf-8").strip()
                if token:
                    return token
        except OSError:
            continue
    return ""


# ── تيليجرام (urllib فقط) ────────────────────────────────────────────────────
class Telegram:
    """إرسال/تعديل بأقل transport: 429 ⇒ نوم retry_after+1 ومحاولة واحدة (كما 01.33)؛ «not modified» ⇒ نجاح."""

    def __init__(self, token: str, chat_id: int):
        self.token = token
        self.chat_id = int(chat_id)
        self.enabled = bool(token)

    def _call(self, method: str, payload: dict) -> dict:
        if not self.enabled:
            return {"ok": False, "description": "BOT_TOKEN_MISSING", "result": {}}
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for attempt in (1, 2):
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=TELEGRAM_TIMEOUT_S) as resp:
                    data = json.loads(resp.read().decode("utf-8", "replace") or "{}")
                    return data if isinstance(data, dict) else {"ok": False, "description": "bad json", "result": {}}
            except urllib.error.HTTPError as e:
                try:
                    data = json.loads(e.read().decode("utf-8", "replace") or "{}")
                except Exception:
                    data = {}
                if e.code == 429 and attempt == 1:
                    retry_after = 3
                    if isinstance(data, dict) and isinstance(data.get("parameters"), dict):
                        retry_after = int(data["parameters"].get("retry_after") or 3)
                    log(f"⚠️ HTTP 429 من تيليجرام ({method}) — انتظار {retry_after + 1}s")
                    time.sleep(float(retry_after) + 1.0)
                    continue
                return {"ok": False, "description": str(data.get("description") or e.code) if isinstance(data, dict) else str(e.code), "result": {}}
            except Exception as e:  # شبكة/مهلة — لا نُسقط الفحص بسبب تيليجرام
                return {"ok": False, "description": f"{type(e).__name__}", "result": {}}
        return {"ok": False, "description": "429 twice", "result": {}}

    def send(self, text: str, reply_markup: dict | None = None, silent: bool = False) -> int | None:
        payload = {"chat_id": self.chat_id, "text": text[:LIVE_TEXT_MAX], "parse_mode": "HTML",
                   "disable_web_page_preview": True, "disable_notification": bool(silent)}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self._call("sendMessage", payload)
        if res.get("ok"):
            return int((res.get("result") or {}).get("message_id") or 0) or None
        log(f"⚠️ sendMessage فشل: {res.get('description')}")
        return None

    def edit(self, message_id: int, text: str, reply_markup: dict | None = None) -> tuple[bool, str]:
        payload = {"chat_id": self.chat_id, "message_id": int(message_id), "text": text[:LIVE_TEXT_MAX],
                   "parse_mode": "HTML", "disable_web_page_preview": True}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        res = self._call("editMessageText", payload)
        desc = str(res.get("description") or "")
        if res.get("ok") or "message is not modified" in desc.lower():
            return True, ""
        return False, desc

    def delete(self, message_id: int) -> bool:
        return bool(self._call("deleteMessage", {"chat_id": self.chat_id, "message_id": int(message_id)}).get("ok"))


# ── علامة «مشغول» ───────────────────────────────────────────────────────────
def acquire_busy(path: pathlib.Path, now: float | None = None) -> tuple[bool, str]:
    """O_CREAT|O_EXCL؛ فشل ⇒ لو mtime حديث: (False, سبب)؛ لو يتيم (> BUSY_ORPHAN_S): استبدال بتحذير."""
    payload = json.dumps({"pid": os.getpid(), "started_at": _dt.datetime.now().isoformat(timespec="seconds")})
    for _ in (1, 2):
        try:
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            return True, ""
        except FileExistsError:
            try:
                age = (time.time() if now is None else now) - path.stat().st_mtime
            except OSError:
                continue  # اختفت بين الفحصين ⇒ أعد المحاولة
            if age < BUSY_ORPHAN_S:
                return False, f"فحص لايف آخر يعمل منذ {age / 60:.1f} دقيقة ({path.name})"
            log(f"⚠️ {path.name} يتيمة بعمر {age / 60:.0f} دقيقة — تُستبدل")
            try:
                path.unlink()
            except OSError:
                return False, f"تعذر إزالة {path.name} اليتيمة"
        except OSError as e:
            return False, f"تعذر إنشاء {path.name}: {type(e).__name__}"
    return False, f"تعذر حجز {path.name}"


def heartbeat(path: pathlib.Path) -> None:
    try:
        os.utime(path, None)
    except OSError:
        pass


def release(path: pathlib.Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# ── عرض النصوص ──────────────────────────────────────────────────────────────
def running_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "🛑 إيقاف الفحص التلقائي", "callback_data": "lc_stop", "style": "danger"}]]}


def fmt_dur(seconds: float) -> str:
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"


def render_counters(c: dict) -> str:
    return (
        f"✅ نشط ومُفعَّل: <b>{c.get('active', 0)}</b>\n"
        f"🧊 بُرِّد/مُعزل متأخر الهدية: <b>{c.get('stale', 0)}</b>\n"
        f"🗑️ ميت/محظور → الفاشل: <b>{c.get('dead', 0)}</b>\n"
        f"⚠️ خطأ شبكة (بقي في مكانه): <b>{c.get('net_err', 0)}</b>\n"
        f"🎯 صيد برصيد ≥ {HUNT_MIN_BALANCE}: <b>{c.get('hunted', 0)}</b>"
    )


def render_live(state: dict, headline: str | None = None) -> str:
    c = state.get("counters") or {}
    checked, total = int(c.get("checked", 0)), int(c.get("total", 0))
    remaining = max(0, total - checked)
    pct = (checked * 100 // total) if total else 0
    started = state.get("started_at_ts") or time.time()
    head = headline or "🔍 <b>فحص وتنشيط الحسابات لايف — يعمل الآن</b>"
    mode_ar = "استئناف" if state.get("mode") == "resume" else "من الصفر"
    lines = [
        head,
        f"📊 التقدم: <b>{checked}</b> من <b>{total}</b> ({pct}%) — المتبقي <b>{remaining}</b>",
        f"🧭 الوضع: {mode_ar} · ⏱️ منذ {fmt_dur(time.time() - started)}",
        "",
        render_counters(c),
    ]
    paused_until = state.get("breaker_paused_until") or 0
    if paused_until and paused_until > time.time():
        lines += ["", f"⏸️ قاطع الشبكة: توقف مؤقت {fmt_dur(paused_until - time.time())} (دورة {state.get('breaker_trips', 0)}/{BREAKER_MAX_TRIPS})"]
    if state.get("last_status"):
        lines += ["", f"🕒 آخر حساب: {html.escape(str(state.get('last_status')))} — {html.escape(str(state.get('last_diag') or ''))[:160]}"]
    return "\n".join(lines)[:LIVE_TEXT_MAX]


def render_hunt(email: str, bal: int | None, state: dict) -> str:
    c = state.get("counters") or {}
    return (
        f"🎯 <b>صيد! حساب نشط برصيد</b>\n"
        f"📧 <code>{html.escape(email)}</code>\n"
        f"💰 الرصيد: <b>{(bal or 0):,}</b>\n\n"
        f"📸 لقطة التقدم: {c.get('checked', 0)} من {c.get('total', 0)}\n{render_counters(c)}"
    )[:LIVE_TEXT_MAX]


# ── المشغّل ─────────────────────────────────────────────────────────────────
class LiveChecker:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root = pathlib.Path(args.root).resolve() if args.root else ROOT_DIR
        self.gm = load_gifts_manager(self.root)
        cfg = self.gm.Config
        self.primary = self.gm.resolve_file_path(cfg.PRIMARY_FILE)
        self.folder = self.primary.parent
        self.quarantine = self.folder / cfg.QUARANTINE_FILE
        self.failed = self.folder / cfg.FAILED_FILE
        self.dead = self.folder / cfg.DEAD_FILE
        self.ckpt_path = self.folder / cfg.ROTATION_CHECKPOINT_FILE
        self.queue_file = self.folder / QUEUE_FILE_NAME
        self.state_file = self.folder / STATE_FILE_NAME
        self.busy_file = self.folder / BUSY_FILE_NAME
        self.stop_file = self.folder / STOP_FILE_NAME
        self.account_log = self.folder / ACCOUNT_LOG_NAME
        self.tg = Telegram(load_bot_token(self.root, args.token_file), args.chat_id)
        self.message_id: int | None = int(args.message_id) if args.message_id else None
        self.state: dict = {
            "pid": os.getpid(), "chat_id": int(args.chat_id), "message_id": self.message_id, "mode": args.mode,
            "started_at": _dt.datetime.now().isoformat(timespec="seconds"), "started_at_ts": time.time(),
            "heartbeat": time.time(), "status": "starting",
            "counters": {"checked": 0, "total": 0, "active": 0, "cooldown": 0, "stale": 0, "dead": 0, "net_err": 0, "hunted": 0},
            "last_email_hash": "", "last_status": "", "last_diag": "",
            "breaker_consecutive": 0, "breaker_trips": 0, "breaker_paused_until": 0,
        }
        self.exit_code = EXIT_OK

    # — حالة —
    def save_state(self, status: str | None = None) -> None:
        if status:
            self.state["status"] = status
        self.state["heartbeat"] = time.time()
        atomic_write_json(self.state_file, self.state)

    def push_live(self, headline: str | None = None, keyboard: dict | None = None) -> None:
        text = render_live(self.state, headline)
        kb = running_keyboard() if keyboard is None else keyboard
        if self.message_id:
            ok, why = self.tg.edit(self.message_id, text, kb)
            if ok:
                return
            if "not found" in why.lower() or "message to edit" in why.lower():
                log("⚠️ رسالة اللايف حُذفت — إرسال رسالة جديدة")
            else:
                log(f"⚠️ تعذر تعديل اللايف: {why}")
                return
        new_id = self.tg.send(text, kb, silent=True)
        if new_id:
            self.message_id = new_id
            self.state["message_id"] = new_id

    # — خطاف 05.02 —
    def on_account(self, email: str, status: str, bal: int | None, diag: str) -> None:
        c = self.state["counters"]
        c["checked"] += 1
        if status == "HEALTHY":
            c["active"] += 1
            self.state["breaker_consecutive"] = 0
        elif status == "STALE":
            c["stale"] += 1
            self.state["breaker_consecutive"] = 0
        elif status == "DEAD":
            c["dead"] += 1
            self.state["breaker_consecutive"] = 0
        elif status == "AUTH_FAILED":
            c["net_err"] += 1
            self.state["breaker_consecutive"] += 1
            self._log_net_error(email, diag)
        self.state["last_email_hash"] = email_key(email)
        self.state["last_status"] = status
        self.state["last_diag"] = diag or ""
        heartbeat(self.busy_file)
        self.save_state("running")
        self.push_live()
        if status == "HEALTHY" and (bal or 0) >= HUNT_MIN_BALANCE:
            c["hunted"] += 1
            self.save_state()
            self.tg.send(render_hunt(email, bal, self.state), silent=False)
        self._breaker_check()

    def _log_net_error(self, email: str, reason: str) -> None:
        try:
            entry = {"ts": time.time(), "at": _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                     "event": "live_check_net_error", "email": email, "reason": reason or "",
                     "action": "kept_in_place", "by": "live_account_checker"}
            with open(self.account_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except OSError as e:
            log(f"⚠️ تعذر كتابة {ACCOUNT_LOG_NAME}: {type(e).__name__}")

    def _breaker_check(self) -> None:
        """Q-GO-4: 5 AUTH_FAILED متتالية ⇒ توقف 10 دقائق (قابل للإيقاف بالملف)؛ 3 دورات ⇒ إيقاف ذاتي."""
        if self.state["breaker_consecutive"] < BREAKER_CONSECUTIVE:
            return
        self.state["breaker_consecutive"] = 0
        self.state["breaker_trips"] += 1
        trips = self.state["breaker_trips"]
        if trips >= BREAKER_MAX_TRIPS:
            log(f"⛔ القاطع: {trips} دورات فاشلة متتالية — إيقاف ذاتي")
            self.exit_code = EXIT_BREAKER
            self.tg.send(f"⛔ <b>إيقاف ذاتي للفحص اللايف</b>\n{BREAKER_CONSECUTIVE} أخطاء شبكة متتالية × {trips} دورات — "
                         f"تحقق من الإنترنت/جينسبارك ثم أعد التشغيل بالاستئناف.\n\n{render_counters(self.state['counters'])}")
            try:
                self.stop_file.touch()   # 05.02 يستطلع stop_flag قبل الحساب التالي
            except OSError:
                pass
            return
        until = time.time() + BREAKER_PAUSE_S
        self.state["breaker_paused_until"] = until
        self.save_state("paused")
        log(f"⏸️ القاطع: {BREAKER_CONSECUTIVE} AUTH_FAILED متتالية — توقف {int(BREAKER_PAUSE_S // 60)} دقائق (دورة {trips}/{BREAKER_MAX_TRIPS})")
        self.tg.send(f"⏸️ <b>قاطع الشبكة</b>: {BREAKER_CONSECUTIVE} أخطاء شبكة متتالية — توقف مؤقت {int(BREAKER_PAUSE_S // 60)} دقائق "
                     f"(دورة {trips}/{BREAKER_MAX_TRIPS}). الفحص يستأنف تلقائياً.", silent=True)
        self.push_live()
        while time.time() < until and not self.stop_file.exists() and getattr(self.gm, "IS_RUNNING", True):
            heartbeat(self.busy_file)
            self.state["heartbeat"] = time.time()
            time.sleep(min(5.0, max(0.0, until - time.time())))
        self.state["breaker_paused_until"] = 0
        self.save_state("running")

    # — التشغيل —
    def run(self) -> int:
        ok, why = acquire_busy(self.busy_file)
        if not ok:
            log(f"⛔ {why}")
            self.tg.send(f"ℹ️ <b>فحص لايف آخر يعمل بالفعل</b>\n{html.escape(why)}", silent=True)
            return EXIT_BUSY
        try:
            return self._run_locked()
        except Exception as e:
            log(f"❌ {type(e).__name__}: {e}\n{traceback.format_exc()}")
            self.save_state("error")
            self.push_live(f"❌ <b>توقف الفحص اللايف بخطأ</b>: {html.escape(type(e).__name__)}", keyboard={"inline_keyboard": []})
            return EXIT_ERROR
        finally:
            release(self.busy_file)
            try:
                self.stop_file.unlink()
            except OSError:
                pass

    def _run_locked(self) -> int:
        try:
            self.stop_file.unlink()   # راية إيقاف قديمة
        except OSError:
            pass
        gm = self.gm
        primary_accounts = gm.load_accounts(self.primary)
        emails = [str(a.get("email") or "") for a in primary_accounts if a.get("email")]
        rotation = gm.RotationCheckpoint(self.ckpt_path)
        if self.args.mode == "fresh":
            rotation.state = rotation._fresh(int(rotation.state.get("cycle_no") or 1) + 1)
            rotation.save()
        remaining = rotation.begin_cycle(emails)
        rotation.save()
        # طابور البصمات بترتيب الأساسي (sha256 فقط — Q-23/D68)
        order = [email_key(e) for e in emails if e.strip().lower() in remaining]
        atomic_write_json(self.queue_file, {
            "cycle_id": int(rotation.state.get("cycle_no") or 1), "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "mode": self.args.mode, "total_primary": len(emails), "total": len(order), "order": order,
        })
        c = self.state["counters"]
        c["total"] = len(order)
        self.save_state("running")
        log(f"🚀 بدء الفحص اللايف: {len(order)} حساب متبقٍ من {len(emails)} (وضع {self.args.mode}، دورة #{rotation.state.get('cycle_no')})")
        if not order:
            self.push_live("✅ <b>لا يوجد ما يُفحص</b> — كل حسابات الأساسي مفحوصة في هذه الدورة", keyboard={"inline_keyboard": []})
            self.save_state("done")
            return EXIT_OK
        self.push_live()

        manager = gm.MasterDelayedGiftsManager(
            primary_path=self.primary, quarantine_path=self.quarantine, failed_path=self.failed, dead_path=self.dead,
            threshold_days=gm.Config.STALE_GIFT_DAYS_THRESHOLD, sort_by_balance=gm.Config.SORT_BY_BALANCE,
            auto_relogin=gm.Config.AUTO_RELOGIN, min_delay=float(self.args.delay_min), max_delay=float(self.args.delay_max),
        )
        result = manager.run_quarantine(scan_mode="first_n", limit=len(order), dry_run=bool(self.args.dry_run),
                                        rotation=rotation, on_account=self.on_account, stop_flag=self.stop_file)
        stopped_by_file = self.stop_file.exists()
        if isinstance(result, dict) and result.get("error"):
            self.save_state("error")
            self.push_live(f"❌ <b>انتهى الفحص بخطأ</b>: {html.escape(str(result.get('error')))}", keyboard={"inline_keyboard": []})
            return EXIT_ERROR
        if self.exit_code == EXIT_BREAKER:
            self.save_state("breaker_stop")
            self.push_live("⛔ <b>إيقاف ذاتي بقاطع الشبكة</b>", keyboard={"inline_keyboard": []})
            return EXIT_BREAKER
        if stopped_by_file and c["checked"] < c["total"]:
            self.save_state("stopped")
            self.push_live("🛑 <b>أُوقف الفحص اللايف يدوياً</b> — يمكنك الاستئناف لاحقاً من نفس النقطة", keyboard={"inline_keyboard": []})
            self.tg.send(f"🛑 <b>توقف الفحص</b> عند {c['checked']} من {c['total']}.\n\n{render_counters(c)}", silent=False)
            return EXIT_STOPPED
        self.save_state("done")
        self.push_live("✅ <b>اكتمل فحص وتنشيط الحسابات لايف</b>", keyboard={"inline_keyboard": []})
        self.tg.send(f"✅ <b>اكتمل الفحص</b>: {c['checked']} من {c['total']}.\n\n{render_counters(c)}", silent=False)
        return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MAINT-9 — مشغّل الفحص والتنشيط اللايف (يُطلقه البوت 31)")
    p.add_argument("--chat-id", type=int, required=True)
    p.add_argument("--message-id", type=int, default=0, help="رسالة اللايف التي أنشأها البوت (0 = إرسال جديدة)")
    p.add_argument("--mode", choices=["fresh", "resume"], default="resume")
    p.add_argument("--delay-min", type=float, default=60.0, help="≥ 60 (Q-GO-2 — الفاصل العشوائي إلزامي)")
    p.add_argument("--delay-max", type=float, default=300.0)
    p.add_argument("--root", type=str, default=None, help="جذر المشروع (الافتراضي: أب هذا الملف)")
    p.add_argument("--token-file", type=str, default=None)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.delay_min < 60.0 or args.delay_max < args.delay_min:
        print("⛔ [MAINT-9/Q-GO-2] --delay-min ≥ 60 و--delay-max ≥ --delay-min إلزاميان", flush=True)
        return EXIT_ERROR
    try:
        checker = LiveChecker(args)
    except Exception as e:
        log(f"❌ تعذر تهيئة المشغّل: {type(e).__name__}: {e}")
        root = pathlib.Path(args.root).resolve() if args.root else ROOT_DIR
        Telegram(load_bot_token(root, args.token_file), args.chat_id).send(
            f"❌ <b>تعذر بدء الفحص اللايف</b>\n{html.escape(type(e).__name__)}: {html.escape(str(e))[:300]}\n"
            f"(هل genspark_master_account_manager و{ENGINE_0502_NAME} موجودان؟)")
        return EXIT_ERROR
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
