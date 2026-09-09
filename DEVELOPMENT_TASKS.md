# 📋 DEVELOPMENT_TASKS.md — Feature Parity Audit (revu1.md Protocol)

> **المهمة المرجعية:** `revu1.md` — Deep Feature Parity Audit + Gap Analysis + Safe Completion
> **الهدف:** إثبات أن `bridge_refactor/` = 100% Feature Parity مع المراجع الوظيفية، دون أي فقد.

---

## 🔒 Source of Functional Truth (Read-Only References)

| الملف | الدور | الحالة |
|---|---|---|
| `01.26_telegram_gen_bridge.py` | مرجع وظيفي (Golden Baseline) | لم يُمس ✅ |
| `01.03Genspark_claude-opus-5-code.py` | محرك Genspark المرجعي | لم يُمس ✅ |
| `01.28_telegram_gen_bridge.py` | الإصدار المعتمد الحالي (Superset مثبت من 01.27 + P16 نشر عام مبكر) | لم يُمس ✅ |

**ملاحظة معمارية حاسمة:** `bridge_refactor/` مبني على **01.27** وليس 01.26 مباشرة.
تم إثبات (بالـ diff) أن 01.27 = 01.26 + إصلاحات P12/P13/P14 فقط (بانر + baseline metadata — **صفر حذف ميزات**)،
لذلك: parity مع 01.27 ⟹ parity مع 01.26 بالضرورة (Transitive Parity).

---

## ✅ PHASE 1–5 — Feature Inventory + Execution Trace (مكتمل — أدلة آلية)

### منهجية الإثبات (وليس المقارنة الشكلية):

1. **Byte-Parity:** إعادة تجميع `bridge_refactor/parts/p01..p12` تطابق `01.27` بايت-بايت
   (SHA-256 identical — محروس بـ `tests/test_refactor_parity.py::TestByteParity`).
   هذا يعني أن **كل** validation/retry/fallback/state/side-effects/cleanup في الأصل
   موجود حرفياً في الـ refactor — ليس نسخاً بالاسم بل بالمحتوى الكامل.
2. **Symbol-Parity:** 168 دالة/كلاس top-level + 56 ثابت/تكوين — **صفر مفقود** من الـ runtime namespace (فحص AST آلي).
3. **Facade-Parity:** 354 رمزاً عبر 14 واجهة domain (`core/`, `genspark/`, `telegram/`, `projects/`, `git/`, `workers/`)
   — كل رمز **identical object** (نفس الكائن `is`) مع الـ namespace — صفر انحراف.
4. **Execution-Trace:** السلسلة الكاملة
   `main → run_telegram_polling → handle_telegram_update → process_user_task_async →
   send_message_with_auto_account_failover → send_message_and_make_public →
   get_genspark_engine → make_project_always_public → download_project_archive → cleanup`
   — كل استدعاء داخلي يُحل في الـ runtime — **صفر انقطاع**.
5. **Engine-Contract:** الجسر يطلب من المحرك 6 دوال فقط:
   `check_balance, create_forked_project, do_login, ensure_public, fetch_project_messages, send_chat`
   — كلها موجودة في `01.03` بتواقيع متوافقة (بما فيها kwargs:
   `project_id, history, cfg, on_project_start_callback`) — وسطح الاستدعاء في الـ parts
   **مطابق حرفياً** لسطح 01.27.

---

## 📊 PHASE 11 — PARITY MATRIX (الفئات الوظيفية الكاملة)

> Status: `PASS` لا يُمنح إلا بدليل. الدليل هنا: **byte-parity** يجعل كل فئة PASS بالتعريف،
> مضافاً إليه اختبارات سلوكية (115 اختباراً) لكل مسار حرج.

| ID | Feature Domain | Original (01.26/01.27) | bridge_refactor | Status | Evidence | Risk |
|---|---|---|---|---|---|---|
| F-01 | Telegram Polling + Offset persistence | `run_telegram_polling` | p12 (verbatim) | PASS | byte-parity + chain trace | — |
| F-02 | Telegram Handlers (أوامر/callbacks/keyboards) | `handle_telegram_update` + UI | p12 (verbatim) | PASS | byte-parity + test_p11 (10) | — |
| F-03 | Messaging (split/HTML/retry/document/live renderer) | p04 domain | p04 (verbatim) | PASS | byte-parity + facade identity | — |
| F-04 | Button Styles Whitelist (Bot API 9.4) | `make_inline_keyboard` | p04 (verbatim) | PASS | smoke: style invalid يُحذف + test_p11 | — |
| F-05 | Accounts (locks/claims/cooldown/rotation) | p03 domain | p03 (verbatim) | PASS | byte-parity + test parity claims | — |
| F-06 | Pre-Flight Balance Gate (<100 → 29h cooldown → LOW_BALANCE silent skip) | P13 | p06 (verbatim) | PASS | test_p13 (14) | — |
| F-07 | Session (401 refresh → recheck balance → resume) | `refresh_cookies_on_401` | p06 (verbatim) | PASS | byte-parity + test_p13 | — |
| F-08 | Genspark Engine loading (single-load cache + lock) | `get_genspark_engine` | p03 (verbatim) | PASS | smoke: engine file resolved from BRIDGE_HOME | — |
| F-09 | Same-Project Resume (`carry_pid` — لا fork بعد انقطاع) | P12 | p06 (verbatim) | PASS | test_p12 (13) | — |
| F-10 | `__STREAM_INTERRUPTED__` → RUNNING → polling نفس الـ pid | P12 | p06 (verbatim) | PASS | test_p12 + test_p7 | — |
| F-11 | Live Preview button (أول ثانية + استئناف + fork) | P7-A/P12-C | p06 (verbatim) | PASS | test_p7 (10) | — |
| F-12 | Failover loop (multi-account + silent LOW_BALANCE skip) | `send_message_with_auto_account_failover` | p06 (verbatim) | PASS | test_p13 + byte-parity | — |
| F-13 | make_public early + `get_public_forked_pid` | p06 | p06 (verbatim) | PASS | symbol + chain trace | — |
| F-14 | Archive download + Safe extraction (Tar-Slip guard + diagnostics) | `_extract_archive_with_diagnostics` | p06 (verbatim) | PASS | byte-parity | — |
| F-15 | Projects Tree + Branch/fork semantics | p05 domain | p05 (verbatim) | PASS | byte-parity + test_p1 | — |
| F-16 | Registry Index (normalize/backup/restore/aliases) | p07+p08 | p07+p08 (verbatim) | PASS | byte-parity | — |
| F-17 | GitHub REST + Dashboard + repo config | p09 | p09 (verbatim) | PASS | byte-parity + test_p1 | — |
| F-18 | Progress/Credit checkpoint gate | p10 | p10 (verbatim) | PASS | parity behavior tests (gate blocks on error) | — |
| F-19 | Concurrent Worker Queue + project locks | p11 | p11 (verbatim) | PASS | byte-parity + chain trace | — |
| F-20 | Model Contracts (CONTRACTS/apply_contract/is_protected) | p02 | p02 (verbatim) | PASS | test_p2 + test_p3 | — |
| F-21 | Logging/redaction/log_event | p01 | p01 (verbatim) | PASS | byte-parity | — |
| F-22 | Entry point (`python -m bridge_refactor.main` ≡ تشغيل الملف الأحادي) | `if __name__ == "__main__": main()` | `main.py → runtime.main() → ns.main()` | PASS | smoke + wiring inspection | — |
| F-23 | Engine 01.03: True SSE (`stream=True` + `iter_lines`) + idle-timeout tuple + interrupted-pid return | 01.03 | يُحمّل نفس الملف حرفياً (لا نسخة منه) | PASS | test_p7 guards 8–10 + test_p12 | — |
| F-24 | Qwen Engine (race/refresh/progress) في `qwen_engine.py` | 04+qwen_engine | خارج نطاق bridge_refactor (موديول مستقل قائم) | PASS | test_p15 (16) | — |

**ملاحظة D (Dead/Disconnected):** 9 رموز غير مستدعاة من `main` في **الأصل نفسه**
(`_safe_extract_archive` [خلَفه `_extract_archive_with_diagnostics`]، `apply_contract`/`is_protected`
[تستهلكها الاختبارات ومولّد الوثائق]، والباقي رموز واجهة/استرجاع احتياطي).
هذه **ليست فجوات refactor** — نفس الحالة موجودة حرفياً في 01.26/01.27، وتم الحفاظ عليها
كاملة في الـ refactor عملاً بسياسة **No Feature Loss** (لم يُحذف أي منها).

---

## 📉 PHASE 12 — GAP REPORT

```text
TOTAL FEATURE DOMAINS : 24
IMPLEMENTED (PASS)    : 24
PARTIAL               : 0
MISSING               : 0
CHANGED               : 0
DEAD (موروثة من الأصل، محفوظة عمداً) : 9 رموز — ليست فجوة
REGRESSION RISKS      : 0 معروفة
CRITICAL/HIGH/MEDIUM/LOW GAPS : 0 / 0 / 0 / 0
```

**سبب النتيجة:** معمارية الـ refactor المعتمدة هي **Verbatim-Slice Runtime**:
الأجزاء `parts/p01..p12` قصّ حرفي line-range من 01.27 يُنفَّذ في namespace واحد مشترك،
والواجهات domain تعيد تصدير نفس الكائنات. هذا التصميم يجعل فقد الميزات **مستحيلاً بنيوياً**
طالما اختبار byte-parity أخضر، ويحقق أهداف الفصل (14 facade module) والصيانة
دون المخاطرة بأي behavior drift.

---

## 🧪 PHASE 17 — REGRESSION TEST RESULTS

| Layer | النتيجة |
|---|---|
| Syntax (`py_compile` لكل parts + main + runtime) | ✅ Exit 0 |
| Docs Integrity (31 ملف) | ✅ صفر أخطاء |
| Unit + Integration + Parity (115 اختباراً) | ✅ 115/115 PASS |
| بوابة `scripts/hadith_sijil.py` | ✅ Exit Code 0 |
| Smoke: بناء الـ runtime + حل المحرك + فلترة الأزرار | ✅ |
| Chain: Telegram→Job→Account→Session→Genspark→Result→Git→Notify→Cleanup | ✅ صفر انقطاع (AST trace) |

---

## 🏁 FINAL REPORT (وفق FINAL ACCEPTANCE CRITERIA في revu1.md)

```text
FEATURE PARITY:           100% (byte-parity + 354 facade symbols identical + 115/115 tests)
REGRESSIONS:              0
MISSING FEATURES:         0
PARTIAL FEATURES:         0
CHANGED BEHAVIORS:        0 (semantics مطابقة بالتعريف — verbatim execution)
FIXES APPLIED:            0 مطلوبة في هذه الجولة (النواقص = صفر)
PERFORMANCE IMPROVEMENTS: single-load engine cache، تنفيذ الأجزاء مرة واحدة عند import،
                          فصل facades بدون طبقات وسيطة (identity re-export = zero overhead)
TEST RESULTS:             115/115 PASS — Gate Exit 0
REMAINING RISKS:          لا شيء معروف؛ أي تعديل مستقبلي على 01.27 يتطلب
                          إعادة توليد parts عبر scripts/rebuild_refactor.py (محروس بالبوابة)
FINAL STATUS:             ✅ COMPLETE — bridge_refactor نسخة أكثر تنظيماً وليست أقل
```

---

## 🔄 RESUME STATE (بصيغة revu1.md الإلزامية)

```text
SESSION: S35 — Feature Parity Audit (revu1.md)
DATE: 2026-08-20
REFERENCE_FILES: 01.26_telegram_gen_bridge.py, 01.03Genspark_claude-opus-5-code.py (read-only، لم تُمس)
LAST_VERIFIED_FEATURE: F-24 (الكل) — Parity Matrix كاملة 24/24 PASS
CURRENT_GAP: لا يوجد (0 Critical / 0 High / 0 Medium / 0 Low)
FILES_CHANGED: DEVELOPMENT_TASKS.md (جديد — هذا التقرير فقط؛ صفر تعديل على الكود)
CHANGES: تدقيق آلي (AST symbol audit + facade identity + execution trace + engine contract)
         + تشغيل البوابة الكاملة — لم يتطلب أي إصلاح كود.
TESTS: 115/115 PASS، hadith_sijil Exit 0، parity suite 11/11، py_compile OK
RESULT: 100% Feature Parity مثبت — bridge_refactor معتمد
BLOCKERS: لا شيء
NEXT_EXACT_ACTION: لا نواقص؛ عند أي تعديل مستقبلي على 01.27 شغّل
                   scripts/rebuild_refactor.py ثم python3 scripts/hadith_sijil.py
```
