# RESUME.md — نقطة الاستئناف الحية للوكيل

> يُحدَّث عند كل محطة إنجاز (Milestone) جنبًا إلى جنب مع رأس `PROGRESS.md`.
> لا يحتوي أرقام commit ثابتة كمرجع تنفيذ؛ القاعدة دائمًا = أحدث HEAD في `origin/genspark_ai_developer`.
> لا أسرار هنا أبدًا. **المرجع الذاتي الوحيد للأولويات = جدول الأولويات في رأس `PROGRESS.md`.**

---

## 0) قاعدة دستورية دائمة لحسم MODE (معتمدة من المالك 2026-10-31 — لا تُؤرشف)
إذا ورد كارت الاستئناف بصيغة الخيارين `[ALIGNMENT_ONLY] | أو "ابدأ تنفيذ"` (القالب المعياري الثابت)، فالوضع **الافتراضي الإلزامي = «ابدأ تنفيذ» تلقائياً وذاتياً دون توقف**، طالما: (أ) القرارات اللازمة للخطوة معتمدة ومكتوبة في PROGRESS، و(ب) الخطوة = أول `[ ]` في رأس PROGRESS. **يُحظر التوقف لطلب حسم الخيارين.** الاستثناء الوحيد: خطوة تحتاج قراراً غير مكتوب → تُكتب المواصفة/الأسئلة ويُتوقف عندها فقط.

## 1) أين أقف الآن؟ (2026-10-31 — STEP-3 + STEP-4 (DEC-07) + MAINT-1 مغلقة بالأدلة)

| البند | الحالة |
|---|---|
| الفرع | `genspark_ai_developer` فقط (main READ-ONLY، لا فروع جانبية) — Layer A في أول 30 ثانية من كل جلسة بلا استثناء |
| المرحلة | **STEP-3 مغلق** (+ S3-LOG-1). **STEP-4 (DEC-07) مغلق 2026-10-31:** S4-A مواصفة → S4-A-RATIFIED (قرارات 1–7) → S4-B `tests/test_p50_dec07_breaker.py` 19 اختباراً (حمراء أولاً 10/9) → S4-C ثلاث حقنات في 01.33 (ثوابت `DEC07_*` + `dec07_text_has_suspended_marker`؛ صمام الرد الفارغ في `monitor_chat_completion`؛ فرعا `EMPTY_STREAM_FAILED`/`ACCOUNT_SUSPENDED` في failover) 9660→9736 سطراً CRLF + PARTS p05..p12 محدَّثة وparity 11/11 → S4-D إغلاق بالأسماء. **MAINT-1 مغلق 2026-10-31:** `rebuild_refactor.py` صار purge-only (لا rmtree) + كاتب CRLF + `main(root=)`؛ 5 اختبارات `TestGeneratorSafety` (حمراء أولاً) → parity 16/16؛ تشغيل حي في المكان ⇒ `git status bridge_refactor` فارغ. **التالي بالجدول: MAINT-3** (`FORBIDDEN` في failover) — **معلّق على قرار المالك (§4 بند 1)**. |
| MODE الحالي | **MAINT-3-A منجزة (ALIGNMENT_ONLY 2026-10-31):** مراجعة معمارية + مواصفة Cut&Move في §3 مسندة سطرياً، واكتشاف أن `FORBIDDEN` يُوسم اليوم **نجاحاً** في ملف الحسابات (§3.1 T5). **MAINT-3-B (الكود) لا يبدأ قبل اعتماد D1–D9 في §4** — كارت بالخيارين بلا قرارات مكتوبة = لا كود (استثناء §0: القرارات غير مكتوبة) |
| PR | #9 Draft (يبقى Draft؛ لا merge) |
| وضع التسليم | حفظ محلي في `/home/user/webapp` → أداة المزامنة الخارجية ترفع تلقائيًا. لا push/gh/ZIP من الوكيل. |
| الخط الأساسي للاختبارات | **بالأسماء لا بالرقم**: 26 فاشلة معروفة (12 تاريخية + 14 drift؛ القائمة في `current_execution.baseline_failing_names`). أي اسم جديد = انحدار. آخر قياس: **1206 passed / 26 failed / 1 skipped** (بعد MAINT-1؛ الأسماء الفاشلة مطابقة حرفياً — 0 جديد؛ P50 19/19؛ parity 16/16). |

### القرارات المعتمدة من المالك (مرجع ثابت)
المسار (أ) الهدية الثلاثية؛ READ-ONLY = 01.03 + verifier (verifier بإذن AGENTS:22)؛ فحص **أوفلاين** من بيانات 05.02 فقط؛ UNKNOWN = **Fail-Open**؛ حد `>=14` شامل؛ Q-F دمج المعزل القديم في `accounts_failed.json` مع أرشيف؛ Q-C استبعاد عند الاختيار وin-flight يكمل؛ Q-R منجز؛ DEC-04 تأجيل الـ14 drift؛ **STEP-3**: سكربت مستقل `scripts/merge_legacy_quarantine.py`، عدم لمس 05.02، dry-run افتراضي/`--apply`، `.bak` مؤرخة، تفرد `email.lower()`، `legacy_quarantine`، اختبارات أولاً، حارس المسار `--i-know-this-is-real`؛ **STEP-4 (DEC-07)** مجدول رسمياً بعد STEP-3؛ **MAINT-1** مجدول.

---

## 2) خريطة الطريق (ملخص — التفصيل في PROGRESS)

| # | التذكرة | الحالة |
|---|---|---|
| 1 | STEP-1 اختبارات عزل 05.02 (34 passed) | `[x]` |
| 2 | STEP-2 Pre-Flight أوفلاين في 01.33 (34 passed؛ 0 انحدار؛ parity أخضر) | `[x]` مغلق |
| 3 | **STEP-3 (Q-F)** S3-A..D — سكربت مستقل + 14 اختباراً + إغلاق بالأسماء | `[x]` **منجز** |
| 4 | **STEP-4 (DEC-07)** صمام الرد الفارغ + `user_suspended` في `monitor_chat_completion` | `[ ]` **جارٍ** — S4-A `[x]`؛ S4-B التالي بعد الاعتماد |
| 5 | **MAINT-1** حماية `github_bulk_sync.py` + CRLF في `rebuild_refactor.py` | `[ ]` مجدول (مستقل) |
| 6 | MAINT-2 الـ14 drift | `[ ]` مؤجل بقرار |
| 7 | Layer B/C | مقترح غير معتمد |

**ما تم فعلياً (بالأدلة):** STEP-1، Q-R، SYNC-TEST، ALIGN-0، BASELINE-DRIFT parity، STEP-2 (S2-A..D)، docstring 05.02، حذف GITHUB_SYNC، مراجعة 360°، خريطة الطريق، **STEP-3 (S3-A..D)**.
**لم يُنفَّذ (ولا يُدَّعى):** تشغيل `--apply` على ملفات المالك الحقيقية؛ STEP-4؛ MAINT-1/2؛ إصلاح أي من الـ26؛ أي تشغيل حي؛ V2 §17.6.

---

## 3) MAINT-3 — مراجعة معمارية ومواصفة (ALIGNMENT_ONLY 2026-10-31؛ لا كود) — عزل 403 في `accounts_cooldown.json` + سجل تدقيق `account_log.json`

> مقترح المالك (كارت MAINT-3): (1) عند 403 في failover يُنقل الحساب Cut & Move من `accounts_genspark.json` إلى `accounts_cooldown.json`؛ (2) سجل تدقيق مركزي `account_log.json` بالسبب والتوقيت وتدوير 30 يوماً؛ (3) 05.02 مقدس لا يُمس. كل بند أدناه مُسند بسطره في `01.33_telegram_gen_bridge.py` (9736 سطراً، CRLF، آخر تعديل S4-C). ما لا دليل عليه مكتوب صراحةً كـ«قرار مطلوب»، لا كاستنتاج.

### 3.1 التشخيص: ماذا يحدث فعلاً لـ`FORBIDDEN` اليوم (اكتشاف أخطر من «غياب فرع»)
| # | الحقيقة | الدليل السطري |
|---|---|---|
| T1 | `FORBIDDEN` يُكتشف **حصراً** من كود الـendpoint (403) لا من نص الشات (P46)؛ `FORBIDDEN_KEYWORDS` موجودة لكنها غير مستخدمة (`pass`). | 2043، 2076–2077، 2088–2089 |
| T2 | داخل حلقة المتابعة: `cfg._last_fetch_status == 403` ⇒ `return "FORBIDDEN", last_resp_text` فوراً (شرط خروج شرعي). | 2898، 2928–2930 |
| T3 | في `send_message_and_make_public`: `FORBIDDEN` ضمن مجموعة «المتابعة للأرشفة» (3409) ⇒ **لا يعود مبكراً** بل ينفّذ تنزيل الأرشيف (3441) و`make_project_always_public` (3445) — التي تعيد **رابط viewer احتياطياً دائماً** حتى عند فشل الشبكة (2715، 2757) — ثم `save_project_branch(status=FORBIDDEN)` (3448–3454) ثم `return final_public_url, "FORBIDDEN", ...` (3455). | 3409، 3441، 3445، 2715، 2757، 3448–3455 |
| T4 | في `send_message_with_auto_account_failover` (def 3460) **لا يوجد أي فرع لـ`FORBIDDEN`**: CANCELLED 3579، COMPACT 3594، مجموعة الإرجاع 3615، DEC07 3618/3631، LOW_BALANCE 3644، DATA_RETENTION 3657، is_401 3749 (SESSION_EXPIRED/LOGIN_FAILED فقط)، CREDIT_EXHAUSTED 3813 — لا شيء يطابق. | 3579–3826 |
| T5 | **النتيجة الفعلية:** يصل إلى `if pub_url or status == "COMPLETED":` (3928) و`pub_url` **غير فارغ** (T3) ⇒ يُعامَل كنجاح: `update_account_data(curr_email, {status: active, active: True, cooldown_until: 0, last_success_at})` (3935–3941) ثم `return pub_url, "FORBIDDEN"` (3942). أي: **الحساب الذي أعاد 403 يُوسم «نجاح» في الملف ولا يُجرَّب حساب آخر**، بينما المستخدم يرى بطاقة فشل `⛔ رفض الوصول` (7633–7636). | 3928–3942، 7633–7636 |
| T6 | لا يصل `FORBIDDEN` أبداً إلى ذيل «محاولة فاشلة» (تبريد 5 دقائق 3953) بسبب T5. | 3944–3954 |
| T7 | الكود يعرف أصلاً أن 403 على مشروع ≠ موت الحساب: عند 403 في جلب الرسائل يتجاوز بـ«التفريع العام» (3275–3276). ⇒ إعادة محاولة **نفس الرابط** بحساب آخر (كما يفعل `continue` في LOW_BALANCE 3652 بلا تغيير `active_url/active_query`) متسقة مع الموجود. | 3275–3276، 3644–3652 |

**خلاصة:** MAINT-3 ليست «إضافة فرع» فقط؛ هي إصلاح **تصنيف خاطئ للنجاح** (T5). أي حل يُحقن **قبل** 3928 — الموضع الطبيعي بعد فرع `ACCOUNT_SUSPENDED` (3631–3642) وقبل `LOW_BALANCE` (3644) بنفس قالب DEC07 (observer → كتابة → log → `continue`).

### 3.2 البنية القائمة التي تُبنى عليها الآلية (وقيودها)
| # | الأداة | ما تفعله | القيد المؤثر على التصميم | الدليل |
|---|---|---|---|---|
| I1 | `FILE_LOCK = threading.Lock()` | قفل كل قراءة/كتابة لملف الحسابات | **غير re-entrant**: دالة النقل إن أمسكت `FILE_LOCK` **يُحظر** أن تستدعي `read_accounts_safe`/`update_account_data` داخله (deadlock فوري). | 201، 1056، 1072 |
| I2 | `get_accounts_file_path(json_path)` | `json_path` → `resolve_shared_path` → الأب → cwd؛ تعيد `None` إن لم يوجد | مجلد المعزل والسجل = `acc_file.parent` (سابقة الـverifier 1334–1335). `None` ⇒ لا نقل (Fail-Closed) ولوج فقط. | 1036–1049، 1334–1335 |
| I3 | `update_account_data` | read→modify→`.tmp`→`replace` تحت `FILE_LOCK`؛ IMMUNE-GUARD؛ **تعيد `False` بصمت إن لم يوجد البريد** | بعد Cut&Move كل استدعاء لاحق لنفس البريد = `False` صامت ⇒ النقل يجب أن يكون **آخر كتابة** في المحاولة ويعقبه `continue` فوراً؛ `finally` (3956–3959) لا يكتب للملف ✅. | 1068–1101، 1091–1092، 3956–3959 |
| I4 | `is_account_ready` / `reactivate_account_if_due` | نقية / تعيد تفعيل `cooldown,auth_failed,disabled` فقط | **لا مسار رجوع** من ملف خارجي: حساب في المعزل لا يعود إلا بأداة خارجية (D3). | 1104–1146، 1149–1169 |
| I5 | `all_accounts = read_accounts_safe(json_path)` مرة واحدة عند بدء الـfailover + `tried_emails` | لا حاجة لإعادة القراءة بعد النقل في نفس المهمة؛ المهمة التالية تقرأ الملف الجديد. | 3485، 3545، 1250–1258 |
| I6 | سابقة «عزل في ملف خارجي»: `gve.quarantine_account_atomic` (verifier READ-ONLY) + وسم في الأساسي | النمط الحالي = **نسخ + وسم** لا **قص**؛ اسم ملف الـverifier ثابت ⇒ لا يُعاد استخدامه؛ نمط ذريته (قفل + dedupe بالبريد + `.tmp`→`replace`) هو المرجع المحاكى داخل 01.33. | 1334–1350؛ verifier 39–40، 376–430 |
| I7 | لوج 01.33: `FileHandler` بلا تدوير؛ `log_event` يموّه البريد؛ **لا بدائية تدوير** في الملف | «تدوير 30 يوماً» يُبنى يدوياً: **تقليم عند الكتابة** (حذف الأقدم من 30 يوماً + سقف عددي) — بلا مجدول/ثريد. | 71–78، 93–104 |
| I8 | 05.02 (مقدس): يقرأ قائمة أو `{"accounts": [...]}` (236–245)؛ **يعيد كتابة الأساسي كاملاً** من لقطته (525، 696) | (أ) المعزل = **قائمة JSON مسطحة** ليقرأها 05.02 لاحقاً بلا تعديل؛ (ب) **سباق البعث:** إن نقل 01.33 حساباً أثناء عمل 05.02، فكتابة 05.02 اللاحقة قد تُعيده للأساسي **بلا أي أثر للتبريد** (الأثر الوحيد في ملف آخر). السباق موجود اليوم لكل كتابات 01.33، لكن Cut&Move يجعله مؤذياً لأنه يزيل «الوسم في المكان». | 05.02: 99–103، 236–245، 525، 696 |

### 3.3 رأيي المعماري (صريح)
1. **Cut&Move قابل للتنفيذ بأمان** بشرط ثلاثي: ترتيب «نسخ ثم قص» + dedupe idempotent في المعزل + سجل تدقيق يُكتب **بعد** نجاح القص (best-effort لا يُلغي النقل). بدون هذا الترتيب يصبح فقدان حساب ممكناً عند انقطاع بين الكتابتين — لا ذرية عبر ملفين؛ `replace` ذري لملف واحد فقط (1096–1098؛ 05.02: 226–227).
2. **ثمن Cut&Move مقابل النمط القائم (I6):** يفقد 01.33 إعادة التفعيل التلقائي (I4) ويُدخل باباً أحادي الاتجاه حتى يُطوَّر 05.02 (خارج صلاحياتي نهائياً). لذا أوصي بأداة رجوع يدوية `scripts/return_from_cooldown.py` (dry-run افتراضي، `--apply` بعد `.bak`، حارس مسارات كما في `merge_legacy_quarantine.py`) حتى لا يُحتجز حساب سليم بسبب 403 عابر (D3).
3. **سباق البعث (I8-ب) هو الخطر الحقيقي الوحيد** الذي لا يعالجه 01.33 وحده. الخيارات: (أ) قبوله (إعادة قصّ idempotent عند 403 التالي)؛ (ب) عدم تشغيل 05.02 و01.33 متزامنين؛ (ج) مستقبلاً يفحص 05.02 المعزل قبل إعادة كتابة الأساسي (ملكك). أوصي بـ(أ)+(ب) الآن (D4).
4. **إصلاح T5 إلزامي بأي حال**، حتى لو رُفض Cut&Move: فرع `FORBIDDEN` قبل 3928 يمنع وسم 403 كنجاح — هذا الحد الأدنى لـMAINT-3 (D9).
5. **اختياري منفصل (MAINT-3b):** استبعاد `FORBIDDEN` من مجموعة 3409 يوفّر تنزيل أرشيف (timeout 180s) ونشراً عاماً عبثيين و`save_project_branch` بحالة فشل. لا يمس `P44_STRUCTURED_STATUSES` (2115) لكنه يغيّر شكل الإرجاع (`build_genspark_viewer_url` 5636 بدل `make_project_always_public`) ⇒ اختبار مستقل؛ ليس في الحد الأدنى (D5).

### 3.4 المواصفة التفصيلية المقترحة (لا تُنفَّذ قبل اعتماد D1–D9)
**(أ) ثوابت جديدة (p03، بعد 1297 `mark_account_cooldown`):** `COOLDOWN_VAULT_FILENAME="accounts_cooldown.json"`، `ACCOUNT_LOG_FILENAME="account_log.json"`، `ACCOUNT_LOG_RETENTION_DAYS=30`، `ACCOUNT_LOG_MAX_ENTRIES=5000`، `ACCOUNT_LOG_LOCK=threading.Lock()` (للسجل فقط)، `FORBIDDEN_ISOLATION_ENABLED=True` (مفتاح رجوع كما في DEC07).

**(ب) `append_account_log(event, email, reason, meta, base_dir)`:** تحت `ACCOUNT_LOG_LOCK`: قراءة متسامحة (تالف ⇒ قائمة فارغة + لوج)، إضافة `{ts, at, event: exit_to_cooldown|return_to_primary|move_partial, email (كامل — S3-LOG-1 يسري على ملف بيانات؛ **لا password ولا cookies أبداً**), reason, http_status, project_key, pid, source_file, target_file, bridge_build}`، **تقليم**: حذف `ts < now-30d` ثم قصّ لآخر `ACCOUNT_LOG_MAX_ENTRIES`، كتابة `.tmp`→`replace`. الفشل ⇒ `log_event` فقط، لا استثناء.

**(ج) `move_account_to_cooldown_vault(email, reason, json_path, meta) -> bool` (قلب الآلية):**
1. `acc_file = get_accounts_file_path(json_path)`؛ `None` ⇒ `log_event(error)` و`return False` (الحساب يبقى؛ الـfailover يُكمل بتبريد 5 دقائق الاحتياطي 3953 — **لا** وسم نجاح).
2. `with FILE_LOCK:` قراءة/تعديل/كتابة **يدوية** داخل الدالة (لا `update_account_data`/`read_accounts_safe` — I1): إيجاد السجل بالبريد؛ غياب ⇒ `return False` (idempotent).
3. `record = dict(acc)` + `cooldown_meta = {reason, http_status: 403, moved_at, moved_at_ts, cooldown_until_ts (D1), source: acc_file.name, project_key, pid, bridge_build}`؛ `password`/`cookies` تبقى (D2).
4. **نسخ:** قراءة `accounts_cooldown.json` (قائمة مسطحة I8-أ)؛ dedupe بالبريد lowercase كما في verifier 405–407 (موجود ⇒ تحديث `cooldown_meta` فقط)؛ `.tmp`→`replace`. فشل ⇒ `return False` **قبل** لمس الأساسي.
5. **قص:** حذف السجل من قائمة الأساسي؛ نسخة احتياطية دوّارة `accounts_genspark.json.cooldown_move.bak` (copy2) ثم `.tmp`→`replace`. فشل ⇒ الحساب في الملفين (قابل للاسترداد؛ يُسجَّل `move_partial`) و`return False`.
6. **تدقيق:** `append_account_log("exit_to_cooldown", ...)` best-effort خارج `FILE_LOCK`. `return True`.
7. **الأقفال:** الخطوتان 4 و5 تحت `FILE_LOCK` وحده (ملف المعزل لا يكتبه غير 01.33 حالياً)؛ `ACCOUNT_LOG_LOCK` للسجل فقط ولا يُمسك متداخلاً مع `FILE_LOCK` — لا deadlock.

**(د) فرع الـfailover (p06، بعد 3642 وقبل 3644) — صيغة توضيحية:**
```
if status == "FORBIDDEN" and FORBIDDEN_ISOLATION_ENABLED:
    notify_account_selection_observer(bridge_cfg, "forbidden-isolate", status="FORBIDDEN", max_attempts=max_attempts)
    moved = move_account_to_cooldown_vault(curr_email, reason="FORBIDDEN", json_path=json_path,
                                           meta={"project_key": ..., "pid": extract_project_id(pub_url or active_url)})
    if not moved:
        update_account_data(curr_email, {"cooldown_until": time.time() + 300}, json_path=json_path)  # احتياطي 3953 — لا وسم نجاح
    log_event("warning", "[MAINT3] FORBIDDEN — نُقل للمعزل / تعذر النقل؛ تبريد 5 دقائق — الانتقال للحساب التالي", email=curr_email)
    continue   # active_url/active_query بلا تغيير — عقد LOW_BALANCE 3652 وسابقة 3275
```
`P44_STRUCTURED_STATUSES` (2115) ومجموعتا 2898/3409 لا تتغير في الحد الأدنى.

**(هـ) أداة الرجوع `scripts/return_from_cooldown.py` (D3):** `--vault/--primary/--email|--all/--apply/--i-know-this-is-real`؛ dry-run افتراضي؛ `.bak` قبل الكتابة؛ تحذف من المعزل وتضيف للأساسي بـ`status=active/cooldown_until=0` وتكتب `return_to_primary`؛ exit codes 0/2/3 كما في `merge_legacy_quarantine.py`.

**(و) الاختبارات أولاً `tests/test_p51_forbidden_isolation.py` (harness P50 `TestFailoverHandling` 233–300 + ملفات مؤقتة حقيقية):** (1) FORBIDDEN ⇒ السجل في المعزل، البريد غائب عن الأساسي، `exit_to_cooldown` في السجل، الحساب الثاني يُجرَّب، **لا** `status=active` لـEMAIL_A (إثبات إصلاح T5)؛ (2) نسخ-ثم-قص: فشل كتابة الأساسي ⇒ الحساب في الملفين ولا فقدان؛ (3) idempotent؛ (4) `get_accounts_file_path=None` ⇒ لا نقل + تبريد 5 دقائق + `continue`؛ (5) `FORBIDDEN_ISOLATION_ENABLED=False` ⇒ السلوك القديم حرفياً (يوثّق T5 كخط أساس)؛ (6) تقليم السجل 31 يوماً + السقف؛ (7) السجل بلا `password`/`cookies`؛ (8) المعزل قائمة مسطحة؛ (9) لا deadlock مع `FILE_LOCK` الحقيقي؛ (10) عقود المصدر: فرع واحد قبل 3928، `P44_STRUCTURED_STATUSES`/`is_account_ready`/P48/DEC07 بلا تغيير، CRLF، لا مساس بـ05.02/01.03/verifier.

**(ز) PARTS:** إضافات p03 (بعد 1297) تزيح p04..p12؛ فرع p06 يزيح p07..p12؛ `rebuild_refactor.py` آمن بعد MAINT-1.

### 3.5 خارج MAINT-3 صراحةً
لا لمس 05.02/verifier/01.03؛ لا probe شبكي؛ لا تغيير في كشف 403 (P46 2088)؛ لا تدوير لـ`bridge_bot.log`؛ لا migration للحسابات الحالية.

---

## 4) قرارات مطلوبة من المالك قبل كود MAINT-3-B (بلا تخمين — تُكتب في DECISIONS بالكارت)
| # | القرار | الخيارات | توصيتي ولماذا |
|---|---|---|---|
| D1 | `cooldown_until_ts` في `cooldown_meta` (معلوماتي لـ05.02/أداة الرجوع) | بلا / 1h / 24h / 29h | **24h**: 403 ليس نفاد رصيد (29h) ولا بثاً فارغاً (1h) |
| D2 | `password`/`cookies` في سجل المعزل | إبقاؤهما / تصفير cookies / تصفير الاثنين | **إبقاؤهما**: 403 ليس فشل مصادقة (T1/T7)؛ التصفير يجبر login بلا داعٍ عند الرجوع |
| D3 | مسار الرجوع | 05.02 لاحقاً فقط / أداة dry-run / كلاهما | **كلاهما** — الأداة الآن لمنع احتجاز حساب سليم |
| D4 | سباق البعث (I8-ب) | قبول / منع التزامن تشغيلياً / تعديل 05.02 لاحقاً | **قبول + منع التزامن** الآن |
| D5 | MAINT-3b (استبعاد FORBIDDEN من 3409) | ضمن MAINT-3 / لاحقاً / لا | **لاحقاً** — يغيّر شكل الإرجاع |
| D6 | موقع الملفين | بجوار الأساسي (`acc_file.parent`) / `SCRIPT_DIR` | **بجوار الأساسي** (سابقة 1334–1335؛ حيث يعمل 05.02) |
| D7 | تدوير السجل | تقليم عند الكتابة 30d + سقف 5000 / ملفات شهرية / بلا سقف | **تقليم + سقف** — بلا مجدول، ذري، محدود |
| D8 | الأسماء | `accounts_cooldown.json` و`account_log.json` / أخرى | **كما وردت** (نمط `accounts_*.json` في 05.02 99–103) |
| D9 | الحد الأدنى إن رُفض Cut&Move | فرع `FORBIDDEN` قبل 3928 بتبريد في المكان | إلزامي بأي حال لإصلاح T5 |

(منفصل: `merge_legacy_quarantine.py --apply` على الملفات الحقيقية يحتاج أمراً صريحاً؛ MAINT-2 مؤجلة DEC-04.)

---

## 5) فحص الصحة عند كل استئناف (أقوم به تلقائيًا)
`git fetch origin genspark_ai_developer && git checkout -B genspark_ai_developer origin/genspark_ai_developer && git reset --hard origin/genspark_ai_developer` (إبلاغ الفرع/HEAD/dirty) → قراءة رأس PROGRESS + هذا الملف + `current_execution` → فحص الـGist إن ورد → إن كان MODE تنفيذياً: `pytest tests -q` مطابقة **بالأسماء** + `verify_docs_integrity.py` Exit 0 → البدء من أول `[ ]` في جدول الأولويات.
