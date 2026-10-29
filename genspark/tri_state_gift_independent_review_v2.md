# مراجعة مستقلة ثانية وخطة دمج الهدية والمعزل الثلاثي

## 0. التكليف ونقطة الحفظ

- طلب المالك الحالي يعيد فتح المراجعة من البداية ويطلب ملفًا جديدًا؛ ينسخ تعليمات «لا تعد المراجعة» في سجل التسليم السابق، ولا يمنح GO للتشغيل.
- تاريخ البدء: 2026-10-29. أساس المصادر الأحدث: `d16475814bebf7379b097e26587698194582941c`. استعيد تسليمنا السابق `f3eef4b3a55cdf6ed321b76a7e6eb3a53ae2159c` على فرع `genspark_ai_developer`، ثم زومنت main داخل الفرع، لا العكس.
- الحالة الآن: **المراجعة الجديدة قيد العمل**. الملف الجديد لا ينسخ صحة أحكام التقرير السابق تلقائيًا، ولا يزعم اكتمال القراءة أو نجاح اختبارات لم تُعَد.
- النطاق: الملف الجديد وPROGRESS وrecovery؛ التقرير السابق محفوظ دون تعديل، وكذلك وثائق الوكلاء وPython/tests/generated والحسابات. لا live أو migration أو merge/deploy أو تشغيل05.02.
- التفريغان المرفقان نص من المالك؛ لا ادعاء سماع التسجيل الأصلي. دستور بولا/SRE الخارجي غير متاح فلا شهادة مطابقة له.

## 1. سجل المراجع المثبتة

تم جلب أحدث Git فعليًا. التغيير الوحيد من d2eb49d إلى d164758 هو إضافة1446 سطرًا إلى Arena؛ أول1884 سطرًا مطابقون تمامًا. أصبح الملف3330 سطرًا. Python/tests/generated لم تتغير. هذه مقارنة إصدارات، لا حكم مسبق بصحة الإضافة.

| المرجع | الأسطر | SHA-256 للبايتات الخام |
|---|---:|---|
| [00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md](../00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md) | 304 | `84e10d00365c4d6bea8be5434b8924336919449f38f050ef6c31d73b747d54a3` |
| [00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md](../00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md) | 360 | `8841f6167040e721ea17c8d822f4909f9eca3cd2a3adf2c1ec5120a74565bb75` |
| [012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md](../012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md) | 778 | `66472d8d72c9f778d27ef3ec9cffeffcfe54a93076c62384cef0e855d63548db` |
| [012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md](../012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md) | 235 | `6485ac0b10effea210eb3d895d41e22008dd9d4807469ccb9a62c43f119c05c5` |
| [012345_arena-ai_مراجعة_وخطة_دمج_الهدية_الشاملة.md](../012345_arena-ai_مراجعة_وخطة_دمج_الهدية_الشاملة.md) | 3330 | `bc001cf7252a540aba6b04eab61b9ef3ac08dd73dcfa89b696e18a52a65d4a3b` |
| [05.02_genspark_delayed_gifts_manager.py](../05.02_genspark_delayed_gifts_manager.py) | 756 | `192d3a3445b280d54b8e8475783a6cbe147e6391a39a137fdeee98387cd7b729` |
| [جج-جميع-شات-.MD](../جج-جميع-شات-.MD) | 4276 | `a241c3b63ed008acd090dbcfe822a10d3e0c7a2e451b76efb8fd9227ebc54f3f` |

مراجع ثابتة إضافية:
- [885d7a4](https://github.com/number949481-ux/TTTTT/commit/885d7a41f93aa8293f6baa9f653ddb21d29f1bb9).
- [92f658e](https://github.com/number949481-ux/TTTTT/commit/92f658ebd575407d0bba8e3a682cadd0fc248404).
- [تحديث Arena d164758](https://github.com/number949481-ux/TTTTT/commit/d16475814bebf7379b097e26587698194582941c).
- [تقريرنا السابق عند f3eef4b](https://github.com/number949481-ux/TTTTT/blob/f3eef4b3a55cdf6ed321b76a7e6eb3a53ae2159c/genspark/tri_state_gift_master_review.md): مادة محل نقد، لا سلطة مستقلة.
- AGENTS.md وGEMINI.md و00_MASTER_RESUME_PROTOCOL.md وREADME/PROGRESS: حوكمة متاحة، مع فصل الأرقام التاريخية عن القياس الحالي.

## 2. خطة المراجعة المجمدة

| المرحلة | العمل | الحالة |
|---|---|---|
| V0 | استعادة الفرع ومزامنة المصادر وتثبيت التكليف الجديد والبصمات | مكتملة؛ النشر يتحقق من remote |
| V1 | إعادة قراءة المصادر وكشف المكرر وغير المتعلق بالمشروع وتدقيق قرارات المالك المنقولة | قيد العمل |
| V2 | إعادة تتبع كود الرصيد والهدية والعزل والكتابة والمولد والأمن؛ تجارب مستقلة محدودة | لم تكتمل |
| V3 | محاسبة أحكامنا وأحكام الوكلاء وصياغة BEFORE/AFTER وخطة صغيرة بعقود اختبار | معلقة على الأدلة |
| V4 | تحقق كامل للوثائق وسجل الاستئناف وتسليم PR9 Draft | معلقة |

## 3. ملاحظات أولية تحتاج التحكيم

- Arena1915–1969 يتضمن نصًا عن OSRS/Goblin Diplomacy وPR-18؛ لا يُنسب إلى TTTTT أو يُنفذ أمره. يلزم فصل تلوث المرجع عن المراجعة ذات الصلة التي تبدأ1979.
- Arena1983 يقارن تقريرنا عند b74900c، لا آخر f3eef4b؛ يجب فحص إن كان النقد قد عولج بالفعل قبل وصفه خطأ حاليًا.
- الإضافة تثير نقاطًا مهمة لم يغلقها تقريرنا: أثر python -O على assertions المولد، ونطاق الإذن لتعديل verifier، وحدود zero-mutation تحت التزامن. ستراجع من المصدر، لا تُعتمد لمجرد ورودها.
- Arena ينقل مجددًا جواب «زي05.02» ويختار >=14؛ يلزم فصل هذا النقل عن توجيه مباشر في محادثتنا وعن تناقض وثائق00/012345. لا تبدأ عملية عزل الآن بأي تفسير.

## 4. الاستئناف

بعد reset: افحص remote وPR9 ثم هذا الملف وPROGRESS/current_execution. احفظ كل دفعة commit/push وتحقق مساواة HEAD وremote؛ لا تكتب hash الدفعة داخل نفسها. لا تحول حالة «قيد العمل» إلى اكتمال بلا قراءة وفحص. النتائج القديمة في التقرير السابق تاريخية حتى إعادة التحقق المطلوبة هنا.

## 5. دفعة استعادة بعد reset جديد — 2026-10-29

- استعيد `3111f8f2b50d39da115b89cac7d54283f40447c0` فعليًا من remote؛ main ما زال `d16475814bebf7379b097e26587698194582941c`. الخطة V0–V4 والنطاق في §0–§2 مجمدان؛ الاستئناف ليس إذن تنفيذ.
- **أدلة من ملخص الجلسة المنقطعة، لا إعادة تشغيل في هذه الدفعة:** syntax ناجح؛ pytest:1072 passed/13 failed/+60 subtests؛ canonical:1085 tests/13 failures. سجلاتها المحلية لم تستعد بعد reset، لذلك لا نخلطها بقياسات هذه الجلسة.
- المولد، بحسب ذلك الملخص: الوضع العادي يوقف على9181 مقابل9285 ويحفظ marker؛ optimize=1 أو تغيير نهاية PARTS وحدها يحذف OUT المؤقت ثم يفشل p03 بعد كتابة3 أجزاء. hashes الشجرة المولدة الحقيقية لم تتغير في تلك التجربة. هذه أدلة مرحّلة سيعاد توثيق تحقق مستقل منها.
- بقية المختبر السابق **لم تنفذ**: توقف عند استيراد `curl_cffi` المفقود. لا نتائج جديدة مثبتة منه للرصيد أو claim أو verifier أو HAR/AST. سنستعمل استخلاص AST للوظائف أو mocks مناسبة دون تثبيت عشوائي ودون استيراد05.02.
- القراءة غير مكتملة: Arena2490–2809 و3090–3330، وأجزاء المصادر الأخرى المذكورة في خطة الاستئناف. لا ادعاء قراءة شاملة جديدة أو اكتمال التقرير.
- سياسة مقاومة reset: دفعات توثيق صغيرة، commit ثم fetch/دمج عند الحاجة ثم push ثم مساواة HEAD/remote وتحديث PR9 Draft. النشر لا يثبت حتى تحقق remote؛ لا إعادة كتابة تاريخ الدفعات المحفوظة أثناء الاستعادة.

## 6. فحوص مستقلة منفذة بعد الاستعادة — دفعة الأدلة الأولى

هذه النتائج **أعيدت فعليًا بعد b1cf1a0** على Python3.13.14. كود الإنتاج مطابق لـmain@d164758؛ لا تعديل أو استيراد للمدير05.02. استُخلصت وظائف verifier وresolver من AST دون تنفيذ module imports، وأعطيت fake sessions وبيانات اصطناعية فقط. ملفات التجربة تحت `.tmp` عبر TemporaryDirectory. المولد نُفذ في namespace مستقل مع OUT مؤقت؛ لم يُشغّل على bridge_refactor الحقيقية. هذه تشخيصات للعيوب القائمة، لا اختبارات قبول لميزة منفذة.

### 6.1 نتائج قابلة للتحكيم

| المعرف | التجربة الفعلية | النتيجة والحكم |
|---|---|---|
| D01 | compile للمولد بـoptimize=0 ثم main على خريطة PARTS الحالية | AssertionError: التغطية9181≠9285؛ marker باقٍ؛ صفر أجزاء مكتوبة |
| D02 | نفس المصدر بـoptimize=1، بلا تعديل PARTS | marker حُذف؛ كُتبت3 أجزاء ثم فشل AST فيp03: ` '(' was never closed`، السطر652 من الجزء؛ رسالة «تغطي بالكامل» ليست تحققًا حقيقيًا هنا |
| D03 | optimize=0 وتغيير نهاية آخر جزء في الذاكرة فقط إلى9285 | النتيجة التدميرية المؤقتة نفسها؛ إصلاح النهاية وحدها غير كافٍ |
| D04 | SHA256 لكل ملف في generated الحقيقي قبل وبعدD01–D03 | متطابقة؛ لم يحدث real rebuild |
| D05 | fake balance HTTP502 ونص user_suspended، مع cookie اصطناعية | master verifier أعادSUSPENDED/is_dead=True/balance0؛ تصنيف موت كاذب مؤكد في المسار المجرب |
| D06 | fake balance HTTP502، وuser200/status0/retention enabled | EMPTY_BALANCE/balance0/is_dead=False؛ الخطأ المؤقت تحوّل لصفر |
| D07 | fake B2C landing بمفاتيح وهمية ثم POST502 بنص password verification temporarily unavailable | INVALID_CREDENTIALS؛ الحكم مبني على النص قبل HTTP |
| D08 | خزنة مؤقتة تحتوي`{broken`، ثم quarantine(account, 'SUSPENDED', directory, 'synthetic') | رجعتTrue واستبدلت الملف بقائمة من سجل واحد؛ فساد التخزين لا يوقف الكتابة |
| D09 | get_accounts_file_path بمسار صريح مفقود وresolve_shared_path mocked لملف آخر موجود | أعاد الملف الآخر؛ لا ضمان أن النقل سيستعمل المصدر الصريح المقصود |
| D10 | جردmain باستخدامgit ls-tree -rz وفحصAST دون import |203ملفات:96py+19anchors+81Markdown+2HAR+5أخرى؛115AST ناجحة؛40ملف اختبار، لا تعني40اختبارًا فقط |
| D11 | قراءة JSON بنيوية لملفَيHAR دون طباعة headers/body/URLs |286 و4356 entries؛ صفر URL يحتوي`/api/credit_audit/`؛ لا يثبتان schema/pagination لواجهة الهدية |

**تصحيحان في مختبرنا نفسه:** المحاولة الأولى للجرد استخدمت فواصل الأسطر فعدّت أسماء Git العربية المقتبسة خطأً (72Markdown/14أخرى). أُلغيت هذه الأرقام وأعيدت بـNUL، والنتيجة المعتمدةD10. كما مُرر dict بدلstr في وسيطverdict بأول تجربة خزنة؛ أُعيدتD08 بالتوقيع الصحيح أعلاه وأثبتت الاستبدال. لا نخفي عيوب أدوات الفحص ولا ننسبها للمنتج.

لإعادةD01–D03 دون تعديل المصدر: اقرأscripts/rebuild_refactor.py، `exec(compile(text, path, 'exec', optimize=0 أو1), ns)` مع`__name__` غيرmain؛ اضبط`ns['OUT']` إلى مجلد مؤقت يحتويmarker؛ فيD03 غيّرtuple الأخير في`ns['PARTS']` داخل الذاكرة فقط. نادِ`ns['main']` والتقطAssertionError/SystemExit. قارن raw hashes لشجرةgenerated الحقيقية قبل وبعد. لا تستبدل هذا بإطلاقCLI على المشروع الحقيقي.

### 6.2 البوابات الحالية، لا أرقام README التاريخية

- `python -m py_compile` للجسر والمحرك وverifier و05.02 والمولد: Exit0؛ compile ليس import ولا تشغيل حسابات.
- `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/user/webapp/.tmp python -m pytest -q -p no:cacheprovider`: **1072passed/13failed/+60subtests،5.41s،Exit1**.
- `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/user/webapp/.tmp python -X utf8 scripts/hadith_sijil.py`: **1085tests/13failures،3.003s،Exit1**. توقفت قبل كتابة سجل نجاح؛ tracked tree بقي دون تعديل.
- parity لم يُعد منفصلًا هنا؛ فشله مثبت داخل البوابتين. baseline ما زال أحمر؛ لا تصريح بجاهزية runtime.

معرفات الفشل الفعلية:
```text
tests/test_auto_compact.py::CompactTests::test_account_above_180_does_not_compact
tests/test_auto_compact.py::CompactTests::test_five_minute_credit_exhaustion_does_not_compact
tests/test_auto_compact.py::CompactTests::test_long_credit_after_maintenance_resumes_without_recompacting
tests/test_auto_compact.py::CompactTests::test_new_credit_replaces_old_deferral_and_long_credit_clears_due
tests/test_auto_compact.py::CompactTests::test_threshold_uses_monotonic_span_at_exactly_180_seconds
tests/test_credit_completion_recovery.py::CreditRecoveryTests::test_fast_credit_handoff_preserves_checkpoint_before_second_account
tests/test_credit_completion_recovery.py::CreditRecoveryTests::test_final_fetch_credit_reaches_real_failover_in_fast_mode
tests/test_credit_completion_recovery.py::CreditRecoveryTests::test_real_worker_handoff_uses_cloud_checkpoint_and_second_account
tests/test_p2_model_routing.py::TestP2ModelRouting::test_format_model_display_label
tests/test_p2_model_routing.py::TestP2ModelRouting::test_opus5_has_no_ai_chat_model
tests/test_p32_account_password_lookup.py::TestPasswordCardRendering::test_06_banned_state_described
tests/test_p3_regression.py::TestP3RegressionSnapshots::test_opus5_matches_new_contract
tests/test_refactor_parity.py::TestByteParity::test_parts_reassemble_to_original
```

### 6.3 أثر النتائج على الحكم والخطة

- Arena أصاب في خطر-O وفي تصنيف502 والخزنة والفallback وفي الجرد البنيوي. هذه المطابقة مستقلة الآن، وليست تصديقًا شاملًا لوثيقته أو مختبراته.
- تقريرنا السابق أغفل-O؛ AFTER المقترح للمولد يجب أن يستعمل explicit exceptions لاassert للحماية، وأن يتحقق من التغطية وAST **لكل** الأجزاء في staging قبل المساس بالوجهة. swap/rollback نفسه يحتاج اختبار فشل، وليس ضمان transaction مطلقًا.
- BEFORE verifier: `is_suspended_response`83–105 وmaster257–258 وB2C160–165. AFTER التصميمي: HTTP/transient أولًا، ثم أدلة structured/allowlist؛ missing credentials ليست invalid مثبتة؛ UNKNOWN ليست صفرًا. تعديلverifier يتطلب توسيع نطاق صريح بسببAGENTS22؛ لم يُنفذ.
- BEFORE vault:396–404 تحول فسادJSON/non-list إلى[] ثم replace421–424. AFTER التصميمي: typed read failure يوقف mutation؛ نسخ موثقة وtarget-first/readback/source-cut ضمن عقد writers موحد. نجاحreplace لملف واحد ليس نجاح نقل بين ملفين.
- BEFORE path:957–970 يسمحfallback. AFTER التصميمي: حارس نقل موضعي يثبت المسارات الصريحة ويحظر fallback عند خطأ؛ **لا تعديلresolve_shared_path/P23**.
- استُكملت قراءةArena2490–2809 و3090–3330 في هذه الجلسة؛ سطور التفريغ الطويلة2497/2500 عُرضت مبتورة بالأداة، لذلك لا نسميها قراءة كاملة. الملحق الأخير جرد آلي مرجعي عندd2eb49d، لا claim مراجعة دلالية لكل سطر. بقية إعادة قراءة المصادر لم تكتمل بعد.
- التالي: تشخيص sender/failover/claim ثم استكمال provenance لحد14 وكتّاب التخزين والأمن، وصياغة الخطة التفصيلية. لا نتائج جديدة حتى الآن لتلك المسارات في هذه الدفعة.

## 7. نتائج الجسر المحفوظة من الفحوص السابقة مباشرة للمقاطعة

عند إعادة تأكيد التكليف استعيد2b03cb0 منGitHub، وأعيدfetch فعليًا؛ main ما زالd164758 وArena بنفس البصمة. لم تظهر نسخة أحدث فيremote حتى هذه النقطة. فُقدت`.tmp` بعدreset، لكن **نتائج الأدوات المسجلة في المحادثة** التالية نُفذت فعلًا بعد2b03cb0 وقبل المقاطعة؛ لم نعدها في دفعة حفظها هذه.

### 7.1 المنهج وحدوده

استُعمل fixture القائم `tests/test_credit_completion_recovery.py:25–63` دون تعديله: engine/send/read/update/refresh والواجهات الجانبية mocks، مجلدات اصطناعية داخلworkspace. حُظرتsocket.connect وsocket.create_connection وrequests.Session.request؛ curl_cffi غير مثبت وتم تجاوز استيراده الشرطي دون تثبيت. لاHTTP حقيقي. القياس هنا لاستدعاءات writers وsend mocks، **ليس byte-diff لملفات حسابات فعلية** ولااختبار نظام إنتاج كامل.

| المعرف | المدخل الاصطناعي | النتيجة المثبتة |
|---|---|---|
| D12 | balance=-1 معlast_refresh حديث | send_chat مرة،COMPLETED منfake،لاcooldown |
| D13 | balance=NaN معlast_refresh حديث | send_chat مرة،COMPLETED منfake،لاcooldown |
| D14 | balance=+Infinity | send_chat مرة،COMPLETED منfake،لاcooldown |
| D15 | balance sequence[-2,-1] معrefresh mocked ناجح | send_chat مرة بعدunknown،COMPLETED |
| D16 | balance sequence[100,-1]؛ أولsend يرمي401 ثمrefresh mocked | send_chat مرتان،COMPLETED؛ حارس ما بعد401 يسمحunknown |
| D17 | sender محقونTIMEOUT،بلاURL أو معURL،max_account_attempts=1 | TIMEOUT؛last_used writer استُدعي؛لاcooldown ولاlast_success؛claim محرر |
| D18 | sender محقونUNKNOWN أوTRANSIENT أوAUTH_FAILED **بلاURL** | MAX_ATTEMPTS_EXHAUSTED؛last_used وcooldown_until>0 استُدعيا؛claim محرر |
| D19 | الحالات الثلاث نفسها **معURL** | تعودالحالةنفسها؛last_used وlast_success_at/status active/cooldown0؛claim محرر |
| D20 | get_account_fingerprint يرميRuntimeError بعدclaim | الاستثناءيصعد ويبقىclaimواحد؛ نُظّفsynthetic claim يدويًا بعدassert |

D18–D19 حقن لعقود حالات مقترحة، لا ادعاء أنsender الحالي ينتج هذه الأسماء بنفسه. D19 يثبت أن إضافةstatus جديد دونdispatch صريح قد تجعل وجودURL دليل نجاح زائفًا. التصحيح: ليس كلUNKNOWN يبرد5دقائق؛ النتيجة تتوقف علىURL ومسارdispatch.

**تصحيح أدواتنا:** أولmock أعاد4عناصر بدل5 فتوقف بـValueError. ثم توقع المختبرmark_account_cooldown بينماgeneric branch يكتبcooldown مباشرة عبرupdate_account_data، ومررcfg كوسيطemail الثالث بدلbridge_cfg keyword. أُلغيت استنتاجات تلك المحاولات، وأعيدت المصفوفة كاملة بالتوقيع الصحيح `bridge_cfg=case.cfg`،tuple ذي5عناصر،وفحصwriter نفسه. آخر تشغيل أعاد `FINAL_FAILOVER_MATRIX_ALL_ASSERTIONS_PASSED` وExit0. أرقامD17–D20 تخص هذا التشغيل المصحح فقط.

### 7.2 BEFORE الحقيقي وAFTER المطلوب، لا patch منفذ

- **رصيد:** `01.33:2954–2967,2973–2978,3098–3106`: الحارسان بعدrefresh يوقفانlow فقط؛-1/NaN ليستاlow. AFTER: نتيجةtyped مؤكدة finite/nonbool/nonnegative، وحارسواحد يعادفيالبواباتالثلاث،بلاsend عندUNKNOWN. الحسابالذيبلغه100 يقفزعنهدية؛الثابتالافتراضي100 لايلغيالحاجةلتوثيقoverride.
- **claim:** claim عند3242،reactivate3270،fingerprint3280،last_used3296،try3298،finally3657–3660. AFTER: تبدأمنطقةcleanup فورنجاحclaim وقبلأيعمليةقدترمي؛release داخلfinally محمية حتىإنفشلإغلاقspan. لاdouble release غيرمالك،ولاHTTPداخلقفلملفطويل.
- **dispatch:** `if pub_url or status == "COMPLETED"` عند3630؛generic cooldown3655. AFTER: dispatch صريح للحالاتالمؤكدة/المؤقتة/فشلحفظ/uncertain-send قبلsuccess أوfallback؛URL وسيلةاسترجاعوليسدليلنجاح. TIMEOUT قبلbusiness-send يمكنتخطيه؛بعدsendمحتمل يوقفأويستعلمبعقدidempotency،ولاblind resend.
- **zero-mutation:** last_used يكتبقبلprobe؛reactivateقديكتبأيضًا. AFTER: لاكتابةمنسوبةلمحاولةprobeمجهولة؛عرّفنقطةcommit للكوكيزوالرصيدوالاستخدام. ثباتhash الملفكلهيختبرفيعزل؛تحتالتزامننفحصالأثرالسببيوسجلالwrites كيلايحسبwriteمشروعآخرمخالفة. لايعالجذلكبحبسمُلْكملفطوالHTTP.

### 7.3 اتجاهحد14: تصحيحمنهجالتحكيم

Arena:555 ينقلنصجوابالمالك «مش فارقه زي سكربت بتاع05.02»، و1988/2010 يؤكد>=14. هذا **نقل موثق في مرجع طلب المالك إدراجه**،ليسسماعًامنهولاGOجديدًا. الترجيحالتخطيطيالآن: **elapsed>=14×24ساعة** عندأدلةهديةصحيحةوكافية،اتباعًاللجوابالمنقول؛لااستفتاءجديدتلقائيعلىمساواةحسمهاالمرجع. يوضعهذاالافتراضصريحًافيطلباعتمادالنسخة،وللمالكتصحيحهإنكانالنقلغيردقيق.

نقدنالسابق: دقةUTC لا تختار `>` بدل`>=`؛مدح00/012345 لاقتراحنا>14 كأنهقرارمالكغيرمبرر. إبقاءالسؤالقديمًاكأنهلاحللهأهملprovenance المنقول. فيالمددغيرالسالبة،`.days>=14` يكافئelapsed>=timedelta(days=14)؛floor وحدهليسعيبحد>=. العيوبالفعليةفي05.02 تشملالوقتالمجمد،التاريخغيرالواعي/التالف/المستقبلي،فرزالنص،واكتمالالتاريخ. لا تستنسخأخطاءالمديرمعاعتمادحده.
