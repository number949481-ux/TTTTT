# MAINT-11_403_PRIVATE_PROJECT_GATE_PLAN.md — خطة 360° لإغلاق ثغرة «المشروع الخاص / 403» (PLAN_ONLY — بانتظار GO)

> **STATUS (2026-11-05):** 📋 **PLAN_AND_AUDIT_ONLY — صفر كود مُعدَّل، صفر اختبار مُضاف.** الثغرة **مؤكَّدة بإثبات تشغيلي** (PROOF-A/B/C أدناه). كل بند تنفيذي أدناه يحتاج **GO صريح** من المالك، وكل سؤال في §7 يحتاج **دليلاً مكتوباً** قبل التنفيذ (لا تخمين — 7.28e/7.28f).
>
> **MODE:** `ALIGNMENT_ONLY` (كارت RESUME + تعليمة المالك: «مراجعه فقط بدون عمياني و لا تخمين … بدون تنفيد عمياني نهائي»).
> **BASE المحلي:** `genspark_ai_developer @ 4e22e23` (dirty 0) — 01.33 = **10440 CRLF، sha `aa17a8a980fd2a20`**؛ 01.03 = 4176 sha `279632a89e68c853` (محمي)؛ 05.02 = 1054 sha `e1216b5186d99420` (خارج النطاق).
> **المصادر (أُعيد جلبها هذه الجلسة — 7.28a):** Gist `db5d6f65…` **1695** سطر sha `73bd4b5dcd5710ff` (كان 1348/`00c809ec…`؛ الجديد L1340–1695: فويس 204 + كارت R11 L1437–1464 + كارت P48_PRIVATE_PROJECT_403_GATE_360 L1484–1520 + كارت GO_SURGICAL_FIX_403 L1538–1683)؛ Gist `093e9661…` **7734** سطر sha `0b45ba672894c4f7` (كان 5393/`f1895f25…`؛ الجديد L5393–7734: فويسات 205–212، خريطة الـ API الخمسة L6622–6760، MASTER-360-PLAN L7288–7414، كارت MANDATE L7625+).
> **ملف HAR `download11.har` واللوج الميداني:** غير موجودين في المستودع (`ls *.har` فارغ؛ `grep -rl download11.har` = ملف توثيق قديم فقط) ⇒ كل ما يُنسب إليهما أدناه **مُبلَّغ/غير مُتحقَّق منه** (7.28f) إلى أن يُرفق.

---

## 0) الخلاصة التنفيذية (ما ثبت وما لم يثبت)

| # | البند | الحالة | الدليل |
|---|---|---|---|
| F-1 | **403 من `ask_proxy` لا يصل أبداً إلى حارس A-1 (L3989) بل يتحول إلى `"FAILED"` ويدير الحسابات حتى `MAX_ATTEMPTS_EXHAUSTED`** | 🔴 **FAIL مؤكَّد** | 01.03 L2265–2282: أي كود غير 401/404/410/500 ⇒ `return None, None, None`؛ 01.33 L3713–3716: `not pid` ⇒ `continue` ثم `"FAILED"`؛ الفيل أوفر (L3783–4341) **لا يملك فرع `FAILED`** ⇒ يسقط إلى L4326–4336 (`attempt-failed-continue` + تبريد 300 ث + `continue`). **PROOF-A:** `(None,"FAILED",…)` ⇒ sends=2/2 ⇒ `MAX_ATTEMPTS_EXHAUSTED`. **PROOF-C** (محرك وهمي يرجع `(None,None,None)` كما في L2282): `send_chat` نُودي **مرتين** للحساب الواحد (`max_timeout_retries=2` L990) والحالة الراجعة `'FAILED'`. |
| F-2 | الحارس A-1 نفسه سليم **عند الوصول إليه** | 🟢 PASS | **PROOF-B:** `(None,"FORBIDDEN",…)` ⇒ sends=1، النتيجة `FORBIDDEN`، لا معزل (p51 t11–t14). منتِجا `FORBIDDEN` الوحيدان: L2295 (dict بكود 403 — لا يصدر من `send_chat`) وL3214 (`monitor_chat_completion` — يحتاج pid موجوداً). ⇒ مسار 403-قبل-pid **بلا منتِج**. |
| F-3 | كود السيرفر الداخلي `status:-13` **لا يُلتقط** في الكود الحالي | 🟠 فجوة إثبات | 01.03 L1731–1737 يقرأ `res_json["data"]["status"]` فقط (قيمة مثل `"FINISHED"` — انظر 01.33 L3261) ولا يقرأ `res_json["status"]` العلوي. في مشروع خاص `data={}` ⇒ `_last_project_status=None`، `_last_fetch_status=200`. **⇒ كل اقتراح في الكروت يفحص `cfg._last_project_status == -13` لن يعمل أبداً** (الكارت db5d L1622–1624 / 093e L6221–6225). |
| F-4 | «شبكة أمان الشات» المقترحة لن تلتقط الحادثة | 🟠 خلل في الاقتراح | الكارت (db5d L1657–1663) يفحص `_last_fetch_status==403` أو نص `answer`؛ في الحادثة الفعلية: `answer=None` و`_last_fetch_status=200` (جلب /api/project نجح شبكياً) ⇒ **الشرط كاذب** ⇒ يسقط إلى `"FAILED"` كما اليوم. السبب الجذري: 01.03 **يبتلع كود HTTP** قبل أن يعود للجسر. |
| F-5 | تعارض قرار: الكارت الجديد D-403-04 (تبريد 0) ⟂ A-1 المنفَّذ (تبريد 300 ث — فويس 193، GO db5d L384–402) | 🟡 مرشَّح (7.28e) | L3996 + p51 t11 `assertAlmostEqual(cooldown_until, now+300)` + رسالة L8131. لا يُنفَّذ إلا بإلغاء مكتوب من المالك لـ A-1. |
| F-6 | تعارض تسمية: `P48` مستخدمة فعلاً (Pre-Flight Gift Freshness — 01.33 L1177/L1282، `tests/test_p48_gift_preflight.py`) | 🟡 يحتاج قرار | اقتراح: وسم `[MAINT-11/403-…]` والاختبارات في `tests/test_p60_403_private_gate.py`. |
| F-7 | أرقام الأسطر في الكروت | 🟢 مطابقة للأم / 🟠 غير مطابقة لـ p06 | 01.33: L3590 ✓ (3588–3598)، L3713 ✓، L3996 ✓، L8127 ≈ L8129 ✓. p06: الكارت يقول 995/1615/868–885 والواقع **992/1268/868** (`grep -n`). |
| W-1 | **تسريب بريد خام في نص اللوج** (خارج نطاق 403 لكنه ضمن محور V7) | 🟠 WARNING | `log_event` يُخفي البريد في البادئة فقط (L102–104)، بينما 5 رسائل تُضمِّن `{curr_email}`/`{email}` خاماً في المتن: **L1103، L1564، L3562، L4152، L4175** ⇒ يصل إلى `bridge_bot.log` والترمنال (ليس تليجرام). |

**الحكم:** الثغرة حقيقية ومُثبَتة تشغيلياً، **لكن الكود المقترح في الكروت الثلاثة لا يغلقها** (F-3/F-4) لأن الإشارة الوحيدة الموثوقة (كود HTTP 403 من `ask_proxy`) تموت داخل الملف المحمي 01.03. الحل الممكن بلا لمس 01.03 هو **بوابة استباقية من الجسر نفسه** (§4 T1) + **تضييق التفسير الافتراضي** لحالة `pid is None` (§4 T2) — مع أسئلة §7 المفتوحة.

---

## 1) إعادة بناء الحادثة بالسطور (Ground Truth — من الكود في شجرتي)

```
Telegram /continue <url>  ──▶ send_message_with_auto_account_failover (L3783)
   while attempt < max_attempts(50) (L3827):
     claim account ──▶ send_message_and_make_public (L3381)
        L3588–3598: orig_pid ← url؛ history ← mod.fetch_project_messages
                    (01.03 L1726: GET /api/project → HTTP 200, data={} ⇒ history=[]،
                     _last_fetch_status=200، _last_project_status=None)
        L3597: get_public_forked_pid → create_forked_project (01.03 L1816: continue_conversation
                    بلا redirect صالح ⇒ None) → محاولتا curl مباشرتان (L3076/L3096) ⇒ None
        L3598: project_id = orig_pid  (المشروع الخاص نفسه!)
        L3652 for chat_attempt in range(2):
            L3666: mod.send_chat(… project_id=orig_pid …)
                   01.03 L2252 POST ask_proxy → 403 → L2281 طباعة «❌ Error 403» → L2282 return (None,None,None)
            (لا استثناء ⇒ break L3670)
        L3713: not pid ⇒ attempt<max_retries(2) ⇒ continue  ⇒ تكرار كل ما سبق مرة ثانية
        L3716: return None, "FAILED", None, None, ""
     الفيل أوفر: لا فرع لـ "FAILED" ⇒ L4326 notify("attempt-failed-continue") ⇒ L4335 تبريد 300ث ⇒ continue
   … حتى 50 حساباً ⇒ L4341 "MAX_ATTEMPTS_EXHAUSTED"
```
- الحساب: `status=active`، `active=True`، الرصيد محفوظ (PROOF-A: balance بلا تغيير؛ cooldown_in≈299s) ⇒ **الحساب لم يُعاقَب بشدة** — الضرر هو **الدوران + صمت تليجرام + حرق طلبات 403** (2 POST + 1 GET + ≤3 محاولات fork لكل حساب).
- تليجرام: حدث `attempt-failed-continue` له عنوان L1866 («المحاولة فشلت وسيستمر البحث») يُنشر عبر `transport.publish` (L2034) **إن كان الـ observer موصولاً** (L2072). المالك أبلغ أنه لم يرَ شيئاً ⇒ **سؤال Q-5** (قد يكون الـ observer غير موصول في مسار الاستئناف، أو الرسالة وصلت كتعديل صامت). لا أحكم بلا لوج.

---

## 2) نتائج التفتيش R11 — المحاور السبعة (كارت db5d L1437–1464) — كلها نُفِّذت فعلياً

| V | المحور | النتيجة | الدليل (grep/runtime) |
|---|---|---|---|
| V1 | تزامن الـ claim/الإنعاش | 🟢 PASS مع ملاحظة | `get_account_lock` (L572) يُستخدم في `refresh_cookies_on_401` فقط (L1516). `update_account_data` (L1071) يكتب ذرّياً `tmp.replace()` (L1097–1100) **بلا قفل** — آخر كاتب يفوز لكن لا ملف ممزَّق. اختيار الحساب مُسلسَل بـ owner token (`claim_eligible_account_for_owner` L625) ⇒ لا يُنعَش نفس الحساب من مهمتين. **ملاحظة معمارية قديمة، ليست من نطاق 403.** |
| V2 | راية `generation_started` | 🟢 PASS | تُصفَّر L3892 مع كل محاولة؛ تُرفع فقط L3441 (حارس Q2) وL3576 (استئناف). |
| V3 | Fail-Open للرصيد | 🟢 PASS (runtime) | `get_eligible_accounts(accs, set())`: `None/""/"0"/False/True/"abc"` ⇒ مؤهَّل (1)؛ `0/0.0/99` ⇒ مُستبعَد (0). صفر استثناءات. |
| V4 | 403 تحت مشاريع متعددة | 🔴 **FAIL** | = F-1. الحارس لا يُستدعى لأن الحالة لا تُنتَج. |
| V5 | التناغم مع 05.02 | 🟢 PASS مع ملاحظة | `read_accounts_safe` تُقرأ من القرص في بداية كل مهمة (L3808) وقبل كل تبريد ختامي (L4332)؛ `reactivate_account_if_due` (L1152) يقرأ/يكتب القرص ⇒ كتابة 05.02 تُرى في **المهمة التالية** بلا إعادة تشغيل (لا في منتصف حلقة مهمة جارية). |
| V6 | المقابض المفتوحة | 🟢 PASS | `open(` بلا `with` مرة واحدة فقط L8927 (`log_fh`) ويُغلق L8931 بعد تسليم المقبض للابن؛ الباقي `with`. |
| V7 | عقد صفر إيميلات | 🟠 WARNING | = W-1 (5 مواضع في متن اللوج). تليجرام: لا بريد خام في عناوين الـ observer (L1850–1945) ولا في `describe_terminal_outcome`. |

**الحزمة:** `pytest -q -p no:cacheprovider tests/ -rf` ⇒ **19 failed / 1430 passed / 1 skipped**؛ مقارنة بالأسماء مع worktree `a8d79bc` ⇒ **NEW ∅ / FIXED ∅**. parity 16/16 ضمن الحزمة. **خضرة الحزمة ≠ أمان (7.31ب): الحزمة خضراء والثغرة F-1 موجودة — لأن p51 يحقن `"FORBIDDEN"` مباشرة ولا يختبر التحويل من `(None,None,None)`.**

---

## 3) القرارات المطلوب تصديقها (D-403-01…07 من MASTER-360-PLAN 093e L7328–7350 — مُراجَعة لا مُسلَّمة)

| القرار | نص الكارت | تقييمي بالدليل | الحالة |
|---|---|---|---|
| D-403-01 | بوابة API استباقية `GET /api/project?id=` (5–6 ث، Fail-Open) قبل الشات؛ `status:-13` أو HTTP 403 ⇒ FORBIDDEN | **صحيح معمارياً وهو الحل الوحيد الممكن بلا لمس 01.03** (F-3/F-4). يجب أن تكون **من الجسر** (طلب مستقل بـ `curl_cffi` + بصمة `get_account_fingerprint` كما في L3063–3075) لا عبر `cfg._last_project_status`. شرط الإطلاق: `is_private_by_api and not forked_pid` (التفريع الناجح يحل المشكلة). | ✅ مُوصى به — يحتاج GO + Q-1 (إثبات شكل الـ payload) |
| D-403-02 | شبكة أمان `ask_proxy` 403 ⇒ FORBIDDEN بدل FAILED (L3713) | **غير قابل للتنفيذ كما كُتب** (F-4): لا توجد إشارة 403 تصل للجسر. البدائل: (أ) استنتاج ضيّق «استئناف على `orig_pid` + فشل fork + `answer is None and pid is None` في المحاولتين + البوابة الاستباقية قالت private» ⇒ FORBIDDEN؛ (ب) السماح بتعديل سطر واحد في 01.03 (L2282 يعيد `"__FORBIDDEN__"` كـ pid مثل `"__INVALID_PROJECT__"`) — **يخالف Q5 Zero Edits**؛ (ج) الاكتفاء بـ D-403-01. | ⏸️ قرار مالك مطلوب — Q-2 |
| D-403-03 | لا تكرار بحسابات أخرى عند فشل fork لمشروع خاص | يتحقق تلقائياً إن أُنتجت `FORBIDDEN` (PROOF-B). | ✅ تابع لـ 01/02 |
| D-403-04 | براءة مطلقة: `cooldown_until: 0` (إلغاء 300 ث) | **يناقض A-1 المنفَّذ والمصدَّق** (L3996، p51 t11، رسالة L8131). 300 ث كانت «منع الحلقة الساخنة» إذا أعاد المستخدم الإرسال فوراً على نفس المشروع الخاص. مع `return` الفوري الحلقةُ أصلاً لا تدور ⇒ الإلغاء ممكن لكنه **تغيير عقد** يحتاج نصاً صريحاً «أُلغي A-1/300ث». | ⏸️ مرشَّح (7.28e) — Q-3 |
| D-403-05 | حظر المعزل عند 403 | **منفَّذ فعلاً** (Q3 LOCKOUT-FIX: `"FORBIDDEN"` ليس في `COOLDOWN_VAULT_REASONS` L1341؛ p51 t13). | ✅ قائم |
| D-403-06 | توقف فوري من المحاولة 1 | منفَّذ في الحارس (L3998 `return`) — **يعمل فقط بعد D-403-01/02**. | ✅ قائم مشروطاً |
| D-403-07 | رسالة تليجرام توجيهية | موجودة L8129–8132؛ تحتاج تحديث نصي **فقط إن** اعتُمد D-403-04 (إزالة «تبريد احترازي 5 دقائق فقط»). | ✅ قائم / تعديل مشروط |

---

## 4) خطة التنفيذ الجراحي (TASKS — كلها بانتظار GO؛ الأم 01.33 فقط ثم rebuild)

> قاعدة: **تعديل الأم** `01.33_telegram_gen_bridge.py` ⇒ تحديث جدول `PARTS` في `scripts/rebuild_refactor.py` ⇒ `python3 scripts/rebuild_refactor.py` ⇒ `tests/test_refactor_parity.py` 16/16. parts/ لا تُعدَّل يدوياً.

| T | الموضع (الأم) | التعديل المقترح (بعد الدليل) | قيود |
|---|---|---|---|
| **T1** D-403-01 | بين L3597 (`forked_pid = …`) وL3598 (`project_id = forked_pid or orig_pid`) | دالة جديدة في p06 `probe_project_access(orig_pid, cookies, email, bridge_cfg) -> str` ترجع `"private"` / `"ok"` / `"unknown"` (Fail-Open): `GET /api/project?id=` بـ `curl_cffi` + بصمة الحساب (نمط L3062–3075)، timeout 6؛ `private` ⇔ HTTP 403 **أو** (HTTP 200 و`json.status == -13`) **أو** `json.message == "no permission"`؛ أي استثناء ⇒ `"unknown"`. ثم: `if not forked_pid and probe == "private": log_event(...); return build_genspark_viewer_url(orig_pid), "FORBIDDEN", None, None, None`. وسم `[MAINT-11/403-GATE]`. | لا يُستدعى في المشاريع الجديدة (بلا url). يحتاج Q-1 لتثبيت شكل الـ payload. |
| **T2** D-403-02 (بديل أ) | L3713–3716 | تضييق التفسير: إذا `orig_pid` موجود و`not forked_pid` و`pid is None and answer is None` **في كلتا المحاولتين** ⇒ `return build_genspark_viewer_url(orig_pid), "FORBIDDEN", …` **فقط إذا** كان `probe == "private"` أو `"unknown"`(؟) — **القرار على حالة `unknown` للمالك (Q-2)**؛ وإلا يبقى `"FAILED"`. | لا يلمس 01.03. خطر تصنيف 5xx/شبكة كـ FORBIDDEN إن شُمِل `unknown`. |
| **T3** D-403-04 (مشروط) | L3996 + L8131 + p51 t11 | إن أُلغي A-1 كتابةً: `update_account_data(curr_email, {"cooldown_until": 0})`؛ تحديث نص L8131؛ تعديل `assertAlmostEqual(…+300…)` في p51 t11 إلى `assertEqual(cooldown_until, 0)`. | ⏸️ يتوقف على Q-3 |
| **T4** اختبارات | ملف جديد `tests/test_p60_403_private_gate.py` (لا p48) | (1) محرك وهمي يرجع `(None,None,None)` + probe يرجع private ⇒ الحالة `FORBIDDEN` و`send_chat` **صفر مرات**؛ (2) probe يرجع `unknown` + `(None,None,None)` ⇒ السلوك المقرر في Q-2؛ (3) الفيل أوفر الكامل: حساب واحد مُجرَّب، النتيجة `FORBIDDEN`، لا معزل، الرصيد بلا تغيير؛ (4) مشروع عام (probe ok) ⇒ لا تغيير في المسار (regression)؛ (5) probe يرمي استثناء ⇒ Fail-Open. **اختبار الدورة لا الدالة (7.31أ).** | يبقى p51 t11–t14 كما هو (حقن مباشر) |
| **T5** W-1 (اختياري بـ GO منفصل) | L1103، L1564، L3562، L4152، L4175 | استبدال `{curr_email}`/`{email}` في المتن بـ `{redact_email(…)}` أو حذفه (البادئة تحمل البريد المقنَّع أصلاً). | خارج نطاق 403؛ يُنفَّذ فقط إن أراد المالك «صفر إيميلات في اللوج» أيضاً |
| **T6** sha guards | p51 L10، p56 L421، p57 L142 | تحديث sha الأم بعد التنفيذ. | آلي |
| **T7** توثيق | PROGRESS (سطر MAINT-11 ⇒ `[x]`)، RESUME §3.27 + D-10، كارت v1.18 §14، هذا الملف STATUS ⇒ EXECUTED، `recovery_state.json` | — | عبر سكربت مراسٍ `count==1` (7.15) |

**بوابات القبول:** `py_compile` ✓ · parity 16/16 · الحزمة الكاملة == baseline بالأسماء (0 جديد) · p60 كامل أخضر · `verify_docs_integrity.py` Exit 0 · صفر بريد في الشات/الكروت.

---

## 5) ما لا يُنفَّذ (مرفوض/مؤجَّل بدليل)

- ❌ فحص `cfg._last_project_status == -13` (الكارت) — لا يعمل (F-3).
- ❌ فحص `"403" in str(answer)` بعد `send_chat` — `answer=None` في الحادثة (F-4).
- ❌ تعديل 01.03 (L2282) — محمي (Q5 Zero Edits) ما لم يأذن المالك كتابةً (Q-2ب).
- ❌ وسم `P48` — مستخدم (F-6).
- ❌ `impersonate="chrome124"` ثابت (الكارت 093e L7365) — الجسر يستخدم بصمة الحساب `get_account_fingerprint` (L3063) للاتساق مع المحرك (chrome120 في 01.03 L1715).
- ⏸️ `hadith_sijil.py` كبوابة baseline — السكربت موجود لكنه **لا يحتوي منطق baseline بالأسماء** (grep فارغ)؛ البوابة المعتمدة عندنا هي worktree `a8d79bc` + `comm`.

---

## 6) مصفوفة 360° — المتوقع وغير المتوقع بعد التنفيذ

| السيناريو | المسار | النتيجة المتوقعة |
|---|---|---|
| مشروع خاص + fork فاشل | T1 probe=private ⇒ FORBIDDEN قبل أي POST | حساب واحد، 0 POST، رسالة تليجرام فورية، حساب بريء |
| مشروع خاص + fork ناجح | `forked_pid` موجود ⇒ البوابة لا تُطلق | يستمر طبيعياً على الفورك (السلوك الحالي) |
| مشروع عام | probe=ok | لا تغيير |
| probe timeout/استثناء | probe=unknown ⇒ Fail-Open ⇒ المسار الحالي | إن كان 403 فعلاً ⇒ يعتمد على Q-2 |
| 500 من ask_proxy | 01.03 L2278 ⇒ `__INVALID_PROJECT__` ⇒ L3713 ⇒ FAILED | خارج النطاق (كما اليوم) |
| 401 أثناء الشات | L3674 تجديد كوكيز | بلا تغيير |
| إلغاء المستخدم أثناء probe | probe ≤6 ث ثم فحص `_cancel_event` L3643 | بلا تغيير |
| حساب في تبريد منتهٍ يُختار لمشروع خاص | LOCKOUT-FIX Q1 ⇒ إنعاش ⇒ probe ⇒ FORBIDDEN | الحساب يبقى active/100 |

---

## 7) أسئلة موجَّهة للوكيل/المالك — **مطلوب رد بدليل لا بكلام** (قبل أي GO)

| Q | السؤال | الدليل المطلوب |
|---|---|---|
| **Q-1** | ما **الشكل الحرفي** لرد `GET /api/project?id=` لمشروع خاص؟ الكروت تقول `{"status": -13, "message": "no permission", "data": {}}` بـ HTTP 200، وفي موضع آخر (093e L6700) تذكر `{"status": -1, "message": "permission denied"}` لـ `/api/project/update`. | لصق الـ response body + status code لـ Entry #4/#8 من `download11.har` (مع حذف الكوكيز) في ملف `HAR.md` أو كتعليق في الجيست. بدونه T1 يُكتب على **-13 أو message "no permission" أو 403** معاً (أوسع شرط آمن). |
| **Q-2** | عند `probe == "unknown"` (مهلة/استثناء) و`(None,None,None)` من `send_chat` على استئناف بفشل fork: هل نصنّفها FORBIDDEN (خطر تصنيف 5xx/شبكة كمشروع خاص) أم نبقي `FAILED` (خطر عودة الدوران في حالة الشبكة البطيئة)؟ **أو** يأذن المالك بتعديل سطر واحد في 01.03 L2282 (`return None, "__FORBIDDEN__", None` عند 403) وهو **خرق لـ Q5 Zero Edits**؟ | قرار مكتوب بأحد الخيارات أ/ب/ج (§3 D-403-02). |
| **Q-3** | هل يُلغى A-1 (تبريد 300 ث في مكانه — فويس 193، GO db5d L384–402، p51 t11) لصالح D-403-04 (`cooldown_until: 0`)؟ | نص صريح «أُلغي تبريد 300 ث لحالة 403» من المالك (7.28e). بدونه يبقى A-1. |
| **Q-4** | التسمية: `MAINT-11` + `tests/test_p60_…` بدل `P48` (مستخدم). | موافقة. |
| **Q-5** | هل كان observer التليجرام موصولاً أثناء الحادثة؟ (أي: هل وصلت رسائل «المحاولة فشلت وسيستمر البحث» وتم تعديلها صامتاً، أم لم يصل شيء؟) | مقتطف من `bridge_bot.log` حول 09:18–09:19 يحوي `attempt-failed-continue` أو `publish` (بلا إيميلات). يحدد إن كانت هناك فجوة إشعار مستقلة عن F-1. |
| **Q-6** | W-1 (بريد خام في متن اللوج — 5 مواضع): هل «صفر إيميلات» يشمل ملف اللوج المحلي والترمنال أم الشات/تليجرام/الكروت فقط؟ | قرار. إن نعم ⇒ T5 بـ GO منفصل. |
| **Q-7** | هل يُرفَق لوج الحادثة الميداني (مقنَّع) ليُثبت عدد المحاولات الفعلي (الكارت يقول 6 حسابات؛ PROOF-C يعطي 2 POST/حساب)؟ | مقتطف اللوج. |

---

## 8) مراجع الأسطر (كلها بـ `grep -n` على HEAD 4e22e23)

- 01.33: `send_message_and_make_public` L3381؛ حلقة المحاولات L3452 (`max_retries` L3393 ← `max_timeout_retries=2` L990)؛ مسار url L3588–3610؛ `send_chat` L3666؛ `not pid` L3713–3716؛ `send_message_with_auto_account_failover` L3783؛ `read_accounts_safe` L3808؛ `while attempt < max_attempts` L3827 (`max_account_attempts=50` L991)؛ A-1 FORBIDDEN L3985–3998؛ fallthrough L4326–4336؛ `MAX_ATTEMPTS_EXHAUSTED` L4341؛ `detect_response_status` L2278 (403 من dict فقط L2294)؛ `monitor_chat_completion` L3144 (FORBIDDEN L3214)؛ `get_public_forked_pid` L3044–3106؛ `describe_terminal_outcome` L8034 (FORBIDDEN L8129–8132)؛ `redact_email` L83؛ `log_event` L93؛ `get_account_lock` L572؛ `update_account_data` L1071؛ `reactivate_account_if_due` L1152؛ `COOLDOWN_VAULT_REASONS` L1341؛ observer titles L1850–1945؛ `publish` L2034؛ ربط observer L2072؛ `log_fh` L8927–8931.
- 01.03 (محمي، قراءة فقط): `fetch_project_messages` L1681 (status العلوي غير مقروء L1729–1737)؛ `create_forked_project` L1816؛ `send_chat` L1923؛ POST `ask_proxy` L2252؛ معالجة الأكواد L2258–2282 (`403 ⇒ (None,None,None)` L2281–2282)؛ `share_project` L2551 (`/api/project/update` L2569)؛ `ensure_public` L760 («share فشل» L776).
- bridge_refactor/parts/p06_engine_flow.py: `not pid` L992؛ FORBIDDEN L1268؛ `orig_pid` L868.
- الاختبارات: p51 harness L255–283 (t11–t14 حقن مباشر)؛ p59 `_FakeEngine` L70–89، `_PreflightFixture` L149–164.
