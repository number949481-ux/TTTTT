# مراجعة مستقلة ثانية وخطة دمج الهدية والمعزل الثلاثي

## 0. التكليف ونقطة الحفظ

> أحدث حالة في رأس PROGRESS و§15. أعيد بناء ملحق الاستئناف بعد فقد checkpoint المحلي8e96db4؛ ليس استرجاعاً حرفياً. مصادر§1 وأحكام§9–§10 مرتبطة بإصداراتها التاريخية؛ تحديث المصادر الحالي main@adaf586. لا GO أو نشر جديد مثبت.

- طلب المالك الحالي يعيد فتح المراجعة من البداية ويطلب ملفًا جديدًا؛ ينسخ تعليمات «لا تعد المراجعة» في سجل التسليم السابق، ولا يمنح GO للتشغيل.
- تاريخ البدء: 2026-10-29. أساس المصادر الأحدث: `d16475814bebf7379b097e26587698194582941c`. استعيد تسليمنا السابق `f3eef4b3a55cdf6ed321b76a7e6eb3a53ae2159c` على فرع `genspark_ai_developer`، ثم زومنت main داخل الفرع، لا العكس.
- الحالة الآن: **المراجعة الجديدة قيد العمل**. الملف الجديد لا ينسخ صحة أحكام التقرير السابق تلقائيًا، ولا يزعم اكتمال القراءة أو نجاح اختبارات لم تُعَد.
- النطاق: الملف الجديد و PROGRESS و recovery؛ التقرير السابق محفوظ دون تعديل، وكذلك وثائق الوكلاء و Python/tests/generated والحسابات. لا live أو migration أو merge/deploy أو تشغيل 05.02.
- التفريغان المرفقان نص من المالك؛ لا ادعاء سماع التسجيل الأصلي. دستور بولا/SRE الخارجي غير متاح فلا شهادة مطابقة له.

## 1. سجل المراجع المثبتة عند d164758 — تاريخي؛ التحديث في §15

تم جلب أحدث Git فعليًا. التغيير الوحيد من d2eb49d إلى d164758 هو إضافة 1446 سطرًا إلى Arena؛ أول 1884 سطرًا مطابقون تمامًا. أصبح الملف 3330 سطرًا. Python/tests/generated لم تتغير. هذه مقارنة إصدارات، لا حكم مسبق بصحة الإضافة.

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
- AGENTS.md و GEMINI.md و 00_MASTER_RESUME_PROTOCOL.md و README/PROGRESS: حوكمة متاحة، مع فصل الأرقام التاريخية عن القياس الحالي.

## 2. خطة المراجعة المجمدة

| المرحلة | العمل | الحالة |
|---|---|---|
| V0 | استعادة الفرع ومزامنة المصادر وتثبيت التكليف الجديد والبصمات | مكتملة؛ النشر يتحقق من remote |
| V1 | إعادة قراءة المصادر وكشف المكرر وغير المتعلق بالمشروع وتدقيق قرارات المالك المنقولة | قيد العمل |
| V2 | إعادة تتبع كود الرصيد والهدية والعزل والكتابة والمولد والأمن؛ تجارب مستقلة محدودة | لم تكتمل |
| V3 | محاسبة أحكامنا وأحكام الوكلاء وصياغة BEFORE/AFTER وخطة صغيرة بعقود اختبار | مسودة مكتوبة في§10–§13؛ تنتظر مراجعة الاتساق النهائية |
| V4 | تحقق كامل للوثائق وسجل الاستئناف وتسليم PR9 Draft | تحقق بنيوي أولي ناجح؛ التغطية والتحرير النهائي قيد العمل |

## 3. ملاحظات أولية تحتاج التحكيم

- Arena1915–1969 يتضمن نصًا عن OSRS/Goblin Diplomacy و PR-18؛ لا يُنسب إلى TTTTT أو يُنفذ أمره. يلزم فصل تلوث المرجع عن المراجعة ذات الصلة التي تبدأ 1979.
- Arena1983 يقارن تقريرنا عند b74900c، لا آخر f3eef4b؛ يجب فحص إن كان النقد قد عولج بالفعل قبل وصفه خطأ حاليًا.
- الإضافة تثير نقاطًا مهمة لم يغلقها تقريرنا: أثر python -O على assertions المولد، ونطاق الإذن لتعديل verifier، وحدود zero-mutation تحت التزامن. ستراجع من المصدر، لا تُعتمد لمجرد ورودها.
- Arena ينقل مجددًا جواب «زي 05.02» ويختار >=14؛ يلزم فصل هذا النقل عن توجيه مباشر في محادثتنا وعن تناقض وثائق 00/012345. لا تبدأ عملية عزل الآن بأي تفسير.

## 4. الاستئناف

بعد reset: افحص remote و PR9 ثم هذا الملف و PROGRESS/current_execution. احفظ كل دفعة commit/push وتحقق مساواة HEAD و remote؛ لا تكتب hash الدفعة داخل نفسها. لا تحول حالة «قيد العمل» إلى اكتمال بلا قراءة وفحص. النتائج القديمة في التقرير السابق تاريخية حتى إعادة التحقق المطلوبة هنا.

## 5. دفعة استعادة بعد reset جديد — 2026-10-29

- استعيد `3111f8f2b50d39da115b89cac7d54283f40447c0` فعليًا من remote؛ main ما زال `d16475814bebf7379b097e26587698194582941c`. الخطة V0–V4 والنطاق في §0–§2 مجمدان؛ الاستئناف ليس إذن تنفيذ.
- **أدلة من ملخص الجلسة المنقطعة، لا إعادة تشغيل في هذه الدفعة:** syntax ناجح؛ pytest:1072 passed/13 failed/+60 subtests؛ canonical:1085 tests/13 failures. سجلاتها المحلية لم تستعد بعد reset، لذلك لا نخلطها بقياسات هذه الجلسة.
- المولد، بحسب ذلك الملخص: الوضع العادي يوقف على 9181 مقابل 9285 ويحفظ marker؛ optimize=1 أو تغيير نهاية PARTS وحدها يحذف OUT المؤقت ثم يفشل p03 بعد كتابة 3 أجزاء. hashes الشجرة المولدة الحقيقية لم تتغير في تلك التجربة. هذه أدلة مرحّلة سيعاد توثيق تحقق مستقل منها.
- بقية المختبر السابق **لم تنفذ**: توقف عند استيراد `curl_cffi` المفقود. لا نتائج جديدة مثبتة منه للرصيد أو claim أو verifier أو HAR/AST. سنستعمل استخلاص AST للوظائف أو mocks مناسبة دون تثبيت عشوائي ودون استيراد 05.02.
- القراءة غير مكتملة: Arena2490–2809 و 3090–3330، وأجزاء المصادر الأخرى المذكورة في خطة الاستئناف. لا ادعاء قراءة شاملة جديدة أو اكتمال التقرير.
- سياسة مقاومة reset: دفعات توثيق صغيرة، commit ثم fetch/دمج عند الحاجة ثم push ثم مساواة HEAD/remote وتحديث PR9 Draft. النشر لا يثبت حتى تحقق remote؛ لا إعادة كتابة تاريخ الدفعات المحفوظة أثناء الاستعادة.

## 6. فحوص مستقلة منفذة بعد الاستعادة — دفعة الأدلة الأولى

هذه النتائج **أعيدت فعليًا بعد b1cf1a0** على Python3.13.14. كود الإنتاج مطابق لـ main@d164758؛ لا تعديل أو استيراد للمدير 05.02. استُخلصت وظائف verifier و resolver من AST دون تنفيذ module imports، وأعطيت fake sessions وبيانات اصطناعية فقط. ملفات التجربة تحت `.tmp` عبر TemporaryDirectory. المولد نُفذ في namespace مستقل مع OUT مؤقت؛ لم يُشغّل على bridge_refactor الحقيقية. هذه تشخيصات للعيوب القائمة، لا اختبارات قبول لميزة منفذة.

### 6.1 نتائج قابلة للتحكيم

| المعرف | التجربة الفعلية | النتيجة والحكم |
|---|---|---|
| D01 | compile للمولد بـ optimize=0 ثم main على خريطة PARTS الحالية | AssertionError: التغطية 9181≠9285؛ marker باقٍ؛ صفر أجزاء مكتوبة |
| D02 | نفس المصدر بـ optimize=1، بلا تعديل PARTS | marker حُذف؛ كُتبت 3 أجزاء ثم فشل AST في p03: ` '(' was never closed`، السطر 652 من الجزء؛ رسالة «تغطي بالكامل» ليست تحققًا حقيقيًا هنا |
| D03 | optimize=0 وتغيير نهاية آخر جزء في الذاكرة فقط إلى 9285 | النتيجة التدميرية المؤقتة نفسها؛ إصلاح النهاية وحدها غير كافٍ |
| D04 | SHA256 لكل ملف في generated الحقيقي قبل وبعد D01–D03 | متطابقة؛ لم يحدث real rebuild |
| D05 | fake balance HTTP502 ونص user_suspended، مع cookie اصطناعية | master verifier أعاد SUSPENDED/is_dead=True/balance0؛ تصنيف موت كاذب مؤكد في المسار المجرب |
| D06 | fake balance HTTP502، و user200/status0/retention enabled | EMPTY_BALANCE/balance0/is_dead=False؛ الخطأ المؤقت تحوّل لصفر |
| D07 | fake B2C landing بمفاتيح وهمية ثم POST502 بنص password verification temporarily unavailable | INVALID_CREDENTIALS؛ الحكم مبني على النص قبل HTTP |
| D08 | خزنة مؤقتة تحتوي`{broken`، ثم quarantine(account, 'SUSPENDED', directory, 'synthetic') | رجعت True واستبدلت الملف بقائمة من سجل واحد؛ فساد التخزين لا يوقف الكتابة |
| D09 | get_accounts_file_path بمسار صريح مفقود و resolve_shared_path mocked لملف آخر موجود | أعاد الملف الآخر؛ لا ضمان أن النقل سيستعمل المصدر الصريح المقصود |
| D10 | جرد main باستخدام git ls-tree -rz وفحص AST دون import |203 ملفات:96py+19anchors+81Markdown+2HAR+5 أخرى؛ 115AST ناجحة؛ 40 ملف اختبار، لا تعني 40 اختبارًا فقط |
| D11 | قراءة JSON بنيوية لملفَي HAR دون طباعة headers/body/URLs |286 و 4356 entries؛ صفر URL يحتوي`/api/credit_audit/`؛ لا يثبتان schema/pagination لواجهة الهدية |

**تصحيحان في مختبرنا نفسه:** المحاولة الأولى للجرد استخدمت فواصل الأسطر فعدّت أسماء Git العربية المقتبسة خطأً (72Markdown/14 أخرى). أُلغيت هذه الأرقام وأعيدت بـ NUL، والنتيجة المعتمدة D10. كما مُرر dict بدل str في وسيط verdict بأول تجربة خزنة؛ أُعيدت D08 بالتوقيع الصحيح أعلاه وأثبتت الاستبدال. لا نخفي عيوب أدوات الفحص ولا ننسبها للمنتج.

لإعادة D01–D03 دون تعديل المصدر: اقرأ scripts/rebuild_refactor.py، `exec(compile(text, path, 'exec', optimize=0 أو1), ns)` مع`__name__` غير main؛ اضبط`ns['OUT']` إلى مجلد مؤقت يحتوي marker؛ في D03 غيّر tuple الأخير في`ns['PARTS']` داخل الذاكرة فقط. نادِ`ns['main']` والتقط AssertionError/SystemExit. قارن raw hashes لشجرة generated الحقيقية قبل وبعد. لا تستبدل هذا بإطلاق CLI على المشروع الحقيقي.

### 6.2 البوابات الحالية، لا أرقام README التاريخية

- `python -m py_compile` للجسر والمحرك و verifier و 05.02 والمولد: Exit0؛ compile ليس import ولا تشغيل حسابات.
- `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/user/webapp/.tmp python -m pytest -q -p no:cacheprovider`: **1072passed/13failed/+60subtests، 5.41s، Exit1**.
- `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/user/webapp/.tmp python -X utf8 scripts/hadith_sijil.py`: **1085tests/13failures، 3.003s، Exit1**. توقفت قبل كتابة سجل نجاح؛ tracked tree بقي دون تعديل.
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

- Arena أصاب في خطر-O وفي تصنيف 502 والخزنة والف allback وفي الجرد البنيوي. هذه المطابقة مستقلة الآن، وليست تصديقًا شاملًا لوثيقته أو مختبراته.
- تقريرنا السابق أغفل-O؛ AFTER المقترح للمولد يجب أن يستعمل explicit exceptions لا assert للحماية، وأن يتحقق من التغطية و AST **لكل** الأجزاء في staging قبل المساس بالوجهة. swap/rollback نفسه يحتاج اختبار فشل، وليس ضمان transaction مطلقًا.
- BEFORE verifier: `is_suspended_response`83–105 و master257–258 و B2C160–165. AFTER التصميمي: HTTP/transient أولًا، ثم أدلة structured/allowlist؛ missing credentials ليست invalid مثبتة؛ UNKNOWN ليست صفرًا. تعديل verifier يتطلب توسيع نطاق صريح بسبب AGENTS22؛ لم يُنفذ.
- BEFORE vault:396–404 تحول فساد JSON/non-list إلى[] ثم replace421–424. AFTER التصميمي: typed read failure يوقف mutation؛ نسخ موثقة و target-first/readback/source-cut ضمن عقد writers موحد. نجاح replace لملف واحد ليس نجاح نقل بين ملفين.
- BEFORE path:957–970 يسمح fallback. AFTER التصميمي: حارس نقل موضعي يثبت المسارات الصريحة ويحظر fallback عند خطأ؛ **لا تعديل resolve_shared_path/P23**.
- استُكملت قراءة Arena2490–2809 و 3090–3330 في هذه الجلسة؛ سطور التفريغ الطويلة 2497/2500 عُرضت مبتورة بالأداة، لذلك لا نسميها قراءة كاملة. الملحق الأخير جرد آلي مرجعي عند d2eb49d، لا claim مراجعة دلالية لكل سطر. بقية إعادة قراءة المصادر لم تكتمل بعد.
- التالي: تشخيص sender/failover/claim ثم استكمال provenance لحد 14 وكتّاب التخزين والأمن، وصياغة الخطة التفصيلية. لا نتائج جديدة حتى الآن لتلك المسارات في هذه الدفعة.

## 7. نتائج الجسر المحفوظة من الفحوص السابقة مباشرة للمقاطعة

عند إعادة تأكيد التكليف استعيد 2b03cb0 من GitHub، وأعيد fetch فعليًا؛ main ما زال d164758 و Arena بنفس البصمة. لم تظهر نسخة أحدث في remote حتى هذه النقطة. فُقدت`.tmp` بعد reset، لكن **نتائج الأدوات المسجلة في المحادثة** التالية نُفذت فعلًا بعد 2b03cb0 وقبل المقاطعة؛ لم نعدها في دفعة حفظها هذه.

### 7.1 المنهج وحدوده

استُعمل fixture القائم `tests/test_credit_completion_recovery.py:25–63` دون تعديله: engine/send/read/update/refresh والواجهات الجانبية mocks، مجلدات اصطناعية داخل workspace. حُظرت socket.connect و socket.create_connection و requests.Session.request؛ curl_cffi غير مثبت وتم تجاوز استيراده الشرطي دون تثبيت. لا HTTP حقيقي. القياس هنا لاستدعاءات writers و send mocks، **ليس byte-diff لملفات حسابات فعلية** ولااختبار نظام إنتاج كامل.

| المعرف | المدخل الاصطناعي | النتيجة المثبتة |
|---|---|---|
| D12 | balance=-1 مع last_refresh حديث | send_chat مرة، COMPLETED من fake، لا cooldown |
| D13 | balance=NaN مع last_refresh حديث | send_chat مرة، COMPLETED من fake، لا cooldown |
| D14 | balance=+Infinity | send_chat مرة، COMPLETED من fake، لا cooldown |
| D15 | balance sequence[-2,-1] مع refresh mocked ناجح | send_chat مرة بعد unknown، COMPLETED |
| D16 | balance sequence[100,-1]؛ أول send يرمي 401 ثم refresh mocked | send_chat مرتان، COMPLETED؛ حارس ما بعد 401 يسمح unknown |
| D17 | sender محقون TIMEOUT، بلا URL أو مع URL، max_account_attempts=1 | TIMEOUT؛ last_used writer استُدعي؛ لا cooldown ولا last_success؛ claim محرر |
| D18 | sender محقون UNKNOWN أو TRANSIENT أو AUTH_FAILED **بلا URL** | MAX_ATTEMPTS_EXHAUSTED؛ last_used و cooldown_until>0 استُدعيا؛ claim محرر |
| D19 | الحالات الثلاث نفسها **مع URL** | تعود الحالة نفسها؛ last_used و last_success_at/status active/cooldown0؛ claim محرر |
| D20 | get_account_fingerprint يرمي RuntimeError بعد claim | الاستثناءيصعد ويبقى claim واحد؛ نُظّف synthetic claim يدويًا بعد assert |

D18–D19 حقن لعقود حالات مقترحة، لا ادعاء أن sender الحالي ينتج هذه الأسماء بنفسه. D19 يثبت أن إضافة status جديد دون dispatch صريح قد تجعل وجود URL دليل نجاح زائفًا. التصحيح: ليس كل UNKNOWN يبرد 5 دقائق؛ النتيجة تتوقف على URL ومسار dispatch.

**تصحيح أدواتنا:** أول mock أعاد 4 عناصر بدل 5 فتوقف بـ ValueError. ثم توقع المختبر mark_account_cooldown بينما generic branch يكتب cooldown مباشرة عبر update_account_data، ومرر cfg كوسيط email الثالث بدل bridge_cfg keyword. أُلغيت استنتاجات تلك المحاولات، وأعيدت المصفوفة كاملة بالتوقيع الصحيح `bridge_cfg=case.cfg`، tuple ذي 5 عناصر، وفحص writer نفسه. آخر تشغيل أعاد `FINAL_FAILOVER_MATRIX_ALL_ASSERTIONS_PASSED` و Exit0. أرقام D17–D20 تخص هذا التشغيل المصحح فقط.

### 7.2 BEFORE الحقيقي و AFTER المطلوب، لا patch منفذ

- **رصيد:** `01.33:2954–2967,2973–2978,3098–3106`: الحارسان بعد refresh يوقفان low فقط؛ -1/NaN ليستا low. AFTER: نتيجة typed مؤكدة finite/nonbool/nonnegative، وحارسواحد يعاد في البوابات الثلاث، بلا send عند UNKNOWN. الحساب الذي بلغه 100 يقفزعنهدية؛ الثابت الافتراضي 100 لا يلغي الحاجة لتوثيق override.
- **claim:** claim عند 3242، reactivate3270، fingerprint3280، last_used3296، try3298، finally3657–3660. AFTER: تبدأ منطقة cleanup فور نجاح claim وقبل أي عملية قد ترمي؛ release داخل finally محمية حتىإنفشلإغلاق span. لا double release غيرمالك، ولا HTTP داخل قفل ملف طويل.
- **dispatch:** `if pub_url or status == "COMPLETED"` عند 3630؛ generic cooldown3655. AFTER: dispatch صريح للحالات المؤكدة/المؤقتة/فشلحفظ/uncertain-send قبل success أو fallback؛ URL وسيلة استرجاع وليس دليل نجاح. TIMEOUT قبل business-send يمكنتخطيه؛ بعد send محتمل يوقف أو يستعلم بعقد idempotency، ولا blind resend.
- **zero-mutation:** last_used يكتبقبل probe؛ reactivate قديكتبأيضًا. AFTER: لا كتابة منسوبة لمحاولة probe مجهولة؛ عرّفنقطة commit للكوكيز والرصيد والاستخدام. ثبات hash الملف كله يختبر في عزل؛ تحت التزامن نفحص الأثر السببي وسجل ال writes كيلايحسب write مشروع آخر مخالفة. لا يعالج ذلك بحبس مُلْك ملف طوال HTTP.

### 7.3 اتجاهحد 14: تصحيح منهج التحكيم

Arena:555 ينقل نص جواب المالك «مش فارقه زي سكربت بتاع 05.02»، و 1988/2010 يؤكد>=14. هذا **نقل موثق في مرجع طلب المالك إدراجه**، ليس سماعًا منه ولا GO جديدًا. الترجيح التخطيطي الآن: **elapsed>=14×24 ساعة** عند أدلة هدية صحيحة وكافية، اتباعًا للجواب المنقول؛ لا استفتاء جديد تلقائي على مساواة حسمها المرجع. يوضع هذا الافتراض صريحًا في طلب اعتماد النسخة، وللمالك تصحيحه إن كان النقل غير دقيق.

نقدنالسابق: دقة UTC لا تختار `>` بدل`>=`؛ مدح 00/012345 لاقتراحنا>14 كأنه قرار مالك غير مبرر. إبقاء السؤال قديمًا كأنه لا حل له أهمل provenance المنقول. في المدد غير السالبة،`.days>=14` يكافئ elapsed>=timedelta(days=14)؛ floor وحدهليسعيبحد>=. العيوب الفعلية في 05.02 تشمل الوقت المجمد، التاريخ غير الواعي/التالف/المستقبلي، فرزالنص، واكتمال التاريخ. لا تستنسخ أخطاء المدير مع اعتماد حده.


## 8. استعادة ea9ab27 وتجميد النطاق — 2026-10-29

- بدأ workspace بعد reset على main؛ أُجري fetch و ls-remote واستعيد فرع `genspark_ai_developer` عند `ea9ab278d4b938cf1815ade4f9919d3daf01740f`. main ثابت عند `d16475814bebf7379b097e26587698194582941c` ومضمّن في الفرع. الشجرة كانت نظيفة.
- تحقق SHA256 مجددًا: Arena مطابق لبصمة §1؛ التقرير السابق `342b4ca585be8df4934acb7681b51be662d6a98632158c46a248f3625280ae0d` محفوظ دون تغيير. لا نسخة أحدث ظهرت في fetch الحالي.
- خطة V0–V4 مستمرة؛ V1/V2 جزئيتان، V3/V4 غير مكتملتين. هذه الدفعة للاستعادة فقط، وليست تسليمًا نهائيًا أو GO. النطاق ثلاثة ملفات: هذا التقرير و PROGRESS و recovery.
- نتائج D01–D20 والبوابات في §6–§7 أدلة محفوظة من الجلسات السابقة؛ لم تعَد بعد reset الحالي. baseline الموثق أحمر: 13 failure؛ لا نفترض بقاء logs المحلية.
- أول عمل تالٍ: إكمال التشخيص المنقطع للفلتر و`math.isfinite(10**1000)` وقراءات 05.02/Qwen/uploader، ثم تتبع snapshot وبطاقة كلمة المرور، وتوثيق scripts والكتّاب. لا ننسب نتيجة للأداة المنقطعة.
- لا Python/tests/generated/accounts edits؛ لا استيراد أو تشغيل 05.02؛ لا Genspark/Telegram/Qwen live أو migration أو merge/deploy. Arena مرجع دائم؛ لا تعديل له أو لوثائق الوكلاء الأصلية. لا أسرار أو HAR خام في الوثائق.
- كل دفعة: commit ثم fetch ودمج main عند الحاجة ثم push ثم مطابقة HEAD مع remote و PR9 والتأكد من Draft. يُسجل hash السابق داخل الدفعة؛ hash الحالي يُتحقق خارجيًا بعد النشر.


## 9. التشخيص المنقطع، الأمن والكتّاب — أدلة جديدة بعد fef72ea

هذه الدفعة قراءات مصدر وتشخيص AST معزول، لا استيراد للجسر أو 05.02/Qwen/uploader ولا اتصال بالخدمات. نتائج البوابات في §6 لم تعَد. الملفات الأصلية والتقرير السابق محفوظة دون تعديل.

### 9.1 نتائج D21–D22 ونقد أدواتنا

| المعرف | المنهج والمدخل | النتيجة الفعلية وحدودها |
|---|---|---|
| D21 | استخراج `_is_never_copy_file` الحقيقي من AST للجسر:2324–2331، واستخراج AFTER فقط من 012345 NOTES:757–766، وتنفيذهما في الذاكرة على 15 اسمًا اصطناعيًا | تسعة أسماء محجوبة حاليًا أصبحت غير محجوبة بالمقترح، أدناه. Assertions نجحت و Exit0. لا snapshot أو upload فعلي في هذا التشخيص |
| D22 | `math.isfinite(10**1000)`، وهو الشرط نفسه في C1 من تقريرنا السابق:381–382 | `OverflowError: int too large to convert to float`. مثالنا المقترح غير كافٍ؛ هذه ليست مشكلة أضفناها إلى runtime، لأن المثال وثيقة فقط |

تفصيل D21، حيث True تعني **منع النسخ**:

| أسماء العينة | الحالي | المقترح |
|---|---|---|
| bundle.tar.gz؛ bundle.tar؛ bundle.zip؛ record.failed | True | False |
| .env.local؛ accounts_genspark.json؛ accounts_qwen.json؛ accounts_deepseek.json؛ keys.txt | True | False |
| accounts_failed.json؛ accounts_delayed_gifts_credits.json | False | True |
| .env | True | True |
| dead_accounts.json؛ telegram_bot_token.txt؛ accounts_genspark.json.tmp_1234 | False | False |

العدد 9 خاص بهذه العينة، لا تعداد لكل الأسماء الممكنة. عبارة «سبعة» في التقرير السابق تصف عينة أقدم؛ لا تُستعمل حدًا أقصى للتراجع. BEFORE في 012345 NOTES:745–754 ليس الدالة القائمة أصلًا. AFTER المطلوب تصميميًا: الحفاظ على جميع الاستثناءات القائمة، وإضافة الخزائن والـ legacy و success/dead والنسخ المؤقتة والاحتياطية والأسرار، مع فحص basename والمسار المطبّع عند حدود snapshot/archive/REST، لا الاعتماد على `.gitignore`. لا حظر شامل لكل JSON يفقد ملفات المشروع السليمة.

**خطأ مختبرنا الحالي:** المحاولة الأولى فشلت بـ IndentationError عند تحليل code fence المزاح، قبل مقارنة الأسماء أو فحص huge-int. صُححت بـ`textwrap.dedent` واختيار الكتلة التي تحتوي الدالة والخزنة الجديدة، ثم تحقق وجود كتلة AFTER واحدة. لا تُنسب نتائج المحاولة المصححة إلى المحاولة الأولى.

**تصحيح C1 المقترح:** لا تمرر كل int إلى تحويل float ضمني. حدد مجال القيم حسب الحقل؛ `type(value) is int` يعالج بحدود صحيحة مباشرة، و`type(value) is float` يفحص finite، و bool والنصوص و NaN/Infinity والمدخل خارج المجال تعاد كبيانات غير صالحة. للرصيد: لا حد أقصى اعتباطي دون schema؛ يمكن رفض الحجم غير المدعوم صراحةً كـ UNKNOWN بدل crash. للاستخدام الزمني: مجال timestamps مستقل. الـ default الخاص بترتيب cached لا يصبح رصيدًا حيًا موثوقًا. هذا عقد مقترح يحتاج قبولًا واختبارات، لا patch منفذ.

### 9.2 مسار النسخ والأسرار: من المصدر إلى المخرج

1. `snapshot:4592–4699` يحصر الملفات ويستدعي الفلتر الحقيقي على `item.name` عند 4608، ثم مرشح مجلدات على المسار عند 4612؛ النسخ الفعلي عند 4616. إذن ليست هناك طبقة snapshot بلا فلتر مطلقًا؛ العيب هو نقص قائمته وغياب دفاع مستقل كافٍ عند المخارج الأخرى.
2. `_write_checkpoint_archive:4462–4475` يضيف عناصر checkpoint إلى tar دون فحص أسرار خاص به؛ snapshot يستدعيه عند 4663. إن مر ملف حساس عبر snapshot، لا يظهر في هذه الطبقة حارس آخر يمنعه. هذه قراءة مسار، لا تجربة تسريب ملفات حقيقية.
3. `_default_github_uploader:4275–4356` يفحص `_should_skip_archive_member` عند 4307؛ هذا يستبعد مجلدات cache/git/node_modules عند 2317–2321 ولا يصنف أسرارًا. يقرأ الملف عند 4322 ثم PUT عند 4331. لا يقرأ `.gitignore` في هذه الدالة. كذلك مسار DELETE عند 4337–4351 يحتاج سياسة منفصلة: إضافة فلتر يجب ألا تحوّل ملفات مستبعدة تلقائيًا إلى حذف بعيد بلا قرار؛ snapshot يبني deleted_files عند 4642–4654.
4. لذلك يجب اختبار `upload_files` و`delete_files` و queue القديمة و archive، لا نجاح فلتر منفرد فقط. التحقق النهائي من provenance ومسار الملف داخل checkpoint ضروري؛ لا ادعاء أن فحص هذه الدالة وحده راجع كل منتجي payload.
5. `render_account_password_card:6338–6355` يضع password داخل HTML code. مسارا callback/message يرسلان الناتج إلى chat_id عند 8721/8801. الحارس العام عند 7890/8745 يقبل مجموعة معتمدة أو مستخدمًا معتمدًا داخل مجموعة أخرى، وفق 196–216؛ لا يوجد شرط private خاص بهذين الفرعين. خطر نشر البطاقة في مجموعة قائم مصدرًا، لا واقعة تسريب مثبتة. AFTER الأمني المقترح: منع كشف السر في المجموعة واشتراط مستخدم مصرح ووجهة خاصة، ضمن إذن منفصل لتغيير UX، لا افتراض أن HTML escaping يحمي السر.
6. `qwen_engine:290–324` يرسل قيمة password_hash كحقل password إلى signin عند 313. الاسم لا يجعل القيمة غير حساسة. لم تُطبع قيم ولم يُختبر أي حساب. وجود حسابات literal موثق تاريخيًا؛ لم نفتح قيمها أو نتحقق من صلاحيتها هنا.
7. `04_upload_to_Fable_github:915–916` يبني URL يحوي token ويمرره إلى git clone؛ `run_cmd:324–334` يحجب token في رسالة الاستثناء عبر mask_token. إذن لا يصح الادعاء أن رسالة الخطأ حتمًا تطبعه كما هو. يبقى خطر argv و remote config للنسخة المؤقتة؛ لم يُشغّل السكربت ولا clone بهذا المسار. هذا uploader مستقل، وليس مسار REST الحالي للجسر كما يوضح 4275–4285.

### 9.3 scripts: صلاحية القراءة لا تعني صلاحية التشغيل

| السكربت | الدليل من المصدر | قرار المراجعة |
|---|---|---|
| cleanup_redundant_venvs.py | base Windows عند 42؛ rmtree عند 92؛ main guard111 | قراءة فقط؛ اسم cleanup ووصفه «آمن» لا يبرران التنفيذ |
| migrate_existing_projects_to_fast_mode.py | local/parent registries21–24؛ backup72؛ write77 و replace78 | migration فعلية؛ ممنوعة في هذا التكليف، ولا تضمن atomic replace وحدها سلامة كل الحالات |
| generate_docs.py | import الجسر 13–15؛ mkdir22؛ write73 عند module scope | حتى import ذو أثر جانبي؛ لم يُشغّل أو يُستورد |
| verify_docs_integrity.py | PROGRESS32–34 و docs walk36–39 فقط؛ امتداد.md حساس للحالة؛ external/anchors تُتخطى 57–58 | ليس شهادة مراجعة لكل root/genspark/uppercase.MD ولا صلاحية الروابط الخارجية؛ يلزم فحص مخصص للتقرير |
| hadith_sijil.py | compile53؛ unittest73؛ failure قبلكتابةسجل النجاح، كما قرئ سابقًا | بوابة §6 حمراء؛ لا تشغيل جديد هنا ولا نجاح مصطنع |
| rebuild_refactor.py | asserts191–194 قبل rmtree199؛ AST الأجزاء بعد حذف OUT | D01–D04 تثبت الخطر؛ لا real rebuild، والحماية يجب أن تبقى فعالة مع-O |

### 9.4 جرد كتّاب أولي وحدود استنتاج single-writer

أعيد AST للجسر والمحرك و Qwen، مع إخراج أسماء الوظائف وأرقام الأسطر فقط. هذا جرد مرشحين وليس call graph كاملًا؛ البحث عن أسماء معينة قد يفوّت aliases أو methods أو writers خارجيين، وبعض json.dump تخص المشاريع لا الحسابات.

- الجسر: `update_account_data:989–1022` كاتب الحسابات؛ reactivate1079 و cooldown1112 و refresh1163/1194/1201/1212 و sender2961/2988 و failover3296/3316/3469/3482/3512/3637/3655 عملاء كتابة. الـ refresh له مسار عزل عبر verifier منفصل، ويجب ألا يسقط من الجرد لمجرد أن AST المحدود لم يطابق method alias.
- المحرك: save_accounts962–968؛ pick_account1320؛ lock_pick_and_reserve1355؛ release_account1382؛ cli2791/2814؛ relogin2995/3017؛ balance3124؛ main3607/3658/3692/3735؛ parallel3931/3955. وجودها لا يثبت أن send_chat بالجسر يستدعي جميعها؛ ولا يثبت غياب تشغيل CLI آخر على الملفات نفسها.01.03 يظل READ-ONLY.
- Qwen: load_or_create_qwen_accounts227/245 و_save_qwen_accounts276/282–283. خزنة أخرى، لا تُدمج في المعزل الثلاثي؛ لكنها مهمة لجرد الأسرار وآثار import والأدوات.
- verifier: VAULT_LOCK مستقل عن FILE_LOCK، كما ثبت في المراجعة السابقة؛ 05.02 له save_checkpoint وترتيب source-first مستقل. لا تنشئ RLock ثالثًا وتسمهتوحيدًا.
- المطلوب قبل GO التخزيني: خريطة paths الفعلية و namespace/process/CLI والمشغلات التي يمكنها الكتابة، ودليل منع writer ثانٍ. إن لم يثبت single-writer، تتوقف الخطة الدنيا ويُطلب إذن أقفال بين العمليات أو storage coordinator؛ لا يوهمنا نجاح thread test بضمان متعددالعمليات.

### 9.5 استكمال قراءة 05.02 وحدود التغطية

أعيدت 309–418 مباشرة: auth_status بعد relogin عند 352 لا يعاد حراسته قبل int(balance)367؛ missing password364 قد يصبح DEAD؛ retention372؛ missing/empty list388 وتاريخ تالف 397 يصبحان STALE999؛ sort نصي 394؛ now ثابت من self.now_utc402؛ حد>= عند 408؛ exception يبتلع عند 413–414 ثم AUTH_FAILED416. هذا يؤيد الأحكام السابقة ولا يمنح إذن نسخ المدير كاملًا.

سجل التغطية: استكمال السطور الطويلة 00 NOTES18/21 و Arena2497/2500 تم في الجلسة السابقة عبر textwrap بحسب سجل الاستئناف، ولم يُعد هنا. لذلك عبارة «مبتورة» في §6.3 تصف لحظة القراءة الأولى فقط، لا آخر حالة قراءة. لا يزال لا يوجد ادعاء إعادة قراءة دلالية لكل 4276 سطرًا من chat أو كل Arena1–1884؛ AST والجرد البنيوي ليسا ذلك. V1/V2 ما زالتا غير مكتملتين، والمطلوب التالي مصفوفة التحكيم و BEFORE/AFTER والخطة والاختبارات والمخاطر.


## 10. مصفوفة تحكيم الوكلاء وتقريرنا السابق

هذه محاسبة للأحكام لا للأشخاص. المرجع الزمني هو main@d164758 والتقرير السابق عند f3eef4b؛ لا نحاكم أحدث وثيقة على مثال قديم دون قراءة التصحيح اللاحق. «صحيح» هنا يصف الاستنتاج المحدد، لا صلاحية ملف كامل أو جاهزية التنفيذ. D تشير إلى تشخيص منفذ موثق؛ ما عداها قراءة مصدر أو دليل مرحّل مصرح به، لا اختبار قبول منفذ.

### 10.1 أحكام 00 و 012345 و Arena

| الادعاء/المصدر | الحكم بالأدلة | التصحيح الواجب في خطتنا |
|---|---|---|
| لا يوجد live balance في الجسر؛ 012345 NOTES461 | خطأ: sender2951 يفحصه؛ D12–D16 تثبت فجوات التعامل لا غياب الفحص | تعديل البوابات القائمة وربطها، لا وصفها اختراعًا جديدًا |
| tier=1 للمؤهل؛ 012345 NOTES453 | خطأ في المثال القديم؛ صححته 535–537 و 00 PLAN120 | نعترف بالتصحيح، لكن bool/NaN/mixed last_used و random-first-five ليست محلولة بذلك |
| لا startup cleanup ولا revival، والمحركمجمد | صحيح في أحدث 00 PLAN118/133–135/325–331 و 012345 NOTES538–540 | اتهام أحدث الخطة بإبقائها خطأ؛ المقاطع القديمة أرشيف تعارض، لا تكليف حالي |
| >=14 في TASK103/303 مقابل>14 في D1؛ 00 PLAN96/125/301–305 | تناقض داخل نفس الخطة؛ UTC لا يحسمعامل المقارنة | اتجاه>=14 بحسب جواب المالك المنقول Arena555؛ لا إعادة استفتاء تلقائية ولا GO |
| غير STALE يعني هدية طبيعية؛ 00 PLAN263 و 012345 NOTES483 عند d164758 | خطأ تاريخي؛ صحح الفرع الثلاثي لاحقاً كما في §15.3 و§16 | نعترف بالتصحيح؛ يبقى dispatch الخارجي وكتابات المحاولة بحاجة إلى معالجة |
| RLock + replace = نقل ذري 100%؛ 00 PLAN108/200/234 | ضمان زائد؛ قفل العملية لا يوحدكتّابًا آخرين ولا transaction لملفين | target-first/readback ثم source-cut، pending/conflict ومنع اختيار النسخة المكررة |
| 13failure قديمة فلا baseline أحمر؛ 012345 NOTES555–556 | خطأ منطقي: قدم الفشل يفسرسببه ولا يغير نتيجة القياس؛ §6 | لا نسبتها للهدية غيرالمنفذة، ولاادعاءأخضر. أسبابها ليست compact/model فقط: password UX و parity ضمنالقائمة |
| مطابقة 05.02 في DEAD كافية؛ 012345 NOTES733–737 | غير مثبت، والمديرنفسه يصنف missing password كـ DEAD عند 364 | HTTP-first ثم schema/code موثق؛ 403 عام واسم domain_banned وحدهما ليساعقددليل |
| BEFORE الفلترحرفي؛ 012345 NOTES745–754 | خطأ؛ الحقيقي 2324–2331 مختلف؛ D21 يثبتتراجع AFTER | لا نسخالمثال؛ حفظ الاستثناءات وإضافةدفاع عندالمخارج |
| staging وكلحدود PARTS؛ 00 PLAN140–143 | اتجاهصحيح تحسن عن تغيير النهاية فقط؛ لكن assert غير كافٍ مع-O | explicit validation و AST للجميعقبل delete/swap؛ D01–D04 |
| SHA-256 «تشفير» و rollback بال anchors؛ 00 PLAN84/338–351 | SHA بصمة لا تشفير؛ وجود anchor متجانس غيرمضمون؛ تشغيل rebuild مباشرةخطر | Gitrevision موحد، تحقق tree و generated، وتراجع البيانات منفصل |
| Arena كشف-O/HTTP/path/claim/secret routes | صحيح للنقاط المعاد فحصها في D01–D22 و§9 | لا يعني صحة كل التقرير أو أن مختبراته acceptance منفذة |
| Arena ينتقد تقريرنا الحالي | يحتاجقيدًا:1983 يحدد b74900c، بينما التقرير المحفوظ f3eef4b | نفصلنقدًا عولجسابقًا عن ثغرات ما زالت قائمة؛ C1/-O/claim تحتاجتصحيحًا |
| هل يكفي جرد Arena لـ203 ملفًا أو نجاح AST لإثبات مراجعة معنوية شاملة؟ | لا؛ الجرد بنيوي لا قراءة كل سطر؛ D10 يؤكدالعددعند main المحدد | سجلتغطيةمجزأ، ولا claim اكتمالكل chat/Arena القديم |
| OSRS/PR-18/75tests داخل Arena1915–1969 | مادة غير متعلقة بهذا المشروع | لا تنفذتعليماتها ولا تنسبنتائجها لـ TTTTT |
| مطابقة دستور بولا/SRE/skills100% | غير قابلة للإثبات بالمراجع المتاحة؛ Arena560 نفسهيسجلنقصها | نطبق AGENTS/GEMINI/بروتوكول المستودع فقط، ولا شهادة خارجية مختلقة |

### 10.2 إعادة تحكيم F01–F34 من تقريرنا

هذه مصفوفة 34 بندًا كاملة من حيث **تغطية معرفات التقرير السابق**؛ لا تعني اكتمال مراجعة المشروع كله. مواضع المصدر هنا كافية لتعقب الحكم، وبعضها أعيد الآن وبعضها موثق في§6–§9 أو سجل القراءة الموروث.

| المعرف | حكم V2 علىحكمنا | الدليل والتعديل |
|---|---|---|
| F01 | صحيح تاريخيًا، جزئي إذاعمم على أحدث الخطة | 012345453 مقابل 535–537؛ sort مصححجزئيًا، randomfirst-five لا يضمن الأعلى؛ C1 عندنايفشل huge-int |
| F02 | يلزم تصحيح الترجيح | 05.02:408 و Arena555؛ >=14 اتجاهالخطة، لا>14 بحجة UTC |
| F03 | صحيح | 05.02:388–400؛ absence/invalid ليست STALE999؛ اكتمال history شرط إثبات التأخر |
| F04 | صحيح جزئيًا | sort394 و now402 عيبان؛ لكن.days>=14 يعادل elapsed>=14d للمدة غير السالبة، فلا ننسب خطأ المساواة لـ floor وحده |
| F05 | صحيح مع حدود schema | parse/عرض 05.02:132/153؛ UTC-aware و ZoneInfo؛ naive يحتاج عقد منطقة موثوقًا لا تخمينًا |
| F06 | صحيح مثبت تشخيصيًا | verifier160–165؛ D07 يثبت 502/password→INVALID_CREDENTIALS |
| F07 | صحيح | verifier119 و 05.02:364؛ missing credentials ليسدليل invalid منالمنصة |
| F08 | صحيح | verifier298–303؛ status جديد/مفقود قديموتخطأ؛ لا schema evolution كعقوبة |
| F09 | صحيح لكن حارسنا غير كافٍ | verifier286–290 و D06؛ D12–D16؛ C1 يحتاجتعديل D22 وحماية bool/nonfinite |
| F10 | صحيح من المصدر، لا reproduction جديدهنا | verifier295–337 يهيئ retention داخل user200 فقط؛ payload363–365 يقرأه خارج الشرط؛ exception372 قديسميالخطأ NETWORK_ERROR |
| F11 | صحيحمثبت | verifier397–404 و D08؛ corrupt/non-list→[] ثم overwrite |
| F12 | صحيح | 05.02:525 قبل 527–529؛ نتائج atomic_save مهملة؛ target-first ليسكلالحل |
| F13 | صحيح بشرط منع الضمان المطلق | FILE_LOCK و VAULT_LOCK مستقلان؛ §9.4 جردأولي؛ single-writer لم يثبتتشغيليًا |
| F14 | صحيح | verifier407–430 duplicate→False؛ bridge1160/1163 يهملالحفظ؛ يلزمتمييز already-present/conflict/failure |
| F15 | صحيح، وناقص claimcleanup | snapshot3214/claim3242؛ D20 يثبتتسرب claim قبل try؛ re-read قبل probe وقبل commit |
| F16 | صحيح | gve.check_live_balance و sess في 012345472/479 ليست واجهات جاهزة موصولة؛ C2 عندنا أيضًا pseudo-code لا patch |
| F17 | صحيح مع تصحيح التعميم | 00PLAN263 و 012345483؛ D18 بلا URL→cooldown، D19 مع URL→success metadata؛ الحالات محقونة لعقد مستقبلي |
| F18 | صحيح من المصدر | bridge1198–1218 fallback وعقوبة 30m؛ التمييزقبل وبعد business-send ضروري |
| F19 | صحيح ضمن المحرك فقط | 01.03:1093–1108 و 1298؛ حارس الجسر لا يصلح CLI المستقل؛ لا إذنلتعديله |
| F20 | صحيح، وإصلاحنا سابقًا ناقص | D01–D04؛ كلحدود PARTS و-O و staging؛ normalizedparity ليست rawbytes |
| F21 | تاريخي صححته أحدث الخطة | 00PLAN118 claim-time قرائي؛ لا startupmutation حاليًا؛ لا استمرار في اتهام مقترح ملغى |
| F22 | صحيح مع فصل الأرشيف | revival/success/dead خارجدمجالجسر؛ حمايتها منالنسخ تظلواجبة؛ لااستيراد 05.02 |
| F23 | صحيح بحدود الدليل | أرقام 185/130/279 رواية بيئة غير متاحة؛ legacy اسمفعليفي verifier، لا إثبات وجود ملف حسابات حي الآن |
| F24 | صحيح | SHA بصمة؛ rollback موحد؛ الأمنيشمل temp/backup/REST لا gitignore فقط |
| F25 | صحيح | اختبارات قليلة لا تثبتغياب PermissionError أو Windowsbehavior؛ faultmatrix مطلوبة |
| F26 | صحيح، مصدر/دليلسبق | 05.02:61 dependency و 86signal؛ compile لايثبت import آمن؛ لم نستوردالمدير |
| F27 | صحيح وأعيدت قراءته | 05.02:352 ثم 367 دونحراسة auth_status الجديدة؛ إعادة فحص بعد التجديد لازمة |
| F28 | صحيح | retention372 يسبقحراسة dry_run في save486؛ dry_run المحليلا يعني HTTPread-only |
| F29 | صحيح وأعيدت قراءته | backup522–523 عند final؛ 5writes525–529 بلا bool؛ رسالة 599 تقول 3 ملفاتونجاحًا غيرمتحقق |
| F30 | صحيح | verifier411–417 يفرض suspended/zero/emptycookies؛ حفظ الحقول للاسترداد اليدوي منفصلعن reason |
| F31 | صحيح، ومعيارناناقص | last_used/reactivate قبل probe؛ zero-mutation سببيةللمحاولة؛ fullhash في عزل لا underconcurrency |
| F32 | صحيح كتعارض قديم؛ الحالة الآن مجمدة | أحدث 00/012345 وتقريرنا C5 يثبت READ-ONLY؛ verifier أيضًا يحتاج إذن نطاق بسبب AGENTS22 |
| F33 | صحيح | PRIMARY مكان لغير المعزول، قديشمل cooldown؛ membership ليست readiness |
| F34 | صحيح | liveprobe لقطة وليسرصيدًا محجوزًا لدىالمنصة؛ credit-in-flight يظلخطرًا ولا blindresend |

### 10.3 تصحيح BEFORE/AFTER C1–C8 الخاص بنا

- **C1:** يبقىفرز cached خيارًا لاافتراضيًا؛ تصحيح huge-int موضح§9.1، ولاوعد highest-first مع randompool.
- **C2:** عبارة «داخل try/finally القائم» غيركافية؛ يبدأ cleanup فور claim، لا عند 3298 فقط. re-read قبل probe و revalidate عند commit؛ حالةغير READY تحتاج dispatch صريح قبل URL-success/genericcooldown، وعدم إسقاط URL/checkpoint القائم.
- **C3:** المبدأ HTTP-first صحيح، لكن helpers مقترحة ومصدر أكواد الموت غير موثق كفاية؛ 403 وحدهلايكفي. AGENTS22 لايسمحبتعديل verifier تلقائيًا؛ يلزمإذنإضافي.
- **C4:** مثال>14 في التقرير القديم لا يحكم V2. AFTER التخطيطي: احسب elapsedUTC؛ negative/naive/malformed→UNKNOWN؛ recent الموثوق عند elapsed<14d ينفيالتأخر؛ elapsed>=14d لايثبت STALE دون history كافٍ. غياب lastgift يحتاج دليل نافذة كاملة لا 999؛ schema هذا المسار لم يثبت من HAR.
- **C5:** مؤجل خارج المسار الأساسي؛ لا ادعاء استئصال التخمين من كل المحرك بحارسالجسر.
- **C6:** target-first/readback/source-cut صحيح كأساس استرداد، لا transaction كاملة؛ unique temps و fsync/error policy و versionconflict ومنع استخدام المكرر مطلوبة. لا return MOVED قبل readback للطرفين.
- **C7:** أضفحماية-O و validation لكل الأجزاء قبل المساس بالوجهة، واختبارفشلال swap. لا تسمي read_text parity «تطابقبايت 100%».
- **C8:** حفظ التاريخ صحيح؛ عبارات«الآنأعيدت» في الأقسام القديمة تقرأ بتاريخ دفعتها. current_execution يجب ألا يعرض عائق curl الموروث كعائقحالي، ولا يعد D تشخيصات اختبارات قبول.

### 10.4 ما لم يثبت بعد، وما لا يحتاج إعادة سؤال

لا نعيد طلب إذن revival/startupcleanup/TTL أو رفع تجميد 01.03؛ هذه مستبعدة. اتجاه>=14 له provenance واضح، ويذكر في نسخة الاعتماد لا كاستفتاءجديد. يبقىقبل أي implementation: GO محددبال revision والملفات؛ schema منقح للهدية واكتمال pagination؛ allowlist أدلة failed؛ إثبات single-writer أوإذنحلأوسع؛ عقود baseline الأحمر؛ سياسة credit-in-flight. الترتيب الافتراضي يبقى كما هو، فلا يتوقف المسار الأساسي على اختيار فرز جديد. migration/security UX/live/merge/deploy كلمنهاخارج GO الضمني. اكتمالمصفوفة 34 معرفًالا يحول هذه الأمور إلى محسومة.


## 11. استعادة 4fea565 وعقد الدمج المقترح

### 11.1 حالة الاستعادة والنطاق

بعد reset التالي، بدأ workspace على main. جرى fetch واستعيد `4fea56561a5e0895146278d2e4d2fed1b253e3f9` من remote؛ main بقي `d164758`. فُحص التقرير فعليًا: ينتهي عند§10، ولا يحتوي§11–§13 من الأداة المنقطعة. لذلك لا تُحسب تلك الدفعة محفوظة، ويُعاد فقط الجزء المفقود في دفعات أصغر. D01–D22 ومصفوفة F01–F34 محفوظة ولا تعاد لمجرد reset.

الخطة V0–V4 والنطاق مجمدان: ثلاثة ملفات توثيق فقط؛ لا Python/tests/generated/accounts، ولا تعديل التقرير السابق أو مراجع 00/012345/Arena؛ لا live أو migration أو merge/deploy.01.03 مجمد، وتعديل verifier مستقبلًا يتطلب إذن نطاق صريح. الأقسام التالية **تصميم مقترح لا تنفيذ**، ولا أسماء API موجودة تلقائيًا. لم تعَد بوابات runtime بعد هذا reset.

### 11.2 ثلاثة محاور مستقلة

| المحور | العقد المقترح |
|---|---|
| مكان التخزين | PRIMARY=`accounts_genspark.json` المحسوم؛ FAILED=`accounts_failed.json`؛ DELAYED=`accounts_delayed_gifts_credits.json`. الوجهتان بجوار PRIMARY المحسوم، لا cwd اعتباطي. حارس النقل يرفض fallback لمسار صريح مفقود؛ لا تعديل P23/resolver العام |
| نتيجة الفحص | balance: KNOWN(value)/UNKNOWN؛ auth: مؤكدة/NEEDS_CREDENTIALS/TRANSIENT/CONFIRMED_FAILED بدليل موثق؛ gift: RECENT/STALE/UNKNOWN. نقص كلمة المرور ليس موتًا؛ UNKNOWN ليس 0 |
| نتيجة الحفظ | COMMITTED أو MOVED بعد readback؛ ALREADY_PRESENT بعد تحقق التطابق الآمن؛ PENDING_SOURCE_CLEANUP؛ CONFLICT؛ STORAGE_ERROR. bool واحد لا يكفي، ونتيجة الحفظ لا تختلط بحكم الحساب |

الهوية المطبّعة تكشف duplicates ولا تدمج السجلات المتعارضة تلقائيًا. نتائج الفحص الداخلية تحمل revision ووقتًا ومصدر دليل واكتماله وجيل الجلسة؛ لا cookies/password في logs أو repr أوالنتيجة العامة. أسماء الحالات هنا تصميمية، وتحتاجتعريف adapter يحفظ tuple العامة ذات 5 عناصر. legacy يقرأ لمنع الاستخدام والتعارض؛ لا migration تلقائية. success/dead خارج دورةالجسر لكن حمايتهما منالنسخ واجبة.

### 11.3 lifecycle من claim إلى dispatch

1. اختر بالسياسة القائمة، ثم claim بمالك محدد؛ **ابدأ cleanup فور نجاح claim** قبل reactivate/fingerprint/span أوغيرها مماقديرمي.
2. أعدقراءة PRIMARY والمعازل و legacy. غيابالحساب أوتعارضنسخته يمنعاستخدام snapshot قديم. gift HTTP خارجقفلملف طويل.
3. نفذ live balance للجلسة الحالية؛ تجديد محدود عند دليل انتهاء صلاحيتها ثمإعادةفحص. نفس حارس القيم عند البوابة الأولى وبعد refresh وبعد 401؛ لا READY من cached أو cookie generation قديم.
4. الرصيدالمؤكد>=threshold يعطي READY دون gift query. الافتراضي 100 منإعدادواحد؛ أي override موثق ومختبر.
5. low+RECENT موثوق: cooldown افتراضي 29h مع حفظمتحقق، لا send. low+STALE مثبت: نقل DELAYED. CONFIRMED_FAILED بدليل مسموح: نقل FAILED.
6. UNKNOWN/TRANSIENT/NEEDS_CREDENTIALS: تخطي محاولة بلا send أونقل أوعقوبة أو كتابة حساب منسوبة للمحاولة. لااستدعاء refresh القديمكماهو ثمادعاء zero-mutation: cookies الجديدة تبقىمؤقتًا في الذاكرة و last_used/reactivate يؤجلان إلىنقطة commit معتمدة.
7. قبل commit: re-read/version check تحتقفل writers المشترك القصير. فشل حفظ أو تعارض أو pending يمنع send؛ لا success log كاذب.
8. dispatch صريح قبل URL-success و generic cooldown. URL للاسترجاع وليس دليل نجاح؛ TIMEOUT قبل business-send يختلف عنه بعد إرسال محتمل. لاإعادةإرسال عمياء، ولاخلط giftpreflight بنفاد الرصيد أثناء العمل أو DATA_RETENTION/compact.
9. افحصالإلغاء قبل HTTP وبعده وقبل commit وقبل send. الإلغاء بعد ثبوت الهدف لا يرجعه إلى PRIMARY. أخيرًا close_span معضمان release حتى عند فشل الإغلاق.

zero-mutation تقاس سببيًا: لا write منسوب للمحاولة المجهولة. hash للملفكله صالحفي عزل؛ تحتالتزامن قد تكتب محاولة مشروعة أخرى. لا نفرضثباته بحبس filelock طوال HTTP. أثر telemetry المنقح مستقل عن ملفات الحسابات.

### 11.4 عقد الوقت والدليل

- الاتجاه التخطيطي `elapsed >= timedelta(days=14)` وفقجوابالمالك **المنقول** في Arena555؛ ليس سماعًا مباشرًا ولا GO. لا استفتاء جديد تلقائي علىالمساواة.
- الساعة UTC-aware حديثة لكلقرار؛ Cairo عبر ZoneInfo للعرضفقط. future/naive/malformed ليست STALE999. `.days>=14` ليسخطأحدبذاته للمدد غير السالبة.
- latest daily gift يختار بعد parseUTC لا sort نصي. recent موثوق ينفي التأخر؛ إثبات STALE يحتاج history/window/pagination كافية. missing/emptylist يبقى UNKNOWN دونعقداكتمال مثبت؛ HAR الحالي لا يثبت واجهة الهدية.
- giftprobe قرائي: لا retention POST أو signal/CLI/revival. فصلآثار auth/retention القائمة عنبوابةالهدية يحتاجاختبارات تحفظ P20، لا حذفهاخلسة. سياسة credit-in-flight تبقى محفوظة حتى اعتماد عقد محدد مع checkpoint/URL/prompt-once.

### 11.5 نقل قابل للاسترداد، لا transaction كاملة لملفين

strict read للملفات والهوية وال revision؛ corrupt/non-list ليس[]. قبلأول mutation: backup خاص موثق، ومنعنسخه إلى Git أو snapshot. temp فريد على filesystem الوجهة، flush/fsync وفققدرةالنظام، ثم replace و readback للهدف. لا source-cut قبل ثبوت الهدف؛ readback فاشل بعد replace يعنيحفظًا غير مؤكد لا«لم يكتب» بالضرورة.

بعد ثبوت الهدف، أعدالتحقق من المصدر ثمقصه واحفظه واقرأه. الفشل يترك PENDING_SOURCE_CLEANUP، والهدفالمثبت يمنع اختيار نسخة PRIMARY المتبقية. retry مطابق idempotent بعدالتحقق؛ duplicate مختلف CONFLICT. metadata الاسترداد يمكنأن تكون في السجل الخاص بالهدف؛ لا خزنة حسابات رابعة ضمنيًا. لا revival ولا startup sanitizer. طريقة التسوية اليدوية أو الأداة المحدودة تحتاجاعتمادًا.

single-writer شرط **لم يثبت**؛ RLock وحده ليس دليلًا. إن لم يثبت استبعاد writer آخر/namespace آخر/CLI، توقف الخطة الدنيا واطلبإذنحل بينالعمليات. Windows busy-file و diskfull وفشلال fsync تحتاجاختبارات، لا ضمان 100% من Linux mocks.


## 12. مراحل التنفيذ المستقبلية ومصفوفة القبول

**كل V2T غير منفذ، وكل V2X مخطط ولم يُنشأ كاختبار في المستودع.** هذه ليست نتائج D01–D22 التشخيصية. لا نسبة إنجاز تنفيذية؛ الموجود الآن توثيق وأدلة فقط. T/X في التقرير السابق محفوظة للتاريخ، ولا تُنفذ القائمتان بالتوازي؛ هذه المسودة الأحدث تحتاج اعتمادًا صريحًا.

### 12.1 المراحل والتبعيات

| المرحلة | العمل | شرط الدخول والخروج | الحالة |
|---|---|---|---|
| M0 تثبيت العقود | V2T01–05 | GO محدد بالإصدار والملفات؛ دليل schema وخطة writers | محجوبة بلا GO |
| B خط الأساس، مسار منفصل | V2T06–07 | اعتماد عقود الإخفاقات؛ نجاح البوابات قبل قبول runtime | غير منفذ |
| M1 نتائج وفحوص قرائية | V2T08–11 | بعد M0؛ اختبارات حمراء للسبب المحدد ثم خضراء بالعقد | غير منفذ |
| M2 التخزين والاسترداد | V2T12–15 | بعد M0/M1؛ إثبات عدم فقد البيانات ومنع استخدام المكرر | غير منفذ |
| M3 توصيل الجسر | V2T16–19 | بعد M1/M2؛ UNKNOWN لا يرسل أو يعاقب، وعقود الاستئناف محفوظة | غير منفذ |
| M4 المخارج والبناء | V2T20–22 | نطاق أمني معتمد؛ أسرار اصطناعية محمية وبناء مرحلي صالح | غير منفذ |
| M5 التحقق والتسليم | V2T23–24 | B و M1–M4؛ syntax/pytest/canonical/parity ناجحة ثم remote متحقق | غير منفذ |

يمكن كتابة TDD بعد GO مع توثيق baseline الأحمر، لكن ذلك ليس قبولًا للميزة. إصلاح الـ 13 لا يتم بحذف assertions أو تغيير 180/300 والموديل عشوائيًا؛ لا تعني قدم الإخفاقات أن البوابة خضراء.

### 12.2 قائمة 24 مهمة صغيرة

- [ ] V2T01: اعتماد revision التقرير وملفات source/tests/generator المسموحة؛ توسيع نطاق verifier صريح، و 01.03 مستثنى.
- [ ] V2T02: تثبيت >=14 بالـ provenance، و 100/29h والـ override، و UNKNOWN بلا send أو عقوبة، وحد credit-in-flight.
- [ ] V2T03: توفير schema منقح للرصيد والهدية وأكواد failed واكتمال pagination/window؛ لا اعتبار HAR الحالي إثباتًا لواجهة الهدية.
- [ ] V2T04: إنهاء جرد writers والمسارات والعمليات والـ namespaces؛ إثبات منع كاتب ثانٍ أو اعتماد حل بين العمليات.
- [ ] V2T05: تثبيت commit والبيئة و fixtures اصطناعية، وحظر الشبكة ومسارات الحسابات الحقيقية؛ إعادة baseline إذا تغير المصدر.
- [ ] V2T06: اعتماد عقود 13 failure وتصنيف أسبابها في مسار منفصل عن الهدية، بما فيها password UX و parity.
- [ ] V2T07: إصلاح baseline المعتمد بدفعات واختبارات أسباب؛ لا افتراض أن إصلاح parity وحده يجعل الكل أخضر.
- [ ] V2T08: تعريف typed results والهوية/revision/session generation و redaction، ثم adapter يحفظ tuple العامة الخماسية.
- [ ] V2T09: اختبارات numeric/schema/time، بما فيها bool/NaN/Inf/huge-int و DST والحد بالضبط؛ domains مختلفة للرصيد و timestamps.
- [ ] V2T10: probe هدية قرائي مع timeouts و retry budget وإلغاء و pagination موثقة؛ لا CLI/signal/retention POST.
- [ ] V2T11: تعديل auth/refresh محدود بعقد HTTP-first و deferred mutation وإعادة فحص الجلسة الجديدة؛ بعد إذن verifier فقط.
- [ ] V2T12: strict vault reads ومسارات صريحة؛ حفظ metadata ورفض فساد البيانات و duplicates المتعارضة.
- [ ] V2T13: target-first مع temp/flush/replace/readback، ثم revision check و source-cut؛ حقن فشل في كل خطوة.
- [ ] V2T14: reconciliation/idempotency/pending ومنع اختيار النسخة المكررة؛ لا revival أو startup cleanup.
- [ ] V2T15: اختبارات lost update والتزامن وكاتب ثانٍ و Windows busy-file حسب نموذج writers المعتمد.
- [ ] V2T16: cleanup فور claim وإعادة قراءة الحساب؛ ضمان release حتى عند فشل close_span أو الإلغاء.
- [ ] V2T17: توصيل preflight أول مرة وبعد refresh وبعد 401، مع حفظ الواجهة والسياق الحاليين.
- [ ] V2T18: dispatch صريح لكل نتيجة مع URL وبدونه؛ منع generic punishment و false success للحالات المجهولة.
- [ ] V2T19: ربط low/recent cooldown و low/stale delayed و confirmed failed مع تحقق الحفظ؛ حماية uncertain-send و credit checkpoint.
- [ ] V2T20: حماية snapshot/archive/REST باستخدام أسرار اصطناعية؛ حفظ الاستثناءات وسياسة deleted/old queue. بطاقة السر و Qwen/uploader المستقل تحتاج نطاقًا منفصلًا.
- [ ] V2T21: مولد بحماية explicit تعمل مع -O؛ تغطية كل PARTS و AST قبل حذف الوجهة؛ اختبار فشل swap واستعادة البناء السابق.
- [ ] V2T22: توليد مرحلي وفحص 12 جزءًا و 14 facade و entrypoints و normalized parity؛ raw-byte معيار مستقل إن طُلب.
- [ ] V2T23: regressions P13/P17/P23/P25/P29/P30/P16/P18/P20/P35/P40/P42/P43/P44 و syntax/full pytest/canonical؛ نتائج فعلية لا وعود.
- [ ] V2T24: فحص scope/secrets/history/links، وتمرين رجوع واستئناف اصطناعي، وتسليم commit/remote/PR؛ لا merge/deploy/live ضمن هذا الإذن.

### 12.3 مجموعات القبول المخططة

كل صف مجموعة حالات فرعية، لا assertion واحدًا. العدد 24 ليس ضمان تغطية وحده. يسجل التنفيذ المستقبلي المدخل والنتيجة الفعلية والمتوقعة و write/send calls و exit code، ولا يبدل عقود fixtures القديمة خلسة.

| المعرف | الحالات | معيار القبول | المهام V2T |
|---|---|---|---|
| V2X01 | balance0/99.9/100/250 و override | >=threshold READY دون gift؛ low لا send قبل تصنيف gift | 02,09,17 |
| V2X02 | -1/missing/bool/text/NaN/Inf؛ وhuge-int داخل/خارج المجال المعتمد | غير الصالح UNKNOWN بلا send/عقوبة؛ int دون تحويل float؛ المقبول وفق schema يواصل التصنيف، وغير المدعوم UNKNOWN صريح. لا حد أقصى اعتباطي أو crash/صفر مزيف | 08,09,17 |
| V2X03 | initial/refresh/401 وتغير cookies | حارس واحد للثلاث؛ لا READY بإثبات جلسة قديمة ولا login غير محدود | 11,17 |
| V2X04 | cached و random pool و last_used شاذ | السياسة القائمة افتراضيًا؛ cached لا يجيز send؛ الفرز إن اعتُمد له عقد مستقل | 09,16 |
| V2X05 | 429/5xx/timeout/HTML/403 مع password/suspended | لا DEAD اعتمادًا على النص؛ reason منقح و retry محدود | 03,11 |
| V2X06 | missing credentials/unknown status/dead code موثق | نقص محلي NEEDS/UNKNOWN؛ FAILED بالدليل فقط؛ لا unbound retention | 03,08,11 |
| V2X07 | 14d-1s/14d/14d+1s وتقدم الساعة | recent/stale/stale وفق >= ومع تاريخ كافٍ؛ وقت حديث UTC | 02,09,10 |
| V2X08 | offsets/DST/naive/future/invalid/other credit | max بعد parse UTC؛ لا تاريخ مختلق؛ Cairo للعرض، وغير الموثوق UNKNOWN | 09,10 |
| V2X09 | empty/missing list/page failure/short window/recent page | لا STALE دون اكتمال كافٍ؛ recent الموثوق ينفيه؛ pagination محدودة بلا POST جانبي | 03,10 |
| V2X10 | exception بعد claim عند fingerprint/reactivate/span close | release للمالك حتى مع استثناء cleanup؛ لا leak أو double release | 16 |
| V2X11 | UNKNOWN في عزل ومع تزامن | لا account write منسوب للمحاولة؛ hash ثابت في عزل فقط؛ لا lock طوال HTTP | 11,16–18 |
| V2X12 | حذف/نقل/تغير revision/إلغاء بين القراءة وال commit | لا resurrection/overwrite/send؛ CONFLICT أوتسوية محدودة؛ claim محرر | 12–16 |
| V2X13 | explicit missing/local/parent/custom/legacy | لا fallback خاطئ داخل نقل؛ الوجهتان بجوار PRIMARY المحسوم؛ P23 محفوظ | 04,12 |
| V2X14 | corrupt/non-list/empty bytes/target missing | STORAGE_ERROR بلا overwrite؛ المفقود فقط ينشأ بالعقد؛ لا[] لتعويض فساد | 12,13 |
| V2X15 | write/flush/fsync/replace/readback failure للهدف | لا source-cut؛ الحفظ غير المؤكد يوقف dispatch؛ لا نجاح مزعوم | 13 |
| V2X16 | الهدف ثبت ثم source fail/crash/restart | PENDING؛ لا اختيار النسخة المكررة؛ تسوية بلا revival | 13,14 |
| V2X17 | retry identical/duplicate casefold/conflicting record | idempotent للمطابق المتحقق؛ CONFLICT للمختلف؛ metadata محفوظة | 12–14 |
| V2X18 | threads/namespaces/subprocess/Windows busy | لا lost update/deadlock؛ أو رفض كاتب ثانٍ بآلية مثبتة | 04,15 |
| V2X19 | statuses مع URL وبدونه؛ فشل حفظ cooldown/cookies | dispatch صريح؛ لا success بسبب URL، ولا generic300s للمجهول أوكتم فشل الحفظ | 18,19 |
| V2X20 | timeout قبل/بعد send و credit-in-flight و cancel | لا blind resend؛ حفظ URL/checkpoint/prompt-once؛ لا خلط retention/compact بالهدية | 02,19,23 |
| V2X21 | secret/temp/backup/legacy في snapshot/archive/REST و old queue/delete | لا PUT محظور أو DELETE غير معتمد؛ ملفات المشروع السليمة تبقى؛ card فقط بإذن نطاقه | 20 |
| V2X22 | normal/-O/end-only/invalid part/swap fail | فشل آمن قبل حذف بناء صالح؛ فحص الأجزاء وال facades و parity | 21,22 |
| V2X23 | regressions و 01.03 freeze و full gates | hashes المجمد مطابقة؛ baseline fix منفصل؛ البوابات Exit0 قبلجاهزية runtime | 06,07,23 |
| V2X24 | reset قبل commit/قبل push/بعد push؛ code rollback مع pending | لا ادعاء نشر محلي؛ استعادة remote متحقق؛ لا بيانات قديمة تعيد المعزول | 24 |


## 13. خريطة التصحيح والمخاطر والتراجع

### 13.1 BEFORE/AFTER مرتبط بالموضع والقبول

AFTER هنا تصميم مطلوب بعد GO، وليس تعديلًا منفذًا. الأرقام تخص المصادر عند main@d164758؛ تتغير بعد أي تعديل ويجب إعادة تثبيتها.

| الموضع | BEFORE الفعلي | AFTER المقترح | القبول |
|---|---|---|---|
| bridge957–970 | path صريح مفقود قد ينتهي إلى fallback | حارس نقل موضعي يثبت المصدر والمجلد؛ لا تعديل P23 | V2X13 |
| bridge989–1022؛ verifier396–430 | writers مستقلة و bool مهمل؛ فساد الخزنة يتحول[] | strict read ونتائج تخزين صريحة، وقفل موحد مثبت و temp/readback | V2X14–18 |
| bridge3214/3242/3270–3298/3657 | snapshot قديم وعمليات قبل try | cleanup فور claim، و re-read/version check و release محمي | V2X10–12 |
| bridge2951–2989/3098–3106 | unknown/nonfinite قد يمر؛ low يبرد دون gift | حارس typed واحد في البوابات الثلاث و gift عند low فقط | V2X01–04 |
| bridge1122–1219 | refresh يكتب ويعزل وقد fallback بعد transient | auth صريح و deferred commit وإعادة فحص الجلسة، مع حفظ P20 | V2X03/05/11 |
| verifier83–165/257–372 | النص يسبق HTTP؛ balance0 افتراضي و unknown status قديموت | HTTP-first و schema/evidence؛ gift probe بلاآثار جانبية؛ إذن verifier لازم | V2X05–09 |
| bridge3344–3345/3630–3655 | URL أو COMPLETED ثم generic cooldown | dispatch شامل للنتائج وحد uncertain-send مع حفظ URL/checkpoint | V2X19–20 |
| bridge2324–2331/4592–4699/4275–4356/4462–4475 | حجب ناقص ومخارج تعتمد على upstream | جمع الاستثناءات وحارسالمخرج وسياسة upload/delete/old queue | V2X21 |
| generator191–199 وما بعدها | assert ثم delete ثم AST للأجزاء | تحقق explicit في staging لكلالأجزاء ثم swap قابل للاسترداد | V2X22 |
| engine1093/1298 | تخمين cached في مسارات مستقلة | **لا edit**؛ تطويق الجسر لايصلح CLI، والمخاطر موثقة | V2X23 |
| bridge196–216/8721/8801؛ Qwen/uploader مستقل | مخاطرأسرار خارجدمجالهدية | إصلاحأمني منفصل بعدإذن، لا توسيعخفي للنطاق | V2X21 عند اعتماد النطاق |

### 13.2 سجل المخاطر وبوابات التوقف

| الخطر | الكشف/الإيقاف | التخفيف والتراجع |
|---|---|---|
| عزل خاطئ من HTTP/schema/time | UNKNOWN أوعدم اكتمال الدليل | لا source-cut قبل الإثبات؛ النقل ليس أداة تشخيص |
| فقد حساب بينملفين | fault injection وعدّالهويات و readback | target-first، و pending يمنعالاستخدام حتى تسوية معتمدة |
| كاتب آخر أو namespace أخرى | جرد واختبار كاتب ثانٍ اصطناعي | RLock ليسإثباتًا؛ توقف الحل الدنيا حتى منع التوازي أو اعتماد حل أوسع |
| حفظ فوق snapshot قديم | revision/identity/session mismatch | CONFLICT؛ لا overwrite ولا resurrection |
| timeout بعد عمل محتمل | حد business-send وروابط checkpoint | لا blind resend؛ استعلام بعقد موثق أو وقف آمن |
| أسرار في archive/queue/logs/card | fixtures اصطناعية وفحصالمخارج | حجب متعدد الطبقات؛ صلاحياتخاصة؛ security UX بإذنمنفصل؛ إلغاء PAT المكشوفمن GitHub |
| baseline أحمر أو generated جزئي | مقارنة 13failure و staged parity | لاجاهزية runtime؛ رجوع tree موحدةلا anchors مختلطة |
| Windows/busy-file/diskfull | حقنفشل وبيئة Windows عنداعتمادها | retries محدودة وحفظ النسخة المثبتة؛ لاوعد 100% من Linux mocks |
| reset يفقددفعةمحلية | HEAD/remote/PRhead بعدكل push | chunks صغيرةوسجل next؛ Tool بلا result ليسإنجازًا |
| توسيع scope | diffallowlist و hashes للمجمد | وقففوري؛ لا verifier/engine/tests/securityUX دونإذنمحدد |

### 13.3 runbook تراجع بعد تنفيذ مستقبلي معتمد فقط

1. أوقف dispatch والكتّاب بطريقة معتمدة واحفظ حالة الأعمال in-flight وروابطها. لا kill/retry عمياني يعيد prompt.
2. اقرأ PRIMARY والوجهتين و legacy وأي pending metadata قراءة خاصة؛ خذ نسخة خاصة موثقة قبل أيإصلاح، ولا تضع بياناتحسابات في Git.
3. **رجوع الكود:** استعد revision موحدة سبقفحصها تشمل source/generator/generated/tests المتوافقة. لا Copy-Item من anchors غيرمضمونة ولا rebuild مباشرة بمولدغيرصالح.
4. **رجوع البيانات:** ليس git reset ولا copy لملف PRIMARY قديم. راجعالهويات والتعارضات و pending؛ حفظ الهدف المثبت ومنع استخدام المكرر أولوية. لا revival تلقائي.
5. إذا كانت نسخة الكود السابقة لا تفهم pending الجديد، ابق فيوقفآمن حتى تسوية معتمدة؛ لا تشغلها فوق البيانات بلا اختبار توافق. أعدالبوابات واختبارات الاسترداد.
6. سجل مااستعيد وما بقيغير مؤكد، ثم commit/push للملفات المصرح بها فقط. استئناف live خطوةمنفصلة بإذن. هذا runbook **لم ينفذ**.

### 13.4 استئناف المراجعة الحالية بعد reset

- pwd ثمداخل workspace: status/log/fetch/ls-remote؛ استعد آخر رأس متحقق، لا main افتراضيًا.
- اقرأرأس PROGRESS و current_execution وآخر أقسام التقرير؛ طابق HEAD/remote/PR9 و Draft. قدينجح push وينقطعالتعليق؛ استكملالناقص فقط.
- إذا تغير upstream، احفظه وافحص diff وأثره على الأدلة. نتائج D والبوابات السابقة تحتفظ بزمنها؛ لا تعادلمجردفقد`.tmp` ولا تُعرض كقياس جديد.
- الأداة المنقطعة يفحص أثرها قبل إعادة الكتابة. استأنف next بدفعةصغيرة؛ «تابع» ليس GO لتعديلالتشغيل.

### 13.5 حالة التقدم وحدود التسليم

§0–§13 تشمل المراجع والتشخيصات والتحكيم و BEFORE/AFTER وعقودالدمج والمهام والقبول والمخاطر. **هذا اكتمال مسودة هيكل الخطة، لا إعلان اكتمال المراجعة الشاملة أوتنفيذ الميزة.** تبقى مراجعةالتغطية والإحالات والتحرير، خصوصًا الكلمات العربية المتصلة في دفعات الحفظ السريعة. لم تُعدقراءةكل chat أو Arena1–1884 دلاليًا، وجرد AST ليسبديلًا لذلك. schema الهدية و allowlist failed و single-writer التشغيلي والأدلة الخارجية غير متاحة بشكل حاسم. هذهحدودمعلنة، لا اختبارات ناجحة مفترضة.


## 14. تحقق المسودة ونقطة المتابعة

أُجري بعد نشر§13 عند `7ce33052e99a456fd678e71638e35eed652a97e3` تحقق وثائق فعلي، لا إعادة لاختبارات التشغيل:

- `scripts/verify_docs_integrity.py`: Exit0؛34 ملفًا و12 رابطًا داخليًا. نطاقه محدود كما في§9.3؛ لا يغطي هذا التقرير تلقائيًا، ولا يفحص صلاحية روابطGitHub الخارجية.
- فحص مخصص للتقرير: وجود الروابط المحلية، وصحةUTF-8/JSON، وتسلسل34 معرفF و22 معرفD و24 مهمةV2T كلهاunchecked و24 مجموعةV2X مخططة.
- مقارنة الأرشيف مع4fea565: كل حقولrecovery خارجcurrent_execution محفوظة دلاليًا، وذيلPROGRESS التاريخي محفوظ. البصمتان للتقرير السابق وArena مطابقـتان للقيم المثبتة.
- diff منذ4fea565 يقتصر على الملفات الثلاثة المعتمدة. لاPython/tests/generated/accounts أوالمراجع الأصلية. فحص أنماطPAT وcredential URL في النص المضاف لم يجد تطابقًا؛ هذه نتيجة فحص أنماط، وليست ضمانًا مطلقًا لاكتشاف كل الأسرار.
- تحسين مسافات النصوص خارجcode fences وinline code والروابط. تحقق آلي أن محتوى التحسين الميكانيكي لم يتغير بعد حذف whitespace وأن أمثلة الكود بقيت حرفيًا. التعديلات الدلالية المنفصلة اقتصرت على حالةV3/V4 وصياغة سؤال كفايةالجرد كيلا يُنسب ادعاء غير موثق إلىArena.

**الحالة:** مسودة العقود والخطة والمخاطر محفوظة، والتوثيق البنيوي متحقق. ما زالت المراجعة الشاملة قيد العمل: يلزم إغلاق سجل التغطية الدلالية للمصادر والاتساق النهائي والتحرير المتبقي. لا ادعاء قراءة جميعchat أوArena1–1884 من جديد. لاGO للتشغيل، ولا تنفيذ لأيV2T/V2X. البوابات التشغيلية السابقة بقيت13failure ولم تعَد هنا.

المتابعة المباشرة: اقرأ§10–§13 كتقرير واحد بحثًا عن تناقضات وقرارات غير موثقة، وأكمل الأجزاء الحرجة غير المغطاة من المصادر مع سجل دقيق؛ ثم سلّم النسخة النهائية أواذكر النقص المحدد. لا تعِدD01–D22 أوتنفذfeature لمجردreset. كل دفعة صغيرة commit/push ثم مطابقةHEAD/remote/PR9 Draft.

## 15. طلب Gist وطريقة العمل — إعادة بناء محدودة بعد reset آخر

### 15.1 مصدر التكليف وحدود الاستعادة

قرئ [Gist المالك](https://gist.github.com/number949481-ux/b64bef6ac1b186b191024ad3114bfe2a) كاملاً الآن (truncated=false): revision `d6a0088582d51999e141b5846e8e8f784a262c7d`، updated_at=`2026-10-29T16:43:14Z`، SHA256 UTF-8=`295157c416c0163ac8aedbb0d0b9fbd142981d03c3721dc58fcd4b86859b0a9f`. هو تفريغ آلي مكرر؛ لم نسمع التسجيل ولا نحسب التكرار موافقات مستقلة. يطلب تقييم طرق الوكلاء واستقلال القرار وبرومبت استئناف وتحديث المراجعة حتى اعتماد خطة محددة، لا تنفيذ الميزة.

هذه النسخة fresh clone على main@adaf586. استعيد remote review@6a42a05، ثم دمج main داخل فرع المراجعة، لا PR إلى main. ست وثائق upstream تغيرت (1768 إضافة/126 حذف)، لا كود. فحص objects أثبت غياب8e96db4 وdf6fdf6؛ `.tmp` غير موجود. ZIP السابقة ذات SHA256 `8b16f140ac762377ebbbc96e7a9976d7ebf762fd4363820ace09d9a70282c35d` ورفعها المنقطع معروفان من ملخص المالك فقط، لا ملفات مستردة أو رفع مؤكد. لا يمكن استرداد بايتات§15 السابقة من الملخص؛ هذه إعادة بناء صريحة مختلفة. لا واجهة إيصال/رابط للرفع السابق متاحة في الأدوات المستخدمة؛ عدم وجوده محلياً لا يثبت غيابه من التخزين البعيد.

الجدول التالي قياس بايتات جديد بعد مزامنة upstream؛ لا يدل وحده على قراءة دلالية كاملة:

| المرجع | الأسطر | SHA256 |
|---|---:|---|
| `00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md` | 479 | `f9a194d178789e6ae3956910af097716848d1118a3683e31fe8936cbcf2126b2` |
| `00_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md` | 388 | `1b3db0215bf0f9a433f15cdb87ab087463fc5dd08cf69d57c0131f06d3479408` |
| `012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_NOTES.md` | 1040 | `a575b45bdf4711fb57352cdc64c14435ce27f97ed3942fbf0d993c4d36980958` |
| `012345_TRI_STATE_GIFT_INTEGRATION_ARCHITECT_PLAN.md` | 328 | `6e8d8ca14f25227ce4127a17c4f5977b95b6b2d62433b162f05e9e1e748aed6c` |
| `جج-جميع-شات-.MD` | 5299 | `265125393d331aa0c9978e7f47d8cc0c38f600f29c0cff4c7d3b4c56d86658c1` |
| `012345_arena-ai_مراجعة_وخطة_دمج_الهدية_الشاملة.md` | 3330 | `bc001cf7252a540aba6b04eab61b9ef3ac08dd73dcfa89b696e18a52a65d4a3b` |
| `genspark/tri_state_gift_master_review.md` | 805 | `342b4ca585be8df4934acb7681b51be662d6a98632158c46a248f3625280ae0d` |

### 15.2 تحكيم طريقة العمل: الصحيح والخاطئ عند الوكلاء وعندنا

| الطرح والدليل | الحكم المستقل والطريقة المختارة |
|---|---|
| PROGRESS مدخل واحد و[ ] قبل العمل ثم نتيجة موثقة: 00 PLAN349–355 و012345 NOTES963–1037 | مناسب لتنسيق العمل. PROGRESS يحدد المهمة الحالية؛ V2 يحتفظ بالأدلة والعقود؛ current_execution مرآة آلية، لا ثلاث خطط متنافسة. لا يبدأ من أول مربع أرشيفي. |
| اعتبار المربع Write-Ahead Intent ومناعة انقطاع: 012345 NOTES1012–1019 | تسجيل النية مفيد لكنه ليس WAL معاملاتيّاً ولا ضمان دوام؛ فقد8e96db4 والحزمة المحلية يبين أن commit المحلي لا يكفي. لا ضمان صفر أخطاء أو ملاءمة100%. |
| استقلال المنفذ مقابل التلقين: 012345 NOTES951–958 و00 PLAN344–347 | نقرأ المصادر والكود ونقيّم كل اقتراح؛ لا تفويض مطلق لوكيل أو شهادة صحة لمجرد وصف SRE. اختيار المنفذ ليس GO لتنفيذ خطة غير معتمدة. |
| مرحلة واحدة و3–4 مهام لكل PR: 012345 NOTES931–935 | الهدف المحدد القابل للفحص مفيد؛ العدد الثابت ليس معيار أمان. الدفعة تتحدد بالنطاق والدليل والاعتماد، وتبقى هذه المراجعة في PR9 Draft. |
| تحويل كل نتيجة إلى [x]: 012345 NOTES979–982 | قد تكتمل مهمة قياس بتوثيق اختبار فاشل؛ مهمة إصلاحه لا تكتمل مع الفشل. مهمة النشر لا تكتمل دون remote مطابق، ومهمة backup لا تكتمل بوعد أو ZIP محلية. |
| الالتزام بحوكمة بولا/SRE وRoot خارج المستودع | لا ادعاء مطابقة وثائق خارجية غير متاحة، ولا إنكار وجودها عند المالك. لا إنشاء Root/ai_state.json هنا؛ نطاقنا ثلاثة ملفات فقط. |
| مديح دفعاتنا74751b5/3210780/7ce3305/6a42a05: 012345 NOTES895–900 | checkpoints المدفوعة مفيدة بالفعل؛ لا تبرهن وحدها خلو العمل من الأخطاء أو تفوقاً مطلقاً على وكيل آخر. |

**نقدنا الذاتي:** رأسPROGRESS المنشور عند6a42a05 يفتقد طابوراً حيّاً لطلبGist، وفي§10–§13 كلمات عربية متصلة تحتاج تحريراً. الملخص يذكر عدم قراءة PROGRESS أولاً في جلسة أقدم؛ هذه شهادة منقولة لا أثر Git يثبت ترتيب الأدوات. أكدنا الآن فقد الدفعة المحلية: وعد backup لم يكن تسليماً متحققاً، وتأخير تأمينه سمح بتكرار إعادة البناء. علاجنا دفعة محدودة ثم حزمة قابلة للتنزيل، لا تكديس مراجعات جديدة عند انسداد النشر. نجاح فحص الوثائق لا يزيل13 فشل runtime التاريخية.

### 15.3 أثر المراجع الجديدة على عقود الكود

- **تصحيح يُحسب للوكلاء:** 00 NOTES340–357 صار يفصل STALE وHEALTHY وUNKNOWN؛ لا ننسب إليه الآن else قديمة تبرد المجهول. و012345 NOTES805–819 يحتفظ باستثناءات الفلتر الأصلية ويضيف معازل وأسراراً؛ D21 يخص المثال القديم، لا هذه النسخة تلقائياً.
- **ما لم يصلحه الفرع الداخلي:** قرئ bridge3625–3666 الآن: `if pub_url or status == "COMPLETED"` عند3630 يكتب metadata نجاح، و3652–3655 يطبق تبريد300s إلا على quarantined/suspended. status جديد وحده لا يحقق zero-mutation عند وصوله لهذه النهاية؛ يلزم dispatch شامل وفقV2X19، ولا URL دليل اكتمال.
- **الفلتر:** قراءة المثال الجديد تبين أن حجب substring `token` أوسع من حجب الأسرار وحدها، وأن `.bak1`/`.tmp1234` ومسارات nested ليست مغطاة بصيغة suffix/exact المعروضة. GF01 من ملخص الجلسة السابقة فقط:15 أسماء اصطناعية،LOST0 وPROPOSED_BLOCKED15؛ لم يُشغّل الآن ولا يثبت أسماء خزائن حقيقية. يلزم عقد مسارات ومخارج وfixtures قبل اعتمادV2X21.
- **عتبة14:** 012345 PLAN269–273 صارت `>=14`؛ لكن00 NOTES287–289 وPLAN308–311 ما زالت `>14`، مع تأييدNOTES264 لـ`>=14`. لذلك عبارة إجماع الأطراف في012345 NOTES842 مبالغ فيها. يبقى اتجاهV2 هو`elapsed >= timedelta(days=14)` حسب جواب المالك المنقول فيArena555، لا سماع مباشر ولاGO؛ لا إعادة سؤال مساواة14 تلقائياً.
- **المولد:** 012345 NOTES843–844 يرفض assert وحده تحت`-O`، بينماPLAN227 يجعل نجاح assertion شرطاً فيTASK-503. هذا نقص اتساق القبول، وليس غياب staging الذي يذكره نفس السطر. V2X22 يشترط explicit validation تحت`-O` لكل الأجزاء قبل استبدال بناء صالح. لم يشغّل المولد الآن.
- **التخزين والتزامن:** target-first/readback/source-cut أفضل استردادياً، لكنه ليس transaction ذرية لملفين. RLock لا يثبت استبعاد كاتب خارج العملية. نتائج التخزين COMMITTED/MOVED/ALREADY_PRESENT/PENDING_SOURCE_CLEANUP/CONFLICT/STORAGE_ERROR مستقلة عن حكم الفحص ومكان التخزين. rollback الكود منفصل عن تسوية البيانات؛ أوامر Copy-Item من anchors فيPLAN304–318 لا تثبت توافق النسخ أو سلامة البيانات.
- **حدود السلامة باقية:** UNKNOWN ليس0/DEAD/STALE؛ نقص credentials ليس invalid مؤكداً؛ HTTP-first و429/5xx/timeout/challenge ليست موتاً. live balance قبل business-send،threshold100 افتراضياً؛29h فقط low+recent موثوق. cleanup فورclaim وre-read/version/session قبلcommit. timeout قبلsend غير بعدsend محتمل؛ لاblind resend. no revival/no startup sanitizer. تجميد01.03 لا يصلحCLI مستقل، وإذنverifier المستقبلي مطلوب بسببAGENTS22.

القراءة الحالية المحددة: 00 NOTES260–359،00 PLAN300–388،012345 NOTES790–1040،012345 PLAN221–328،bridge3625–3666،وسكريبتverify_docs_integrity كاملاً. بقية قراءات الجلسة السابقة موروثة من الملخص وليست إعادة قراءة الآن. Arena مرجع دائم محفوظ؛ لم يُدَّعَ إعادة قراءته كاملاً.

### 15.4 الطريقة المختارة للمنصة والمراحل

1. اقرأ رأسPROGRESS الموجود، ثمstatus/fetch/remote/PR. استعد فرع المراجعة، لا تعتمد سجلPR8 علىmain ولاhash من الرسائل دون وجوده.
2. سجّل[ ] لمهمة جاهزة محددة مع allowlist وشرط نجاح. نتائج القياس منفصلة عن إصلاح العيب وعن اعتماد التنفيذ؛ المربع لا يمنحGO.
3. اقرأ المصدر وأثبت BEFORE/AFTER واختبار القبول المناسب. لكل تغيير سجل provenance وحدود الدليل. العقود والمهامV2T/V2X في§11–§13 تصميم غير منفذ.
4. احفظ دفعة صغيرة وcommit ثمsync/push وتحققHEAD=remote=PR9 Draft. حالاتPLANNED/IN_PROGRESS/LOCAL_COMMITTED/REMOTE_VERIFIED/BLOCKED تسميات توثيقية فقط، لا برنامج استرداد منفذ. تعليقPR ليسpush.
5. اجمع فقط commits المحلية غير المنشورة إذا لزم مع إثبات ثباتtree؛ لاforce-push أوإعادة كتابة checkpoints منشورة بسببreset. عند تعارضremote توقف وراجع، لا تطبقpatch عميانياً.
6. إذا غابت المصادقة: وثق العائق، أمّن ZIP محدودة بالوثائق وpatch وmanifest، واختبر تنزيلها وبصمتها ثم توقف عن تكديس العمل. لاPAT فيالدردشة. ZIP الجديدة لا تدّعي استعادة الأصل ولا تشمل حسابات/HAR/runtime.
7. بعد تأمين الحفظ: سد تغطية الشات4277–5059 والاتساق§10–§13؛ ثم عرض خطة revision-scoped للاعتماد. إصلاحbaseline/runtime/migration/live كل منها يحتاج نطاقاً وإذناً؛ لا شيء منها منفذ هنا.

### 15.5 برومبت استئناف عملي

```text
استأنف number949481-ux/TTTTT على genspark_ai_developer وPR #9.
اقرأ رأس PROGRESS.md الجذري أولاً، ثم status/fetch/remote/PR قبل أي تعديل.
استعد أحدث حالة متحققة لفرع المراجعة، لا main الافتراضي ولا hash قديم من الرسائل.
اقرأ genspark/tri_state_gift_independent_review_v2.md وcurrent_execution في genspark/recovery_state.json.
النطاق مراجعة وتوثيق في الملفات الثلاثة فقط؛ لا Python/tests/generated/accounts أو01.03 أوالتقرير السابق أومراجع00/012345/Arena.
سجل المهمة الجاهزة [ ] قبل دفعة محددة، ثم النتيجة والدليل؛ لا تبدأ من مربع أرشيفي ولا تعتبره GO.
افحص أثر أي أمر مقاطع قبل تكراره. commit محلي ليس نشراً؛ تحقق HEAD=remote=PR9 Draft بعدpush.
إذا أرفقت حزمة استرداد، افحص manifest وSHA256 والpatch مقابلremote قبل التطبيق؛ لا تستبدل ملفات أحدث ولا تطبق الدفعة مرتين.
عند غياب المصادقة أو تعارض، اذكر العائق وتوقف عن تكديس العمل؛ لا توكن فيالدردشة ولاforce-push.
لا تعد D01–D22/GF01 أو البوابات لمجردreset ولا تدّعِ إعادة تشغيلها. تابع المراجعة حتى اعتماد خطة محددة؛ الاستئناف ليس GO لتنفيذ الميزة أو الدمج أو النشر الحي.
```

### 15.6 حالة التحقق والنشر التاريخية — الأحدث في PROGRESS و§16

PR9 OPEN/Draft ورأسه6a42a05 في آخر تحققAPI. `gh auth status` غير مسجل؛ push Exit128 لتعذرUsername. محاولة تعليق عبرgsk فشلتExit1 بـfree_plan_block؛ لا تعليق ناجح، ولا برهان من ذلك على حالة ربطGitHub خارجCLI. لم يستخدم التوكن المكشوف ويجب إلغاؤه. إنشاء/رفع/تنزيل الحزمة الجديدة يسجل في رأسPROGRESS وcurrent_execution عند تحققه، لا مقدماً. المراجعة الشاملة غير مكتملة والميزة غير منفذة؛13failure وD01–D22/GF01 تاريخية، لاruntime gates جديدة.


## 16. نتيجة قراءة الشات وبروتوكول العمل — إعادة تثبيت الدفعة المفقودة

### 16.1 المصدر وحدود الاسترداد

استعيد d6e09f3 من Git بعد reset؛ commit المحلي9ba5feb غير موجود، وآخر أمر تحديث PROGRESS/recovery قوطع بلا نتيجة. §16 ليس في الرأس المنشور، ولم تكن حزمةv5 قد أُنشئت أو رُفعت في سجل الأدوات. النص هنا إعادة تثبيت محدودة من نتائج القراءة الظاهرة في المحادثة، لا استرداد بايتي لـ9ba5feb ولا ادعاء اكتمال أمره اللاحق. Gist لم يتغير عن revision/SHA في§15.1. PR9 OPEN/Draft ورأسهd6e09f3؛ نجاح الربط والدفع السابق لا يثبت بقاء مصادقة gh بعد reset.

قبل المقاطعات قُرئ الشات4277–5059 متصلاً في ثلاث دفعات4277–4546/4547–4816/4817–5059. وقُرئت V2:212–509 ثم175–206؛ bridge2318–2349/3240–3300/3625–3675؛ 012345 NOTES803–824؛ 00 PLAN200–294 وNOTES260–294؛ manager385–416؛ generator190–268؛ parity test1–65؛ Arena1908–1977. القراءات موثقة بمخرجات الأدوات وليست إعادة تشغيل مختبر. بصمة الشات5299 سطراً ما زالت `265125393d331aa0c9978e7f47d8cc0c38f600f29c0cff4c7d3b4c56d86658c1`. لا D01–D22/GF01 أو runtime gates جديدة.

### 16.2 محاسبة الادعاءات والمقارنة بالمصدر

| ادعاء الشات | الحكم المحدد والأثر على V2 |
|---|---|
| الفرع الثلاثي يغلق UNKNOWN؛4344–4355/4464–4466 | التحسن صحيح في00 PLAN256–273. لكنه يعيد LOW_BALANCE_UNKNOWN_GIFT؛ bridge3630–3655 ما زال يحتوي URL-success والتبريد العام، و3296 يكتب last_used قبل try3298. لا يكفي إصلاح else الداخلي؛ V2T16–19/V2X11/19 تشمل المسار الكامل. status المقترح ليس منفذاً الآن |
| الفلتر يغطي كل .bak* و.tmp*؛4467–4469/4732 | أحدث012345 NOTES805–819 حفظ الاستثناءات الأصلية؛ D21 يخص المثال القديم. suffix .bak/.tmp وsubstring .bak_/.tmp_ لا يشملان كل .bak1/.tmp1234؛ token قد يحجب tokenizer. snapshot يستدعي basename كما في§9.2، فلا ننسب مشكلة nested paths لهذا الاستدعاء عميانياً؛ يلزم عقد كل مخرج وV2X21 |
| إجماع>=14؛4470–4471/4756 | اتجاهV2 محفوظ بلا إعادة استفتاء. manager408 يقارن threshold و402 يحسب delta. 00 NOTES264 يؤيد>= لكن287–289 ما زال>. لا إجماع نصي كامل ولا نسخ لـSTALE999 عند غياب التاريخ فيmanager388–400 |
| كل الثغرات مغلقة ولا مفاجآت؛4370–4377/4504–4512/4624–4626 | يناقض الجزم كون العمل PLANNING في4514/4757. الإجابات4423–4424/4523/4765/5035 تستبدل الاختبار المنفذ بوضع خطة أو عدم تعديل؛ ذلك لا يثبت انعدام regression. لا شهادة100% أو قبول runtime معbaseline أحمر |
| 13failure مجرد compact/models؛4339/4367/4619 | التصنيف الموثق يشمل password UX وparity أيضاً. سبق الفشل للهدية غير المنفذة لا يثبت عدم أثره عند الدمج. الاختباران المقترحان4885–4887 لا يغنيان عن full gates فيM5، وإصلاحB يحتاج عقوداً معتمدة |
| try/finally يحل claim دائماً؛4604–4606/4872 | البدء فورclaim صحيح، لكن close_account_timing_span3658 يسبق release3659؛ فشل الإغلاق قد يمنع التحرير. V2X10 يجب أن يشمل فشلcleanup نفسه إضافة إلى الاستثناءات قبل العمل |
| anchor والبصمة تضمن rollback100%؛4479–4480 | البصمة هوية بايتات وليست ضمان توافق revisions أو رجوع بيانات ملفين. parity test32–41 يستخدم read_text ثمencode؛ ليس دليلاً مستقلاً علىraw bytes. §13.3 يفصل code rollback عن reconciliation/pending |
| تجميد01.03 يعني حماية كاملة؛4620/4734 | التجميد حد نطاق صحيح؛ CLI والكتّاب المستقلون في§9.4 لا يصلحهم guard الجسر. RLock ليس إثباتsingle-writer بين العمليات، وverifier يحتاج إذن نطاق صريح |
| وجودOSRS يبطلArena ويثبت خلو عملنا من الهلوسة؛4475–4478/4837–4840/4973–4980 | Arena1915–1969 فعلاً مادة مشروع آخر؛ تُستبعد و75tests ليست نتائجTTTTT. النص لا يثبت سبب إدخاله أو بطلان بقية الأدلة. خطؤناC1/D22 وفقد الحفظ السابق يمنعان تزكية عملنا100%. Arena مرجع دائم تُحاكم ادعاءاته منفردة |

### 16.3 طريقة العمل المختارة، لا التنفيذ العمياني

في4848–4859/4893–4898 اقتراح انتظار GO Commit بعد تعديل الملفات، بينما4992–5009 يقترح commit/push ثم فحصdiff. الانتظار مع تغييرات غير محفوظة بعيداً لا يناسب reset المتكرر. و«اعتمدنا تقريرك»4893 رسالة **مقترحة** كتبها وكيل، ليست GO مستقلاً من المالك. اختيار المنفذ4809–4825 لا يوسع النطاق.

العقد المختار: **revision المصدر → هدف وBEFORE/AFTER → allowlist وحدود النطاق → معيار الفحص ونتيجته → المخاطر والتراجع → commit/remote/PR Draft → التالي**. اعتماد المالك للنطاق يسبق أي تنفيذ مستقبلي؛ المراجعة الوثائقية وحدها مأذون بها حالياً. بعد فحوص الدفعة المصرح بها تُحفظ وتُدفع إلىDraft ثم يراجع المراجع commit ثابتاً؛ تصحيح الخطأ فيcommit لاحق دون إعادة كتابة checkpoints المنشورة. commit/push ليس قبولاً للميزة أو إذناً بالدمج/live أو الجزء التنفيذي التالي. لا تكفي py_compile/parity وحدهما، ولا TDD أحمر دون إثبات سبب الفشل وإذنtests. عند فقد المصادقة: حزمة محدودة متحققة ثم توقف التكديس. لاPAT فيبرومبت الاستئناف ولا وعد بمنعreset100%.

### 16.4 تصحيحنا وما بقي

صُحح صف§10.1 الذي نسب else القديم إلى أحدث نسخة؛ تحسن الفرع الثلاثي يجب الاعتراف به. وصُححV2X02: كان يجمع huge-int مع المدخل الباطل ويطلبUNKNOWN للجميع، بينما§9.1 يمنع الحد الأقصى الاعتباطي. int المقبول بحسبschema يواصل التصنيف دون تحويلfloat؛ غير المدعومUNKNOWN صريح. لا حد جديد ولا حارس منفذ. صارت§15.6 موسومة كتاريخ لا حالة نشر حالية.

أُغلقت فجوة قراءة4277–5059 وتحكيم الادعاءات الأساسية أعلاه فقط؛ ليست شهادة لكل الشات/Arena1–1884 أوجردwriters. بقي التحرير العربي والإحالات والاتساق الشامل، وschema/pagination وأدلةfailed ونموذجwriters وعقودbaseline قبلGO محدد. كلV2T/V2X غير منفذة. لا شهادة لدستور/skills خارجية غير متاحة، ولا تشغيل05.02 أوخدمات حية.

## 17. Full Review بعد النشر اليدوي — محاسبة الشات 1–4276 وArena 2490–3330 ضد المصدر

### 17.1 المصدر والحالة

- القاعدة المنشورة: `04d9584a743e9194118b1e27e49f7ab9c8d2583d` (رفع المالك اليدوي لمحتوى حزمة v5؛ PR9 OPEN/Draft). main@adaf586 مدموج داخل الفرع. Gist revision d6a0088 لم يتغير وليس GO.
- المصادقة: الجلسة السابقة مررت توكن `Tifo123lord` (push=False → 403)؛ الجلسة الحالية بلا أي ربط. النشر يعتمد على المالك (منح write أو ربط `number949481-ux` أو رفع يدوي لحزمة متحققة).
- ملفا `manifest.json` و`review_recovery.patch` في جذر المستودع أثر جانبي للرفع اليدوي؛ خارج allowlist؛ قرار المالك.
- القراءة أدناه تمت على بصمة الشات `265125393d331aa0c9978e7f47d8cc0c38f600f29c0cff4c7d3b4c56d86658c1` (5299 سطراً) وArena 3330 سطراً، وتحققت كل الإحالات السطرية أدناه على شجرة 04d9584 مباشرة.

### 17.2 محاسبة ادعاءات الشات 1–4276 ضد المصدر الحالي

| نطاق الشات | الادعاء | الحكم بعد التحقق من المصدر |
|---|---|---|
| 1–330 | خطة 00: نقل فحص الهدية من 05.02:376–412 والمعزل الثلاثي 98–104 والفرز 112–114؛ مواضع bridge `is_account_ready` L1025 / `get_eligible_accounts` L1092 / `refresh_cookies_on_401` L1140 | المواضع صحيحة إلا 1140 (الدالة في 1122). الدوال الفعلية: 973 `read_accounts_safe`، 989 `update_account_data`، 1025، 1092، 1108 `mark_account_cooldown`، 1122، 2324 `_is_never_copy_file`. ادعاء «التزام دستور بولا» غير قابل للشهادة (الدستور غير متاح لنا). |
| 444–447، 1216 | 01.03 L170–177: `check_balance_before=False`, `balance_refresh_hours=29`, `refreshed_balance=100` | **صحيح حرفياً** (01.03:170/176/177، مع 167 `prefer_balance=100`، 171 `check_unknown_balance=True`، 172 `tie_break="random"`). 01.03 READ-ONLY بالحوكمة؛ هذه القيم هي مصدر «29h/100» في عقودنا. |
| ~470 | «verifier L39 اسم ملف وهمي غير موجود» | **خطأ**: verifier:39 `QUARANTINE_FILENAME = "accounts_genspark_blocked_failed__block_failed.json"` موجود، و`quarantine_account_atomic` (376–406) تنشئ `records=[]` عند الغياب/التلف. Arena محق. الأرقام الحية 185/130/279 غير قابلة للتحقق (ملفات الحسابات متجاهلة بـgitignore). |
| 693–760 | شجرة القرار: ≥100 يرسل؛ <100 فحص هدية؛ >14 معزل؛ ≤14 تبريد 29h؛ 401→B2C؛ فشل→failed | «فحص الهدية فقط عند <100» يتسق مع عقودنا (§10). الشجرة **تخلو من فرع UNKNOWN/TRANSIENT**؛ وعتبتها `>` تخالف المصدر 05.02:408 `>=` (انظر 17.4). |
| 884–1000 | «8 زوايا» + خريطة BEFORE/AFTER + اختبارات مقترحة | مقترحات تصميم؛ revival/TTL cache/startup sanitizer أُلغيت لاحقاً بأوامر المالك (أصوات 6–8). لا تُحتسب كقرارات. |
| 1059–1104 | sort مقترح `(1 if balance>=100 else 0, -balance, last_used)` تصاعدي | خطأ اتجاه tuple (F18 عند Arena). المصدر الحالي 1104 يفرز بـ`last_used` فقط؛ والاختيار الفعلي 585–596 `candidate_pool = ready_accounts[:5]` ثم `random.choice`، فالفرز وحده لا يفرض الأعلى رصيداً (Arena `SORT_ONLY_DOES_NOT_FORCE_TOP_BALANCE`). |
| 1145–1160 (أصوات 6–10) | أوامر المالك نصاً: لا استرجاع (6)؛ كل BEFORE/AFTER «باللي موجود فعلاً… مش استنتاج» (7)؛ لا TTL ولا تنظيف إقلاع ولا تعقيد، التحديث فقط لما يؤخذ من 5.2 (8)؛ 502/504 ليست failed، اتبع رد 5.2 والانتقال للحساب التالي (9) | **هذه هي المرجعية الحاكمة للعقود** (§10–§12): no revival، no cache، transient≠dead، UNKNOWN ليس 0/DEAD. أي خطة وكيل تخالفها مرفوضة بغض النظر عن «الدستور». |
| 1199–1460 | 012345 BEFORE/AFTER: verifier 38–41 + `STALE_GIFT`؛ `inspect_account_gift_status` ينسخ 05.02 بما فيه `STALE,999` و`except: pass`→AUTH_FAILED؛ bridge 2954–2958 AFTER يستدعي `check_gift_status_for_account`/`isolate_stale_gift_account`؛ «L3270–3303» AFTER يستخدم `gve.check_live_balance` و`sess` غير معرّف و`release_account_selection(curr_email, owner_token)`+`continue` | BEFORE لـ2954–2958 **مطابق** للمصدر الحالي (LOW_BALANCE → cooldown → return None). AFTER **غير قابل للنسخ**: الدوال غير موجودة، `sess` غير معرّف، وفرع else يصنف AUTH_FAILED كهدية منتظمة (F17). يبقى تصميماً لا كوداً. |
| 1461–1629 | «المترجم» rebuild_refactor PARTS 9181 مقابل 9286/9285 | Arena صحح إلى 9285؛ rebuild_refactor 190–216 assert ثم rmtree؛ مختبر Arena: `ONLY_LAST_BOUNDARY_CHANGED exit=1 … p03 '(' was never closed line 652` — أي تعديل حدود PARTS يكسر المولد؛ **شرط قبل GO**. |
| 1630–3513 | تقرير Arena مضمّن | مطابق Arena 1–1884؛ ليس شاهداً مستقلاً؛ لا يُحتسب مرتين. |
| 3535–3850 | «Peer Review Audit» من 00: يقر F02/F05/F13/F18؛ يتهم Arena بـ«Paralysis» وبمخالفة T0/T1/T2؛ «7 مكاسب»؛ «محصنة 100%» | الإقرارات مقبولة؛ الاتهامات الدستورية لا نشهد لها؛ «100%» ادعاء بلا دليل اختباري (لا اختبار واحد نُفذ للميزة). |
| 3849–3940 | الوكيل عدّل الملف الخطأ (00 بدل 012345) ثم نقل | يؤكد ملكية الملفات: 00 لجلسة 00، 012345 للأخرى؛ تقريرنا وحده قابل للتعديل. |
| 3941–4276 | Voice 16: «مش هننفذ عمياني»؛ D1–D6 «محسومة»: D1 `timedelta(days=14)`؛ D2 -1 UNKNOWN بلا إرسال/تبريد/عزل؛ D3 single-writer+RLock؛ D4 zero mutation on transient؛ D5 عزل 13 فشل + المترجم؛ D6 01.03 READ-ONLY؛ «جاهزة للتنفيذ في انتظار GO» | D1/D2/D4/D6 متسقة مع عقودنا. **D3 خاطئ تقنياً**: `threading.RLock` يحمي داخل عملية واحدة فقط؛ Arena `SYNTHETIC_TWO_PROCESS_RLOCK expected 2 actual 1`؛ single-writer يحتاج جرد writers (05.02 + bridge + verifier + أي CLI) وقفل ملف أو مالك وحيد. D5 «عزل» 13 فشل ليس إصلاحاً. **لا GO صادر** حتى آخر الشات. |

### 17.3 Arena 2490–3330: التفريغات والمختبرات والجرد

- 2490–2552 تفريغات الأصوات 1–17 مطابقة لما في الشات (بما فيه صوت 17: التعديل في 012345 فقط).
- 2553–2612 نتائج المختبرات الاصطناعية (stubs، بلا شبكة) — ما يُحتسب دليلاً وما لا:
  - `exact_14_days / 14_days_and_one_hour → STALE days=14`: يثبت `>=` في 05.02:408 ويؤيد الاختيار `>=`.
  - `network_error_and_no_password → DEAD expired_session_no_password` و`simulated_b2c_502_with_password_text → INVALID_CREDENTIALS` و`simulated_balance_502_user_200 → EMPTY_BALANCE balance=0` و`FAKE_502_WITH_SUSPENDED_TEXT → SUSPENDED is_dead=True`: **تناقض مباشر مع أمر المالك صوت 9** (502/504 ليست failed). هذه هي الفجوة الأولى التي يجب أن يغلقها أي عقد: transient → UNKNOWN بلا كتابة.
  - `bridge_balance_minus_one_recent_refresh → send_chat_called=True`: -1 يصل للإرسال؛ يؤيد D2 وعقد «UNKNOWN لا يُرسل business».
  - `INJECTED_FAILOVER_{TIMEOUT,UNKNOWN,TRANSIENT,AUTH_FAILED,LOGIN_FAILED} → primary_changed=True last_used_written=True`: الجسر يكتب في كل مسار فشل؛ ينقض D4 «zero mutation on transient» **بحالة الكود الحالية** — D4 هدف لا واقع.
  - `write_failed_destination: primary=[] destination_exists=False` و`FAIL_VAULT_WRITE: source_quarantined=True vault_exists=False`: target-first/readback غير مطبق؛ فقدان حساب ممكن؛ يؤيد §11 (source-cut بعد readback فقط).
  - `CORRUPT_VAULT overwritten=True`: الملف التالف يُستبدل بصمت؛ يحتاج نسخة `.corrupt-<ts>` قبل الاستبدال.
  - `INJECTED_PRE_TRY_EXCEPTION: claim_still_held`: تسرب claim؛ يحتاج try/finally.
  - `COPY_FILTER` (نسخة d2eb49d من 012345 NOTES): لا يحجب `accounts_genspark.json`/`.env.production`/`telegram_bot_token.txt`. **version-dependent**: النسخة الحالية من 012345 NOTES (803–824) تضم `accounts_genspark.json` و`"token" in f` و`.tmp_`؛ فالنتيجة تاريخية وليست تناقضاً مع قراءتنا. يبقى فحص الفلتر الحالي مطلوباً قبل أي GO يمس النسخ (GF01 غير معاد).
  - `SYNTHETIC_TWO_PROCESS_RLOCK expected 2 actual 1` و`STANDALONE_ENGINE_PICKER live_probe_calls=0`: الأول ينقض D3؛ الثاني يثبت أن picker المحرك المستقل لا يفحص حياً.
  - مختبر المترجم: `CURRENT_MAP exit=1 sentinel_survived=True` (الخريطة الحالية تعمل)؛ أي تغيير حدود يكسر p03 عند السطر 652.
- 2613–3095 كود المختبرات: stubs؛ لم نشغلها (خارج النطاق) ولا نحتاج ذلك لأن استنتاجاتها البنيوية تحققت بقراءة المصدر.
- 3096–3330 جرد SHA256 عند d2eb49d (01.33 `4d0bd7e65fe8…` 542683 B؛ 05.02 `192d3a344…`): 01.33 الحالي 542683 B متطابق الحجم؛ لا إعادة حساب كاملة هنا — راجع §15 لبصمات adaf586.

### 17.4 ما ثبت ضد المصدر وما لا يثبت

ثبت:
1. تعارض داخلي في 05.02: docstring 305 و430 «> threshold_days» بينما الكود 408 `>=`. خطة 00 (PLAN/NOTES) تبنت `>` من الـdocstring. **القرار**: `>=` وفق الكود الحي وجواب المالك (Arena:555)؛ ويُسجل التعارض كملاحظة توثيق لا كتعديل (05.02 خارج النطاق).
2. الجسر لا يملك مسار UNKNOWN: `bal_check >= 0` فقط (2954)؛ -1/None يسقط إلى الإرسال.
3. لا وجود لأي من دوال AFTER المقترحة في 012345؛ الفرق بين «موجود» و«مقترح» لم يُلتزم به (مخالفة صوت 7).
4. RLock ≠ single-writer عبر العمليات.
5. 13 failure تاريخية ما زالت غير مصلحة ولا معاد قياسها؛ «محصنة 100%» بلا أساس.

لا يثبت (ولا ندعيه):
- أي شيء عن الأرقام الحية (185/130/279) أو حالة الحسابات أو سلوك Genspark/B2C الفعلي؛ أي شهادة لدستور/skills خارجية؛ أي نتيجة runtime جديدة.

### 17.5 الشروط قبل GO (مجمّعة) وخطة الاعتماد

شروط لا يُمنح GO قبل إغلاقها (كل بند يحتاج دليلاً revision-scoped على HEAD محدد):
- S1 عقد UNKNOWN/TRANSIENT في الجسر: 502/504/timeout/-1/None → لا إرسال business، لا cooldown، لا عزل، لا كتابة؛ الانتقال للحساب التالي. (صوت 9، D2، D4)
- S2 عتبة `>=14` يوماً UTC موحدة في الكود والوثائق؛ تسجيل تعارض docstring 05.02.
- S3 جرد writers لملفات الحسابات (05.02، bridge 989/1108/1122، verifier 376، أي CLI) ونموذج single-writer أو قفل ملف حقيقي؛ RLock وحده مرفوض.
- S4 حفظ ذري target-first → readback → source-cut؛ نسخة `.corrupt-<ts>` قبل أي استبدال؛ try/finally على claim.
- S5 schema/pagination لاستجابة الهدية (ما الذي يُعد «هدية حديثة»؛ ctime؛ حدود الصفحة) مثبتة من مصدر حي أو HAR منقّح، لا من ذاكرة الوكلاء.
- S6 أدلة allowlist لملف failed (ما الذي يدخله ولماذا؛ لا جمع المعزل القديم فيه إلا بقرار المالك الموثق).
- S7 baseline أحمر: 13 failure إما مصلحة أو مقبولة صراحة من المالك بقائمة أسماء؛ لا «عزل».
- S8 المترجم: أي تغيير PARTS يخضع لمختبر Arena (sentinel + p03 compile) قبل الدمج.
- S9 إذن المالك الصريح لأي لمس لـverifier (AGENTS:22)؛ 01.03 READ-ONLY مطلقاً.
- S10 سياسة credit-in-flight: ما يحدث لرصيد محجوز أثناء العزل/التبريد.

خطة الاعتماد (لا تنفيذ): المالك يراجع §10–§13 و§17.5 ويعتمد/يعدّل كل Sx كتابةً؛ عندها فقط تُحوَّل V2T إلى مهام تنفيذ بفرع منفصل واختبارات قبول لكل Sx؛ GO يُمنح لكل مرحلة على حدة لا للميزة كلها.
