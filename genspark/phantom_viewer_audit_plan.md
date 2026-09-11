# خطة فحص وإصلاح: المعاينة المبكرة وبرومبت العمل غير الظاهر

## تسليم التنفيذ المعتمد — 2026-09-11

اعتمد المالك V2 في `8017af0` مع E1–E5 صراحة؛ نُفذ الجسر والـfaithful split والاختبارات. لا قرارات معلقة. الكود المختبر `54e461f`؛ بعده تقرير/توثيق فقط. PR #8 للمراجعة، لا دمج أو نشر حي.

- [x] Credit-only <=180، clear فقط عند COMPLETED، لا compact لطلب جديد بعد نجاح سابق.
- [x] Fresh fork موثق لا يرث readiness قديمة، مع رفض sentinel ومع بقاء إلغاء/رصيد/أقفال/مراقبة الطلب الحالي.
- [x] trigger_status اختياري schema-v1؛ تنظيف due غير موثقة دون حذف ملفات المستخدم.
- [x] استهلاك trigger محفوظ قبل إرسال الصيانة لمنع replay عند فشل حفظ لاحق؛ لا gate summary جديدة.
- [x] نجاح الصيانة -> تبريد A القياسي -> B مختلف ونفس active_query على آخر رابط؛ لا credit increment أو نجاح مستخدم مزيف.
- [x] فشل الحفظ/التبريد يوقف مع الرابط؛ نقصB/busy/maxattempts يحفظ latest؛ -1 لا يعاقب و<100 يتخطى.
- [x] full session_timeout للصيانة، timeout غير ائتماني لا يدوّر، cancellation أعلى من فشل metadata.
- [x] الاختبارات المعنية والسياسة القديمة حدثت دون skip/xfail؛ R-A-B/failure/legacy/preflight/virtual-clock regressions.
- [x] generator وparity11؛ pytest1085 +60 subtests، canonical1085 Exit0، syntaxExit0، docs34/links8.

الأجزاء التالية أرشيف المقترح وBEFORE/AFTER بأرقامها القديمة. العبارات «انتظار GO» و«غير منفذ» وقرارات E المفتوحة تخص ما قبل الاعتماد وقد استبدلت بهذا التسليم. لا تدّعِ تحققاً حياً؛ جميع الاختبارات offline. حفظ metadata لا يضمن distributed exactly-once تحت أي crash تعسفي.


## V2 — استعادة وتجميد التكليف الجديد، انتظار GO

<!-- PR8_ARCHITECTURE_V2 -->

المرجع الحالي: https://gist.github.com/pijsal1-tech/ca574f7050bc4c92d07d55bbe5d2427c

- استعيد `c2b5d22`؛ commit المقترح المحلي `0d6aac6` فُقد قبل push بعد reset. يعاد المقترح من سجل الجلسة، ولا يعاد runtime أو التحقيق السابق. main=`08943e6`، Python مطابق لـ`3f9b2c5`.
- أجاب المالك: تشغيل monolith عند `3f9b2c5`، مهلة 1000s وزمن مشاهد 1008s ثم TIMEOUT، وmanifest قديم due=false/deferred=true/bypass_ready=false. المسار يطابق 7145/7147 -> 2944 -> timeout -> 2946. هذه إفادة المالك مع المصدر، وليست trace شبكياً فحصناه. حسابياً 1000s=16m40s و1008s=16m48s.
- العقد الجديد: أهلية compact بعد CREDIT_EXHAUSTED مؤكد وduration<=180 فقط؛ COMPLETED يمسح due ولا يجدول؛ نجاح الصيانة على A يؤدي إلى تبريده والعمل على B مختلف؛ fresh fork الموثق يتجاوز readiness الموروثة فقط.
- هذا ينسخ قرارَي جدولة COMPLETED والسقوط للعمل على نفس حساب الصيانة من الاتفاق القديم. تبقى P16 والإلغاء/P18 والرصيد وschema-v1 وzero-artifacts في effective fast وQwen=2.
- اسم حلقة الحسابات الصحيح: `send_message_with_auto_account_failover` (3077). نجاح الصيانة يجب استهلاكه **قبل** فرع URL-success عند 3462، وإلا ينهي المهمة ويعيد الحساب active عند 3471–3473.
- تنفيذ التشغيل غير مصرح قبل تقديم Flow وBEFORE/AFTER والمخاطر في تعليق رسمي على PR #8 واعتماد GO. طلب الاستعادة لا يحل محل بوابة اعتماد المقترح.
- القرارات الباقية للاعتماد: رصيد B المعلوم >=100 مقابل سلوك balance=-1 القائم؛ فشل حفظ latest/due أو cooldown؛ فشل compact غير الائتماني؛ ترحيل due القديمة غير الموسومة؛ أثر `mark_account_cooldown` على حقول last_credit_exhausted.
- نتائج 1066 pytest +51 subtests أدناه من جلسة V1، وليست اختبارات جديدة أو تحققاً من V2. لا ملفات Python أو tests أو generated outputs تغيرت.

### تفاصيل V2 المعمارية

استعيد المقترح من سجل الجلسة بعد دفع تجميد المتطلبات `0491639`. ما يلي مقترح معماري، وليس patch منفذاً. أرقام BEFORE تخص `3f9b2c5`، وتطابق مصدر الفرع الحالي؛ AFTER يُنسب إلى موضع الاستبدال الأصلي لا إلى أرقام مستقبلية مخترعة.

#### 1. Flow للحالات الثلاث

```text
طلب عمل -> اختيار/claim حساب -> preflight رصيد وإلغاء
  -> Continue/Fork القائم -> نشر P16 وبطاقة المعاينة فور PID
  -> fresh fork موثق: تجاهل readiness الموروثة فقط
  -> إرسال العمل ومراقبة الطلب الحقيقي
      |
      +-- COMPLETED
      |    -> clear due=false (لا schedule ولا /compact)
      |    -> تسليم النتيجة النهائية
      |    -> طلب مستقل لاحق: إرسال عادي بدون compact بسبب مدة النجاح السابق
      |
      +-- CREDIT_EXHAUSTED مؤكد، duration >180
      |    -> compact_before_send=false وdue=false
      |    -> checkpoint القائم + تبريد R + بوابة الاستئناف وحدوده
      |    -> الحساب التالي يفرع latest public URL ويرسل الاستئناف مباشرة
      |
      +-- CREDIT_EXHAUSTED مؤكد، duration <=180
           -> due=true من حدث الرصيد الحالي فقط
           -> checkpoint القائم + تبريد حساب العمل R + بوابة الاستئناف/الحدود
           -> اختيار حساب الصيانة A المؤهل -> Fork من آخر رابط محفوظ -> P16
           -> /compact فقط -> monitor maintenance
                 |
                 +-- فشل/إلغاء/غموض: النتيجة الحقيقية، لا نجاح وهمي أو work على A
                 |
                 +-- COMPACT_COMPLETED (انتقال داخلي)
                      -> حفظ latest URL للصيانة واستهلاك due
                      -> تبريد A وإطلاق claim عبر finally القائم
                      -> اختيار B مختلف، preflight، Fork من رابط الصيانة -> P16
                      -> نفس active_query المنتظر مرة واحدة؛ لا compact آخر
                      -> مراقبة رد B الحقيقي، ثم الحالات أعلاه
```

R حساب العمل المستنزف، A حساب الصيانة، B حساب العمل التالي. قد تستخدم السلسلة ثلاثة حسابات. A وB يحسبان ضمن max_account_attempts، لكن نجاح الصيانة لا يزيد credit_continuations. الأهلية iff credit<=180 لا تلغي cancellation أو checkpoint gate أو حدود الحسابات. القياس يبقى span الحساب عبر current_account_duration، لا يتحول إلى زمن توليد خالص.

**مهم:** B يستعمل رابط الصيانة كأصل Continue/Fork وقد يحصل على PID جديد. نحافظ على نفس المشروع المنطقي ومفتاح registry، لا نعد بنفس PID عبر حسابين. لا ننقل cookies أو session/history المثبت لحساب A إلى payload حساب B. يحافظ المحرك على جلب جلسة الهدف الحالية.

#### 2. D1 — استثناء fresh fork من readiness الموروثة فقط

BEFORE: عند 2827 لا يوجد علم fresh fork؛ 2908–2909 ينتج project_id؛ 2941 يطبق شرط deferred على أي target:

```python
project_id, history = None, []
# عند 2908–2909
forked_pid = get_public_forked_pid(orig_pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
project_id = forked_pid or orig_pid
# شرط 2941
elif compact_deferred and getattr(bridge_cfg, "compact_bypass_blocked", False):
```

AFTER، إضافة/استبدال المواضع نفسها:

```python
project_id, history = None, []
is_new_fork = False  # يتصفّر كل محاولة؛ carry_pid ليس fork جديداً
# عند 2908–2909
forked_pid = get_public_forked_pid(orig_pid, cookies, mod=mod, cfg=cfg, email=email, bridge_cfg=bridge_cfg)
project_id = forked_pid or orig_pid
is_new_fork = bool(forked_pid
                   and extract_project_id(forked_pid) == forked_pid
                   and project_id != orig_pid)
# يبقى نشر/callback 2912–2918 في مكانه كما هو
# شرط 2941 فقط
elif (compact_deferred
      and getattr(bridge_cfg, "compact_bypass_blocked", False)
      and not is_new_fork):
```

جسم readiness القائم لـsame PID/fallback، وإلغاء 2949–2950، وفحص الرصيد والجلسة قبل fork، وأقفال project/account وP18 وmonitor بعد work: لا تحذف. هذا استثناء سياسة المالك لا برهان بروتوكولي على خلو كل fork من النشاط. لا يعمم على retry بعد محاولة إرسال غير مؤكدة.

#### 3. D2 — جدولة credit فقط ومسح COMPLETED

BEFORE 3247–3264:

```python
if status == "CREDIT_EXHAUSTED" or (
        status == "COMPLETED" and not is_model_decline_response(last_text)):
    duration = current_account_duration(bridge_cfg, curr_email)
    due = (duration <= COMPACT_TRIGGER_SECONDS
           and not getattr(bridge_cfg, "compact_deferred", False))
    if status == "CREDIT_EXHAUSTED" and due:
        bridge_cfg.compact_before_send = True
    schedule = getattr(bridge_cfg, "compact_schedule_callback", None)
    if callable(schedule) and (due or status == "COMPLETED"):
        # schedule(status, pub_url, duration) مع حارس الخطأ القائم
        ...
```

AFTER المقترح قبل عداد credit 3266:

```python
if status == "CREDIT_EXHAUSTED":
    duration = current_account_duration(bridge_cfg, curr_email)
    bridge_cfg.compact_before_send = duration <= COMPACT_TRIGGER_SECONDS
    bridge_cfg.compact_deferred = False
    bridge_cfg.compact_deferred_this_run = False
    schedule = getattr(bridge_cfg, "compact_schedule_callback", None)
    if callable(schedule):
        try:
            schedule(status, pub_url, duration)
        except Exception as err:
            bridge_cfg.compact_before_send = False
            log_event("warning", f"[COMPACT] Schedule persistence failed: {type(err).__name__}", email=curr_email)
elif status == "COMPLETED":
    bridge_cfg.compact_before_send = False
    clear = getattr(bridge_cfg, "compact_clear_callback", None)
    if callable(clear):
        try:
            clear(pub_url)
        except Exception as err:
            log_event("warning", f"[COMPACT] Clear persistence failed: {type(err).__name__}", email=curr_email)
```

هذا يزيل استدعاء schedule من COMPLETED تماماً؛ clear تنظيف وليس جدولة. يشمل COMPLETED التقني الذي يتحول لاحقاً إلى MODEL_DECLINED. credit طويل يكتب false صراحة فلا تبقى أهلية قصيرة قديمة. credit مؤكد جديد لا يحجبه deferred قديم للأبد. لا نحرّك progress/checkpoint gate أو Live Rebind أو بناء active_query في 3453.

فشل حفظ schedule في هذا المقتطف يسقط الصيانة الاختيارية فقط ولا يمنع checkpoint القائم؛ **هذه سياسة معروضة للاعتماد في E2، ليست قراراً مفترضاً**. لا يمكن ضمان due=false على قرص فاشل؛ يجب إظهار فشل الحفظ لا ادعاء نجاحه.

#### 4. D3 — مصادر الجدولة الأخرى وترحيل المانفيست

تعديل الثلاثة مواضع المذكورة وحدها غير كافٍ:

- worker 7148–7149 يحمّل due القديمة دون سببها.
- callback 7151–7155 يحسب due من duration فقط، متجاهلاً stage_status.
- setter 4360–4366 قد يعيد فرض deferred ويلغي حدث credit جديد حتى بعد تغيير sender.

BEFORE worker:

```python
cfg.compact_before_send = bool(requested_pid and compact_state.get("due") is True
                               and not cfg.compact_deferred)
```

AFTER مقترح، metadata اختيارية داخل schema-v1:

```python
stored_duration = compact_state.get("duration_seconds")
valid_duration = (isinstance(stored_duration, (int, float))
                  and not isinstance(stored_duration, bool)
                  and 0 <= stored_duration <= COMPACT_TRIGGER_SECONDS)
cfg.compact_before_send = bool(
    requested_pid and compact_state.get("due") is True
    and compact_state.get("trigger_status") == "CREDIT_EXHAUSTED"
    and compact_state.get("source_pid") == requested_pid
    and valid_duration and not cfg.compact_deferred
)

def schedule_compact(stage_status, stage_url, duration):
    registry.set_compact_state(
        stage_status == "CREDIT_EXHAUSTED" and duration <= COMPACT_TRIGGER_SECONDS,
        extract_project_id(stage_url), duration,
        chat_session_id=getattr(cfg, "compact_current_session_id", ""),
        trigger_status=stage_status)

def clear_compact(stage_url):
    registry.set_compact_state(False, extract_project_id(stage_url),
                               trigger_status="COMPLETED")

cfg.compact_clear_callback = clear_compact
```

بالـsetter 4342 يضاف keyword-only `trigger_status=None`. بعد بناء state في 4347–4348:

```python
if trigger_status in ("CREDIT_EXHAUSTED", "COMPLETED"):
    state["trigger_status"] = trigger_status
    if trigger_status == "COMPLETED":
        state["due"] = False
```

وبدل شرط 4362 وحده:

```python
if (context is None
        and trigger_status not in ("CREDIT_EXHAUSTED", "COMPLETED")
        and (deferred or keep_deferred)):
    # نفس state.update القديم
    ...
```

يبقى القفل والكتابة والتحقق 4367–4370 كما هي. context نجاح compact يبقى due=false؛ لا تغيير schema أو حذف user files. تنظيف COMPLETED لا يعيد deferred القديمة.

**ترحيل مقترح للاعتماد:** due=true بلا trigger موثوق/مدة صالحة/تطابق requested PID لا تشغّل compact. تنظف due عبر setter القائم عند صلاحية source_pid وتسجل السبب، دون تصنيف التاريخ المجهول كـCOMPLETED مختلق. قد يسقط بهذا compact قديم حقيقي غير موسوم؛ المقايضة معلنة E4. واقعة due=false/deferred=true لا تحتاج حذف manifest؛ يحل fresh-fork guard الحبس.

#### 5. D4 — نجاح الصيانة لا يرسل work على A

BEFORE 2936–2940:

```python
history = verified_compact_context["messages"]
if on_project_start_callback:
    on_project_start_callback(project_id)
# ثم يهبط إلى work send 2971 بنفس account/cookies
```

AFTER:

```python
if _cancel_event is not None and _cancel_event.is_set():
    return build_genspark_viewer_url(project_id), CANCELLED_STATUS, None, "", None
bridge_cfg.compact_before_send = False
bridge_cfg.compact_bypass_blocked = False
return build_genspark_viewer_url(project_id), "COMPACT_COMPLETED", None, "", None
```

يحافظ run_verified_compact على send/monitor/current context وcallback latest؛ لا API جديدة أو تغيير tuple. لا archive أو progress business بعد الصيانة. D4 وD5 ينفذان في نفس chunk؛ نشر D4 وحده يكسر handoff.

#### 6. D5 — التقاط الرمز الداخلي في failover قبل نجاح URL

BEFORE: لا branch لـCOMPACT_COMPLETED؛ URL ينجح في 3462، ثم يعيد الحساب active عند 3471–3473 وينهي المهمة.

AFTER: إضافة بعد معالجة cancellation 3201، وقبل 3208 وبقية progress/success branches:

```python
if status == "COMPACT_COMPLETED":
    if not mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours,
                                 json_path=json_path):
        return pub_url, "COMPACT_HANDOFF_BLOCKED", curr_acc, None, ""
    if not extract_project_id(pub_url):
        return pub_url, "COMPACT_HANDOFF_BLOCKED", curr_acc, None, ""
    active_url = pub_url
    bridge_cfg.compact_handoff_pending = True
    bridge_cfg.compact_before_send = False
    bridge_cfg.compact_bypass_blocked = False
    bridge_cfg.last_credit_resume_target_url = active_url
    bridge_cfg.last_credit_resume_project_id = extract_project_id(active_url)
    log_event("info", "[COMPACT] maintenance complete; rotating account for pending work", email=curr_email)
    # لا تغيير active_query ولا +1 credit_continuations ولا fake CREDIT_EXHAUSTED
    continue
```

- finally 3485–3488 يغلق span ويحرر claim حتى مع continue. tried_emails يحوي A منذ 3157؛ B مختلف ضمن السلسلة. max_account_attempts يبقى كما هو.
- لا progress_callback للعمل ولا credit-handoff إضافي ولا general-success يعيد A إلى active.
- cancellation يفحص قبل claim B أيضاً، وpre-send cancel باقٍ؛ إلغاء قبل إتمام الصيانة لا يسبب تبريداً عقابياً، وإلغاء بعد اكتمالها يمنع work التالي.
- تضاف mapping لـCOMPACT_HANDOFF_BLOCKED في describe_terminal_outcome قرب 6973، لا يستخدم كنجاح أو كنفاد/timeout ملفق.
- إذا لا يوجد B/الحسابات busy/نفدت attempts، تحفظ آخر URL وتعيدها بدلاً من None في 3142/3152/3489 **فقط عند compact_handoff_pending**؛ لا زيادة حدود ولا fallback إلى A. الراية تصفر عند الوصول إلى work dispatch 2971، لا عند تخطي حساب LOW_BALANCE.
- callback حفظ latest موجود في remember_compact 7170–7176، لكن run_verified_compact يبتلع خطأه عند 2723–2728. **D5 وحده ليس ضمان حفظ ذري**. E2 يعرض اشتراط راية `compact_handoff_saved` يضبطها callback بعد نجاح حفظ الحالة والهوية، وتفحص قبل انتقال B. إذا فشل الحفظ: تبريد A حسب نجاح الصيانة ثم توقف صريح مع URL، لا إعادة ضغط ولا summary gate ثانية. هذا التفصيل مشروط باعتماد E2.
- لا ننقل verified_compact_context الخاص بـA إلى B؛ B يجلب تاريخه/جلسته بواسطة المحرك القائم. لا تعديل engine أو model contracts.

#### 7. القرارات الباقية للاعتماد — ليست إعادة Q1–Q3

**E1 — رصيد B:** أوصي بالإبقاء على 100 كحد أدنى `>=100`، لا اشتراط مساواة 100 أو حد أعلى، والتبريد 29h من bridge_cfg. لكن preflight القائم قد يستمر مع balance=-1/فشل القياس؛ هل تبقيه أم تشترط على B رصيداً **مقاساً** >=100، وإلا توقف مؤقت بلا عقوبة؟ التشديد إن اعتمد يقتصر على مرحلة handoff ولا يغيّر كل حسابات النظام خلسة.

**E2 — فشل الحفظ/التبريد:** أوصي بعدم إرسال B إن فشل cooldown أو حفظ latest بعد الصيانة، مع COMPACT_HANDOFF_BLOCKED ورابط قابل للاستعادة ودون compact مكرر. فشل حفظ due قبل الصيانة: هل يعتمد إلغاء الصيانة الاختيارية فقط مع استمرار checkpoint العادي، أم يمنع الانتقال؟ عند فشل clear بعد COMPLETED يجب إظهار تحذير وعدم الادعاء أن due=false حُفظت؛ لا يمكن توفير ضمان القرص بمجرد شرط برمجي.

**E3 — فشل compact غير الائتماني:** مقترح الاعتماد هو إبقاء TIMEOUT/READ_FAILED/ACTIVITY_STOPPED/CREDIT_UNCONFIRMED كوقف مؤقت، بلا تبريد لمجرد الغموض وبلا إرسال موازٍ على B. نجاح الصيانة وحده يفعل التبريد الخاص. typed credit الحقيقي أثناءها يبقى خطأ حقيقياً له حدود الحسابات والاستئناف، ولا يخلط بالرمز الداخلي.

**E4 — due القديمة:** هل تعتمد تنظيف/تجاهل الأهلية غير الموسومة بسبب CREDIT_EXHAUSTED موثوق؟ يمنع ضغط نجاح قديم، مقابل احتمال إسقاط صيانة قديمة حقيقية غير موسومة. لا bulk reset أو حذف checkpoints.

**أثر cooldown المحاسبي:** helper 1099–1109 يكتب last_credit_exhausted ووقته ولو الصيانة نجحت دون نفاد. استخدام mark_account_cooldown مطلوب في التكليف. هل تعتمد أثره كما هو مع reason صيانة في اللوج، أم تسمح بوسيط reason اختياري يحافظ على cooldown دون تسجيل نفاد وهمي؟ المقترح لا يفترض أن نجاح compact يساوي استنزافاً فعلياً.

#### 8. الأثر والمخاطر وRegression Matrix

لا يمكن تأكيد «صفر مخاطر» قبل التنفيذ/الاختبار. المخاطر المحددة والضوابط:

| السيناريو/الخطر | اختبار القبول |
|---|---|
| manifest المبلغ عنه + fresh fork | worker حقيقي ومحرك وهمي: readiness الموروثة لا تستدعى، original prompt مرة واحدة |
| fork=None/same/sentinel أو carry_pid retry | لا fresh-fork bypass؛ cancellation وsame-PID readiness محفوظة |
| COMPLETED/رفض موديل بمدد 0/55/180/180.001/300 | due=false؛ schedule لا يستدعى؛ worker التالي لا compact |
| credit<=180 وcredit>180 | حدود 179.999/180/180.001؛ short ينشئ أهلية، long يمسح true القديمة؛ deferred قديم لا يلغي حدثاً جديداً |
| R credit -> A compact -> B work | صفر work على A، cooldown مرة، prompt B مطابق active_query، لا +1 credit بسبب نجاح الصيانة |
| internal success مع URL | لا يصل إلى general-success/update active ولا ينهي user task |
| نجاح الصيانة بلا fresh summary | لا تعاد بوابة summary أو الست قراءات؛ معنى maintenance completion محفوظ |
| latest PID/session | B يفَرّع آخر رابط A، P16 يعرض PID الحالي؛ لا pin سياق A إلى B |
| no B/busy/max attempts/low balance | لا إعادة استخدام A؛ حفظ latest، سبب صريح، لا COMPLETED كاذبة |
| cancellation/P18/transport error | لا business send بعد الإلغاء، no blind overlap/resend، finally يغلق ويحرر |
| فشل الحفظ/التبريد | اختبارات E2 واستخراج السبب؛ لا ادعاء حفظ أو ضمان exactly-once عبر crash |
| legacy registry/restart | schema-v1 وlocks وcheckpoints محفوظة؛ اختبار metadata الجديدة والقديمة وعدم تكرار compact المكتملة |
| artifact policy | صفر archive/snapshot/diff/scan/upload في effective fast؛ GitHub precedence وallow_non_fast ثابتان |
| اختبارات قديمة تعاقدياً | تحدّث توقعات COMPLETED scheduling/same-account بإذن المالك، لا skip/xfail أو ضعف للحراس |
| package drift | rebuild canonical وضبط PARTS؛ parity11، full pytest، syntax، hadith_sijil Exit0 |

التعديل المستهدف: الجسر الأساسي + tests القائمة + generator/faithful generated package + تقارير الاستعادة. Qwen=2، المحرك، anchors، Telegram architecture وP16/الأزرار خارج التغيير. لا تغيير نص البطاقة ضمن V2 دون موافقة منفصلة؛ التكليف يطلب P16 كما هي.

#### 9. Micro-tasks والـchunks

| ID | المهمة | الاعتماد/التسليم |
|---|---|---|
| V2-00 | استعادة الريموت وإجابات المالك ومراجعة source | مكتمل؛ لا تعاد PR #7 أو محاكاة V1 |
| V2-01 | دفع تجميد المتطلبات قبل استعادة التفاصيل | مكتمل عند 0491639 |
| V2-02 | استعادة Flow وD1–D5 وE والمخاطر؛ تعليق رسمي PR #8 | الدفعة الحالية، docs-only |
| V2-03 | GO صريح على المقترح والقرارات المفتوحة | **STOP قبل runtime** |
| V2-04 | regressions fresh fork/credit-only/legacy migration | بعد GO؛ اختبارات قبل الإصلاح |
| V2-05 | D1+D2+D3 ومولد/حراس متسقة | chunk صغير متماسك، اختبار ثم commit/push قبل التالي |
| V2-06 | D4+D5 والحفظ/انعدام B وفق E | sender+loop معاً، لا نشر D4 منفرداً |
| V2-07 | worker R-A-B/accounting/cancellation/artifacts matrix | تحقق offline، لا منصة حية |
| V2-08 | syntax/full pytest/parity/canonical gate | تقرير حقيقي فقط؛ لا اعتبار baseline القديم نجاحاً للجديد |
| V2-09 | sync/squash مع tree equality وتسليم PR للمراجعة | checkpoints كل chunk؛ لا merge/deploy |

عند reset: اقرأ current_execution وPROGRESS، fetch وقارن رأس PR، ثم تحقق من تعليق العلامة PR8_ARCHITECTURE_V2 قبل إعادة نشره. لا تحول طلب استعادة عام إلى GO على قرارات لم تُعتمد. بعد عرض هذا المقترح نتوقف للموافقة، والتجربة الحية تحتاج تصريحاً مستقلاً.

## أرشيف V1 — قبل إفادة المالك وتغيير العقد

القسم V2 أعلاه هو الحالي؛ الأسئلة غير المجابة والقرارات المخالفة أدناه تاريخية.

## 0. نقطة التجميد والنطاق

- التاريخ: 2026-09-11. المصدر المقروء: `main@08943e6` بعد `git fetch origin`؛ هذا commit دمج PR #7 ويحوي `3f9b2c5`. الإصلاح السابق مدموج، لا يعاد تنفيذه.
- تكليف المالك: قراءة Gist، عدم الافتراض، السؤال عن المجهول، وخطة كاملة بتاسكات؛ حفظ ودفع نقاط صغيرة لمقاومة reset.
- المرجع: https://gist.github.com/pijsal1-tech/7972532cfcf3be03c01d83954880dfc5
- قرئت نسخة raw كاملة لأن تحويل الصفحة إلى Markdown أسقط معظم النص العربي.
- هذه **خطة تحقيق ومعالجة مشروطة**، وليست إعلاناً بإثبات سبب الواقعة أو اعتماداً لحذف بوابات الأمان. لم يتغير runtime أو tests أو generated package.
- أرقام السطور التالية تخص revision أعلاه. تطابق رقمي 2908/2971 المذكورين في Gist مع المصدر الحالي لا يثبت أن جهاز التشغيل استخدم نفس الملفات.
- لا فتح لرابط مشروع Genspark، لا استخدام لحسابات المنصة أو بيانات HAR، لا تجربة حية أو merge/deployment.

## 1. النتيجة المؤكدة وحدود الدليل

### مؤكد من المصدر

1. استلام PID ثم النشر العام والبطاقة يحدثان قبل إرسال برومبت العمل. البطاقة لا تثبت حدوث POST ولا بدء SSE.
2. توجد ثلاثة مواضع `return` مباشرة بين التفريع واستدعاء العمل: 2935 و2946 و2950. توجد أيضاً استدعاءات يمكنها الانتظار أو رفع استثناء قبل الإرسال.
3. حالة deferred المخزنة تطلب فحص جاهزية حتى على PID متغير؛ شرط worker لا يقارن `source_pid` أو session بالمشروع المستهدف عند تحميل العلم.
4. فحص الجاهزية ليس `return` ثابتاً: يستطيع إرجاع COMPLETED ثم يرسل العمل. ويمكن أن ينتظر حتى timeout أو يخرج بسبب cancellation/structured failure/P18.
5. عنوان البطاقة 7336 يدعي بدء البناء مبكراً؛ هذا خلل دقة عرض مثبت بغض النظر عن السبب الذي أوقف الطلب.
6. فحص readiness دون attempt evidence قد يصنف credit موروثاً من آخر assistant كنفاد حالي، قبل اختبار snapshot FINISHED. هذه إمكانية مثبتة بالمصدر وبمحاكاة، وليست إثباتاً أنها حدثت في الواقعة.

### غير مثبت من اللوج المتاح

- أن POST لم يحدث فعلاً: غياب سطر send_chat/SSE من مقطع اللوج ليس دليلاً شبكياً.
- أن الدالة خرجت فوراً، لا أنها كانت داخل callback أو قراءة شبكة أو readiness.
- قيمة compact_state الفعلية وقت الواقعة ومكان manifest الذي اختاره التشغيل.
- هل التفريع أعاد PID مختلفاً فعلاً عن الأصل؛ PID الظاهر وحده غير كافٍ.
- أن آخر رد قديم credit، أو أن المنصة تعطي FINISHED/current session للفرع الجديد.
- أن مجرد PID جديد يعني مشروعاً آمناً للإرسال المتداخل. لا نحذف الأمان بهذه الفرضية.

## 2. خريطة التنفيذ بالأرقام

كل الأرقام في هذا القسم تخص `01.33_telegram_gen_bridge.py` إلا عند تسمية المحرك.

| الموضع | ما يحدث | ما يثبته وما لا يثبته |
|---|---|---|
| 2843–2858 | فحص رصيد قبل fork/chat؛ LOW_BALANCE | يفسر آلية تخطي الحساب الأول في الوصف؛ لا يفسر خروج الحساب الثاني |
| 2903–2907 | جلب تاريخ الأصل أو fallback فارغ | قد يكون السجل القديم مستخدماً؛ ليس إقراراً بإرسال البرومبت |
| 2908–2909 | `forked_pid` ثم `project_id = forked_pid or orig_pid` | وجود project_id لا يثبت نجاح fork جديد |
| 2912–2918 | نشر مبكر + callback مباشر | يحدث قبل كل بوابات compact والعمل |
| 2768–2788 | خيط P16 في الخلفية | ترتيب سطر نجاحه في اللوج لا يحدد موضع الخيط الرئيسي |
| 2777–2781؛ 2388–2440 | helper النشر قد يعيد رابط fallback، والخيط يسجل النجاح بعدها | رسالة Public ليست تحققاً مستقلاً من صلاحية المعاينة أو بدء التوليد؛ لا نلغي P16 |
| 2920–2935 | compact مطلوب وغير deferred؛ أي نتيجة غير COMPACT_COMPLETED تعاد | **return 2935** يمكن أن يعيد URL دون work send |
| 2682–2684 | جلب baseline للضغط؛ HTTP غير 200 -> READ_FAILED | قد يمنع حتى إرسال /compact نفسه |
| 2691؛ 2700–2712 | إرسال /compact ثم متابعة ثم جلب سياق العمل | هنا قد يكون /compact أُرسل بالفعل رغم عدم إرسال العمل |
| 2936–2940 | compact مكتمل: تسليم history ثم callback | الاستثناء المعتمد باقٍ: لا ينهي مهمة المستخدم، ثم يسقط إلى work send؛ callback هنا غير محاط محلياً بـ try/except |
| 2941–2946 | deferred + bypass_blocked -> readiness | **return 2946** فقط إذا كانت نتيجة الجاهزية ليست COMPLETED |
| 2948 | مسح علم الفحص في الذاكرة بعد نجاحه | ليس حفظاً لـ bypass_ready في manifest هنا |
| 2949–2950 | فحص cancellation | **return 2950** مشروع ولا يُلغى |
| 2958–2971 | بناء kwargs ثم استدعاء العمل | مدخل send_chat، لا دليل وحده على أن HTTP أُرسل |
| المحرك 1902 وما بعدها؛ 2231 | send_chat يبني payload قبل `sess.post(...ask_proxy...)` | يلزم الفصل بين دخول الدالة، محاولة POST، وقبول طلب حالي من المنصة |
| 3208 وما بعدها | TIMEOUT/READ_FAILED/ACTIVITY_STOPPED/CREDIT_UNCONFIRMED لا تدوّر الحساب | تجنب تكرار الطلب تحت عدم اليقين؛ لا نغيّر السياسة تلقائياً |
| 7325–7348 | callback بطاقة المعاينة | نص «بدأ البناء» 7336 يسبق work send؛ ضغط السياق يبدل عنوانه فقط |

### فحص الجاهزية في `monitor_chat_completion`

- 2567–2569: readiness يبدأ RUNNING ثم قراءة نشاط.
- 2576–2589: cancellation والمهلة؛ الافتراضي 1000 ثانية من 2551، وليس مهلة فورية. زمن استدعاء شبكة منفرد قد يؤخر العودة عن هذا الفحص الدوري؛ لا ندعي deadline صلباً لكل عمليات الشبكة.
- 2592–2597 ثم 2660–2661: تغيّر نشاط P18 يوقف، ولا يمنح تصريح إرسال جديد.
- 2601–2608: قراءة التاريخ؛ 401/403 خروج صريح، وغير 200 يستمر حتى المهلة.
- 2609–2618: آخر assistant يصنف؛ typed credit قد يخرج قبل فحص FINISHED.
- 2631–2644: snapshot موثوق/current session أو terminal reply يمكن أن يثبت الجاهزية، بشرط عدم نشاط ظاهر.
- جاهزية المشروع ليست اكتمال مهمة المستخدم. بعد نجاحها يجب الوصول إلى 2971 بالبرومبت الأصلي.

## 3. سلسلة الحالة المخزنة

```text
ProjectRegistry.get_compact_state (4337–4339)
  -> worker (7143–7149)
  -> compact_deferred = (deferred is True)
  -> compact_bypass_blocked = deferred and (bypass_ready is not True)
  -> fork / publication / preview (2908–2918)
  -> readiness (2941–2944)
  -> غير جاهز: return 2946؛ جاهز: إرسال 2971
```

- absent `bypass_ready` يعامل كغير True، لكن غياب deferred لا يفعل هذا الفرع.
- `source_pid` و`chat_session_id` محفوظان عبر setter 4341–4370؛ worker 7145–7149 لا يستعملهما لربط علم الفحص بالهدف.
- setter 4360–4366 يحتفظ بالتأجيل عندما session مجهولة أو مساوية للقديمة؛ لا يوجد شرط PID داخل keep_deferred.
- 7157–7159 يربطان callback حفظ التأجيل؛ 7162–7168 يطبعان due المتناقض بصورة best-effort، لا يمسحان كل manifest.
- بعد readiness ناجح يمسح العلم في الذاكرة فقط؛ restart يمكن أن يعيد تحميل deferred/bypass_ready القديمين. هذا لا يثبت حجباً دائماً؛ القراءة الحالية قد تنجح مرة أخرى.
- وجود هذه السلسلة لا يثبت أن manifest الواقعة يحملها. نحتاج قيمه المنقحة من ملف التشغيل الحقيقي، لا ننشئ قيماً مفترضة للمالك.

## 4. المحاكاة المنفذة الآن — دليل سلوك لا replay للحادث

شُغّل sender وmonitor الحقيقيان باستخدام fixtures الاختبارات القائمة، مع محرك/شبكة/Telegram والنشر mocked، PID أصل وفرع مختلفان، وsession_timeout=0.03 للحالات السلبية. لم ينشأ ملف اختبار جديد؛ لم تُلمس بيانات تشغيل حقيقية.

| مدخل صناعي | النتيجة | مرات work send | ترتيب | archive |
|---|---|---:|---|---:|
| deferred، فرع جديد، snapshot FINISHED/current-session | COMPLETED | 1 | preview ثم business_send | 0 |
| deferred، فرع جديد، trailing /compact، لا terminal proof | TIMEOUT | 0 | preview فقط | 0 |
| deferred، فرع جديد، آخر assistant typed credit موروث | CREDIT_EXHAUSTED | 0 | preview فقط | 0 |
| cancellation بعد preview | CANCELLED | 0 | preview فقط | 0 |
| compact مطلوب، baseline HTTP 503 | READ_FAILED | 0 | preview فقط | 0 |

كل الحالات أعادت viewer URL. هذه نتائج sender فقط؛ سيناريو credit لم يشغّل حلقة failover في هذا reproducer، فلا نستنتج منه عدد الحسابات اللاحقة.

Baseline جديد فعلي: `TMPDIR=/home/user/webapp PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider` -> **1066 passed +51 subtests، Exit 0**. نجاح baseline لا ينفي الواقعة. لم تُشغّل البوابة canonical في هذه المراجعة الوثائقية، ولم يحدث تحديث لتقرير نجاح الاختبارات.

## 5. أسئلة المالك قبل تثبيت العلاج

### Q1 — النسخة التي كانت تعمل

ما commit التشغيل وقت 03:26:05؟ وهل المدخل monolith أم `bridge_refactor/main.py`؟ هل حدثت تحديثات/نسخ يدوية؟ أرسل المسار وأمر التشغيل و`git rev-parse HEAD` إن كان المجلد Git، أو بصمات SHA256 للجسر والمحرك عند غيابه. إذا تعذر استرجاع نسخة الواقعة نثبت ذلك، ولا ننسبها للنسخة الحالية يقيناً.

### Q2 — خروج أم انتظار؟

بعد بطاقة المعاينة: انتظرت قد إيه؟ هل ظهرت رسالة نهائية وما نص الحالة؟ هل البوت ظل مستجيباً؟ هل ضغطت إلغاء أو أعدت تشغيله؟ نحتاج اللوج من قبل اختيار الحساب إلى النتيجة النهائية/traceback أو نهاية مدة الانتظار، مع حجب البريد والأسرار والبرومبتات الخاصة. قيمة `session_timeout` مهمة.

### Q3 — حالة المشروع الفعلية

أرسل فقط `compact_state` من manifest الصحيح لمشروع تليجرام 17 كما كان قريباً من الواقعة: due/deferred/bypass_ready/source_pid/chat_session_id/verified/updated_at، مع project key وربط PID الأصل بالفرع aliases ثابتة إن أردت. اذكر المسار الذي قرأ منه البرنامج (المحلي أم الأب). لا ترسل ملف الحسابات أو `.env` أو tokens/cookies ولا manifest كاملاً إذا احتوى معلومات خاصة. إذا الحالة تغيرت بعد الواقعة اذكر ذلك.

### Q4 — المقصود بعبارة «يرسل دائماً على الفرع الجديد»

هل المطلوب إزالة أثر حالة الصيانة القديمة مع **الإبقاء** على الإلغاء والنفاد الحالي المثبت وأخطاء الصلاحيات ومنع التداخل؟ أم تريد تغيير سياسة التعامل مع جاهزية مجهولة أيضاً؟ لا نفترض الموافقة على إرسال أعمى لمجرد اختلاف PID. ونحتاج موافقتك على بطاقة فورية صادقة: «المعاينة متاحة، جارٍ تجهيز إرسال الطلب» بدل ادعاء بدء البناء قبل الإرسال، بدون تأخير النشر أو الزر.

### طلب HAR مشروط، لا طلب لتنزيل ملفات المشروع

- ملف مقترح `fork_resume_incident_sanitized.har`: العملية نفسها من continue_conversation إلى قراءات مشروع الفرع ومحاولة ask_proxy والنتيجة. السبب: 2908–2909، 2601/2631–2640، ومحرك 2231؛ نحتاج status/schema/current session وrequest identity، لا محتوى الملفات.
- إن أردنا نفي POST من البوت نحتاج التقاط **حركة عملية البوت نفسها** أو trace طلباتها؛ HAR متصفح viewer وحده لا يثبت عدم إرسال Python لطلب.
- HAR يدوي لـ fork ثم إرسال عادي مفيد للمقارنة فقط إذا تعذر التقاط العملية؛ لا ندعي أنه replay.
- إزالة Authorization/Cookie/Set-Cookie وtokens وquery secrets والمحادثات؛ الحفاظ على علاقات المعرفات عبر aliases متسقة وحقول الأدوار والحالة والنوع.
- لا حاجة لإعادة ملفي compact الموجودين؛ لا يثبتان بروتوكول fork أو حالة هذه الواقعة.

## 6. خطة التاسكات الكاملة واعتمادياتها

| ID | المهمة | الملفات/المخرجات | شرط القبول | الحالة/الاعتماد |
|---|---|---|---|---|
| T00 | استعادة main والـcheckpoint والتحقق من دمج السابق | Git + PROGRESS + recovery | لا تكرار PR #7، أساس ثابت 08943e6 | مكتمل |
| T01 | قراءة Gist كامل وتتبع كل مخارج pre-send | هذه الخطة مع أرقام السطور | فصل دليل المصدر عن ادعاءات الواقعة | مكتمل |
| T02 | محاكاة المسارات وbaseline بلا منصة حية | نتائج القسم 4 | preview قبل send مثبت، عدة مخارج مميزة، صفر archive | مكتمل |
| T03 | حفظ هذه الخطة وcheckpoint ودفع PR وثائقي | genspark + PROGRESS | hash بعيد يساوي المحلي؛ لا runtime diff | تسليم هذه الدفعة |
| T04 | استلام Q1–Q4 والأدلة المتاحة | ملحق evidence منقح | تحديد نسخة الواقعة والمدة والحالة أو تسجيل فقدان الدليل | ينتظر المالك |
| T05 | تحديد المسار الذي حدث فعلاً أو إثبات أن الأدلة لا تكفي | سجل diagnosis/decision | شرط return معروف من trace/state، أو instrumentation مصرح به؛ لا جزم اصطناعي | بعد T04 |
| T06 | إضافة regressions منقحة للفرع الجديد والـworker الحقيقي | tests/test_auto_compact.py وtests/test_credit_completion_recovery.py؛ اختبارات P16/P25 عند الحاجة | الاختبار الخاص بالعيب المثبت يفشل قبل إصلاحه؛ لا تغيير متوقع اختبار لإخفاء عيب | بعد اعتماد T05 |
| T07 | تعديل جراحي لمسار السبب فقط | 01.33 sender/worker أو monitor وفق الدليل | prompt الأصلي يصل مرة واحدة عند الجاهزية؛ لا compact-success خاتمة للعمل؛ لا نقل تلقائي لمعلومات parent كحالة current | بعد T06 واعتماد سياسة Q4 |
| T08 | دقة البطاقة وتشخيص المراحل بلا تأخير P16 | callback 7325 وما حول بوابات 2920–2971 | زر فور PID؛ تمييز preview/maintenance/waiting/dispatch/ack، ولا ادعاء قبول خادم من دخول دالة | يعتمد على Q4؛ يمكن فصله عن علاج الجاهزية |
| T09 | إعادة توليد faithful package | scripts/rebuild_refactor.py + bridge_refactor | تحديث PARTS إن تحركت الحدود، parity 11/11، لا تعديل أجزاء مولدة يدوياً | مباشرة مع كل chunk runtime |
| T10 | اختبارات مركزة ثم كامل وsyntax وcanonical | tests + تقرير البوابة الحقيقي | كل الاختبارات خضراء؛ لا skips/xfails؛ عدم تغيير Qwen=2 | بعد كل chunk/ختام الإصلاح |
| T11 | حفظ checkpoint ودفع كل chunk قبل التالي | genspark/recovery_state.json + PROGRESS + Git/PR | لا شغل غير مدفوع قبل بدء التالي؛ عند reset يُستعاد remote لا الذاكرة فقط | مستمر |
| T12 | تسليم diff محدود وقرار Ready | PR مع summary/evidence/tests/limitations | fetch/sync، squash تغييرات هذه المهمة فقط مع tree equality؛ no merge/deploy | بعد T10 |
| T13 | تحقق ميداني منظم بموافقة مستقلة | نسخة محددة + logs/network منقحة | نفس PID المعاينة، prompt جديد موثق ثم رد حقيقي؛ لا تكرار/تنزيل | ليس مصرحاً تلقائياً |

لا مدة تقديرية رقمية قبل معرفة الأدلة. T07 لا يبدأ لمجرد أن T03 دُفع؛ freeze يعني حفظ المؤكد ونقاط القرار، لا تثبيت تشخيص غير مثبت.

## 7. BEFORE / AFTER المقترح وحدود كل تعديل

المقتطفات التالية **مقترحات غير مطبقة**. لا يمكن تقديم patch نهائي للسبب الجذري قبل Q1–Q4. لا ننسب أرقام سطور نهائية لـ AFTER قبل كتابته.

### A. تمييز تهيئة المعاينة عن الإرسال — تغيير عرض يمكن عزله

BEFORE، 7335–7336: عنوان البطاقة «بدأ بناء المشروع السحابي فوراً!» عند callback المستدعى في 2916.

AFTER المقترح:

```python
# داخل callback الموجود، دون تأخير _early_make_public_async أو زر المعاينة
text = (
    "<b>المعاينة متاحة؛ جارٍ تجهيز إرسال الطلب.</b>\n"
    # نفس حقول المشروع والحساب والموديل والكيبورد القائمة
)
```

- مرحلة compact تحتفظ بعنوانها.
- إضافة مرحلة «جارٍ إرسال الطلب» عند الاقتراب من 2971 لا تعني أن الخادم قبله.
- مرحلة «الطلب قيد التنفيذ» لا تظهر إلا بدليل طلب حالي. إن احتاج الدليل hook في المحرك، يطرح scope صريح منفصل؛ لا نتوسع تلقائياً إلى المحرك.
- إعادة استخدام وتحديث نفس البطاقة وفق الإمكانات القائمة، وعدم إضافة سبام أو تأخير استدعاء الإرسال. فشل Telegram لا يبتلع البرومبت.

### B. إزالة صمت بوابة الجاهزية — logging مشروط بلا تغيير السياسة

BEFORE، 2941–2946:

```python
elif compact_deferred and getattr(bridge_cfg, "compact_bypass_blocked", False):
    cfg._chat_attempt = None
    ready_status, ready_text = monitor_chat_completion(
        mod, cookies, cfg, bridge_cfg, project_id, None, time.time(), email, readiness=True)
    if ready_status != "COMPLETED":
        return build_genspark_viewer_url(project_id), ready_status, None, ready_text, None
```

AFTER مقترح أولي للرصد، لا يمثل علاج الحالة:

```python
elif compact_deferred and getattr(bridge_cfg, "compact_bypass_blocked", False):
    log_event("info", "[PRE_SEND] stage=readiness business_dispatched=false")
    cfg._chat_attempt = None
    ready_status, ready_text = monitor_chat_completion(
        mod, cookies, cfg, bridge_cfg, project_id, None, time.time(), email, readiness=True)
    log_event("info", f"[PRE_SEND] stage=readiness_result status={ready_status} business_dispatched=false")
    if ready_status != "COMPLETED":
        return build_genspark_viewer_url(project_id), ready_status, None, ready_text, None
```

تضاف علامات مكافئة قبل compact وبعده، وعند cancellation وقبل استدعاء العمل. لا يسجل query/cookies/history. يمكن استخدام attempt correlation غير سري لتتبع الترتيب؛ دخوله يحتاج تحديد نطاقه مع الاختبارات. لا يُسمى هذا الإصلاح وحده علاجاً لعدم الإرسال.

### C. الحالة القديمة على فرع مختلف — patch العلاج يتوقف على الدليل

BEFORE، 7145–7149:

```python
cfg.compact_deferred = compact_state.get("deferred") is True
cfg.compact_bypass_blocked = cfg.compact_deferred and compact_state.get("bypass_ready") is not True
cfg.compact_before_send = bool(requested_pid and compact_state.get("due") is True
                               and not cfg.compact_deferred)
```

AFTER التعاقدي المقترح إذا أثبتت الواقعة انتقال latch قديم:

```text
احتفظ بتأجيل الصيانة الاختيارية وفق نطاقها المعتمد.
انقل source_pid/session كبيانات ربط لا كحالة جاهزية للفرع الجديد.
بعد نتيجة fork الفعلية حدّد: PID جديد موثق / نفس PID / fallback للأصل.
احسم جاهزية الهدف من دليله الحالي وسياسة Q4 المعتمدة.
لا تفسر خطأ assistant موروثاً بوصفه نفاد المحاولة الجديدة دون دليل حالي.
إذا جاهز: أرسل original query عبر 2971 مرة واحدة.
إذا إلغاء/نشاط/غير معلوم/صلاحيات: أظهر السبب الحقيقي واحفظ عدم يقين الإرسال؛ لا blind resend.
```

لا مقترح من نوع `if forked_pid: compact_bypass_blocked=False` بلا شروط: helper 2453–2457 يعيد أي fk_pid صالح ظاهرياً دون اشتراط اختلافه عن الأصل في هذا المسار، و2909 قد يرجع للأصل. وحتى PID مختلف لا يثبت وحده أن التوليد غير نشط.

إذا السبب بدلاً من ذلك baseline READ_FAILED للضغط، يعالج مصدر القراءة/خطأها وما تعرضه البطاقة، لا يطبق تعديل latch غير ذي صلة. وإذا المحرك وصل 2231 فالتشخيص ينتقل إلى الاستجابة/العرض بدلاً من حذف pre-send gate.

## 8. مصفوفة القبول للإصلاح بعد اعتماده

1. أصل وفرع مختلفان، delayed old compact metadata، هدف موثوق جاهز -> preview فوري ثم original prompt مرة واحدة على الفرع، مراقبة الرد الحقيقي.
2. same PID أو fork fallback -> لا يعامل كفرع جديد؛ الحفاظ على قواعد safety الحالية.
3. قديم deferred + unknown/active target -> لا نجاح وهمي ولا إرسال أعمى؛ حالة صريحة ومحدودة وقابلة للإلغاء.
4. آخر assistant قديم typed credit في فرع جديد -> لا ينسب تلقائياً إلى محاولة لم تبدأ؛ إشارات نفاد الحساب الحالي الفعلية محفوظة.
5. compact مطلوب: نجاح -> /compact مرة ثم original prompt مرة، لا return نجاح خاص بالصيانة للمستخدم.
6. compact read failure أو timeout -> عدم عرض بدء العمل؛ السبب واضح؛ لا تنزيل ولا تدوير بسبب عدم يقين فقط.
7. cancellation قبل/بعد preview وأثناء القراءة -> صفر work send بعد الإلغاء؛ الموارد تحرر.
8. P18 -> وقف فوري دون تحويله إلى إذن إرسال متداخل.
9. Telegram callback يفشل أو يتأخر -> اختبار يميز هذا المسار ولا ينسبه للصيانة؛ سياسة عدم ابتلاع البرومبت محفوظة.
10. restart + manifest قديم/حديث: no bulk reset، schema v1، إثبات قيمة الحقول الفعلية لا افتراضها.
11. low balance أول حساب -> تخطٍ قبل fork/send؛ الحساب التالي يستخدم query الصحيح ولا يتكرر العمل.
12. P16 -> النشر والزر قبل الإرسال، لا إلغاء/تأخير الميزة؛ public log ليس ack للعمل.
13. effective fast -> صفر archive/snapshot/diff/scan/upload؛ GitHub precedence القائمة ثابتة.
14. threshold <=180 وQwen=2 وcloud resume allow_non_fast وtyped credit وأولوية cancellation ثابتة.
15. engine entry مقابل HTTP attempt مقابل correlated acknowledgement -> لا مساواة بينها في اللوج أو UI.

## 9. chunking والتراجع والاستعادة

- دفعة هذه الجلسة: docs-only تشمل الخطة والجذر PROGRESS وrecovery؛ فحص UTF-8/JSON/diff/security ثم commit/push وPR وثائقي. لا حاجة لإعادة توليد package لتوثيق فقط.
- بعد اعتماد العلاج: regression + أضيق patch + package parity في chunk متماسك، اختباره وcommit/push قبل التالي؛ الرصد/UI يمكن فصله إن كان معتمداً ولا يعتمد على patch غير مكتمل.
- لا تدخل raw HAR أو بيانات الحسابات أو manifest الحقيقي في Git. لا تحفظ credential في origin أو الملفات؛ تستخدم مصادقة مؤقتة.
- عند reset: اقرأ أول PROGRESS ثم `current_execution`؛ fetch وقارن main/head/PR؛ استعد المدفوع فقط ولا تعد PR #7 أو مهام T00–T02 المكتملة. إذا لم يثبت push لا تدعِ أن العمل محفوظ عن بعد.
- التراجع عن إصلاح مستقبلي: revert للـchunk المعني مع generated counterpart وtests المتسقة؛ لا تعكس Qwen=2 ولا compact-credit المدموج، ولا تحذف بيانات المستخدم.
- عند التسليم تجمع commits المهمة الجديدة فقط فوق أساسها بعد sync، مع التحقق من تطابق الشجرة. يتوقف التنفيذ التشغيلي الآن عند أسئلة T04/Q1–Q4، وليس عند مشكلة قديمة أو نقص في إعادة تنفيذ إصلاح سابق.
