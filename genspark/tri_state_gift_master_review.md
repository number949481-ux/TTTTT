# المراجعة المرجعية وخريطة تنفيذ المعزل الثلاثي والهدايا

## 0. نقطة الاستئناف المثبتة

> **تحديث نطاق 2026-10-29 بعد روابط المالك الجديدة:** استعيد PR9 عند `b74900c`؛ وصل main إلى `d2eb49d` بتعديل الوثائق الأربع وإضافة2647سطرًا للأرشيف دون تعديل Python. بدأت مراجعة Arena وتغييرات هذه الوثائق؛ تسليم §0–§14 السابق تاريخي لهذه الإضافة، والتحديث الحاكم قيد الإعداد في §15. لا runtime ولا تعديل ملفات الوكلاء الأصلية.

- تاريخ المراجعة: 2026-10-29.
- أساس التحقيق والمواقع البرمجية: `92f658ebd575407d0bba8e3a682cadd0fc248404`. تمت المزامنة مع `origin/main@a181f35` (وثيقة إضافية فقط، Python لم يتغير؛ §13.5).
- الفرع الجديد: `genspark_ai_developer`. عند بداية الجلسة لم يوجد فرع بعيد آخر؛ لا توجد نقطة منشورة لهذه المراجعة يمكن الادعاء باستعادتها.
- رأس `PROGRESS.md` و`current_execution` في `genspark/recovery_state.json` يخصان PR9؛ سجل PR8 محفوظ تاريخيًا ولا يمثل baseline الحالي.
- التكليف: قراءة المصادر الثمانية، تدقيقها مقابل التنفيذ، إنشاء ملف شامل مصحح بالمراحل والأدلة والاختبارات والقرارات والتراجع.
- نطاق العمل: مراجعة وتصحيح الخطة وتوثيق أدلة التنفيذ، دون تغيير كود التشغيل أو بيانات الحسابات أو إجراء اتصالات Genspark/Telegram حية.
- الحالة: **المراجعة والتصميم A0–A5 مكتملة؛ سجل A6 جاهز للتسليم بعد التحقق من النشر. baseline أحمر. T00–T39 وX01–X30 خطة مستقبلية، لا تنفيذ ولا اعتماد مزعوم.**
- الحفظ: commit ثم fetch/rebase ثم push والتحقق من الرأس البعيد بعد كل دفعة. يبقى PR مفتوحاً للمراجعة؛ لا merge أو deployment.

## 1. المصادر والمرجعية

1. [00 NOTES](../00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md).
2. [00 PLAN](../00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md).
3. [012345 NOTES](../012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md).
4. [012345 PLAN](../012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md).
5. [مدير الهدايا المرجعي 05.02](../05.02_genspark_delayed_gifts_manager.py).
6. [أرشيف المحادثات](../جج-جميع-شات-.MD).
7. [commit 885d7a4](https://github.com/number949481-ux/TTTTT/commit/885d7a41f93aa8293f6baa9f653ddb21d29f1bb9): إضافة وثائق ومحادثات، لا تنفيذ للميزة.
8. [commit 92f658e](https://github.com/number949481-ux/TTTTT/commit/92f658ebd575407d0bba8e3a682cadd0fc248404): إضافة السكريبت المرجعي فقط، لا دمج بالجسر.

المرجع للأماكن البرمجية هو revision أعلاه وأسماء الدوال، وليس أرقام السطور المنسوخة من جهاز Windows. الوثائق القديمة تحفظ كسجل؛ التصحيح الحاكم لهذه المراجعة هنا. لا نستنتج اعتماد المالك من وصف وكيل سابق للخطة بأنها «معتمدة 100%».

## 2. الخطة المجمدة للمراجعة

| المعرف | المهمة | شرط الإغلاق | الحالة |
|---|---|---|---|
| A0 | استعادة Git والفروع ونقطة الحفظ | head وremote وقراءة السجل | مكتملة |
| A1 | قراءة كل المصادر ومقارنة التوجيهات المتعارضة | مصفوفة مصدر/قرار/تصحيح | مكتملة |
| A2 | تتبع الاختيار والرصيد والتجديد والعزل والكتابة | خريطة أسماء دوال وأماكن فعلية | مكتملة |
| A3 | baseline كامل وsyntax وparity والبوابة | نتائج فعلية مع الفشل لا عدد تاريخي | الفحص مكتمل، البوابات حمراء قبل التعديل |
| A4 | تصميم مصحح للزمن والأخطاء والمعاملة متعددة الملفات | حالات النجاح والفشل والتزامن والاسترداد | مكتملة كتصميم، §8 |
| A5 | BEFORE/AFTER وعقود الاختبار وخطة المراحل والتراجع | ربط كل خطر بمهمة واختبار | مكتملة كخطة، §9–§13 |
| A6 | تحديث نقطة الاستئناف وتسليم التقرير وPR | شجرة نظيفة ورأس بعيد متحقق | السجل محدث؛ تحقق التسليم النهائي عبر PR9 وremote وفق §14 |

المراحل التنفيذية للميزة لا تبدأ تلقائياً بسبب إكمال مراجعة الورق. أي تغيير سلوكي غير محسوم يُعرض صراحةً؛ لا تشغيل لترحيل بيانات حقيقية ولا إحياء حسابات معزولة ولا تشغيل المدير المرجعي على حسابات المالك.

## 3. خلاصة التعارضات الأولية

- `012345 PLAN:TASK-301` يطلب `sanitize_accounts_on_startup`؛ `00 NOTES:48–55` يلغي Startup Sanitize/TTL/UI. يلزم حذف هذا المسار من الخطة الحاكمة، لا تنفيذه لمجرد وجود checkbox.
- `05.02:408` يستخدم `days_elapsed >= threshold_days`؛ الخطط تكتب `>14`. يلزم تحديد حد دقيق واختبارات الحدود، لا نقل الشرط حرفياً مع توثيق مخالف.
- `05.02:61–67` يعتمد على `genspark_master_account_manager` غير الموجود في قائمة ملفات المستودع الحالية؛ لا يُستورد السكريبت كاملاً في الجسر.
- `genspark_verifier_engine.py:376–430` يكتب معزلاً واحداً، ولا يقص المصدر بنفسه. قفل و`replace` لملف واحد ليسا برهان معاملة ذرية لملفين.
- بيانات أعداد الحسابات والمسارات المحلية في الملاحظات ليست قياسات هذه البيئة. لا توجد صلاحية لنشر أسرار أو نقل خزائن حقيقية إلى Git.

## 4. التالي مباشرة عند reset

1. افحص remote head وPR9 وgit status قبل تكرار أي دفع؛ لا reset قسريًا على عمل محلي.
2. اقرأ رأس `PROGRESS.md` ثم هذا التقرير وcurrent_execution؛ لا تنفذ PR8 المؤرشفة.
3. المصادر الثمانية قُرئت والمحاكاة اكتملت (§7)؛ §9–§13 أضيفت بعد استعادة a06218c. لا تبدأ من الصفر.
4. آخر دفعة تفاصيل متحقق منها قبل سجل التسليم: `4491b1bbe3b1c35c18abb717092cf9644e1658fb`. رأس التسليم قد يكون أحدث أو squashed؛ المرجع remote/PR لا hash قديم من الملخص.
5. إذا بقي نشر سجل التسليم فأكمله فقط بعد diff/validation؛ وإلا انتظر D1–D6 وGO. لا runtime أو migration أو live. PR: https://github.com/number949481-ux/TTTTT/pull/9 .

## 5. نتيجة الفحص الفعلية على الأساس — لا تختلط بتاريخ PR #8

نُفذت الأوامر التالية قبل reset، على شجرة Python المطابقة لـ `92f658e`، في 2026-10-29. هذه نتائج Terminal المسجلة في المحادثة، وليست الأرقام المنسوخة من README. فقدت ملفات `.tmp` عند reset؛ تبقى النتيجة الموثقة هنا، ويمكن إعادة الأوامر للتحقق.

| الفحص | النتيجة |
|---|---|
| `python -m pytest -q -p no:cacheprovider` | **1072 passed، 13 failed، 60 subtests passed**، 5.89s |
| `python -m pytest tests/test_refactor_parity.py -q -p no:cacheprovider` | **10 passed، 1 failed، exit 1** |
| `python -X utf8 scripts/hadith_sijil.py` | **1085 tests، failures=13، exit 1**؛ لا يكتب تقرير نجاح جديد عند الفشل |
| `python -m py_compile` على 01.33 و01.03 وverifier و05.02 وrebuild | **exit 0**؛ نجاح syntax لا يثبت قابلية استيراد 05.02 أو نجاح التشغيل |

### جميع الاختبارات الـ13 الفاشلة

```text
test_auto_compact.py::CompactTests::test_account_above_180_does_not_compact
test_auto_compact.py::CompactTests::test_five_minute_credit_exhaustion_does_not_compact
test_auto_compact.py::CompactTests::test_long_credit_after_maintenance_resumes_without_recompacting
test_auto_compact.py::CompactTests::test_new_credit_replaces_old_deferral_and_long_credit_clears_due
test_auto_compact.py::CompactTests::test_threshold_uses_monotonic_span_at_exactly_180_seconds
test_credit_completion_recovery.py::CreditRecoveryTests::test_fast_credit_handoff_preserves_checkpoint_before_second_account
test_credit_completion_recovery.py::CreditRecoveryTests::test_final_fetch_credit_reaches_real_failover_in_fast_mode
test_credit_completion_recovery.py::CreditRecoveryTests::test_real_worker_handoff_uses_cloud_checkpoint_and_second_account
test_p2_model_routing.py::TestP2ModelRouting::test_format_model_display_label
test_p2_model_routing.py::TestP2ModelRouting::test_opus5_has_no_ai_chat_model
test_p32_account_password_lookup.py::TestPasswordCardRendering::test_06_banned_state_described
test_p3_regression.py::TestP3RegressionSnapshots::test_opus5_matches_new_contract
test_refactor_parity.py::TestByteParity::test_parts_reassemble_to_original
```

تصنيف لا يبرر تعديل الاختبارات لإخفاء الفشل:

- **ثمانية compact/credit:** الثابت الحالي `COMPACT_TRIGGER_SECONDS=300` في الجسر:2588؛ الاختبارات والسجل السابق يتوقعان 180. يجب حسم العقد الحالي لا إرجاع 180 أو اعتماد 300 صامتاً.
- **ثلاثة routing:** العقد الحالي يربط alias `claude-opus-5` بـ `claude-opus-5-5` و`models=[gpt-4.1]`؛ الاختبارات القديمة تتوقع عقد Opus 5. لا تُعدل عقود المنصة بلا اعتماد/دليل.
- **واحد وصف banned:** `describe_account_state` أصبح يعيد «معزول نهائياً (QUARANTINED)» بدل لفظ «محظور» المتوقع؛ تغيير UX سابق لا دليل فساد لحساب بعينه.
- **واحد parity:** النسخة المجزأة لا تحمل تعديلات الحماية والعزل الموجودة في الأحادي. هذا اختلاف سلوكي، وليس مجرد CRLF.

### بصمات الملفات المقروءة

SHA-256 هنا للبايتات الخام؛ لا تخلطها ببصمة اختبار parity الذي يقرأ النص ويطبّع نهايات الأسطر.

| الملف | عدد الأسطر `splitlines()` | raw SHA-256 |
|---|---:|---|
| `01.33_telegram_gen_bridge.py` | 9285 | `4d0bd7e65fe8fe4e731d54864dcf90b888bc7ca1ba28d27bffea4845c187195d` |
| `01.03Genspark_claude-opus-5-code.py` | 4155 | `52c828d056613a079b0416d4e33c6c170d0b9d0412bc97c6ad112a97b909c9c8` |
| `genspark_verifier_engine.py` | 430 | `59a9caf641ae49c0dc74d9933f1a0f794542982fd477250a0078eb5eb387a3b0` |
| `05.02_genspark_delayed_gifts_manager.py` | 756 | `192d3a3445b280d54b8e8475783a6cbe147e6391a39a137fdeee98387cd7b729` |
| `scripts/rebuild_refactor.py` | 268 | `9dfbde1620c931aaaa7ea94b443651cb44d0bdde6583f4cec7269590f0906795` |

`PARTS` ينتهي عند 9181، مقابل 9285 فعلياً: **104 أسطر** لا 105 على هذا revision. بصمة النص الأحادي في parity: `76a15eb704a208dbd12192b90f77330bafb03400fff42379644172533010ce24`، والمجمع: `3d8b5c776536fba8ecc580192b2bbbaf905799209e211437b060fd9ed2325669`.

## 6. خريطة الاستدعاء الفعلية ومواقع التعديل المحتملة

الأرقام التالية على الأساس فقط؛ يجب إعادة حسابها بعد أي تعديل. لا تعني هذه الخريطة أن الكود تغير.

```text
process_user_task_async
  -> send_message_with_auto_account_failover (3189)
     -> read_accounts_safe (973): لقطة الحسابات مرة عند 3214
     -> claim_eligible_account_for_owner: eligibility ثم claim
     -> reactivate_account_if_due (1070): يكتب قبل preflight
     -> تسجيل journey/span + last_used (3277–3296)
     -> send_message_and_make_public (2833)
        -> قراءة الحساب الحالي والكوكيز (2929)
        -> mod.check_balance (2949–2963): فحص حي موجود فعلاً
        -> refresh_cookies_on_401 (1122) عند الحاجة
           -> master_inspect_and_heal_account (verifier:210)
              -> فحص كوكيز، B2C عند الحاجة، balance/user/subscriptions/retention
           -> إن is_dead: quarantine_account_atomic ثم وسم الأساسي (1151–1173)
           -> إن cookies: حفظ ثم إرجاع؛ fallback إلى mod.do_login
        -> إعادة فحص الرصيد بعد التجديد (2972–2980)
        -> fork / compact / send_chat / monitor / final fetch
     -> LOW_BALANCE / CREDIT_EXHAUSTED / DATA_RETENTION / session / terminal
     -> finally: close_account_timing_span + release_account_selection (3657–3660)
```

| الموضع | الواقع | المطلوب في التصميم المصحح |
|---|---|---|
| `resolve_shared_path:121` و`get_accounts_file_path:957` | أولوية محلي ثم مشترك؛ json_path مخصص | لا تغيير resolver؛ خزائن إخراج بجانب **المسار الأساسي المحسوم فعلاً** |
| `FILE_LOCK:159`، `update_account_data:989` | قفل محلي وملف `.tmp` ثابت | ضم كل كتّاب الحسابات إلى بروتوكول واحد، لا قفل منفصل للعزل وحده |
| `is_account_ready:1025` | يفحص flags/cooldown؛ ليس HTTP checker | إبقاؤه نقياً؛ استبعاد المعزولين عند الاختيار دون تنظيف إقلاع |
| `get_eligible_accounts:1092` | FIFO حسب last_used | sort رصيد مخزن كمؤشر أولوية فقط، ثم فحص حي للحساب المحجوز |
| `reactivate_account_if_due:1070` | يكتب active قبل إثبات الصحة ويتجاهل فشل الحفظ | لا ادعاء تفعيل دائم عند فشل التخزين؛ فصل انتهاء مهلة الفحص عن أهلية الإرسال |
| `refresh_cookies_on_401:1122` | dict أو None يطمس سبب الفشل | مسار نتيجة داخلية مهيكلة؛ wrapper متوافق عند الحاجة؛ تمييز transient عن dead |
| `send_message_and_make_public:2943–2989` | preflight حي موجود، لا gift checker | بوابة موحدة للرصيد/الهدية وتجديد محدود، لا تكرار بالفحص الخارجي |
| failover:3214/3270/3296 | لقطة قديمة وكتابات قبل معرفة transient | إعادة تحقق بعد claim؛ منع إحياء محذوف، تحديد معنى «لا مساس» قبل التطبيق |
| failover:3347/3451/3651 | LOW_BALANCE ثم session ثم generic cooldown | فروع صريحة للمؤقت/المعزول/فشل التخزين قبل generic branch |
| `verifier:119–165` | missing password وبعض كلمات النص => INVALID_CREDENTIALS | نقص محلي ليس موتاً؛ 5xx/429/challenge قبل تحليل مضمون الخطأ |
| `verifier:286–303` | رصيد مجهول يصير 0؛ status غير مألوف يصير inactive/dead | unknown يبقى unknown؛ allowlist فقط للأدلة القطعية |
| `verifier:376–430` | معزل واحد، read failure => []، duplicate => False | حفظ قابل للاسترداد، لا قص مصدر قبل ثبوت الهدف، idempotent نتيجة واضحة |
| `01.03:_maybe_refresh_balance:1093` | يرفع balance إلى 100 بعد مدة | إزالة التخمين في نطاق المحرك المعتمد بعد موافقة النطاق؛ الوقت ليس إثبات رصيد |
| `01.03:pick_account:1190–1336` | `already_checked` مبني على قيمة الرصيد لا حدوث HTTP | `check_balance_before=True` وحده لا يصلح السبب؛ إثبات نتيجة probe في المحاولة |
| `01.03:save_accounts:962` | `.tmp` ثابت؛ بعض المسارات لها OS file_lock | لا ضمان cross-process دون مشاركة جميع الكتّاب للبروتوكول |
| `05.02:483–529` | المصدر يُحفظ قبل المعازل، نتائج الحفظ مهملة | لا تنسخ checkpoint batch إلى المسار الحي |
| `rebuild_refactor:26–39` | حدود قديمة؛ 12 part و14 facade | معايرة كل حدود top-level لا آخر حد فقط؛ فحص normalized parity وimports |

**تصحيح سببي مهم:** التخمين موجود فعلاً في picker الخاص بالمحرك، لكن sender الخاص بالجسر يستدعي `mod.check_balance` بالفعل. لا يصح وصف الجسر بأنه «لا يفحص الرصيد أبداً»، ولا تغيير flag المحرك وحده على أنه إصلاح لمسار Telegram.

## 7. سجل التصحيحات: الصحيح والخطأ وما لا تثبته الأدلة

`P0` = احتمال فقد بيانات أو عزل خاطئ يستوجب الحجب قبل النقل. `P1` = خلل قرار أو دمج أو انحدار. `P2` = دقة توثيق/تشغيل. هذه أولوية تصميم، وليست ادعاء وقوع حادثة حقيقية.

| ID | الحكم والدليل | التصحيح المطلوب |
|---|---|---|
| F01 / P1 | 012345 NOTES:267–272 و451–456 يضعان 1 للمؤهل و0 لغيره في sort تصاعدي | اعكس tier إلى 0 للمؤهل، مع numeric validation؛ لا تنقل الكود المقترح كما هو |
| F02 / P1 | 05.02:408 و012345 NOTES:425 يستخدمان >=14، بينما النص >14 | قارن مدة UTC كاملة بـ `timedelta(days=14)`؛ حد المساواة قرار واضح أدناه |
| F03 / P0 | 05.02:388–400: غياب سجل أو تاريخ تالف => STALE/999 | لا عزل عند جهل الدليل؛ UNKNOWN مع سبب، إلا إثبات اكتمال نافذة كافية |
| F04 / P1 | 05.02:394 sort نصي؛ :402 `.days`؛ :295 now ثابت عند إنشاء المدير | parse timestamps قبل max، ساعة حقن حديثة لكل فحص، عدم إسقاط كسور اليوم |
| F05 / P1 | 05.02:153 يفترض Cairo=UTC+3 دائماً؛ parse قد يرجع naive | UTC-aware للحساب وZoneInfo Africa/Cairo للعرض؛ تاريخ naive/مستقبلي يعامل كغير موثوق دون اختلاق منطقة زمنية |
| F06 / P0 | verifier:160–165 يصنف بكلمات password/incorrect/400 قبل فحص HTTP | 5xx/429/HTML/challenge مؤقت؛ structured allowlist فقط للموت القطعي |
| F07 / P0 | verifier:119 و05.02:364: غياب كلمة المرور قد يعتبر حساباً ميتاً | نقص بيانات محلية => NEEDS_CREDENTIALS، لا Failed ولا حذف |
| F08 / P0 | verifier:298–303: status مفقود أو غير معروف => INACTIVE_ACCOUNT/is_dead | غير المعروف UNKNOWN؛ لا تُحوّل تطور schema إلى عقوبة حساب |
| F09 / P1 | verifier:286–290: non-200 أو balance مفقود => 0؛ :63 يقبل int(bool) | تمييز unknown عن zero؛ finite numeric غير bool مع schema موثق، لا اختيار رقم عشوائي من payload |
| F10 / P1 | verifier:305–365 متغيرات retention/already_cached لا تهيأ في بعض مسارات non-200 | تهيئة صريحة + نتيجة جزئية آمنة؛ لا تحويل بيانات ناجحة إلى NETWORK_ERROR بسبب UnboundLocalError |
| F11 / P0 | verifier:397–404: JSON تالف أو شكل غير list => [] ثم كتابة | افشل دون تغيير أي بايت؛ الملف المفقود وحده يجوز إنشاؤه، والتالف يحتاج إصلاحاً مستقلاً |
| F12 / P0 | 05.02:525–529 يحذف من الأساسي أولاً ويفقد قيم bool للكتابة | الهدف يُثبت أولاً، ثم المصدر؛ خطأ التخزين نتيجة صريحة لا log نجاح |
| F13 / P0 | Lock + replace يضمنان ملفاً واحداً، لا ملفين؛ FILE_LOCK != VAULT_LOCK | معاملة قابلة للاسترداد + أقفال مشتركة لجميع الكتّاب أو تشغيل single-writer معلن |
| F14 / P1 | verifier:407–430: الموجود مسبقاً => False؛ bridge:1160/1171 يتجاهل bool | نتيجة `already_present` سليمة idempotent أو `conflict`، لا خلطها بفشل الحفظ؛ لا ادعاء نقل بلا تحقق |
| F15 / P1 | 01.33:3214 snapshot؛ :2929 غياب الحساب يعطي cookies={} ويمكن login | إعادة قراءة بعد claim؛ غياب/عزل الحساب يمنع إحياءه من snapshot أو كلمة مرور قديمة |
| F16 / P1 | 012345 AFTER يستدعي `gve.check_live_balance` غير المعرف و`sess` غير موصول؛ tuple أسماء متعارضة | واجهات محددة أدناه؛ المقاطع السابقة pseudo-code لا patch جاهز |
| F17 / P1 | 00 AFTER:82 و012345:483 يجعلان كل غير STALE «هدية طبيعية» | فرع HEALTHY مستقل، UNKNOWN/TRANSIENT لا cooldown عقابي ولا عزل |
| F18 / P1 | refresh:1198 fallback يعمل حتى بعد تقرير مؤقت من verifier؛ :1212 و:2988 و:3512 تكتب auth_failed/30m | لا تكرار login عشوائي ولا عقوبة شبكة؛ فصل نتائج التجديد وتمريرها إلى caller |
| F19 / P1 | 01.03:1093–1108 تخمين حقيقي؛ :1298 already_checked يعني رصيداً غير صفري لا probe ناجحاً | لا يكفي تغيير flag أو حذف ثابت وحده؛ فصل scheduled eligibility عن verified balance في كل picker |
| F20 / P1 | PARTS قديمة والأجزاء لا تحمل quarantine protections؛ test parity يفشل | إصلاح baseline وإعادة توليد حدود كل جزء قبل بناء ميزة جديدة، لا آخر رقم فقط |
| F21 / P1 | 012345 PLAN:TASK-301 يناقض 00 NOTES:53 والمحادثة:1162–1163 | حذف startup mutation وTTL وUI الزائدة من الخطة المعتمدة؛ فلترة on-demand فقط |
| F22 / P1 | NOTES القديمة تقترح revival ثم تلغيه؛ 05.02 يحمل revival وsuccess/dead archive | لا استيراد revival أو CLI أو scan-all أو success/dead أو signal handler إلى الجسر |
| F23 / P2 | وصف الأرقام 185/130/279 بأنها حية وملف العزل القديم بأنه «وهمي» | هذه رواية بيئة سابقة غير متاحة؛ الاسم القديم ملف يكتبه الكود فعلاً، لا دليل أنه لم يوجد |
| F24 / P2 | «نسخة مشفرة بـ SHA-256» وrollback متفاوت وRoot paths محلية | SHA بصمة لا تشفير؛ Git revision موحد وتراجع كود منفصل عن بيانات الحسابات |
| F25 / P2 | أربع/خمس اختبارات فقط وادعاء «لا PermissionError 100%» | مصفوفة fault injection وحدود/timing/concurrency؛ لا ضمان Windows من Linux mocks وحدها |
| F26 / P1 | 05.02:61 dependency مفقود؛ :86 يثبت signal handler عند import | نقل parser/probe المحدود لا استيراد البرنامج batch؛ py_compile لا يكفي |
| F27 / P1 | 05.02:352 لا يعيد حراسة auth_status بعد relogin؛ :367 يصفر المجهول | revalidate auth بعد التجديد ثم probe صحيح، لا الانتقال للهدية بناءً على جلسة غير مؤكدة |
| F28 / P1 | 05.02:371 يغير retention حتى dry_run؛ :454 success يجعل stale snapshots تُتخطى | dry-run المحلي ليس read-only على المنصة؛ لا تشغيله في التدقيق، ولا نسخ already_done لبوابة preflight |
| F29 / P1 | 05.02:599 يطبع نجاحاً ولو فشل save؛ backup فقط عند final | نجاح بمقابل commit/readback فقط؛ backup قبل أول mutation لا بعد checkpoints سابقة |
| F30 / P1 | `quarantine_account_atomic` يفرض status suspended ويمسح cookies والرصيد | احتفظ بالحقول المطلوبة للاسترداد اليدوي في خزنة خاصة؛ افصل reason عن status؛ لا طباعة أسرار |
| F31 / P1 | transient «لا مساس» يصطدم بـ reactivate/last_used قبل probe | حسم معنى العبارة: لا حالة/رصيد/تبريد بسبب transient، أو عدم تغيير أي بايت بما فيه attempt telemetry؛ اختبار كلا الفهمين قبل اعتماد أحدهما |
| F32 / P1 | READ-ONLY engine في البروتوكول القديم يقابله Phase4 يطلب تعديله | اطلب اعتماد نطاق محدد لـ picker/checker/writers فقط، لا رفع تجميد المحرك كله |
| F33 / P2 | جملة «الأساسي حسابات جاهزة فقط» غير دقيقة مع cooldown | الأساسي يحتوي غير المعزول بما فيه cooldown؛ readiness ليست مرادف membership |
| F34 / P1 | ادعاء >=100 يغلق الاستهلاك اليدوي تماماً غير صحيح | probe لقطة لحظية لا حجز لدى المنصة؛ نفاد الرصيد أثناء العمل يظل مساراً مطلوباً |

### ما هو صحيح ويجب الحفاظ عليه

- ثلاثة مخازن تشغيل فقط: primary وfailed وdelayed؛ success ليس مطلوباً للبوت.
- فحص الرصيد قبل fork/send موجود وصحيح كموضع؛ الهدية فقط عند رصيد مؤكد أقل من العتبة.
- إعادة استخدام الكوكيز الصالحة وتجديد 401، لا login لكل حساب صالح.
- تبريد 29h عند الرصيد المنخفض **مع دليل هدية حديثة**؛ 500/502/504 ليست موت حساب.
- claims و`finally` وjourney/span والإلغاء ومسارات P16/P18/P20/P35/P40/P42/P43/P44 لها عقود واختبارات يجب ألا تُستبدل بنسخ جديدة.
- الأصل الأحادي مرجع والحزمة مولدة؛ لا تحرير الأجزاء المولدة يدوياً.

### دليل المحاكاة المحلية بعد الاستعادة

أعيد فقط الأمر الذي انقطع، باستخدام AST لاستخراج دوال 05.02 دون import برنامجه، وHTTP mocks، وملف اصطناعي داخل `.tmp` أزيل بعد الفحص. لم تستخدم ملفات أو حسابات حقيقية. المخرجات الفعلية، exit 0:

```text
REFERENCE exactly14 ('STALE', 14)
REFERENCE invalid-date ('STALE', 999)
REFERENCE empty ('STALE', 999)
DOCUMENT_SORT [20, 0, 250, 100]
VERIFIER_502 INVALID_CREDENTIALS
VERIFIER missing-user-status INACTIVE_ACCOUNT True 0
VERIFIER missing-balance EMPTY_BALANCE False 0
CORRUPT_VAULT save_return= True overwritten= True duplicate_return= False
MISSING_DEPENDENCY True
```

هذه **إثباتات عيوب قائمة** وليست اختبارات قبول ناجحة للميزة. الحالة 502 اصطنعت body=`upstream password service unavailable` لإثبات أن كلمة عامة تستطيع تجاوز تصنيف HTTP؛ لا ندعي أن المنصة أرسلت هذا النص بعينه.

## 8. التصميم الحاكم المصحح — مقترح للتنفيذ وليس كوداً منفذاً

### 8.1 المتطلبات المحسومة ومصدرها

| R | المطلوب | مصدر التوجيه | ما يستبعده |
|---|---|---|---|
| R1 | مراجعة قبل تعديل تشغيل، خطة وأماكن واختبارات موثقة | التسجيل 2 و5 و7 و11؛ الطلب الحالي | دمج AFTER القديمة دون فحص |
| R2 | primary + failed + delayed في مجلد الحسابات الفعلي | التسجيل 3 | success/dead archive في الجسر |
| R3 | كوكيز قديمة صالحة، فحص حي قبل الاستخدام، >=100 قابل للإرسال | التسجيل 4 | استعمال cached balance كإثبات أو هدية لكل حساب غني |
| R4 | <100: فحص هدية؛ حديثة => 29h؛ متأخرة مثبتة => delayed | التسجيل 4 | معاملة 1–99 على أنه رصيد مؤهل؛ عزل UNKNOWN |
| R5 | موت قطعي فقط => failed مع السبب والوقت | التسجيل 3 و9 | عزل 502/504 أو نقص محلي أو challenge |
| R6 | لا revival داخل الجسر | التسجيل 6 | زر/أمر/background revive؛ الاسترداد اليدوي ملك المالك |
| R7 | بساطة وعدم تغيير UI/TTL/startup | التسجيل 8، التصحيح بالمحادثة:1162–1163 | sanitize عند الإقلاع، busy UX جديد، scans شاملة |
| R8 | المؤقت ينتقل للتالي دون عزل أو عقوبة حالة | التسجيل 9 | تحويل الشبكة إلى auth_failed دائم/تبريد جزائي |
| R9 | الأصل والمجزأ والتوثيق متوافقون، حفظ قابل للاستئناف | التسجيل 5 و11 والطلب الأخير | نجاح مزعوم دون gate أو نقطة غير مدفوعة |

لا نعيد سؤال المالك عن R6 أو عن success أو عتبة الرصيد الجزئي؛ حُسمت. الأسئلة المفتوحة أدناه تخص الغموض الفعلي أو التعارض مع العقد القديم.

### 8.2 فصل ثلاثة أنواع مختلفة من الحالة

1. **موضع التخزين**: PRIMARY / FAILED / DELAYED. هذه هي Tri-State؛ ليست ثلاث حالات HTTP.
2. **نتيجة الفحص**: READY / LOW_BALANCE_RECENT / STALE_GIFT / DEAD_CONFIRMED / TRANSIENT / UNKNOWN / SESSION_EXPIRED / NEEDS_CREDENTIALS / CANCELLED.
3. **نتيجة التخزين**: MOVED / ALREADY_PRESENT / PENDING_SOURCE_CLEANUP / STORAGE_ERROR / CONFLICT.

الحساب مجهول الرصيد ليس حساباً صفرياً. الحساب المبرد ليس حساباً معزولاً. نجاح حفظ الهدف وحده ليس اكتمال القص. عدم وجود معرّف جلسة ليس دليلاً على حذف المستخدم من المنصة.

### 8.3 واجهات موحدة محددة قبل كتابة الاختبارات

الأسماء التالية **مقترحة وجديدة** وليست ادعاء وجودها:

```python
# genspark_verifier_engine.py — قراءة شبكة فقط، لا كتابة خزائن
probe_live_balance(cookies, *, timeout, cancel_event=None) -> dict
inspect_account_gift_status(session, *, now_utc, threshold_days=14,
                            timeout=25, cancel_event=None) -> dict

# نتيجة الفحص الموحدة (بلا أسرار في detail)
{
    "status": "READY | TRANSIENT | UNKNOWN | SESSION_EXPIRED | DEAD_CONFIRMED ...",
    "balance": None,              # رقم موثوق أو None، لا صفر بديل
    "balance_observed_at_utc": None,
    "reason_code": "...",
    "http_status": None,
    "last_gift_at_utc": None,
    "elapsed_seconds": None,
    "days_without_gift": None,    # للعرض فقط، ليس لاتخاذ قرار الحد
    "evidence_complete": False
}

# جهة التخزين القائمة — لا module جديد بلا ضرورة
move_account_to_vault(primary_path, email, destination_kind,
                      evidence, *, expected_revision=None) -> dict
# destination_kind محدود بـ failed/delayed، وليس مساراً حراً من المستخدم
# نتيجة: status + source_removed + destination_verified + reason_code

# 01.33 — نقطة سياسة واحدة يخدمها preflight وكل relogin path
preflight_account(account, *, mod, bridge_cfg, json_path) -> dict
```

عقد التجديد: تُبقي الدالة العامة `refresh_cookies_on_401` توافق callers إن لزم؛ تضيف helper داخلياً بنتيجة مهيكلة، ويستهلك sender هذه النتيجة، ولا يستدل على DEAD من `None`. لا تُسرّب cookies/password أو رد HTML خام داخل نتيجة تُرسل للوج/Telegram. تُحصر الكوكيز في قناة داخلية غير مسجلة.

**الحدود الرقمية:** رفض bool وNaN وInfinity والسالب كرصيد صالح. الأنواع النصية لا تُقبل إلا بعقد endpoint/fixture موثق. لا truncation يحول 99.9 إلى دليل مختلف؛ السياسة تقارن العدد الحقيقي ثم تنسقه للعرض. `min_preflight_balance` الحالي قابل للضبط؛ يبقى مصدر العتبة الوحيد بدل نسخ 100 في كل helper.

### 8.4 مصفوفة القرار ومخرجات الآثار الجانبية

| نتيجة القراءة | هل يسمح fork/send؟ | فحص gift؟ | كتابة الحساب | الإجراء التالي |
|---|---|---|---|---|
| إلغاء قبل probe | لا | لا | لا عقوبة/عزل | CANCELLED وتحرير claim |
| primary غير مقروء/مخطط تالف | لا | لا | لا | STORAGE_ERROR وتوقف واضح |
| الحساب محذوف/في معزل | لا | لا | لا إحياء | تخطي مع تحرير claim |
| balance موثوق >= threshold | نعم بعد الإلغاء الأخير | لا | تحديث قيمة مرصودة إن حفظت فعلاً | العمل القائم، دون تغيير compact/stream |
| balance موثوق < threshold + gift حديث موثوق | لا | نعم مرة | cooldown=now+29h مع تحقق الحفظ | LOW_BALANCE ثم التالي |
| balance موثوق < threshold + gift متأخر مثبت | لا | نعم | نقل recoverable إلى DELAYED | التالي بعد نتيجة تخزين مقبولة |
| 401 صريح | لا قبل نجاح التجديد والفحص | بعد التجديد وفقط <threshold | كوكيز مؤكدة وفق commit ناجح | تجديد محدود مرة ثم نفس البوابة |
| موت قطعي من دليل مسموح | لا | لا | نقل recoverable إلى FAILED | التالي بعد تحقق التخزين |
| 429 / 5xx / timeout / HTML / Cloudflare | لا في السياسة المقترحة | لا إضافي | لا عقوبة ولا افتراض رصيد | تخطي لهذه المحاولة فقط؛ احترام Retry-After المحدود |
| gift UNKNOWN/غير مكتمل/تاريخ تالف | لا لأن balance المؤكد <threshold | لا تكرار غير محدود | لا عزل ولا cooldown بسبب UNKNOWN | تخطي لهذه المحاولة؛ reason محفوظ دون أسرار |
| لا password لتجديد 401 | لا | لا | لا Failed | NEEDS_CREDENTIALS؛ لا إعادة login لا نهائية |
| فشل write/readback | لا | لا | لا قص مصدر قبل target موثوق | STORAGE_ERROR، حفظ رابط المشروع إن وجد |
| نفاد رصيد أثناء العمل | مسار الاستكمال الحالي | لا فحص gift داخل stream | checkpoint ثم السياسة الحالية | الحفاظ على CREDIT_EXHAUSTED/P20/compact كما يعتمد المالك |

**تغيير صريح يحتاج قرار D2:** العقد القديم يسمح أحياناً بالمتابعة عند balance=-1 بلا عقوبة، أما السياسة المقترحة فتتخطى هذه المحاولة. لا يُطمس التعارض تحت عبارة «لا تغيير سلوكي». لا تثبت READY من cached balance عند probe فاشل.

**HTTP أولاً:** ترفض استجابات 5xx/429/challenge كدليل موت مهما احتوت كلمات `password` أو `suspended`. لا يكفي 403 لإثبات domain_banned. نجاح B2C يُقرأ JSON بنوع status موثق، وليس البحث عن الحرفية `"status":"200"` التي تفشل مع المسافات/الرقم. تحويل الحظر يُقبل فقط من host/path موثقين ضمن التدفق؛ أي URL/HTML غير معروف => UNKNOWN. لا نغير منطق `detect_response_status` العام أو قواعد P35/P40.

### 8.5 الزمن وسجل الهدية

- الوقت المرجعي `now_utc` محقون لكل probe، لا ساعة إنشاء batch. UTC aware في القراءة والمقارنة والتخزين؛ Cairo للعرض فقط عبر `zoneinfo.ZoneInfo("Africa/Cairo")` مع `tzdata` إن لم تتوافر قاعدة النظام.
- المقترح D1: `now_utc - last_gift_utc > timedelta(days=14)`. عند 14 يوماً بالضبط يبقى حديثاً؛ ثانية بعدها متأخر. لا `.days > 14` لأنه يؤخر القرار إلى 15 يوماً.
- اختر أحدث `daily_gift` من timestamps المحللة، لا من ترتيب ISO نصياً. تجاهل أنواع credits الأخرى دون أن تصبح قائمة يومية فارغة دليلاً قطعياً.
- وجود daily_gift حديث صالح يكفي لنفي التأخر حتى لو الأقدم غير مقروء. إثبات التأخر يحتاج إثبات عدم وجود هدية أحدث: pagination/نافذة زمنية/سجل تالف قد تبطل الإثبات.
- list غير موجودة تختلف عن list فارغة. استجابة نجاح ذات قائمة فارغة لا تثبت عمر حساب جديد أو اكتمال سجل المنصة؛ UNKNOWN ما لم يثبت عمر ونافذة كافية من بيانات موثوقة. لا `999` ولا تاريخ مختلق.
- التواريخ naive/المستقبلية/غير القابلة للتحليل => UNKNOWN دون عزل. لا تعالج timestamp مستقبلياً بـ max(0, ...) فتجعله HEALTHY كذباً.
- تنسيق Cairo لا يحدد العتبة؛ تغيير التوقيت الصيفي لا يبدل مدة 14×24 ساعة. عرض reason=`no_history` أدق من «متأخر 999 يوماً».

### 8.6 التخزين: تعافي آمن، وليس «ذرية ملفين 100%»

**مسارات:** احسم primary مرة بواسطة resolver القائم أو `json_path`، ثم اشتق `parent / accounts_failed.json` و`parent / accounts_delayed_gifts_credits.json`. لا تحسم كل اسم على حدة فتخلط local مع parent. لا fallback إلى SCRIPT_DIR عند فشل تحديد الأساسي؛ ولا تحويل مفاجئ لبنية JSON حقيقية لم نرها.

**بروتوكول القراءة:** ملف هدف مفقود يمكن اعتباره مخزناً جديداً. موجود فارغ بايتياً/تالف/شكل غير مدعوم/إيميلات متضاربة => STORAGE_ERROR بلا كتابة. metadata غير المعروفة تبقى محفوظة. تطبيع الهوية `strip().casefold()` للمطابقة فقط؛ لا تغيير كتابة الإيميل الأصلي أو password. duplicates المتعارضة تُرفع CONFLICT ولا تختزل بـ dict comprehension فتضيع بيانات.

**الانتقال الأدنى دون قاعدة بيانات جديدة:**

1. خارج قفل الملفات: claim، probe، جمع الدليل، ثم فحص الإلغاء.
2. داخل قفل مشترك: أعد قراءة primary والهدف وتحقيق أن الحساب/جيل بياناته لم يتغير أثناء الشبكة. لا network ولا Telegram callback داخل القفل.
3. جهز نسخة الهدف كاملة تحتفظ ببيانات الحساب اللازمة للمالك، reason موحد وUTC timestamp وmetadata الهدية. الهدف يرفض وجهة خارج failed/delayed.
4. اكتب target إلى ملف مؤقت فريد **في نفس المجلد**، flush/fsync حسب النظام، replace، ثم readback للتحقق من العضوية والحقول المقصودة. الصلاحيات مقيدة؛ temp/backups أسرار لا تدخل Git.
5. بعد ثبوت الهدف فقط: اكتب primary دون الحساب بالطريقة نفسها. نجاح الاثنين => MOVED. الموجود مسبقاً بنفس البيانات => ALREADY_PRESENT مع تنظيف المصدر المكرر تحت القفل. البيانات المختلفة => CONFLICT.
6. فشل target => المصدر كما كان. فشل primary بعد target => PENDING_SOURCE_CLEANUP؛ نسخة آمنة موجودة، لكن قد يوجد تكرار مؤقت. **الهدف يفوز في الاختيار** فلا يستخدم الحساب. لا تطبع «قص ونقل مكتمل».
7. انقطاع بين الخطوتين: فلترة on-demand بوجود الهدف تمنع الاستخدام؛ استكمال تنظيف **هذا الحساب فقط** عند عملية لاحقة موثقة أو أداة إصلاح يوافق عليها المالك، وليس startup sweep. لا revival من الهدف إلى المصدر.
8. لا تلغِ خطوة المصدر في منتصف transaction بسبب cancel بعد تثبيت target؛ أتمم الخطوة الصغيرة أو سجل pending، ثم حرر القفل والـclaim وأعد CANCELLED. لا rollback تلقائي يعيد المعزول للعمل.

**نطاق الضمان:** هذا تسلسل recoverable ذو نسختين لفترة قصيرة، وليس all-or-nothing بين ملفين. ضمان all-or-nothing حقيقي يحتاج transaction store/journal أو بنية أخرى واعتماداً إضافياً. fsync/replace لا يضمنان كل أنواع network filesystem أو فقد طاقة على كل OS؛ اختبارات crash وبيئة المالك مطلوبة.

**التزامن:** `RLock` ليس علاجاً لتعدد العمليات. يجب اعتماد أحد الخيارين D3:

- single-writer معلن: عملية جسر واحدة لكل primary، إيقاف manager/CLI/نسخ الجسر الأخرى أثناء الكتابة؛ كل threads والnamespace داخل العملية تستعمل قفل الحسابات نفسه، لا FILE_LOCK وVAULT_LOCK مستقلين.
- أو shared OS lock موحد يستخدمه **كل** كاتب، ومنها engine CLI و05.02 وأي أدوات خارجية. لا فائدة من قفل جديد في verifier وحده. هذا يزيد النطاق ويحتاج إذناً وتست subprocess/Windows.

ترتيب الأقفال المقترح: claim منطقي غير ممسوك كـmutex أثناء IO، ثم قفل refresh للإيميل عند الحاجة، ثم قفل المخزن. لا مسار عكسي، ولا hold file lock أثناء HTTP. يُعاد استخدام الأقفال الحالية أو توحيد ملكيتها بدل تكديس قفل فوق قفل non-reentrant. الاستبدال على Windows يمكن أن يفشل: retries محدودة عند PermissionError فقط، ثم فشل صريح بلا فقد المصدر؛ ليس ضمان «لن يفشل أبداً».

**الخزنة القديمة:** لا تكتفِ بتغيير QUARANTINE_FILENAME فتفقد اعتبار المعزولين القدامى. افحص وجود الاسم القديم وأشكاله read-only، وأدرجه في الاستبعاد المؤقت؛ ترحيل منفصل idempotent بعد مراجعة counts/hashes محلياً ونسخة خاصة. لا حذف للقديم ولا نشر بياناته ولا نقل آلي عند الإقلاع. هو مصدر migration legacy، لا خزنة رابعة جديدة للعمل.

### 8.7 حدود المحافظة على المنظومة

- لا نسخ لمنطق البث/polling/compact ولا لمس P18 أو كشف الرفض؛ الضم قبل business send فقط.
- P16 يظل عند أول PID فعلي؛ الفحص يسبقه كما preflight الحالي. لا إبطاء متعمد بخمسين probe قبل اختيار أول حساب.
- العمل في worker القائم لا polling thread. مهلة محدودة لكل HTTP وإلغاء قبل/بعده؛ request synchronous لا ينقطع فورياً في منتصف read إلا بدعم transport. سقف الاستجابة هو timeout المعلن، لا وعد «لحظي».
- probe واحد لكل محاولة وجلسة مؤكدة، والثاني فقط بعد تغير الكوكيز أو 401. لا TTL cache بين الطلبات.
- transient/UNKNOWN لا يدخل progress checkpoint الخاص بنفاد الرصيد ولا يزيد credit_continuations ولا يرسل prompt مرة ثانية.
- كل مسار يحرر claim ويغلق span مرة واحدة. لا `continue` جديد قبل try/finally كما في AFTER المختصرة القديمة.
- رصيد مخزن للفرز ليس حقيقة حية؛ بعد مرور cooldown يعاد الفحص حتى إن القيمة المخزنة 0، وإلا تجوع الحسابات المتجددة.
- «لا مساس» في D4 لا يلغي bookkeeping القائم صامتاً. المقترح ألا تغيّر transient أي ملف حساب؛ تُحفظ attempt telemetry في الذاكرة واللوج المنقح، ثم يؤجل persist إلى إثبات صالح.
- لا يضاف post-success cooldown عام جديد؛ النجاح ليس نفاداً. تبريد maintenance A ثم الانتقال B القائم لا يغيره دمج الهدية.
- حماية الأسرار تشمل `.tmp_*` و`.bak` وملف القفل وجميع خزائن legacy، وليس `accounts*.json` وحده. ignore الحالي لا يحمي كل suffixes؛ يلزم اختبار `git check-ignore` و`git ls-files` قبل أي بيانات حقيقية.

## 9. BEFORE / AFTER المصحح وخريطة التغيير

كل BEFORE أدناه مقتطف أو تلخيص محدد من الأساس §6، وكل AFTER **تصميم غير منفذ، لا patch جاهز**. أسماء helpers الجديدة تحتاج تنفيذًا واختبارات وتعريف imports وعقود callers قبل استخدامها. لا تنسخ المقاطع إلى التشغيل مباشرة.

### C1 — ترتيب الحسابات: `get_eligible_accounts`، الجسر:1104

BEFORE (الواقع): ترتيب last_used فقط. اقتراح 012345 المرفوض يضع tier=1 للمؤهل في sort تصاعدي، فيقدم غير المؤهل.

```python
eligible.sort(key=lambda x: x.get("last_used", 0)
              if isinstance(x.get("last_used"), (int, float)) else 0)
```

AFTER المقترح: `min_balance` يمرر من إعداد العتبة القائم، لا global موازٍ.

```python
import math

def finite_number(value, default):
    return value if type(value) in (int, float) and math.isfinite(value) else default

def account_priority(account):
    balance = finite_number(account.get("balance"), -1)
    used = finite_number(account.get("last_used"), 0)
    return (0 if balance >= min_balance else 1, -balance, used,
            str(account.get("email", "")).strip().casefold())

eligible.sort(key=account_priority)
```

الترتيب مؤشر فقط؛ لا يستبعد صفرًا مخزنًا بعد انتهاء cooldown، ولا يجيز الإرسال قبل probe حي. إعادة القراءة بعد claim تمنع العمل من snapshot قديم (F01/F15/F34).

### C2 — بوابة واحدة: sender:2943–2989 وfailover:3214–3660

BEFORE: `mod.check_balance(cookies)` موجود؛ `<min_balance` يؤدي مباشرة إلى cooldown وLOW_BALANCE، و-1 قد يسمح بالمتابعة. لا gift probe حاليًا.

AFTER (pseudo-code) داخل نطاق try/finally القائم، وبعد revalidation:

```python
result = preflight_account(acc, mod=mod, bridge_cfg=bridge_cfg, json_path=json_path)
if result["status"] != "READY":
    return result.get("public_url"), result["status"], None, None, None
cookies = result["cookies"]  # قناة داخلية فقط، ممنوع تسجيلها
```

يحافظ wrapper على tuple العامة ذات 5 عناصر؛ يجب ربط public_url القائم لا فقده عند فشل الحفظ. يستهلك failover النتائج صراحة قبل generic cooldown. لا تضف continue خارج finally، ولا تعِد إرسال prompt عند TRANSIENT. READY يتطلب probe صالحًا للجلسة الحالية؛ D2 وD4 يحددان التغيير السلوكي (F15–F18/F31).

### C3 — التصنيف: verifier:119–165 و286–303

BEFORE: كلمات `password/incorrect/400` تكفي لـINVALID_CREDENTIALS، وstatus غير معروف قد يصبح is_dead. missing password ليس استجابة منصة أصلًا.

AFTER (helpers مقترحة، ليس API موجودًا):

```python
if response.status_code == 429 or response.status_code >= 500:
    return transient("http_temporary")
if is_challenge_or_untrusted_response(response):
    return unknown("untrusted_auth_response")
body = parse_validated_auth_json(response)
if exact_confirmed_dead_code(body):
    return confirmed_dead(sanitized_reason_code(body))
return unknown("auth_result_unrecognized")
```

تسبق ذلك حراسة transport exceptions؛ parse failure يعيد UNKNOWN لا استثناء يترجم لموت. حدد allowlist من دليل endpoint صالح، لا اختراع أكواد حظر. NEEDS_CREDENTIALS مستقل، وجميع متغيرات retention مهيأة؛ فحص الهدية read-only لا يفعّل retention (F06–F10/F18/F27/F28).

### C4 — حد الهدية: منطق 05.02:376–416 إلى probe محدود في verifier

BEFORE:

```python
days_elapsed = max(0, (self.now_utc - last_dt).days)
if days_elapsed >= self.threshold_days:
    return "STALE", days_elapsed, cairo_time_str, real_balance, last_gift
```

AFTER، بعد parsing والبحث عن أحدث هدية يومية صحيحة والتحقق من الثقة:

```python
elapsed = now_utc - latest_gift_utc
if elapsed.total_seconds() < 0:
    return unknown("future_gift_timestamp")
if elapsed <= timedelta(days=threshold_days):
    return recent_gift(latest_gift_utc, elapsed.total_seconds())
if not history_complete:
    return unknown("incomplete_gift_history")
return stale_gift(latest_gift_utc, elapsed.total_seconds())
```

absence/naive/invalid لا تصل لهذه المقارنة بل UNKNOWN. إذا وُجد تاريخ حديث موثوق مع عناصر أقدم تالفة يمكن نفي التأخر؛ لا يمكن إثباته بسجل ناقص. `ZoneInfo("Africa/Cairo")` للعرض فقط. لا استيراد CLI أو signal handler أو revival من 05.02 (F02–F05/F22/F26).

### C5 — إزالة التخمين: المحرك:1093 و1298 بعد اعتماد D6

BEFORE:

```python
if hours_passed >= cfg.balance_refresh_hours:
    acc["balance"] = cfg.refreshed_balance
already_checked = (bal is not None and bal != 0)
```

AFTER: انتهاء الوقت يجعل الحساب eligible للفحص ولا يغير balance. `already_checked` يستبدل بإثبات probe ناجح **في هذه المحاولة وبنفس جيل الكوكيز**؛ قيمة الرصيد القديمة ليست إثباتًا. إذا لم يوجد الإثبات، نفذ probe مرة؛ unknown يبقى None ويخضع لـD2. لا تغيير stream/payload/decline، ولا نقل flag `check_balance_before=True` وحده باعتباره إصلاحًا (F19/F32).

### C6 — نقل قابل للاسترداد: verifier:376 وbridge:1151–1173

BEFORE: `quarantine_account_atomic(...)` تُهمل نتيجته ثم يُوسم الأساسي؛ batch:525 يحفظ المصدر قبل الهدف.

AFTER (تسلسل تصميم):

```text
strict read under shared lock
 -> validate identity / expected revision / destination conflicts
 -> unique target temp + flush/fsync + replace + readback
 -> source without account + replace + readback
 -> MOVED, or ALREADY_PRESENT if already safely complete
```

target failure => STORAGE_ERROR والمصدر لم يُحذف. source failure بعد target => PENDING_SOURCE_CLEANUP والهدف يمنع الاختيار. لا استرجاع تلقائي من الهدف إلى primary؛ لا اعتبار duplicate مختلف نجاحًا؛ لا استخدام records=[] لتعويض corruption. ضمان all-or-nothing لملفين غير مقدم هنا. البيانات الخاصة تحفظ فقط في خزائن خاصة؛ telemetry يحتفظ reason ووقتًا دون cookies/password (F11–F14/F24/F29/F30).

### C7 — generated parity: `scripts/rebuild_refactor.py:PARTS`

BEFORE: حد نهاية 9181 ومقاطع قديمة، source=9285؛ 104 أسطر فرق على الأساس.

AFTER: حساب **كل** حدود top-level المتأثرة ثم إعادة التوليد من الأحادي، لا تحرير parts يدويًا أو تغيير hash الاختبار ليمر. فحص 12 جزءًا و14 facade وentrypoints وsymbol parity. اختبار read_text الحالي يثبت normalized-source equality؛ إن احتجنا raw-byte parity نضيف معيارًا مستقلًا معلنًا ولا ندعي أنه متحقق الآن (F20).

### C8 — الاستئناف والتوثيق، لا إعادة كتابة التاريخ

BEFORE: أعلى PROGRESS وcurrent_execution يعلنان PR8/1085 green، رغم baseline الحالي الأحمر.

AFTER: أعلى PROGRESS يشير PR9 وهذا التقرير؛ current_execution جديد مع نقل PR8 إلى مفتاح أرشيف واضح. نتائج PR8 التاريخية تبقى بتاريخها، لا تستعمل baseline جديدًا. كل reset يبدأ من remote hash ثم diff؛ أي Edit بلا نتيجة لا يعد منجزًا (F23–F25).

## 10. خريطة المراحل التنفيذية والاعتمادات

هذه checklist **للتنفيذ المستقبلي بعد اعتماد D1–D6**. لا checkbox تنفيذ مغلق: تصحيح الخطة ليس إصلاح runtime. يتبع كل chunk اختبار محدد وcommit وpush والتحقق من remote؛ لا دمج أو deployment ضمن هذه المراجعة.

### E0 — اعتماد وتجميد، قبل أي source edit

- [ ] T00: تسجيل إجابات D1–D6 وGO صريح على revision التقرير.
- [ ] T01: تثبيت schema النتائج والهوية والحقول المحفوظة ومعيار evidence_complete.
- [ ] T02: جرد كل كاتب primary/failed/delayed/legacy واختيار قفل D3 وترتيب الأقفال.
- [ ] T03: تثبيت main/branch والبيئة ونسخة اختبار اصطناعية؛ baseline جديد إن تغير المصدر.

### E1 — إغلاق انحدارات الأساس بعقد معتمد

- [ ] T04: حسم وتنفيذ عقد compact 180/300 دون مساس P18/P35/P40.
- [ ] T05: حسم alias/model payload بالدليل دون تغيير tests لتجميل النتائج.
- [ ] T06: اعتماد وصف banned/quarantined المتوافق مع UX المطلوبة.
- [ ] T07: تصحيح PARTS الحالية وإعادة توليدها؛ full gate/parity أخضر قبل إضافة الميزة.

### E2 — اختبارات تثبت العيب أولًا، بعد E0/E1

- [ ] T08: fixtures اصطناعية للـHTTP/schemas/تعدد صفحات history، بلا أسرار حقيقية.
- [ ] T09: اختبارات numeric/classifier/time boundaries/UNKNOWN.
- [ ] T10: fault injection لكل read/write/replace/readback/crash boundary.
- [ ] T11: worker tests للـclaims/stale snapshot/cancellation/URL/prompt-once.

### E3 — probes والسياسة الخالصة

- [ ] T12: validator رصيد حي finite غير bool؛ unknown مستقل عن الصفر.
- [ ] T13: تصنيف HTTP أولًا، allowlist للموت، missing credentials بلا عزل.
- [ ] T14: gift probe محدود read-only؛ completeness وUTC وD1.
- [ ] T15: إعادة استخدام session/cookies، تجديد محدود، close وفق ملكية session.
- [ ] T16: timeout/cancel budgets وحد أقصى للطلبات، بلا sleep طويل تحت lock.

### E4 — التخزين بعد T02 وT10

- [ ] T17: مسارات مشتقة من primary الفعلي وstrict JSON وحفظ metadata.
- [ ] T18: توحيد الأقفال والكتّاب وفق D3 وحماية temp/backup/secrets.
- [ ] T19: target-first مع readback وexpected_revision وعدم فقد المصدر.
- [ ] T20: idempotency/conflicts/pending cleanup واستبعاد target on-demand.
- [ ] T21: خطة legacy منفصلة read-only ثم migration بعد إذن خاص؛ لا startup sweep.
- [ ] T22: اختبارات crash/restart/subprocess وWindows قبل ادعاء ضمان بيئته.

### E5 — ربط الجسر بعد E3/E4

- [ ] T23: ترتيب validated cached balance ثم claim ثم re-read، لا resurrect من snapshot.
- [ ] T24: preflight موحد قبل fork/send مع tuple العامة والرابط القائم.
- [ ] T25: تجديد 401 مرة واحدة ثم probe الجلسة الجديدة؛ لا fallback بعد transient.
- [ ] T26: فروع نتائج صريحة قبل generic cooldown؛ D2 بلا عقوبة أو credit checkpoint.
- [ ] T27: تنفيذ D4 للـlast_used/reactivate/telemetry والتحقق من الحفظ.
- [ ] T28: finally/span/release مرة واحدة، prompt-once، compact/resume/fast invariants.

### E6 — نطاق المحرك فقط بعد D6

- [ ] T29: إزالة رفع الرصيد الزمني والتعويض التخميني بـmin_balance.
- [ ] T30: إثبات live probe لكل محاولة، لا already_checked من cached balance.
- [ ] T31: ضم writers المختارة إلى D3 دون لمس stream/model/decline.

### E7 — التوليد والقبول، بعد E5/E6

- [ ] T32: معايرة PARTS وإعادة التوليد من مصدر نهائي واحد.
- [ ] T33: py_compile/import smoke للمدخلين والـfacades، بلا networking import side effects.
- [ ] T34: full pytest وcanonical وparity Exit0؛ لا skips/xfails لإخفاء انحدار.
- [ ] T35: نتائج فعلية وتحديث التقرير وPROGRESS/recovery؛ لا تعديل تقرير نجاح يدويًا.

### E8 — التسليم والتشغيل بإذن منفصل

- [ ] T36: تمرين rollback/restart على بيانات وهمية بما فيها pending/conflict.
- [ ] T37: تحقق محلي read-only على inventory منقح بإذن المالك؛ لا تشغيل dry-run القديم الذي يكتب retention.
- [ ] T38: canary حي محدود بإذن منفصل وحدود توقف؛ لا broad migration أو revival.
- [ ] T39: sync، مراجعة diff واختبارات آخر tree، توحيد commits للتسليم عند الحاجة مع حفظ checkpoints، push والتحقق وتحديث PR؛ لا merge تلقائي.

**ترتيب الاعتماد:** E0 → E1 → E2 → E3/E4 → E5/E6 → E7 → E8. يمكن تصميم E3/E4 بالتوازي، لكن لا ربط نقل حساب قبل نجاح E4، ولا ادعاء اكتمال runtime قبل E7. T38 لا يبرر تشغيلًا حيًا الآن.

## 11. مصفوفة اختبارات القبول والتتبع

**الحالة لجميع X01–X30: مخطط، غير منفذ كاختبار ميزة.** محاكاة §7 تثبت عيوب الأصل فقط. تستخدم الاختبارات ساعة محقونة وHTTP mocks وملفات اصطناعية في temporary workspace؛ لا خزائن حقيقية، ولا نقل logs تحتوي أسرارًا إلى Git. في اختبارات النقل قارن هوية ومحتوى الحسابين والمصدر/الهدف قبل وبعد، لا return value فقط.

| X | المدخل/العطل المحقون | النتيجة ومعيار القبول | F → T |
|---|---|---|---|
| X01 | cached balances: 20,0,250,100؛ ties/last_used/bool/NaN/None | 250 ثم100 ثم20 ثم0 للأرقام السليمة؛ قيم شاذة لا تسبق المؤهل؛ cached ليس إذن send | F01 → T09,T23 |
| X02 | live: 0,1,99.9,100,250؛ threshold مختلف | <threshold لا fork/send؛ >=threshold READY دون gift؛ config مصدر واحد | F09,F34 → T12,T24 |
| X03 | missing balance/negative/bool/NaN/Infinity/schema آخر | UNKNOWN لا صفر، لا cooldown أو vault، لا رقم منتقى عشوائيًا | F09,F19 → T09,T12,T30 |
| X04 | HTTP429/500/502/504، timeout، HTML؛ body يحوي password أو suspended | TRANSIENT/UNKNOWN، لا DEAD ولا حذف/عقوبة؛ Retry-After محدود | F06,F08,F18 → T13,T16,T26 |
| X05 | auth JSON صالح مع status رقم/نص موثق ومسافات؛ code موت مسموح؛ 403 مجهول | نجاح وفق schema؛ موت فقط بالدليل المعتمد؛ 403 وحده UNKNOWN | F06,F08 → T08,T13 |
| X06 | password مفقود؛ status مفقود/جديد؛ user endpoint فاشل | NEEDS_CREDENTIALS أو UNKNOWN؛ عدم نقل failed؛ لا UnboundLocalError | F07,F08,F10 → T09,T13 |
| X07 | كوكيز صالحة، 401 ثم نجاح، 401 مكرر، verifier transient | صفر login للصالح؛ تجديد واحد فقط؛ probe جديد للجلسة الجديدة؛ لا fallback متكرر | F18,F27 → T15,T25 |
| X08 | gift عند 14d-1s،14d،14d+1s مع history كامل | وفق D1 المقترح: حديث/حديث/متأخر؛ الاختبار النهائي يتبع الاعتماد المسجل | F02,F04 → T09,T14 |
| X09 | ISO offsets مختلطة، ترتيب عكسي، عدة أنواع credits | أحدث daily_gift حسب UTC لا النص؛ غير اليومية لا تؤثر على max | F04 → T08,T14 |
| X10 | absent/empty/malformed/naive/future timestamps | UNKNOWN بلا999 ولا اختلاق عمر؛ لا delayed؛ recent صالح ينفي stale عند دليل موثوق | F03,F05 → T09,T14 |
| X11 | pagination ناقصة/صفحة فاشلة/نافذة قصيرة؛ recent في صفحة لاحقة | لا STALE دون اكتمال كافٍ؛ لا loop غير محدود؛ recent ينفي التأخر | F03,F04 → T08,T14,T16 |
| X12 | تواريخ القاهرة شتاء/صيف وتغير DST | عرض ZoneInfo صحيح وelapsed UTC ثابت؛ timezone database الغائبة خطأ واضح لا offset مختلق | F05 → T09,T14 |
| X13 | low+recent؛ low+stale؛ low+unknown | cooldown29h فقط للأول؛ delayed للثاني بعد حفظ موثوق؛ الثالث تخطي بلا عقوبة | F02,F17 → T14,T24,T26 |
| X14 | primary تالف/فارغ بايتياً/unsupported؛ target مفقود أو تالف | المفقود فقط قابل للإنشاء؛ التالف STORAGE_ERROR ولا تغيير بايتات الملفين | F11,F12 → T10,T17 |
| X15 | write/flush/fsync/replace/readback للهدف تفشل، disk full/permission | المصدر لا يُحذف؛ نتيجة صريحة؛ لا success log؛ temp آمن ولا سر في telemetry | F12,F13,F29 → T10,T18,T19 |
| X16 | target ناجح ثم source write/readback فاشل أو crash بينهما | PENDING_SOURCE_CLEANUP؛ نسخة الهدف قابلة للقراءة وتمنع الاختيار؛ restart لا revival | F12–F14 → T10,T19,T20,T36 |
| X17 | إعادة نقل identical، duplicate casefold، بيانات متعارضة أو وجهة ثانية | idempotency للحالة المطابقة؛ CONFLICT للمختلفة؛ لا overwrite أو تجاهل سجل | F11,F14 → T10,T17,T20 |
| X18 | threadان/namespaceان؛ subprocess كاتب؛ lock order؛ Windows replace busy | لا lost update/deadlock؛ أو رفض تشغيل writer ثانٍ وفق D3؛ retries محدودة | F13,F25 → T02,T18,T22,T31 |
| X19 | primary محلي ثم parent ثم json_path مخصص؛ targets legacy | الخزائن بجوار primary المحسوم؛ لا خلط folders؛ legacy يمنع الاختيار دون startup write | F21,F23 → T17,T20,T21 |
| X20 | حذف الحساب أو تغير credentials/revision بين snapshot/probe/commit | لا إحياء ولا login من snapshot؛ CONFLICT أو إعادة فحص محدودة؛ claim يحرر | F15 → T11,T19,T23 |
| X21 | إلغاء قبل/أثناء probe وقبل/بعد target commit؛ exception بكل فرع | لا business send بعد الإلغاء؛ span/release مرة؛ transaction آمنة أو pending | F15,F16 → T11,T16,T28 |
| X22 | probe transient بعد last_used/reactivate candidate | سياسة D4 معتمدة؛ المقترح hashes ملفات الحسابات ثابتة؛ لا auth_failed/credit continuation | F17,F18,F31 → T11,T26,T27 |
| X23 | فشل حفظ cooldown/cookies/updated balance أو استنفاد الحسابات | لا نجاح حفظ مزعوم؛ وقف آمن مع الرابط الموجود؛ لا إرسال مكرر | F14,F29 → T11,T24,T27,T28 |
| X24 | تقدم ساعة balance_refresh_hours؛ cached nonzero؛ probe=-1 | لا زيادة رصيد بالزمن؛ cached لا يساوي already_checked؛ D2 واضح | F19,F32 → T29,T30 |
| X25 | import checker، dry-run، session مملوكة أو مستعارة | لا signal/CLI/revival/retention POST؛ close المملوك فقط؛ لا dependency مفقود | F22,F26–F28 → T14,T15,T33 |
| X26 | P13/P17/P23/P25/P29/P30/P16/P18/P20/P35/P40/P42/P43/P44؛ compact A→B | العقود القائمة محفوظة؛ prompt مرة؛ fast دون artifact APIs؛ نفاد أثناء العمل يبقى مدعومًا | F16,F34 → T04,T11,T28,T34 |
| X27 | regenerate ثم compile/import/parts/facades؛ full suite | normalized parity و11 tests الحالية وكل البوابات Exit0؛ لا تعديل assertions للإخفاء | F20,F25 → T07,T32–T34 |
| X28 | temp/backup/legacy paths؛ injected secrets في synthetic fields | git check-ignore وgit ls-files؛ لا أسرار في tracked diff/logs/errors؛ صلاحيات خاصة | F24,F30 → T18,T35,T37 |
| X29 | بيانات خزائن بها cookies/metadata غير معروفة | حفظ حقول الاسترداد دون فرض suspended أو balance0 بلا دليل؛ لا تسريب للواجهة | F30,F33 → T01,T17,T19 |
| X30 | reset بعد commit وقبل push وبعده؛ rollback كود مع pending vault | الاستعادة من remote verified لا وعد محلي؛ لا استرجاع primary قديم يعيد المعزول | F23–F25,F29 → T35,T36,T39 |

**تغطية كل finding:** F01→X01؛ F02→X08/X13؛ F03→X10/X11؛ F04→X08/X09/X11؛ F05→X10/X12؛ F06→X04/X05؛ F07→X06؛ F08→X04–X06؛ F09→X02/X03؛ F10→X06؛ F11→X14/X17؛ F12→X14–X16؛ F13→X15/X16/X18؛ F14→X16/X17/X23؛ F15→X20/X21؛ F16→X21/X26؛ F17→X13/X22؛ F18→X04/X07/X22؛ F19→X03/X24؛ F20→X27؛ F21→X19؛ F22→X25؛ F23→X19/X30؛ F24→X28/X30؛ F25→X18/X27/X30؛ F26→X25؛ F27→X07/X25؛ F28→X25؛ F29→X15/X23/X30؛ F30→X28/X29؛ F31→X22؛ F32→X24؛ F33→X29 ومعيار readiness في §8؛ F34→X02/X26.

## 12. القرارات المفتوحة D1–D6 — قبل GO للتنفيذ

| D | موضع الغموض | التوصية المحددة | ما يمنعه عدم الحسم |
|---|---|---|---|
| D1 | >14 بالنص مقابل >=14 في السكريبت | مدة UTC كاملة **أكبر من14×24h**؛ عند14بالضبط حديث | دمج predicate النهائي واختبار X08 |
| D2 | baseline يسمح أحيانًا بالمتابعة عند -1؛ التوجيه الجديد يطلب تخطي المؤقت | لا send بلا balance موثوق؛ تخطي المحاولة دون عقوبة أو تغيير credit state | تغيير مسار -1/UNKNOWN بالجسر والمحرك |
| D3 | عملية واحدة أم عدة writers للملفات نفسها | البداية single-writer معلن وقفل موحد داخل العملية؛ إن لزم التزامن بين العمليات فاعتماد كل writers وقفل OS مشترك | أي ادعاء أمان نقل أو تشغيل أدوات متزامنة |
| D4 | «لا مساس» قد تعني no penalty فقط أو عدم كتابة أي بايت | transient لا يكتب ملفات الحسابات، حتى last_used/reactivate؛ telemetry بالذاكرة/log منقح | نقل bookkeeping القائم واختبار hashes |
| D5 | 13 failure سابقة: compact180/300، Opus5/5.5/payload، لفظ banned | قرارات منفصلة موثقة: هل تُستعاد عقود PR8 أم تُعتمد التغييرات اللاحقة؟ لا نفترض صحة المصدر أو test تلقائيًا | إصلاح E1 واعتماد baseline أخضر |
| D6 | تجميد المحرك القديم مقابل ضرورة إصلاح picker/writers | إذن محدود لـbalance/picker/writers واختباراتها؛ stream/model/decline خارج النطاق إلا D5 المنفصل | تنفيذ E6، لا يبيح refactor شاملًا |

**صيغة رد مقترحة للمالك:** «أوافق D1/D2/D3/D4 كما في الجدول؛ D5 compact=…، model/alias/payload=…، وصف banned=…؛ أوافق/أرفض D6؛ GO للتنفيذ على revision …». لا تستنتج هذه الإجابات من كلمة «تابع» التي طلبت استعادة المراجعة غير المكتملة. R1–R9 التي حسمها المالك أصلًا لا يعاد فتحها.

## 13. المخاطر والتراجع وخطة الاسترداد

### 13.1 حدود المخاطر وشرط التوقف

- P0: عزل مؤقت كميت، فقد الحساب عند نقل متعدد الملفات، overwrite خزنة تالفة، lost update من writers متزامنة. تمنع E4/E5 حتى إثبات X04–X06 وX14–X20.
- P1: تجويع حساب برصيد مخزن0، re-login متكرر، تسريب claim، timeout غير محدود، تكرار prompt، كسر compact/model/parity. تمنع E7 حتى X01/X07/X20–X27.
- P2: وثيقة قديمة تُقرأ كحالة حية، timestamps محلية أو raw secrets في logs. تمنع التسليم الصحيح حتى X12/X28/X30.
- STOP عند تغير P18 أو رفض/stream دون اعتماد، أو unexpected writer، أو JSON corruption/conflict، أو دليل DEAD غير معتمد، أو اختلاف gate عن baseline. لا «إصلاح» بالتصفير أو حذف البيانات أو زيادة retries بلا حد.

### 13.2 تراجع هذه المراجعة فقط

لا تغييرات runtime أو حسابات كي تتراجع عنها. إزالة/عكس تغييرات وثائق PR9 فقط ممكنة بعد طلب المالك عبر revert لمراجعة docs، لا `reset --hard` على workspace فيه عمل آخر. لا تسترجع source من anchors القديمة ولا تمس وثيقة أضافها المالك إلى main أثناء المراجعة.

### 13.3 تراجع تنفيذ مستقبلي — الكود منفصل عن البيانات

1. قبل أي canary، وثق revision الكود **المعتمد والأخضر**، ومداخل monolith/package، والبيئة، وإعداد single-writer/lock. الأساس `92f658e` أحمر فلا يسمى safe production rollback تلقائيًا.
2. أوقف قبول jobs الجديدة والكتّاب الخارجيين بطريقة الإغلاق القائم؛ لا تقتل عملية في منتصف commit إلا في تجربة crash اصطناعية. احتفظ بالرابط ونتيجة العملية الحالية.
3. نسخة خاصة من **كل** الخزائن ذات العلاقة قبل أول mutation، مع permissions وحصر identities/counts/checksums منقح محليًا. SHA-256 تحقق سلامة لا تشفير. النسخ لا تدخل Git أو تعليقات PR.
4. ارجع مجموعة source + generated + schema readers المتوافقة كوحدة واحدة إلى revision المختبر المعتمد. لا تستخدم checkout شاملًا يمس تغييرات المستخدم الأخرى.
5. **لا تسترجع primary قديمًا وحده**: قد يعيد حسابًا معزولًا أو يضيع updates لاحقة. اقرأ source/targets/legacy read-only، وأكمل pending بإجراء موجه معتمد؛ target precedence يظل قائمًا.
6. إن كان الكود القديم لا يعرف target precedence أو schema الجديد، لا تشغله مباشرة على البيانات المنقولة. حافظ على الإيقاف حتى تحويل/توفيق يدوي معتمد واختبار X30؛ rollback code ليس rollback data تلقائيًا.
7. تحقق من عدم فقد أي identity ومن عدم جاهزية حساب معزول؛ شغّل البوابات offline، ثم إذن منفصل لإعادة التشغيل ومراقبة canary. لا revival آلي بحجة rollback.

### 13.4 Runbook الاستئناف بعد reset

```bash
cd /home/user/webapp && pwd
# قراءة فقط أولًا؛ لا تحذف تغييرات محلية
git status --short --branch
git log -5 --oneline
git ls-remote origin refs/heads/main refs/heads/genspark_ai_developer
git diff --stat
```

ثم اقرأ رأس PROGRESS وهذا التقرير وcurrent_execution في recovery JSON. إن كنت على main وشجرتك نظيفة: fetch ثم switch للفرع الموجود (أو tracking إذا غاب محليًا). إن وجدت تغييرات غير ملتزمة افحصها واحفظها دون overwrite؛ لا تعِد Edit من الملخص عميانيًا. قارن عناوين الأقسام وgit diff لتحديد ما وصل فعليًا.

لكل دفعة: scope diff → فحص المحتوى → commit → fetch/main sync مع حفظ تغييرات المالك → push → مساواة `git rev-parse HEAD` مع `git ls-remote` → تحديث PR9. إذا لزم rebase/squash، تحقق من رأس الفرع البعيد واستخدم lease صريحًا، لا force أعمى؛ تحقق من tree قبل/بعد squash. لا تكتب hash commit الجاري داخل نفسه؛ سجل آخر نقطة مؤكدة ثم استعمل PR/remote لاكتشاف رأس التسليم.

### 13.5 سجل الاستعادة وحدود الإثبات

- نقاط قديمة مؤكدة قبل reset: 491256c،85fd33e،6f2f25d،a06218c. أعيد a06218c فعليًا في هذه الجلسة؛ §9/§10 المنقطعتان لم تكونا موجودتين.
- أثناء sync تقدم main من92f658e إلى **a181f35** بإضافة ملف `012345_arena-ai_مراجعة_وخطة_دمج_الهدية_الشاملة.md` فقط. حُفظ كما هو؛ لم يُراجع محتواه ضمن المصادر الثمانية، ولا يوصف بأنه معتمد أو مكافئ لهذا التقرير. لا تغير Python بين الأساسين.
- أعيدت commits المراجعة فوق main الجديد دون تعارض؛ checkpoint الأقسام9/10 **d969e3814e12be77e90d640e557b7d2eea9bf620** دُفع بـlease على a06218c وتحقق remote. تغيرت hashes القديمة بفعل rebase؛ لا تعتمدها كرأس حالي.
- الأدلة offline على Linux؛ لا تشغيل Windows فعلي، ولا حسابات حقيقية، ولا Genspark/Telegram حي، ولا deployment. اختبارات mocks لا تثبت schema جميع ردود الإنتاج أو متانة filesystem عند فقد طاقة.
- لا تدعي قراءة الوثيقة الجديدة أو نجاح اختبارات X المخططة أو تنفيذ T00–T39. التقرير يميز نتيجة المراجعة عن readiness للإنتاج. PR9 يبقى Draft حتى المراجعة والقرارات.

## 14. سجل التحقق والتسليم النهائي للمراجعة

أعيدت الاختبارات بعد آخر reset وعلى Python المطابق للأساس، بتاريخ 2026-10-29، قبل تحديث سجل التسليم:

| الفحص المعاد | نتيجة Terminal الفعلية |
|---|---|
| py_compile للملفات الخمسة في §5 | Exit0 |
| full pytest، no cacheprovider | **1072 passed، 13 failed، 60 subtests passed، 5.44s، Exit1** |
| parity فقط | **10 passed، 1 failed، 0.40s، Exit1**، نفس البصمتين في §5 |
| canonical hadith_sijil | **1085 tests، failures=13، 3.103s، Exit1** |

الأخطاء الـ13 هي نفس قائمة §5. فشل البوابة ليس أثر تعديل جديد ولا نجاحًا يمكن إغلاقه؛ لا يعدل التقرير المولد للبوابة لإظهاره أخضر. لوجات التشغيل المعاد `.tmp/audit_*.log` محلية ignored وقد تفقد بعد reset؛ النتائج محفوظة هنا.

**نطاق تسليم PR9:** هذا التقرير + رأس PROGRESS + recovery JSON فقط. يظل Python والاختبارات وgenerated والحسابات دون تعديل عن main. نُقلت current_execution القديمة إلى completed_pr8_execution مع الحفاظ على محتواها؛ بقية سجلات recovery القديمة تاريخية كما يوضح المفتاح الجديد. لم يُعَد تنفيذ PR8 ولم تغير عقود model/compact.

**فحص الوثائق قبل النشر:** UTF-8 وJSON، روابط المصادر المحلية، اكتمال معرفات F01–F34/T00–T39/X01–X30/D1–D6، عدم إدخال secret prefixes، حفظ أرشيف PR8، git diff --check، وقصر diff على الملفات الثلاثة. ينفذ validator قبل commit؛ إخفاقه يمنع النشر. بعد sync/squash يلزم تطابق tree والتحقق من head البعيد وPR9؛ إذا انقطع النشر يستكمل دون تكرار المراجعة.

**حكم التسليم الأول (تاريخي؛ انظر تحديث §15):** تصحيح المراجعة والخطة مكتمل، وليس الميزة. التوقف التالي عند اعتماد §12، ثم T00 وتثبيت baseline معتمد. لا merge/deployment/live أو تنظيف/إحياء خزائن. README والبروتوكولات التاريخية ذات أرقام974 لا تستبدل نقطة الاستئناف الجديدة أو نتائج §5/§14.

## 15. المراجعة الإضافية: Arena وتحديثات الوكلاء عند d2eb49d

### 15.1 النطاق والتسلسل وحجية الأدلة

هذا القسم تحديث حاكم على الأحكام التاريخية في §0–§14 عند التعارض، وليس إذن تنفيذ. أضيف [تقرير Arena](../012345_arena-ai_مراجعة_وخطة_دمج_الهدية_الشاملة.md) إلى المصادر الثمانية. استعيد الفرع من `d072816` بعد reset جديد؛ main بقي `d2eb49d9e72ac18f213c48e432ecdab765583b16`. مزامنة main داخل فرع المراجعة لا تعني دمج PR9 في main.

- Arena موجود منذ `a181f35` ولم يتغير في d2eb49d؛ الإضافة الأخيرة تعدل وثائق00/012345 والأرشيف فقط. لا تغيير Python بين أساس التحقيق والمصادر الجديدة.
- اكتملت قراءة ذيل الأرشيف3514–4276 وملحق Arena D1855–1884؛ ثبت تطابق Arena1–1884 حرفيًا مع الأرشيف1630–3513. التكرار ليس شاهدًا مستقلًا.
- نصوص التفريغ منقولة عن الوثائق؛ التسجيلات الأصلية ودستور بولا/skill الأصلي غير متاحين. لا شهادة «حرفي100%» ولا حكم مخالفة قواعد خارجية لم نقرأها. اختلاف صياغة التسجيل11 محفوظ في Arena1880 ولا نصححه بالتخمين.
- الأرشيف3851–3862 و4035–4043 ينقل طلب المقارنة بلا اتباع أعمى، و3947–3951/4219–4230 يميز ملكية00 و012345. نحافظ على ملفاتهم؛ تقريرنا وسجلنا فقط قابلان للتعديل هنا.
- نسبة Arena إلى PR8 في الأرشيف3866–3869 ليست مرجعًا صحيحًا لعملنا: PR8 سجل compact السابق، PR9 هذه المراجعة، وArena ملف مستقل على main. لا نستنتج هوية مؤلف commit من اسم وكيل في حوار.
- ادعاء أن الخطة «محصنة100%» أو أن التجميد دليل اختبار بلا regression (الأرشيف3823–3824،4127–4128،4257) غير مسند؛ عدم تعديل التشغيل لا يثبت سلامة تنفيذ لم يبدأ.

### 15.2 حقائق جديدة تحققنا منها من المصدر، قبل المحاكاة

| الموضع | الملاحظة المثبتة | التصحيح المطلوب في الخطة، لا الكود الآن |
|---|---|---|
| الجسر583–600 | `claim_eligible_account_for_owner` يأخذ أول خمسة ثم `random.choice` | C1 يصلح ترتيب القائمة فقط؛ لا يضمن اختيار الأعلى. فصل سياسة الفرز عن شرط live balance؛ لا تغيير العشوائية بلا قرار |
| الجسر2324–2331،4608–4616 | الفلتر الحالي يحمي archives و`.failed` و`.env*` وprimary/Qwen/DeepSeek/keys، والنداء يمرر `item.name` | وسّع الحماية مع حفظ القائمة الحالية؛ `.gitignore` ليس بديلًا لمسار snapshot/REST |
| 012345 NOTES742–767 | BEFORE لا يطابق الفلتر الحالي؛ AFTER يستبدل القائمة ولا يحفظ الاستثناءات القائمة | لا نسخ حرفي؛ المقارنة مع current source إلزامية. لا ننسب حماية registry للفلتر الحالي، فهو لا يحميها هنا |
| rebuild181–216 | coverage قبل `rmtree`؛ تحليل أجزاء AST بعد حذف OUT وكتابة كل جزء | الخريطة الأصلية تفشل قبل الحذف، لكن إصلاح النهاية وحدها قد يصل للحذف ثم يفشل. staged validation لكل الأجزاء قبل أي استبدال |
| Qwen290–314 | `password_hash` يمرر إلى حقل `password` في signin | الاسم ليس ضمان تشفير/أمان. لا إعادة طباعة القيم أو اختبار صلاحيتها |
| uploader915–916 | GitHub credential مضمّن في clone URL | خطر انكشاف محلي/في remote؛ لم نشغّل uploader ولم نثبت تسريبًا حيًا |
| الجسر196–216 و6338–6354 | بوابة المحادثة تسمح مجموعات في حالات معينة، وكارت الحساب يعرض password | يلزم تتبع مسار الإرسال وحراسة مستقلة قبل وصفه آمنًا للمجموعات؛ لا تجربة Telegram حيّة |

**تصحيح أمني للوثائق:** التوكن المرسل في هذه المحادثة GitHub PAT؛ إلغاؤه من إعدادات GitHub لا BotFather. BotFather يخص توكن بوت Telegram. ادعاء وجود نفس التوكن في `.env` في الأرشيف3908 لم نتحقق منه. لا قيمة سرية تُنسخ إلى التقرير أو سجل الاستعادة.

### 15.3 التحقق المستقل المعاد في هذه الإضافة

أُجريت التجارب التالية بعد استعادة d072816، على المصدر نفسه، بلا تشغيل05.02 أو حسابات فعلية. استُخرجت دالتا الفلتر والاختيار بالـAST دون تشغيل الجسر كاملًا؛ استُخدمت أسماء اصطناعية وحقن تبعيات. ملفات تجربة المولد تحت `.tmp` فقط، مع مقارنة SHA-256 لجميع ملفات الحزمة الحقيقية قبل/بعد؛ لم تتغير.

| التجربة | النتيجة الفعلية | حدود الإثبات |
|---|---|---|
| الفلتر الحالي مقابل AFTER في012345 NOTES | سبعة أسماء محمية حاليًا أصبحت مسموحة: primary،Qwen،DeepSeek،keys،`.env.production`،`bundle.tar.gz`،`bundle.failed` | عيب في المقترح، لا تغيير مطبق ولا إثبات رفع أسرار بالفعل |
| تغطية الفلترين | كلاهما سمح `dead_accounts.json` و`telegram_bot_token.txt` و`accounts_genspark.json.tmp_1234`؛ AFTER منعfailed/delayed و`.bak` | `.tmp` suffix لا يمسك `.tmp_*`؛ يلزم حفظ الاستثناءات القديمة وإضافة الجديدة |
| دالة claim الفعلية، قائمة مرتبة500/400/300/200/50، وchoice محقون ليختار الأخير | اختارت50 وأرجعتclaimed | يثبت أن sort لا يفرض الأولوية. لم ننفذ preflight/send ولا نقول إن50 أُرسل فعليًا |
| rebuild الأصلي مع OUT مؤقت وعلامة قديمة | `التغطية 9181 ≠ إجمالي الأسطر 9285`؛ العلامة بقيت | الفشل الأصلي قبل الحذف؛ لا نكرر الادعاء أن هذا الاستدعاء يمسح الحزمة |
| تغيير نهايةp12 فقط إلى9285 في الذاكرة، OUT مؤقت | فشلp03: `'(' was never closed` عند سطر652 للجزء؛ العلامة حُذفت وبقيت3parts | يعيد مستقلاً تجربة Arena؛ لا يكفي إصلاح آخر رقم، ويجب تحليل كل الأجزاء قبل الاستبدال |
| AST لـQwen | أربع سجلات literal ذاتemail/password_hash غير فارغ في198/205/212/219 | لم تُطبع القيم. مع مسار290–314 تُعامل كاعتمادات منشورة تحتاج إلغاء/تدوير من المالك، لا فحص صلاحيتها |
| خمسcompact وثلاثcredit tests، نفس الاختبارات مرتين | الثابت300:8fail/0error؛ حقن180 في الذاكرة:8pass؛ رجع الثابت300 بعد التجربة | network socket محظور في التجربة وtransport mocked. تشخيص اعتماد الاختبارات على الحد، لا تعديل سياسة ولا إصلاح production |

المسار الأمني لكارت كلمة المرور اكتمل تتبعه: بوابة callback عند7890 ثم `acc_view`8708–8723 يرسل إلى نفسchat_id؛ ومسارmessage عند8745 ثم8794–8803 كذلك. مع سماح196–216 بالمجموعات، يوجد **مسار ممكن لإرسال الكارت إلى مجموعة مسموحة**. لا دليل هنا على أن مجموعة فعلية استلمت كلمة مرور. المعالجة الأمنية المنفصلة المقترحة: هوية مستخدم مصرح بها مع وجهة خاصة، دون تغيير مجموعات باقي البوت عشوائيًا.

**البوابات أعيدت فعليًا، وليست نقلًا عن Arena:**

- py_compile للملفات الخمسة الواردة في§14: Exit0.
- كامل pytest: **1072passed،13failed،60subtests،9.37s،Exit1**؛ نفس أسماء§5.
- parity: **10passed،1failed،0.36s،Exit1**؛ المقارنة الحالية normalized text عبرread_text، لا إثباتraw-byte identity.
- canonical: **1085tests،13failures،3.064s،Exit1**؛ فحصdocs اجتاز، ولم تُكتب وثيقة نجاح جديدة.
- اللوجات `.tmp/arena_pytest.log` و`arena_parity.log` و`arena_gate.log` محلية ignored وقد تضيع بعدreset؛ النتائج الجوهرية محفوظة هنا.

لم نُعِد كل مخزون Arena العددي202/115/61 أو فحصHAR لكلrecharge_logs؛ تبقى هذه أرقامًا منسوبة لمراجعته علىrevisionالمذكور، لا شهادة تدقيق دلالي منا. كذلك لم نُعِد كل محاكاةbackup/lost-write في ملحقه. ملحقC مفلطح في أسطر Markdown طويلة؛ لم نشغّله بالنسخ الأعمى، بل أعدنا التجارب المحددة أعلاه من المصدر الفعلي.

### 15.4 المقارنة المنصفة وما يلزم تصحيحه

| المصدر | ما أصاب فيه | ما أخطأ فيه أو يلزمه تقييد/تحديث |
|---|---|---|
| Arena،65/75/89–90/120،§9 وQ1–Q8 عند554–562 | نقد05.02، حمايةUNKNOWN، استبعادimport، مخاطرالمزامنة، randomfirst5، تجميد01.03 مبدئيًا، وتصحيح أحكامه السابقة عنrebuild وREAD_FAILED والأسرار | أحكامه القديمة التي اعترف بها لا تبقى أدلة: لا تشغيلrebuild مباشرة ولا إثبات فقد مشروع حي من3mocks. حد>=14 قرار منقول عن المالك في ملفه، يتعارض مع خلاصات أخرى؛ لا نختار أحدهما خفية |
| أحدث00/012345 PLAN | TASK301 صارclaim-time read-only بدلstartup، Phase4 تجمد01.03، TASK503 تطلبstaging؛ تطور صحيح يستحق إثباته | TASK103/303>=14 بينماD1>14؛ أرقام9286/105 القديمة باقية؛ RLock وحده لا يوحد الكتّاب. لا يكفي وصف«حسمD1–D6» لإزالة تناقضالأمثلة |
| 00 PLAN235،254–267،283؛012345 NOTES666–693/717–737 | تتجه للفصل بينtemporary/permanent وtarget-first | حذفrefreshed_balance يناقضfreeze؛ `else→cooldown` يصنفUNKNOWN كـrecent؛ AFTER Lock يخالفTASK202RLock؛403عام ليسbanned؛AUTH_FAILED قد يدخل مسار عقوبة. Two-file move ليس«ذرية100%» |
| 012345 NOTES742–767 | اكتشاف حاجة حظر خزائن وbackups صحيح | BEFORE غير مطابق، AFTER يسقط حمايات قائمة؛ محاكاة§15.3 أثبتت regression قبل التطبيق |
| نقد الوكلاء فيالأرشيف3588–3594/3748–3789/3870–3885 | تبسيط التصميم وحصر النطاق بدل إعادة بناء النظام مطلب صحيح؛ فصلbaseline عنميزة لم تنفذ صحيح | Q1Arena عنالعتبة لاrevival، وQ1/Q3 يحملان جوابين بالفعل. نقدstartup كان صحيحًا للنسخة السابقة؛ تصحيحها الآن لا يبطل النقد التاريخي. لا202ملفAST: Arena يقول202جردًا و115AST. «خالفRoot/ai_state» غير مثبت فيبيئة لا تتيح ذلكالمسار |
| تقريرنا§0–14 | تتبعcallpaths،34finding، الفصل بينprobe/storage/outcome، HTTP-first،target-precedence،UTC، التوثيق والاسترداد | C1 لم يوضحrandomfirst5 بما يكفي؛ ترتيب الرصيد سياسة لا شرط لاستخدامlive balance. C4/D1>14 توصية لا قرارمالك. E6 أخذ حيزًا أكبر من اللازم: يسحب من المسار الأساسي. لا يلزم رد على ستة أسئلة قديمة كما هي بعد المصادر الجديدة |
| تقييمbaseline فيكلاالتقريرين | 13failure موجودة قبل دمجالهدية، فلا تنسب للميزة ولا تمنع إكمالالمراجعة/تصميمTDD | لا يجوز تسليمruntime«أخضر» أو تجاوزبوابةالمشروع لأنهاقديمة. تجربة8/8 توضحالسببالاختباري، لا تثبت intent المالك أو صلاحية300/180 للإنتاج |

**ردنا على النقد دون دفاعية:** لم نعدل01.03 أصلًا، وطلب إذنD6 ليس كسرfreeze، لكن البديلالأبسط أولى: bridge-first مع فاحص محدود وخدمةحفظواحدة. لا حاجةframework أوcache/TTL أوstartup sweep. في المقابل، فصلUNKNOWN عنDEAD ونتيجةالحفظ عننتيجةالفحص ليس تعقيدًا شكليًا؛ حذف هذهالفروق يعيدالعيوب المثبتة.

### 15.5 القرارات المحدثة — هذا الجدول ينسخ إلزام الرد القديم في§12

| البند | الحالة الحاكمة الآن | المطلوب فعلاً قبل التنفيذ |
|---|---|---|
| D1 الحد | **تعارض غيرمحسومبينالمصادر**: Arena89/555 ينقل«زي05.02»>=14؛00PLAN96/125 و012345PLAN90/119 توافقه؛D1فيهما>14/exact14recent | سؤال واحدمحدد: عند14يومًا بالضبط،متأخر أمحديث؟ UTCلا يحسمعاملالمقارنة. C4وX08مثالانمشروطان لااعتماد |
| D2/D4 | الاتجاهالمتكرر فيالتوجيهات:UNKNOWN/transient تخطٍّ بلاsend/عزل/تبريد؛ نعتمدفيالخطةzero-mutation لملفاتالحسابات | لا نعيدسؤال«هل502ميت؟». ضمنGOالجديديظهر صراحة تغيير-1عنPR8القديم، وتأجيلlast_used/reactivate حتىقرارمؤكد؛ اختباراتhashesقبلوبعد |
| D3 | نبسطإلىعمليةواحدة/single-writer **كشرطتشغيلمعلن** وقفلواحدمشتركلكلread-modify-write | جردالكتّابومداخلCLI/namespace أولًا؛ منع05.02وأيكاتبخارجي أثناءالعمل. إذا تعذرإثباتذلك،توقفواطلبنطاققفلOS؛RLockمستقللايكفي |
| D5 | baselineمنفصلعنالميزةومازالأحمر | لا يعطلإكمالالخطةواختباراتTDD؛ لكنproductionقبلهbaselineمعتمد وبواباتخضراء. compact/model/وصفbanned تحتاجعقدالمالك،لاfixلتجميلtests |
| D6 | **01.03 READ-ONLY افتراضيًا،E6مستبعدمنالمسارالأساسي** | أثبتbridgeguards قبلbusinesssendعلىكلالمسارات. إذاكشفاختبارحاجةلتعديله،قدمالسببوالبديلثمإذنمنفصل. لاتدّعِأنbridge-onlyيصلحCLIالمستقلأوكلwriters |
| failed evidence | INVALID_CREDENTIALSالمثبتةليستmissingcredentials؛403وINACTIVEالمجهولليسادليلينكافيين | أمثلةمنقحةأوschemaموثقوallowlistمراجعة. عندغيابالدليلUNKNOWN،لانقلدائم. لاطلبأسرارأوحساباتحقيقية |
| legacy | Arena90/557 ينقلاتجاه«نجمعفيfailedمعإبقاءالقديم»؛ نسجلهاباعتبارهقرارخطةمنقولًاولانعيدفتحأصلالاتجاه | جردread-onlyومعالجةالتعارضاتوموافقةنقلمنفصلةقبلأيmutation؛لاmigrationعندالإقلاع |
| sorting | الحفاظعلىالاختيارالحاليهوالافتراضي؛liveprobeإلزاممستقل | C1وT23فرزرصيداختياريبعداعتمادالأولوية. إنأرادالمالكالأعلىدائمًا،يلزممعالجةrandompoolلاsortفقط؛لافحصحيشامللخمسينحسابًادونطلب |
| gift أثناءالمهمة | lowbalanceقبلالاستخداميشغّلgiftcheck؛DATA_RETENTIONوcompactلايثبتانstale | حددنطاقدمجcredit-in-flightدونكسرcheckpoint/URL/عدمإرسالpromptمرتين؛لااستبدالكلcooldownعميانيًا |
| GO | لايوجدإذنتنفيذمنإرسالالروابطأوطلباستئنافالمراجعة | اعتمادنسخةالخطةالمحدثةونطاقهاصراحة؛live/migration/merge/deployإذونمنفصلة |

لا نطلبإعادةحسممنعrevival أوTTL أوstartupsanitize أوتبديلresolver. وتبقىبياناتالصوتوالدستورالأصليةمطلوبةفقطإنأرادالمالكشهادةمطابقةحرفية؛ليستذريعةلتعطيلقراءةالكود.

### 15.6 BEFORE/AFTER تصحيحي مختصر، غير منفذ

1. **الفلتر:** BEFORE الحقيقي هوالجسر2324–2331، لا المثالالمنسوخفي012345. AFTER يحفظالشروطالقديمة ثم يضيفخزائنfailed/delayed/dead وTelegramtoken ونسخالحسابات/`.tmp_*` والـbackups ذاتالصلة. اختبارregressionيؤكدحفظالاستثناءاتالسبعة في§15.3 معالسماحلمصدرعادي. فحصregistryيحتاجمسارًا/سياسةمستقلة؛لاتزعمحمايتهبفلترbasenameفقط.
2. **gift branch:** BEFORE `if STALE: move; else: cooldown`. AFTER فروعصريحة:STALE→حفظموثق؛RECENT→29h؛UNKNOWN/TRANSIENT/NEEDS_CREDENTIALS→تخطيبلاتغييرحساب. فشلstorage→وقوفآمنمعالرابط،لاsuccessولاgenericcooldown.
3. **حدالزمن:** BEFORE `.days >=14` في05.02 مقابل`elapsed <=14→recent` فيC4. AFTER مقارنةUTCfull-durationبعاملواحدمعتمد،واختبارات14d−1s/14d/14d+1s. لاالتفافبكلمة«دقيقرياضيًا»لتقريرسياسةمالك.
4. **المولد:** BEFOREcoverageثمdeleteثمAST. AFTERcompile/ASTلكلchunkوتغطيةكاملةفيstaging،فحصimports/parity،ثمترقيةبناءمكتملمعrollback؛latestsnapshot/codeversionمتطابقان. لااستعادةanchorsقديمةغيرمطابقةلمجردوجودها.
5. **القفل:** BEFOREقفلvaultمستقلعنFILE_LOCK. AFTERملكيةكتابةموحدةلكلread-modify-writeبالعمليةالمعتمدة،ترتيبقفلواحدوre-readبعدclaim،والشبكةخارجالقفل. target-first/readbackثمsource-cutمعpending/conflict؛هذهقابليةاستردادلاذريةملفين.

### 15.7 خريطة التنفيذ المبسطة وربط الخطة السابقة

كلT/Xمازالتغيرمنفذة. §10يبقىسجلتتبع، معالتعديلاتالحاكمةالتالية:

- **M0 اعتمادوتثبيت:** T00–T03وفق§15.5بدلإعادةD1–D6حرفيًا؛ لايتغيرfreeze. الأمانالعاجللتدويرالاعتماداتيجريهمالكهاخارجGit،لاينتظرميزةالهدية.
- **M1 baselineواختبارات:** T04–T11؛ يمكنكتابةتصميم/fixturesواختباراتredبالتوازي معحسمbaseline. لايعلنقبولنهائيولانشرتشغيلقبلgreen. ثبتمصفوفةالفشل13كيلايختبئانحدارجديدبينها.
- **M2 فاحصوحفظمحدودان:** T12–T22؛ probesصغيرةtypedنتائجهاواضحة،sessionملكيةمعلنة،singlewriterمتحقق،target-first. لاإطارعملجديدولاTTLولاread-failure→[]ولاwipecookies.
- **M3 bridgeintegration:** T23–T28؛ افتراضT23يحافظعلىسياسةالاختيار،ويضيفtargetexclusion/re-read/liveprobe. يشملpreflight2943–2989 و401mid3089–3108؛ يراجعcredit3523–3529 وretention3360–3371 وmaintenance3330–3342/3441–3449 كمساراتمختلفةلايستبدلتبريدهاكلهابفحصهدية.
- **E6/T29–T31:** مؤجلةخارجالمسارالأساسي؛ لاتعديل01.03. تنقلحراسةقبلsendوجردwritersإلىM3داخلنطاقهالمعتمد،ولاX24يدعيإصلاحclockbalanceفيCLIالمجمد.
- **M4 قبولواستئناف:** T32–T39و§13؛ stagedrebuild،parity،fullgate،faultinjection،reset/rollback،ثمpushومراجعة. source/generatedكوحدة،والبياناتلاتتراجعبرجوعprimaryقديموحده.
- **تحديثX01:** فرزالرصيدواختيارالأعلىاختياريان؛ أضفاختبارrandompoolوعدمادعاءالأولوية. **X08:** يعتمدD1غيرالمحسوم. **X18:** إثباتsinglewriterوكلالكتّاب،لاقفلvaultفقط. **X24:** bridgeguardsمعfreeze،لاادعاءتعديلCLI. **X28الأمن:** أضفالاستثناءاتالحاليةو`.env.production`وtmp/backupsومسارpasswordcard؛تعديلQwen/uploaderالأمنيإنطُلبلهنطاقمنفصل.

### 15.8 سجل التسليم وحدود النتيجة

القراءة الإضافية والمقارنة والمحاكاة المحددة مكتملة. المراجعةلا تقولإنالميزةنُفذتأوإنكلثغراتالمشروعأُغلقت. لاPython/tests/generated/accountchanges، ولااتصالاتخدماتحيةولادمجPRأونشر. الخلاصة: نحافظعلىتحسيناتالوكلاءالحقيقيةونرفضالأمثلةالمتناقضة،ونصححتوصياتناأيضًا؛القرارالأبرزالمتبقيهوحد14يومًاالدقيق،ثمGOمحددللخطةوعقودbaselineوالأدلةقبلالعزل.

نقطةحفظسابقةمؤكدة: `166afc4bbd38409ad24a0ec99159fdd20ac50c5b` بعداستعادةd072816. النشرالنهائييُتحققمنremote/PR9،وقديتغيرhashمعsquashمعثباتtree. عندresetاقرأرأسPROGRESSوcurrent_execution،واستكملالنشرالناقصفقط؛لاتعدالمراجعةولاالتجاربولاPR8.
