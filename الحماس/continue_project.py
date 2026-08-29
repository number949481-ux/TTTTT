#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════
🔗 continue_project.py — تكملة نفس مشروع Genspark من رابط (CLI مستقل)
═══════════════════════════════════════════════════════════════════════
موثّق في: genspark-session-bridge/06_CONTINUE_SAME_PROJECT_API.md
جلسة: SESSION-GSB-001

الفكرة:
    الرابط لوحده مش بيكمّل — الرابط بيديك الـ Project ID (PID)،
    والتكملة الفعلية = send_chat(project_id=PID) من محرك 01.03.

    هذا السكريبت يغلّف السلسلة كاملة في أمر واحد:
      رابط/UUID  ➔  extract_project_id  ➔  is_probable_project_id
                 ➔  اختيار حساب        ➔  send_chat(project_id=PID)
      ولو حساب مختلف (--fork):
                 ➔  ensure_public       ➔  create_forked_project
                 ➔  send_chat(project_id=NEW_PID)

أمثلة استخدام:
    # 1) فحص الرابط فقط بدون أي اتصال شبكة (آمن تماماً)
    python3 continue_project.py --dry-run \
        "https://www.genspark.ai/autopilotagent_viewer?id=<UUID>" "كمّل"

    # 2) تكملة مباشرة بنفس الحساب (Fork=False) — تلقائي باختيار أفضل حساب
    python3 continue_project.py \
        "https://www.genspark.ai/agents?id=<UUID>" "كمّل من حيث توقفت"

    # 3) تكملة بحساب محدد بالاسم
    python3 continue_project.py --email me@example.com "<UUID>" "كمّل"

    # 4) تكملة من حساب مختلف عبر فورك سيرفري كامل (Fork=True)
    python3 continue_project.py --fork --owner-email owner@x.com \
        "https://www.genspark.ai/autopilotagent_viewer?id=<UUID>" "كمّل"

ملاحظات أمان:
    - لا يطبع كوكيز ولا أسرار أبداً (الإيميلات تُقنّع جزئياً).
    - --dry-run لا يفتح أي اتصال شبكة إطلاقاً.
    - يعتمد على ملف الحسابات من Config في المحرك (accounts_genspark.json).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import re
import sys
import time

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
# 🔎 اكتشاف ديناميكي: أي محرك بنمط *Genspark_claude-opus-5-code.py جنب السكريبت
#    (عشان النسخ اللي جنب 01.04 في الحماس/ و 02.07 في جديد/ تشتغل برضو)
ENGINE_GLOB = "*Genspark_claude-opus-5-code.py"
CANONICAL_ENGINE = "01.03Genspark_claude-opus-5-code.py"


def discover_engine_names(directory=None) -> list:
    """أسماء المحركات المرشحة في مجلد السكريبت — الأساسي 01.03 أولاً لو موجود."""
    d = pathlib.Path(directory) if directory else SCRIPT_DIR
    try:
        names = sorted((p.name for p in d.glob(ENGINE_GLOB)), reverse=True)
    except OSError:
        return []
    if CANONICAL_ENGINE in names:
        names.remove(CANONICAL_ENGINE)
        names.insert(0, CANONICAL_ENGINE)
    return names

# ══════════════════════════════════════════════════════════════
# 🎨 طباعة بسيطة (بدون اعتماديات خارجية إلزامية)
# ══════════════════════════════════════════════════════════════
_C = {
    "r": "\033[0m", "b": "\033[1m", "red": "\033[31m", "grn": "\033[32m",
    "yel": "\033[33m", "cyn": "\033[36m", "gry": "\033[90m",
}
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(color: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"{_C.get(color, '')}{text}{_C['r']}"


def say(icon: str, msg: str, color: str = "cyn") -> None:
    print(c(color, f"{icon} {msg}"), flush=True)


_LAST_ERROR = {"msg": ""}  # آخر رسالة خطأ — تقرأها continue_from_link بعد SystemExit


def die(msg: str, code: int = 2):
    _LAST_ERROR["msg"] = msg
    say("❌", msg, "red")
    sys.exit(code)


def mask_email(email: str) -> str:
    """تقنيع الإيميل في اللوج — user@dom ➔ us***@dom"""
    e = str(email or "")
    if "@" not in e:
        return e[:3] + "***" if e else "unknown"
    user, _, dom = e.partition("@")
    return f"{user[:2]}***@{dom}"


# ══════════════════════════════════════════════════════════════
# 🧭 SSOT لتحليل الرابط — منسوخ حرفياً بالسلوك من 01.33_telegram_gen_bridge
#    (extract_project_id سطر ~2025 + is_probable_project_id سطر ~4307)
#    نُسخ محلياً بدل استيراد الوحدة الضخمة (لا يستدعي تلغرام ولا يفتح شبكة).
# ══════════════════════════════════════════════════════════════
_UUID_RE = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"


def extract_project_id(url_or_id: str) -> str:
    if not url_or_id:
        return ""
    url_str = str(url_or_id).strip()
    match = re.search(r"id=([a-f0-9\-]{36})", url_str, re.IGNORECASE)
    if match:
        return match.group(1)
    uuid_match = re.search(f"({_UUID_RE})", url_str, re.IGNORECASE)
    if uuid_match:
        return uuid_match.group(1)
    return url_str


def is_probable_project_id(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text or text == "غير معروف" or "__INVALID_PROJECT__" in text:
        return False
    if "login" in text.lower() or "/" in text or " " in text:
        return False
    return bool(re.fullmatch(_UUID_RE, text, re.IGNORECASE))


def parse_project_locator(text) -> dict:
    """التصنيف المركزي: kind = pid | malformed | none"""
    raw = str(text or "").strip()
    result = {"kind": "none", "pid": "", "raw": raw}
    if not raw:
        return result
    has_domain = "genspark.ai" in raw.lower()
    has_uuid = bool(re.search(_UUID_RE, raw, re.IGNORECASE))
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


# ══════════════════════════════════════════════════════════════
# 🔌 تحميل محرك 01.03 (نفس نمط _ENGINE_CACHE في 01.33 سطر ~512)
# ══════════════════════════════════════════════════════════════
_ENGINE = {"mod": None, "path": ""}


def load_engine():
    if _ENGINE["mod"] is not None:
        return _ENGINE["mod"]

    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))

    candidates = discover_engine_names()
    if not candidates:
        die(f"لا يوجد أي محرك بنمط {ENGINE_GLOB} جنب السكريبت ({SCRIPT_DIR}).\n"
            "   حط السكريبت في نفس مجلد محرك Genspark (مثل 01.03/01.04/02.07).", 3)

    errors = []
    for name in candidates:
        path = SCRIPT_DIR / name
        if not path.exists():
            errors.append(f"{name}: غير موجود")
            continue
        try:
            spec = importlib.util.spec_from_file_location("genspark_engine", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not hasattr(mod, "send_chat"):
                errors.append(f"{name}: لا يحتوي send_chat")
                continue
            _ENGINE["mod"] = mod
            _ENGINE["path"] = str(path)
            say("🔌", f"المحرك محمّل: {name}", "grn")
            return mod
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {type(e).__name__}: {e}")

    die("فشل تحميل محرك Genspark:\n   - " + "\n   - ".join(errors), 3)


def fork_supported(mod) -> bool:
    """هل المحرك المحمّل يدعم الفورك؟ (01.04/02.07 مثلاً ناقصهم create_forked_project)"""
    return hasattr(mod, "create_forked_project") and hasattr(mod, "ensure_public")


def _release_quietly(mod, email: str, cfg) -> bool:
    """فك حجز الحساب فوراً بدل انتظار TTL الـ60 ثانية — بدون ما يرمي أبداً.

    send_chat في المحرك لا تفك الحجز بنفسها (الفك في cli_mode/main هناك)،
    فلازم السكريبت يفك بنفسه وإلا الحساب يفضل محجوز عن أي عملية موازية.
    """
    if not email or not hasattr(mod, "release_account"):
        return False
    try:
        mod.release_account(email, cfg)
        return True
    except Exception:  # noqa: BLE001
        return False


# ══════════════════════════════════════════════════════════════
# 👤 اختيار الحساب
# ══════════════════════════════════════════════════════════════
def find_account_by_email(mod, cfg, email: str):
    """يرجع (acc, cookies) لإيميل محدد — أو None"""
    target = str(email or "").strip().lower()
    for acc in mod.load_accounts(cfg):
        if str(acc.get("email", "")).strip().lower() == target:
            cookies = acc.get("cookies") or {}
            if not cookies.get("session_id"):
                die(f"الحساب {mask_email(email)} موجود بس بدون session_id صالح.", 4)
            return acc, cookies
    return None


def resolve_account(mod, cfg, email: str | None, role: str = "المُرسِل"):
    """اختيار حساب. يرجع (acc, cookies, reserved) —
    reserved=True فقط لو الحجز الذري (lock_pick_and_reserve) هو اللي نجح،
    وساعتها السكريبت مسؤول عن فك الحجز في النهاية."""
    if email:
        found = find_account_by_email(mod, cfg, email)
        if not found:
            die(f"لم أجد الحساب {mask_email(email)} في {cfg.accounts_file}", 4)
        acc, cookies = found
        say("👤", f"{role}: {mask_email(acc.get('email'))} (محدد يدوياً)")
        return acc, cookies, False

    reserved = False
    picked = None
    if hasattr(mod, "lock_pick_and_reserve"):
        try:
            picked = mod.lock_pick_and_reserve(cfg)
            reserved = bool(picked)
        except Exception as e:  # noqa: BLE001
            say("⚠️", f"lock_pick_and_reserve فشل ({e}) — بجرب pick_account", "yel")
    if not picked and hasattr(mod, "pick_account"):
        picked = mod.pick_account(mod.load_accounts(cfg), cfg)
    if not picked:
        die("لا يوجد حساب صالح متاح (رصيد/كوكيز/cooldown). راجع ملف الحسابات.", 5)

    acc, cookies = picked
    say("👤", f"{role}: {mask_email(acc.get('email'))} | 💰 {acc.get('balance')}")
    return acc, cookies, reserved


# ══════════════════════════════════════════════════════════════
# 🚀 المنطق الرئيسي
# ══════════════════════════════════════════════════════════════
def build_cfg(mod, args):
    cfg = mod.Config()
    # تكملة نفس المشروع = نعتمد على السيرفر في التاريخ (توفير رصيد) — إلا لو المالك غيّر
    if args.history is not None:
        cfg.cli_history_max = args.history
    if args.model:
        cfg.model = args.model
    if args.timeout:
        cfg.timeout = args.timeout
    if args.accounts:
        cfg.accounts_file = args.accounts
    cfg.show_debug = bool(args.debug)
    cfg.persistent = False  # لا نلمس ملف المحادثات — الرابط هو مرجعنا
    return cfg


def run(args, result: dict | None = None) -> int:
    t0 = time.time()
    res = result if result is not None else {}

    # ── 1) تحليل الرابط (SSOT) ──
    locator = parse_project_locator(args.link)
    print()
    say("🧭", "تحليل المُحدِّد (Project Locator):", "b")
    print(c("gry", f"     المدخل : {locator['raw'][:100]}"))
    print(c("gry", f"     التصنيف: {locator['kind']}"))

    if locator["kind"] == "malformed":
        die("الرابط يشبه رابط مشروع Genspark لكن بدون UUID صالح (صيغة 8-4-4-4-12).\n"
            "   الصيغ المقبولة:\n"
            "     https://www.genspark.ai/agents?id=<UUID>\n"
            "     https://www.genspark.ai/autopilotagent_viewer?id=<UUID>\n"
            "     <UUID> خام", 6)
    if locator["kind"] != "pid":
        die("لم أستطع استخراج Project ID من المدخل. مرّر رابط مشروع أو UUID كامل.", 6)

    pid = locator["pid"]
    res["source_pid"] = pid
    res["forked"] = bool(args.fork)
    print(c("grn", f"     ✅ PID   : {pid}"))
    print(c("gry", f"     رابط    : https://www.genspark.ai/agents?id={pid}"))
    print()

    mode = "Fork=True (حساب مختلف — فورك سيرفري)" if args.fork else "Fork=False (نفس الحساب — تكملة مباشرة)"
    say("🎯", f"الوضع: {mode}", "b")
    say("💬", f"البرومبت: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print()

    # ── 2) Dry-run: نتوقف هنا بدون أي شبكة ──
    if args.dry_run:
        say("🧪", "DRY-RUN — لم يُفتح أي اتصال شبكة. الخطة اللي كانت هتنفّذ:", "yel")
        plan = ([f"ensure_public({pid[:8]}…, owner_cookies)",
                 f"create_forked_project({pid[:8]}…, actor_cookies) ➔ NEW_PID",
                 "send_chat(actor_cookies, prompt, project_id=NEW_PID)"]
                if args.fork else
                [f"send_chat(actor_cookies, prompt, project_id={pid[:8]}…)"])
        for i, step in enumerate(plan, 1):
            print(c("gry", f"     {i}. {step}"))
        print()
        say("✅", "الرابط صالح والخطة جاهزة. شيل --dry-run للتنفيذ الفعلي.", "grn")
        return 0

    # ── 3) تحميل المحرك + التهيئة ──
    mod = load_engine()
    cfg = build_cfg(mod, args)
    say("⚙️", f"موديل: {cfg.model} | history: {cfg.cli_history_max} | حسابات: {cfg.accounts_file}", "gry")

    # فحص مبكر: --fork مع محرك لا يدعم الفورك = خطأ واضح بدل AttributeError غامض
    if args.fork and not fork_supported(mod):
        die(f"المحرك المحمّل ({pathlib.Path(_ENGINE['path']).name}) لا يدعم الفورك —\n"
            "   create_forked_project/ensure_public غير موجودة فيه.\n"
            "   استخدم نسخة السكريبت اللي جنب محرك 01.03، أو شيل --fork.", 7)

    # ── 4) الحساب المُرسِل ──
    actor_acc, actor_cookies, reserved = resolve_account(mod, cfg, args.email, "المُرسِل")
    reserved_email = actor_acc.get("email", "") if reserved else ""

    target_pid = pid
    try:
        return _run_send_phase(args, mod, cfg, pid, target_pid,
                               actor_acc, actor_cookies, t0, res)
    finally:
        # 🔓 فك الحجز فوراً (send_chat لا تفكه بنفسها) — بدل انتظار TTL الـ60 ثانية.
        #    يعمل حتى مع die()/Ctrl+C بفضل finally.
        if reserved_email and _release_quietly(mod, reserved_email, cfg):
            say("🔓", f"فُكّ حجز {mask_email(reserved_email)} فوراً (بدل انتظار TTL)", "gry")


def _run_send_phase(args, mod, cfg, pid, target_pid,
                    actor_acc, actor_cookies, t0, res) -> int:
    # ── 5) مسار الفورك (حساب مختلف) ──
    if args.fork:
        owner_cookies = actor_cookies
        if args.owner_email:
            owner_found = find_account_by_email(mod, cfg, args.owner_email)
            if not owner_found:
                die(f"لم أجد حساب المالك {mask_email(args.owner_email)} في ملف الحسابات.", 4)
            owner_cookies = owner_found[1]
            say("🔑", f"مالك المشروع: {mask_email(args.owner_email)} (للمشاركة العامة)")
        else:
            say("⚠️", "لم تحدد --owner-email — بحاول المشاركة بكوكيز المُرسِل "
                      "(هينجح فقط لو المشروع عام أصلاً).", "yel")

        say("🌐", "خطوة 1/2: ضمان أن المشروع عام (ensure_public)…")
        try:
            public_url = mod.ensure_public(pid, owner_cookies, cfg, label="FORK")
            print(c("gry", f"     ➔ {public_url or '(بدون رابط عام)'}"))
        except Exception as e:  # noqa: BLE001
            say("⚠️", f"ensure_public فشل: {e} — بكمل على أمل إن المشروع عام بالفعل.", "yel")

        say("🔀", "خطوة 2/2: إنشاء فورع سيرفري كامل (create_forked_project)…")
        new_pid = None
        try:
            new_pid = mod.create_forked_project(pid, actor_cookies, cfg)
        except Exception as e:  # noqa: BLE001
            die(f"create_forked_project رمى استثناء: {e}", 7)

        if not new_pid or not is_probable_project_id(new_pid):
            die("الفورك فشل — السيرفر لم يرجّع PID جديد صالح.\n"
                "   الأسباب الشائعة: المشروع ليس عاماً، أو كوكيز المُرسِل منتهية.", 7)

        target_pid = new_pid
        res["forked_pid"] = new_pid
        say("✅", f"الفورك نجح ➔ PID جديد: {new_pid}", "grn")
        print(c("gry", f"     (Root Project ID = {pid})"))
        print()

    # ── 6) الإرسال الفعلي — قلب التكملة ──
    say("🚀", f"إرسال على المشروع {target_pid[:16]}… (send_chat(project_id=…))", "b")
    print(c("gry", "─" * 60))
    try:
        answer, live_pid, msg_id = mod.send_chat(
            cookies=actor_cookies,
            question=args.prompt,
            email=actor_acc.get("email", ""),
            project_id=target_pid,
            cfg=cfg,
        )
    except Exception as e:  # noqa: BLE001
        die(f"send_chat رمى استثناء: {type(e).__name__}: {e}", 8)

    print(c("gry", "─" * 60))
    print()

    final_pid = live_pid if is_probable_project_id(live_pid or "") else target_pid
    elapsed = time.time() - t0
    res.update({"final_pid": final_pid, "answer": answer, "message_id": msg_id,
                "elapsed_sec": round(elapsed, 2),
                "resume_url": f"https://www.genspark.ai/agents?id={final_pid}"})

    if not answer:
        say("❌", f"لم يرجع رد. (PID: {final_pid[:16]}…، {elapsed:.1f}s)", "red")
        say("🔗", f"https://www.genspark.ai/agents?id={final_pid}", "yel")
        return 9

    say("✅", f"تم — {len(answer)} حرف في {elapsed:.1f}s", "grn")
    say("🔗", f"رابط الاستئناف: https://www.genspark.ai/agents?id={final_pid}", "cyn")
    if msg_id:
        print(c("gry", f"     message_id: {msg_id}"))
    print()

    # ── 7) حفظ الرد لو المالك طلب ──
    if args.out:
        out_path = pathlib.Path(args.out)
        if not out_path.is_absolute():
            out_path = SCRIPT_DIR / out_path
        try:
            if out_path.suffix.lower() == ".json":
                out_path.write_text(json.dumps({
                    "input": args.link, "source_pid": pid, "final_pid": final_pid,
                    "forked": bool(args.fork), "prompt": args.prompt,
                    "answer": answer, "message_id": msg_id,
                    "elapsed_sec": round(elapsed, 2),
                    "resume_url": f"https://www.genspark.ai/agents?id={final_pid}",
                }, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                out_path.write_text(answer, encoding="utf-8")
            say("💾", f"الرد محفوظ: {out_path}", "grn")
        except Exception as e:  # noqa: BLE001
            say("⚠️", f"تعذر حفظ الملف: {e}", "yel")

    if not args.quiet:
        print(c("b", "══════════════════ الرد ══════════════════"))
        print(answer)
        print(c("b", "═════════════════════════════════════════"))

    return 0


# ══════════════════════════════════════════════════════════════
# 🔌 واجهة الاستدعاء الخارجي (Embeddable API)
#    للاستخدام من أي سكريبت بايثون تاني بدون subprocess:
#        from continue_project import continue_from_link   # (بعد ضبط sys.path)
#        r = continue_from_link("<رابط أو UUID>", "كمّل")
#        if r["ok"]: print(r["answer"])
#    ⚠️ عكس run(): لا ترمي SystemExit أبداً — بترجع dict دايماً.
# ══════════════════════════════════════════════════════════════
def continue_from_link(link: str, prompt: str, *, fork: bool = False,
                       email: str = "", owner_email: str = "", model: str = "",
                       history: int | None = None, timeout: int = 0,
                       accounts: str = "", out: str = "", dry_run: bool = False,
                       debug: bool = False, quiet: bool = True) -> dict:
    res = {"ok": False, "exit_code": None, "source_pid": "", "final_pid": "",
           "forked": bool(fork), "answer": None, "message_id": None,
           "resume_url": "", "error": ""}
    if not str(prompt or "").strip():
        res.update(exit_code=2, error="البرومبت فاضي — مرّر نص فعلي للإرسال.")
        return res

    _LAST_ERROR["msg"] = ""
    args = argparse.Namespace(
        link=link, prompt=prompt, fork=fork, email=email, owner_email=owner_email,
        model=model, history=history, timeout=timeout, accounts=accounts,
        out=out, dry_run=dry_run, debug=debug, quiet=quiet)
    try:
        code = run(args, res)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        code = 130
    except Exception as e:  # noqa: BLE001 — عزل كامل: الخطأ يرجع في dict مش استثناء
        code = 8
        res["error"] = f"{type(e).__name__}: {e}"
    res["exit_code"] = code
    res["ok"] = (code == 0)
    if code != 0 and not res["error"]:
        res["error"] = _LAST_ERROR["msg"]
    if res["source_pid"] and not res["resume_url"]:
        res["resume_url"] = f"https://www.genspark.ai/agents?id={res['final_pid'] or res['source_pid']}"
    return res


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="continue_project.py",
        description="تكملة نفس مشروع Genspark من رابط (agents?id= أو autopilotagent_viewer?id= أو UUID خام)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "أمثلة:\n"
            "  %(prog)s --dry-run 'https://www.genspark.ai/autopilotagent_viewer?id=<UUID>' 'كمّل'\n"
            "  %(prog)s 'https://www.genspark.ai/agents?id=<UUID>' 'كمّل من حيث توقفت'\n"
            "  %(prog)s --email me@x.com '<UUID>' 'كمّل'\n"
            "  %(prog)s --fork --owner-email owner@x.com '<رابط>' 'كمّل'\n"
        ),
    )
    ap.add_argument("link", help="رابط المشروع أو UUID خام")
    ap.add_argument("prompt", help="البرومبت المطلوب إرساله على نفس المشروع")
    ap.add_argument("--fork", action="store_true",
                    help="Fork=True — للتكملة من حساب مختلف (ensure_public + create_forked_project)")
    ap.add_argument("--email", default="", help="إيميل الحساب المُرسِل (افتراضي: Smart Picker)")
    ap.add_argument("--owner-email", default="",
                    help="إيميل مالك المشروع الأصلي — يُستخدم مع --fork لجعله عاماً")
    ap.add_argument("--model", default="", help="تجاوز الموديل (افتراضي من Config)")
    ap.add_argument("--history", type=int, default=None,
                    help="cli_history_max: -1 اعتماد كامل على السيرفر (افتراضي) | 0 كل الرسائل | N آخر N")
    ap.add_argument("--timeout", type=int, default=0, help="تجاوز مهلة الطلب بالثواني")
    ap.add_argument("--accounts", default="", help="مسار/اسم ملف حسابات بديل")
    ap.add_argument("--out", default="", help="حفظ الرد في ملف (.json = تقرير كامل، غير كده = نص خام)")
    ap.add_argument("--dry-run", action="store_true",
                    help="فحص الرابط وطبع الخطة فقط — بدون أي اتصال شبكة")
    ap.add_argument("--debug", action="store_true", help="تفعيل show_debug في المحرك")
    ap.add_argument("--quiet", action="store_true", help="عدم طبع نص الرد في النهاية")

    args = ap.parse_args()

    if not str(args.prompt or "").strip():
        die("البرومبت فاضي — مرّر نص فعلي للإرسال.", 2)
    if args.owner_email and not args.fork:
        say("⚠️", "--owner-email بلا معنى بدون --fork — سيُتجاهل.", "yel")

    try:
        return run(args)
    except KeyboardInterrupt:
        print()
        say("🛑", "أُلغي بواسطة المستخدم.", "yel")
        return 130


if __name__ == "__main__":
    sys.exit(main())
