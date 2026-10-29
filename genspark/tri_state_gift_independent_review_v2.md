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


## 8. استعادة ea9ab27 وتجميد النطاق — 2026-10-29

- بدأ workspace بعد reset على main؛ أُجري fetch وls-remote واستعيد فرع `genspark_ai_developer` عند `ea9ab278d4b938cf1815ade4f9919d3daf01740f`. main ثابت عند `d16475814bebf7379b097e26587698194582941c` ومضمّن في الفرع. الشجرة كانت نظيفة.
- تحقق SHA256 مجددًا: Arena مطابق لبصمة §1؛ التقرير السابق `342b4ca585be8df4934acb7681b51be662d6a98632158c46a248f3625280ae0d` محفوظ دون تغيير. لا نسخة أحدث ظهرت في fetch الحالي.
- خطة V0–V4 مستمرة؛ V1/V2 جزئيتان، V3/V4 غير مكتملتين. هذه الدفعة للاستعادة فقط، وليست تسليمًا نهائيًا أو GO. النطاق ثلاثة ملفات: هذا التقرير وPROGRESS وrecovery.
- نتائج D01–D20 والبوابات في §6–§7 أدلة محفوظة من الجلسات السابقة؛ لم تعَد بعد reset الحالي. baseline الموثق أحمر: 13 failure؛ لا نفترض بقاء logs المحلية.
- أول عمل تالٍ: إكمال التشخيص المنقطع للفلتر و`math.isfinite(10**1000)` وقراءات05.02/Qwen/uploader، ثم تتبع snapshot وبطاقة كلمة المرور، وتوثيق scripts والكتّاب. لا ننسب نتيجة للأداة المنقطعة.
- لا Python/tests/generated/accounts edits؛ لا استيراد أو تشغيل05.02؛ لا Genspark/Telegram/Qwen live أو migration أو merge/deploy. Arena مرجع دائم؛ لا تعديل له أو لوثائق الوكلاء الأصلية. لا أسرار أو HAR خام في الوثائق.
- كل دفعة: commit ثم fetch ودمج main عند الحاجة ثم push ثم مطابقة HEAD مع remote وPR9 والتأكد من Draft. يُسجل hash السابق داخل الدفعة؛ hash الحالي يُتحقق خارجيًا بعد النشر.


## 9. التشخيص المنقطع، الأمن والكتّاب — أدلة جديدة بعد fef72ea

هذه الدفعة قراءات مصدر وتشخيص AST معزول، لا استيراد للجسر أو05.02/Qwen/uploader ولا اتصال بالخدمات. نتائج البوابات في §6 لم تعَد. الملفات الأصلية والتقرير السابق محفوظة دون تعديل.

### 9.1 نتائج D21–D22 ونقد أدواتنا

| المعرف | المنهج والمدخل | النتيجة الفعلية وحدودها |
|---|---|---|
| D21 | استخراج `_is_never_copy_file` الحقيقي من AST للجسر:2324–2331، واستخراج AFTER فقط من012345 NOTES:757–766، وتنفيذهما في الذاكرة على15 اسمًا اصطناعيًا | تسعة أسماء محجوبة حاليًا أصبحت غير محجوبة بالمقترح، أدناه. Assertions نجحت وExit0. لا snapshot أو upload فعلي في هذا التشخيص |
| D22 | `math.isfinite(10**1000)`، وهو الشرط نفسه في C1 من تقريرنا السابق:381–382 | `OverflowError: int too large to convert to float`. مثالنا المقترح غير كافٍ؛ هذه ليست مشكلة أضفناها إلى runtime، لأن المثال وثيقة فقط |

تفصيل D21، حيث True تعني **منع النسخ**:

| أسماء العينة | الحالي | المقترح |
|---|---|---|
| bundle.tar.gz؛ bundle.tar؛ bundle.zip؛ record.failed | True | False |
| .env.local؛ accounts_genspark.json؛ accounts_qwen.json؛ accounts_deepseek.json؛ keys.txt | True | False |
| accounts_failed.json؛ accounts_delayed_gifts_credits.json | False | True |
| .env | True | True |
| dead_accounts.json؛ telegram_bot_token.txt؛ accounts_genspark.json.tmp_1234 | False | False |

العدد9 خاص بهذه العينة، لا تعداد لكل الأسماء الممكنة. عبارة «سبعة» في التقرير السابق تصف عينة أقدم؛ لا تُستعمل حدًا أقصى للتراجع. BEFORE في012345 NOTES:745–754 ليس الدالة القائمة أصلًا. AFTER المطلوب تصميميًا: الحفاظ على جميع الاستثناءات القائمة، وإضافة الخزائن والـlegacy وsuccess/dead والنسخ المؤقتة والاحتياطية والأسرار، مع فحص basename والمسار المطبّع عند حدود snapshot/archive/REST، لا الاعتماد على `.gitignore`. لا حظر شامل لكلJSON يفقد ملفات المشروع السليمة.

**خطأ مختبرنا الحالي:** المحاولة الأولى فشلت بـIndentationError عند تحليل code fence المزاح، قبل مقارنة الأسماء أو فحص huge-int. صُححت بـ`textwrap.dedent` واختيار الكتلة التي تحتوي الدالة والخزنة الجديدة، ثم تحقق وجود كتلة AFTER واحدة. لا تُنسب نتائج المحاولة المصححة إلى المحاولة الأولى.

**تصحيح C1 المقترح:** لا تمرر كلint إلى تحويلfloat ضمني. حدد مجال القيم حسب الحقل؛ `type(value) is int` يعالج بحدود صحيحة مباشرة، و`type(value) is float` يفحص finite، وbool والنصوص وNaN/Infinity والمدخل خارج المجال تعاد كبيانات غير صالحة. للرصيد: لا حد أقصى اعتباطي دون schema؛ يمكن رفض الحجم غير المدعوم صراحةً كـUNKNOWN بدل crash. للاستخدام الزمني: مجال timestamps مستقل. الـdefault الخاص بترتيب cached لا يصبح رصيدًا حيًا موثوقًا. هذا عقد مقترح يحتاج قبولًا واختبارات، لا patch منفذ.

### 9.2 مسار النسخ والأسرار: من المصدر إلى المخرج

1. `snapshot:4592–4699` يحصر الملفات ويستدعي الفلتر الحقيقي على `item.name` عند4608، ثم مرشح مجلدات على المسار عند4612؛ النسخ الفعلي عند4616. إذن ليست هناك طبقة snapshot بلا فلتر مطلقًا؛ العيب هو نقص قائمته وغياب دفاع مستقل كافٍ عند المخارج الأخرى.
2. `_write_checkpoint_archive:4462–4475` يضيف عناصر checkpoint إلىtar دون فحص أسرار خاص به؛ snapshot يستدعيه عند4663. إن مر ملف حساس عبر snapshot، لا يظهر في هذه الطبقة حارس آخر يمنعه. هذه قراءة مسار، لا تجربة تسريب ملفات حقيقية.
3. `_default_github_uploader:4275–4356` يفحص `_should_skip_archive_member` عند4307؛ هذا يستبعد مجلدات cache/git/node_modules عند2317–2321 ولا يصنف أسرارًا. يقرأ الملف عند4322 ثمPUT عند4331. لا يقرأ `.gitignore` في هذه الدالة. كذلك مسارDELETE عند4337–4351 يحتاج سياسة منفصلة: إضافة فلتر يجب ألا تحوّل ملفات مستبعدة تلقائيًا إلى حذف بعيد بلا قرار؛ snapshot يبني deleted_files عند4642–4654.
4. لذلك يجب اختبار `upload_files` و`delete_files` وqueue القديمة وarchive، لا نجاح فلتر منفرد فقط. التحقق النهائي من provenance ومسار الملف داخل checkpoint ضروري؛ لا ادعاء أن فحص هذه الدالة وحده راجع كل منتجي payload.
5. `render_account_password_card:6338–6355` يضعpassword داخلHTML code. مسارا callback/message يرسلان الناتج إلىchat_id عند8721/8801. الحارس العام عند7890/8745 يقبل مجموعة معتمدة أو مستخدمًا معتمدًا داخل مجموعة أخرى، وفق196–216؛ لا يوجد شرط private خاص بهذين الفرعين. خطر نشر البطاقة في مجموعة قائم مصدرًا، لا واقعة تسريب مثبتة. AFTER الأمني المقترح: منع كشف السر في المجموعة واشتراط مستخدم مصرح ووجهة خاصة، ضمن إذن منفصل لتغيير UX، لا افتراض أنHTML escaping يحمي السر.
6. `qwen_engine:290–324` يرسل قيمةpassword_hash كحقلpassword إلىsignin عند313. الاسم لا يجعل القيمة غير حساسة. لم تُطبع قيم ولم يُختبر أي حساب. وجود حسابات literal موثق تاريخيًا؛ لم نفتح قيمها أو نتحقق من صلاحيتها هنا.
7. `04_upload_to_Fable_github:915–916` يبني URL يحويtoken ويمرره إلىgit clone؛ `run_cmd:324–334` يحجبtoken في رسالة الاستثناء عبرmask_token. إذن لا يصح الادعاء أن رسالة الخطأ حتمًا تطبعه كما هو. يبقى خطرargv وremote config للنسخة المؤقتة؛ لم يُشغّل السكربت ولا clone بهذا المسار. هذا uploader مستقل، وليس مسارREST الحالي للجسر كما يوضح4275–4285.

### 9.3 scripts: صلاحية القراءة لا تعني صلاحية التشغيل

| السكربت | الدليل من المصدر | قرار المراجعة |
|---|---|---|
| cleanup_redundant_venvs.py | base Windows عند42؛rmtree عند92؛main guard111 | قراءة فقط؛ اسمcleanup ووصفه «آمن» لا يبرران التنفيذ |
| migrate_existing_projects_to_fast_mode.py | local/parent registries21–24؛backup72؛write77 وreplace78 | migration فعلية؛ ممنوعة في هذا التكليف، ولا تضمنatomic replace وحدها سلامة كل الحالات |
| generate_docs.py | import الجسر13–15؛mkdir22؛write73 عندmodule scope | حتىimport ذو أثر جانبي؛ لم يُشغّل أو يُستورد |
| verify_docs_integrity.py | PROGRESS32–34 وdocs walk36–39 فقط؛امتداد.md حساس للحالة؛external/anchors تُتخطى57–58 | ليس شهادة مراجعة لكلroot/genspark/uppercase.MD ولا صلاحية الروابط الخارجية؛ يلزم فحص مخصص للتقرير |
| hadith_sijil.py | compile53؛unittest73؛failure قبلكتابةسجل النجاح، كما قرئ سابقًا | بوابة §6 حمراء؛ لا تشغيل جديد هنا ولا نجاح مصطنع |
| rebuild_refactor.py | asserts191–194 قبلrmtree199؛AST الأجزاء بعد حذفOUT | D01–D04 تثبت الخطر؛ لا real rebuild، والحماية يجب أن تبقى فعالة مع-O |

### 9.4 جرد كتّاب أولي وحدود استنتاج single-writer

أعيد AST للجسر والمحرك وQwen، مع إخراج أسماء الوظائف وأرقام الأسطر فقط. هذا جرد مرشحين وليس call graph كاملًا؛ البحث عن أسماء معينة قد يفوّت aliases أوmethods أوwriters خارجيين، وبعضjson.dump تخص المشاريع لا الحسابات.

- الجسر: `update_account_data:989–1022` كاتب الحسابات؛ reactivate1079 وcooldown1112 وrefresh1163/1194/1201/1212 وsender2961/2988 وfailover3296/3316/3469/3482/3512/3637/3655 عملاء كتابة. الـrefresh له مسار عزل عبرverifier منفصل، ويجب ألا يسقط من الجرد لمجرد أنAST المحدود لم يطابقmethod alias.
- المحرك: save_accounts962–968؛ pick_account1320؛ lock_pick_and_reserve1355؛ release_account1382؛ cli2791/2814؛ relogin2995/3017؛ balance3124؛ main3607/3658/3692/3735؛ parallel3931/3955. وجودها لا يثبت أنsend_chat بالجسر يستدعي جميعها؛ ولا يثبت غياب تشغيلCLI آخر على الملفات نفسها.01.03 يظلREAD-ONLY.
- Qwen: load_or_create_qwen_accounts227/245 و_save_qwen_accounts276/282–283. خزنة أخرى، لا تُدمج في المعزل الثلاثي؛ لكنها مهمة لجرد الأسرار وآثارimport والأدوات.
- verifier: VAULT_LOCK مستقل عنFILE_LOCK، كما ثبت في المراجعة السابقة؛05.02 لهsave_checkpoint وترتيبsource-first مستقل. لا تنشئRLock ثالثًا وتسمهتوحيدًا.
- المطلوب قبلGO التخزيني: خريطة paths الفعلية وnamespace/process/CLI والمشغلات التي يمكنها الكتابة، ودليل منعwriter ثانٍ. إن لم يثبتsingle-writer، تتوقف الخطة الدنيا ويُطلب إذن أقفال بين العمليات أو storage coordinator؛ لا يوهمنا نجاحthread test بضمان متعددالعمليات.

### 9.5 استكمال قراءة05.02 وحدود التغطية

أعيدت309–418 مباشرة: auth_status بعدrelogin عند352 لا يعاد حراسته قبلint(balance)367؛missing password364 قد يصبحDEAD؛retention372؛missing/empty list388 وتاريخ تالف397 يصبحانSTALE999؛sort نصي394؛now ثابت منself.now_utc402؛حد>= عند408؛exception يبتلع عند413–414 ثمAUTH_FAILED416. هذا يؤيد الأحكام السابقة ولا يمنح إذن نسخ المدير كاملًا.

سجل التغطية: استكمال السطور الطويلة00 NOTES18/21 وArena2497/2500 تم في الجلسة السابقة عبرtextwrap بحسب سجل الاستئناف، ولم يُعد هنا. لذلك عبارة «مبتورة» في §6.3 تصف لحظة القراءة الأولى فقط، لا آخر حالة قراءة. لا يزال لا يوجد ادعاء إعادة قراءة دلالية لكل4276 سطرًا منchat أو كلArena1–1884؛AST والجرد البنيوي ليسا ذلك. V1/V2 ما زالتا غير مكتملتين، والمطلوب التالي مصفوفة التحكيم وBEFORE/AFTER والخطة والاختبارات والمخاطر.


## 10. مصفوفة تحكيم الوكلاء وتقريرنا السابق

هذه محاسبة للأحكام لا للأشخاص. المرجع الزمني هوmain@d164758 والتقرير السابق عندf3eef4b؛ لا نحاكم أحدث وثيقة على مثال قديم دون قراءة التصحيح اللاحق. «صحيح» هنا يصف الاستنتاج المحدد، لا صلاحية ملف كامل أو جاهزية التنفيذ. D تشير إلى تشخيص منفذ موثق؛ ما عداها قراءة مصدر أو دليل مرحّل مصرح به، لا اختبار قبول منفذ.

### 10.1 أحكام00 و012345 وArena

| الادعاء/المصدر | الحكم بالأدلة | التصحيح الواجب في خطتنا |
|---|---|---|
| لا يوجدlive balance فيالجسر؛012345 NOTES461 | خطأ: sender2951 يفحصه؛ D12–D16 تثبت فجوات التعامل لا غياب الفحص | تعديل البوابات القائمة وربطها، لا وصفها اختراعًا جديدًا |
| tier=1 للمؤهل؛012345 NOTES453 | خطأ في المثال القديم؛ صححته535–537 و00 PLAN120 | نعترف بالتصحيح، لكنbool/NaN/mixed last_used وrandom-first-five ليست محلولة بذلك |
| لا startup cleanup ولا revival، والمحركمجمد | صحيح في أحدث00 PLAN118/133–135/325–331 و012345 NOTES538–540 | اتهام أحدث الخطة بإبقائها خطأ؛ المقاطع القديمة أرشيف تعارض، لا تكليف حالي |
| >=14 فيTASK103/303 مقابل>14 فيD1؛00 PLAN96/125/301–305 | تناقض داخل نفس الخطة؛UTC لا يحسمعامل المقارنة | اتجاه>=14 بحسب جواب المالك المنقولArena555؛ لا إعادة استفتاء تلقائية ولاGO |
| غيرSTALE يعنيهديةطبيعية؛00 PLAN263 و012345 NOTES483 | خطأ باقٍ فيpseudo-code؛UNKNOWN يندرج تحته | فرعRECENT موثوق فقط للتبريد؛UNKNOWN منفصل |
| RLock + replace = نقل ذري100%؛00 PLAN108/200/234 | ضمان زائد؛قفل العملية لا يوحدكتّابًا آخرين ولاtransaction لملفين | target-first/readback ثمsource-cut، pending/conflict ومنع اختيارالنسخةالمكررة |
| 13failure قديمة فلاbaseline أحمر؛012345 NOTES555–556 | خطأ منطقي: قدم الفشل يفسرسببه ولايغيرنتيجةالقياس؛§6 | لا نسبتها للهدية غيرالمنفذة، ولاادعاءأخضر. أسبابها ليستcompact/model فقط: password UX وparity ضمنالقائمة |
| مطابقة05.02 فيDEAD كافية؛012345 NOTES733–737 | غيرمثبت، والمديرنفسه يصنفmissing password كـDEAD عند364 | HTTP-first ثمschema/code موثق؛403عام واسمdomain_banned وحدهما ليساعقددليل |
| BEFORE الفلترحرفي؛012345 NOTES745–754 | خطأ؛الحقيقي2324–2331 مختلف؛D21 يثبتتراجعAFTER | لا نسخالمثال؛حفظالاستثناءات وإضافةدفاع عندالمخارج |
| staging وكلحدودPARTS؛00 PLAN140–143 | اتجاهصحيح تحسن عنتغييرالنهايةفقط؛لكنassert غيركافٍ مع-O | explicit validation وAST للجميعقبلdelete/swap؛D01–D04 |
| SHA-256 «تشفير» وrollbackبالanchors؛00 PLAN84/338–351 | SHA بصمة لا تشفير؛وجودanchorمتجانس غيرمضمون؛تشغيلrebuild مباشرةخطر | Gitrevision موحد،تحققtree وgenerated،وتراجعالبياناتمنفصل |
| Arena كشف-O/HTTP/path/claim/secret routes | صحيح للنقاطالمعادفحصها فيD01–D22 و§9 | لايعنيصحةكلالتقريرأوأنمختبراته acceptance منفذة |
| Arena ينتقدتقريرناالحالي | يحتاجقيدًا:1983 يحددb74900c،بينماالتقريرالمحفوظf3eef4b | نفصلنقدًا عولجسابقًا عنثغراتمازالتقائمة؛C1/-O/claim تحتاجتصحيحًا |
| Arena جرد203 ملفًا أوAST ناجح = مراجعةمعنويةشاملة | لا؛الجردبنيويلاقراءةكلسطر؛D10 يؤكدالعددعندmainالمحدد | سجلتغطيةمجزأ،ولا claim اكتمالكلchat/Arenaالقديم |
| OSRS/PR-18/75tests داخلArena1915–1969 | مادةغيرمتعلقةبهذاالمشروع | لا تنفذتعليماتها ولا تنسبنتائجها لـTTTTT |
| مطابقةدستوربولا/SRE/skills100% | غيرقابلةللإثباتبالمراجعالمتاحة؛Arena560 نفسهيسجلنقصها | نطبقAGENTS/GEMINI/بروتوكولالمستودع فقط،ولا شهادةخارجيةمختلقة |

### 10.2 إعادة تحكيم F01–F34 من تقريرنا

هذه مصفوفة34 بندًا كاملة من حيث **تغطية معرفات التقرير السابق**؛ لا تعني اكتمال مراجعة المشروع كله. مواضع المصدر هنا كافية لتعقب الحكم، وبعضها أعيد الآن وبعضها موثق في§6–§9 أو سجلالقراءةالموروث.

| المعرف | حكمV2 علىحكمنا | الدليل والتعديل |
|---|---|---|
| F01 | صحيح تاريخيًا،جزئي إذاعمم علىأحدثالخطة | 012345453 مقابل535–537؛sort مصححجزئيًا،randomfirst-five لايضمنالأعلى؛C1 عندنايفشلhuge-int |
| F02 | يلزمتصحيحالترجيح | 05.02:408 وArena555؛>=14 اتجاهالخطة،لا>14بحجةUTC |
| F03 | صحيح | 05.02:388–400؛absence/invalid ليستSTALE999؛اكتمالhistory شرطإثباتالتأخر |
| F04 | صحيحجزئيًا | sort394 وnow402 عيبان؛لكن.days>=14 يعادلelapsed>=14d للمدةغيرالسالبة،فلا ننسبخطأالمساواةلـfloor وحده |
| F05 | صحيحمعحدودschema | parse/عرض05.02:132/153؛UTC-aware وZoneInfo؛naive يحتاجعقدمنطقةموثوقًا لا تخمينًا |
| F06 | صحيحمثبتتشخيصيًا | verifier160–165؛D07 يثبت502/password→INVALID_CREDENTIALS |
| F07 | صحيح | verifier119 و05.02:364؛missing credentials ليسدليلinvalid منالمنصة |
| F08 | صحيح | verifier298–303؛statusجديد/مفقود قديموتخطأ؛لاschema evolution كعقوبة |
| F09 | صحيحلكنحارسناغيركافٍ | verifier286–290 وD06؛D12–D16؛C1 يحتاجتعديلD22 وحمايةbool/nonfinite |
| F10 | صحيحمنالمصدر،لاreproduction جديدهنا | verifier295–337 يهيئretention داخلuser200 فقط؛payload363–365 يقرأهخارجالشرط؛exception372 قديسميالخطأNETWORK_ERROR |
| F11 | صحيحمثبت | verifier397–404 وD08؛corrupt/non-list→[] ثمoverwrite |
| F12 | صحيح | 05.02:525قبل527–529؛نتائجatomic_saveمهملة؛target-first ليسكلالحل |
| F13 | صحيحبشرطمنعالضمانالمطلق | FILE_LOCK وVAULT_LOCK مستقلان؛§9.4 جردأولي؛single-writer لم يثبتتشغيليًا |
| F14 | صحيح | verifier407–430 duplicate→False؛bridge1160/1163 يهملالحفظ؛يلزمتمييزalready-present/conflict/failure |
| F15 | صحيح،وناقصclaimcleanup | snapshot3214/claim3242؛D20 يثبتتسربclaim قبلtry؛re-read قبلprobe وقبلcommit |
| F16 | صحيح | gve.check_live_balance وsess في012345472/479 ليستواجهاتجاهزةموصولة؛C2 عندنا أيضًاpseudo-codeلاpatch |
| F17 | صحيحمعتصحيحالتعميم | 00PLAN263 و012345483؛D18بلاURL→cooldown،D19معURL→success metadata؛الحالاتمحقونةلعقدمستقبلي |
| F18 | صحيحمنالمصدر | bridge1198–1218 fallback وعقوبة30m؛التمييزقبل وبعدbusiness-send ضروري |
| F19 | صحيحضمنالمحركفقط | 01.03:1093–1108 و1298؛حارسالجسرلايصلحCLIالمستقل؛لا إذنلتعديله |
| F20 | صحيح،وإصلاحناسابقًاناقص | D01–D04؛كلحدودPARTS و-O وstaging؛normalizedparity ليستrawbytes |
| F21 | تاريخيصححتهأحدثالخطة | 00PLAN118 claim-timeقرائي؛لاstartupmutation حاليًا؛لااستمرارفياتهاممقترحملغى |
| F22 | صحيحمعفصلالأرشيف | revival/success/dead خارجدمجالجسر؛حمايتها منالنسخ تظلواجبة؛لااستيراد05.02 |
| F23 | صحيحبحدودالدليل | أرقام185/130/279 روايةبيئةغيرمتاحة؛legacy اسمفعليفيverifier،لا إثباتوجودملفحساباتحيالآن |
| F24 | صحيح | SHAبصمة؛rollbackموحد؛الأمنيشملtemp/backup/REST لاgitignoreفقط |
| F25 | صحيح | اختباراتقليلةلا تثبتغيابPermissionError أوWindowsbehavior؛faultmatrix مطلوبة |
| F26 | صحيح،مصدر/دليلسبق | 05.02:61 dependency و86signal؛compileلايثبتimportآمن؛لم نستوردالمدير |
| F27 | صحيحوأعيدتقراءته | 05.02:352ثم367 دونحراسةauth_status الجديدة؛إعادةفحصبعدالتجديد لازمة |
| F28 | صحيح | retention372 يسبقحراسةdry_run فيsave486؛dry_runالمحليلايعنيHTTPread-only |
| F29 | صحيحوأعيدتقراءته | backup522–523 عندfinal؛5writes525–529 بلاbool؛رسالة599 تقول3ملفاتونجاحًا غيرمتحقق |
| F30 | صحيح | verifier411–417 يفرضsuspended/zero/emptycookies؛حفظالحقولللاسترداداليدوي منفصلعنreason |
| F31 | صحيح،ومعيارناناقص | last_used/reactivate قبلprobe؛zero-mutation سببيةللمحاولة؛fullhash فيعزل لا underconcurrency |
| F32 | صحيحكتعارضقديم؛الحالةالآنمجمدة | أحدث00/012345 وتقريرناC5 يثبتREAD-ONLY؛verifierأيضًايحتاجإذننطاق بسببAGENTS22 |
| F33 | صحيح | PRIMARY مكانلغيرالمعزول،قديشملcooldown؛membership ليستreadiness |
| F34 | صحيح | liveprobe لقطة وليسرصيدًا محجوزًا لدىالمنصة؛credit-in-flight يظلخطرًا ولاblindresend |

### 10.3 تصحيح BEFORE/AFTER C1–C8 الخاص بنا

- **C1:** يبقىفرزcached خيارًا لاافتراضيًا؛تصحيحhuge-int موضح§9.1،ولاوعدhighest-first معrandompool.
- **C2:** عبارة «داخلtry/finally القائم» غيركافية؛يبدأcleanup فورclaim،لا عند3298 فقط. re-read قبلprobe وrevalidate عندcommit؛حالةغيرREADY تحتاجdispatchصريح قبلURL-success/genericcooldown،وعدم إسقاطURL/checkpointالقائم.
- **C3:** المبدأHTTP-first صحيح،لكنhelpers مقترحةومصدرأكوادالموت غيرموثقكفاية؛403 وحدهلايكفي. AGENTS22 لايسمحبتعديلverifier تلقائيًا؛يلزمإذنإضافي.
- **C4:** مثال>14 فيالتقريرالقديملايحكمV2. AFTER التخطيطي: احسبelapsedUTC؛negative/naive/malformed→UNKNOWN؛recent الموثوق عندelapsed<14d ينفيالتأخر؛elapsed>=14d لايثبتSTALE دونhistoryكافٍ. غيابlastgift يحتاجدليلنافذةكاملة لا999؛schemaهذاالمسارلميثبتمنHAR.
- **C5:** مؤجل خارجالمسارالأساسي؛لاادعاءاستئصالالتخمينمنكلالمحرك بحارسالجسر.
- **C6:** target-first/readback/source-cut صحيحكأساساسترداد،لاtransactionكاملة؛unique temps وfsync/error policy وversionconflict ومنعاستخدامالمكرر مطلوبة. لاreturn MOVED قبلreadbackللطرفين.
- **C7:** أضفحماية-O وvalidation لكلالأجزاءقبلالمساسبالوجهة،واختبارفشلالswap. لا تسميread_text parity «تطابقبايت100%».
- **C8:** حفظالتاريخصحيح؛عبارات«الآنأعيدت» فيالأقسامالقديمةتقرأبتاريخدفعتها. current_execution يجبألايعرضعائقcurlالموروث كعائقحالي،ولا يعدDتشخيصاتاختباراتقبول.

### 10.4 ما لم يثبت بعد، وما لا يحتاج إعادة سؤال

لا نعيد طلب إذنrevival/startupcleanup/TTL أو رفع تجميد01.03؛ هذه مستبعدة. اتجاه>=14 لهprovenance واضح،ويذكر فينسخةالاعتمادلا كاستفتاءجديد. يبقىقبلأيimplementation: GO محددبالrevisionوالملفات؛schema منقح للهدية واكتمالpagination؛allowlist أدلةfailed؛إثباتsingle-writer أوإذنحلأوسع؛عقودbaselineالأحمر؛سياسةcredit-in-flight. الترتيبالافتراضييبقىكماهو،فلايتوقفالمسارالأساسيعلىاختيارفرزجديد. migration/security UX/live/merge/deploy كلمنهاخارجGO الضمني. اكتمالمصفوفة34معرفًالا يحولهذهالأمورإلىمحسومة.
