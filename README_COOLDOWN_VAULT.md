# معزل التبريد الموحد — `accounts_cooldown.json` + `account_log.jsonl` (MAINT-4-B)

> صفحة واحدة لأي وكيل/مالك قادم. القرارات الحاكمة: `RESUME.md §3–§3.11.8` + جدول D1–D39. الميثاق الدائم في رأس `PROGRESS.md`. هذه الصفحة تحلّ محلّ نسخة MAINT-3 (التي كانت تعتمد العتبة `FORBIDDEN_MOVE_AFTER_N=2` و`cooldown_until_ts` وسجل `account_log.json` مُقنَّعاً).

## لماذا
- قبل MAINT-3 كان حساب يرجع **403 (FORBIDDEN)** يُوسم **نجاحاً** في `accounts_genspark.json` (RESUME §3.1 T5).
- MAINT-3 عالجت ذلك بعتبة «403 على مشروعين مختلفين خلال 24h». المالك قرر في MAINT-4 (D26) أن **أي إشارة واحدة** كافية: **نقل أعمى فوري N=1** — 05.02 هو الحَكَم الوحيد على صحة الحساب لاحقاً.

## الملفات (كلها بجوار `accounts_genspark.json` — D6)
| الملف | الدور | من يكتب | من يقرأ |
|---|---|---|---|
| `accounts_genspark.json` | الأساسي | 01.33 + 05.02 | 01.33 + 05.02 |
| `accounts_cooldown.json` | **معزل التبريد الدائم** (قائمة مسطحة؛ سجل الحساب كاملاً + `quarantine_info{reason, moved_at, by}` — **بلا** `cooldown_until_ts`/ساعات — D27) | 01.33 (Cut&Move) + 05.02 (`--revive -q` يحذف المنقول) | 05.02 فقط (الفحص الدوري) |
| `accounts_cooldown.json.lock` | **القفل المشترك** بين العمليتين (D33/R-B) — يُنشأ ويُحذف تلقائياً | 01.33 + 05.02 | — |
| `account_log.jsonl` | سجل حركات **JSON Lines** — سطر واحد لكل نقل، إلحاق فقط O(1) (D28/D32) | 01.33 (`by="01.33"`) + 05.02 (`by="05.02"`) | بشر/أدوات مراجعة |
| ⛔ `accounts_failed.json` / ⛔ `accounts_delayed_gifts_credits.json` | وجهتا كتابة فقط | 05.02 | **لا يُمرَّران للفحص أبداً** |

### سجل الحركات `account_log.jsonl` — **البيانات كاملة بقرار المالك المحلي (D28)**
```
{"ts": 1762000000.0, "at": "2026-11-01T12:00:00", "event": "move_to_cooldown_vault", "email": "...", "password": "...", "cookies": {...}, "reason": "FORBIDDEN", "from_path": "/ABS/accounts_genspark.json", "to_path": "/ABS/accounts_cooldown.json", "by": "01.33", "meta": {...}}
```
- الحقول الثابتة (`ACCOUNT_LOG_FIELDS`): `ts, at, event, email, password, cookies, reason, from_path, to_path, by` (+ `meta` اختياري). **لا إخفاء ولا تقنيع** — الملف محلي على جهاز المالك ومحمي بـ`.gitignore` (D37: `account_log.jsonl*`, `*.lock`, `*.bak`, `*.cooldown_move.bak`, `accounts*.json.tmp*`).
- 01.33 **يُلحق فقط** (لا `json.load`، لا تقليم). التقليم (30 يوماً / 5000 سطر) يقع **حصراً** في 05.02 `_trim_account_log` عند بدء كل `run_revival`.
- أحداث 05.02: `return_to_primary` (HEALTHY) · `move_to_failed` (DEAD) · `move_to_delayed_gifts` (STALE).

## متى يُنقل الحساب (01.33 — `send_message_with_auto_account_failover` + preflight P13)
النقل = **أعمى فوري من أول إشارة** (D26). الأسباب في `COOLDOWN_VAULT_REASONS` (01.33 p03):

| السبب | الإشارة | إن فشل النقل (الاحتياطي فقط) |
|---|---|---|
| `FORBIDDEN` | أول 403 — بلا `forbidden_hits`، بلا عتبة | تبريد 5 دقائق في المكان |
| `EMPTY_STREAM_FAILED` | صمام DEC-07 | تبريد 5 دقائق |
| `LOGIN_FAILED` (C1) | فشل تجديد الجلسة **ثم** فشل الدخول بالبيانات عبر `gve.master_inspect_and_heal_account` — في المواقع الأربعة كلها (استثناء التجديد، P13، failover، إعادة المحاولة) | تبريد 5 دقائق (**لا** 1800s بعد الآن) |
| `BALANCE_UNREADABLE` | `check_balance` = −1 | تبريد 5 دقائق |
| `ZERO_BALANCE_STALE_GIFT` (D35) | رصيد 0 **و** `classify_gift_freshness(acc)[0] == "STALE"` | التبريد القديم 29h |

- رصيد 0 مع هدية `FRESH`/`UNKNOWN` ⇒ التبريد القديم 29h في المكان (`COOLDOWN_SECONDS`) — **لا نقل** (الهدية ستُصرف).
- **قاطع الشبكة (D34):** `BALANCE_UNREADABLE_BREAKER_N = 2` — حسابان متتاليان بـ−1 في المهمة نفسها ⇒ المهمة تنتهي بحالة **`NETWORK_DOWN`** (غير قابلة للتنفيذ، الحساب الثالث لا يُمَسّ، `NON_ACTIONABLE_PROGRESS_STATUSES`). الحسابان المنقولان يعيدهما 05.02 في الدورة التالية إن كانت الشبكة هي السبب.
- **D29 (الرد الفارغ):** سطرا 01.03 الترمينالية `⏳ بيفكر...` و`⚠️ مفيش نص في الرد!` **توثيقيان فقط**؛ ما يصل 01.33 فعلياً هو `answer = None` ⇒ `detect_response_status(None) == "EMPTY"` ⇒ مسار `EMPTY_STREAM_FAILED` أعلاه. لا تُفتَّش النصوص.
- **tuple فارغ = تعطيل كامل** (السلوك القديم حرفياً). حذف اسم واحد يعطّل سببه فقط. التوسع لحالة جديدة = اسم في الـtuple + `move_account_to_cooldown_vault(email, reason=..., json_path=...)` في فرعها.

النقل = **نسخ أولاً** إلى المعزل ثم **قصّ** من الأساسي (مع `accounts_genspark.json.cooldown_move.bak` دوّار) داخل `FILE_LOCK` + القفل المشترك. فشل القص ⇒ الحساب في الملفين (`move_partial` في السجل) — لا فقدان أبداً. النقل idempotent (`duplicate_detected`). **لا وسم نجاح أبداً** لحساب فشل.

## كيف يعود الحساب (05.02 فقط — لا سكربتات موازية، A5)
```
python "/ABS/PATH/05.02_genspark_delayed_gifts_manager.py" --revive -q "/ABS/PATH/accounts_cooldown.json" -f "/ABS/PATH/accounts_genspark.json" -l 0
```
- **`-l 0`** (D38): `limit <= 0` = فحص **كل** المعزل. **[MAINT-5/Q-15]** صار هو **الافتراضي** مع `--revive` عند إغفال `-l` (كتابته صراحةً ما زالت صحيحة)؛ `-l N` صريح يُحترم.
- **[MAINT-5/Q-14] حارس Rate Limit (الثابت 7.11):** تشغيل 05.02 **بلا** `--revive` (= فحص الأساسي شبكياً) يُرفض بـ`exit 1` ورسالة واضحة ما لم يُمرَّر `--allow-primary-scan` صراحةً — حتى مع `--dry-run` لأن `check_account_status` يتصل بالشبكة. الدورة المجدولة تبقى `--revive -q accounts_cooldown.json` فقط. 01.33 لم يُلمس (Q-11).
- **كود الخروج (D39):** `0` نجاح · `1` عند أي استثناء أو `result["error"]` (مثل `vault_lock_busy`) — المجدول الخارجي يستطيع اكتشاف الفشل.
- الدورة (`run_revival`): تقليم السجل → قراءة المعزل → `check_account_status` لكل حساب → `HEALTHY` ← الأساسي · `DEAD` ← `accounts_failed.json` · `STALE` ← `accounts_delayed_gifts_credits.json` · غير المحسوم يبقى. يحذف `quarantine_info`/`quarantined` عند الإنعاش ويضع **`status=active`، `active=True`، `last_updated`، ورصيد ≥100 ⇒ `cooldown_until=0` + `cooldown_released_at`** (MAINT-4-C D40/D41 — نفس الحقول في فحص `run_quarantine` للحساب HEALTHY) فيقبله `is_account_ready` في 01.33 فوراً؛ **ورصيد <100 ⇒ [MAINT-4-D] `status=cooldown`، `active=False`، `cooldown_until=now+29h` في مكانه** (نفس شكل `mark_account_cooldown` في 01.33 — لا نقل لملف خارجي) فيرفضه `is_account_ready` حتى تنزل الهدية. **[MAINT-4-E] لا ملف `accounts_success.json`:** السليم (في `run_revival` و`run_quarantine`) يبقى في `accounts_genspark.json` فقط (فويس 104/الوثيقة 21؛ Q-7/Q-9/Q-10)؛ علم `--success-file` مهمَل يطبع `[DEPRECATED]` ويُتجاهَل بلا انهيار؛ أي ملف ناجح قديم على القرص يُترك ميتاً ولا يُقرأ. ثم خروج فوري.
- عودة `STALE` من معزل الهدية = يدوياً/جدول المالك (D23) — لا فحص دوري لذلك الملف.

### الجدولة الرباعية (D33/D36 + **D48/MAINT-6**: `--revive` يفحص `accounts_cooldown.json` **فقط**؛ `--sweep` وجبة ≤20 من الأساسي بشيك بوينت دوار — الفاشل/معزل الهدية لا يُفحصان أبداً)
| الدورة | من يستدعي | كيف |
|---|---|---|
| **12:00 ظهراً** | مجدول **نظام التشغيل** على جهاز المالك (Task Scheduler / cron) | السطر أعلاه حرفياً |
| **00:00 منتصف الليل** | **`main.py` الخارجي** للمالك (خارج هذا المستودع) | `subprocess.run([... السطر أعلاه ...])` ثم فحص `returncode != 0` |
| **06:00 صباحاً** [MAINT-6/D48] | مجدول نظام التشغيل (مهلة المهمة ≥ ساعتين) | `python "/ABS/PATH/05.02_genspark_delayed_gifts_manager.py" --sweep -f "/ABS/PATH/accounts_genspark.json"` |
| **06:00 مساءً** [MAINT-6/D48] | مجدول نظام التشغيل (مهلة المهمة ≥ ساعتين) | السطر نفسه حرفياً |

السكربت **جاهز للأمرين** بلا فرق: كلاهما استدعاء CLI عادي؛ التزامن مع 01.33 (أو مع دورة متداخلة) يضمنه **القفل المشترك** أدناه. لا يوجد `main.py` داخل المستودع (A5) — ولا يحتاج.

### ماكينة الكنس الدوار بالتنقيط — `--sweep` (MAINT-6/D48، فويسات 123–133)
- **ما تفعله:** تأخذ وجبة (`-l`، الافتراضي 10، السقف 20 — Q-24) من `accounts_genspark.json` بالنمط `first_n` (Q-21؛ `-m random` مسموح، `-m all` مرفوض)، تفحصها شبكياً بفاصل **60–300 ثانية** بين الحساب والآخر (فويس 130)، وتطبّق مصفوفة الفرز نفسها: ≥100 ⇒ `active/True/cooldown_until=0`؛ <100 ⇒ تبريد في مكانه (**Q-19/فويس 124:** تبريد سارٍ وضعه 01.33 يُترك كما هو ولا يُمدَّد؛ المنتهي/الصفر ⇒ `now+29h`)؛ هدية راكدة ≥14 يوماً ⇒ قص إلى `accounts_delayed_gifts_credits.json`؛ ميت/403/باسورد خاطئ ⇒ قص إلى `accounts_failed.json`؛ خطأ شبكة مؤقت ⇒ يبقى ويُحتسب مفحوصاً (Q-20).
- **الشيك بوينت `genspark_rotation_checkpoint.json`** (بجوار ملف الحسابات، في `.gitignore` — Q-23): يحوي **بصمات sha256 للبريد فقط** (لا بريد ولا باسورد) + `cycle_no`. كل حساب في الأساسي يدخله حتماً (تبريد/صفر/حصانة)؛ يُحفظ ذرياً **بعد كل حساب** (انقطاع الكهرباء لا يعيد المفحوص)؛ وعند `(الأساسي الحالي − المفحوص) == 0` يُصفَّر تلقائياً وتبدأ دورة جديدة (حلقة لا نهائية). طول الدورة ≈ ⌈N/20⌉ يوماً.
- **التزامن (Q-22):** كتابة الملفات الأربعة تتم تحت القفل المشترك `accounts_cooldown.json.lock` (D33 — نفسه في `--revive` و01.33) وبـ**دمج حقول** 05.02 فوق السجل الطازج من القرص (ما يكتبه 01.33 أثناء الفحص مثل `last_used` لا يُفقد). قفل مشغول ⇒ لا كتابة + `exit 1` (يُعاد في الجولة التالية).
- **لا يجتمع** `--sweep` مع `--revive`؛ ولا يحتاج `--allow-primary-scan` لأنه محدود بالتصميم. ضبط **مهلة مهمة Task Scheduler ≥ ساعتين** (الوجبة تستغرق 15–50 دقيقة).

### المشغل الموحد المطور — `bridge_refactor/main_upgrade.py` (MAINT-7/D49–D54، فويسات 135–137)
- **بديل مهام Task Scheduler/cron الأربع كلها:** من مجلد البوت كعادتك: `cd bridge_refactor && python main_upgrade.py` (أو `python bridge_refactor/main_upgrade.py` من أي مكان — المسارات مطلقة من `__file__`). يشغّل `main.py` (البوت 31) كعملية ابن بـ`cwd=bridge_refactor/`، ويطلق 05.02 كعملية ابن منفصلة بـ`cwd=الجذر` في: **00:00/12:00 `--revive -q accounts_cooldown.json -f accounts_genspark.json -l 0`** و**06:00/18:00 `--sweep -f accounts_genspark.json -l 10`** (توقيت الجهاز). مخرجات 05.02 كلها إلى `logs/scheduler_0502.log` (شاشة التيليجرام نظيفة)؛ لوج المشغل `logs/main_upgrade.log`.
- **الإغلاق (D53):** Ctrl+C / SIGTERM ⇒ إنهاء المهمة الجارية ثم البوت (terminate ثم kill بعد 10s) — صفر Zombie؛ خروج البوت لأي سبب ⇒ المشغل يخرج بنفس الكود (يصلح للمراقبة الخارجية). مهمة متداخلة لا تُضاعَف (تُتخطى بتحذير). `--run-now sweep|revive` لتشغيل مهمة فوراً؛ `--no-bot` للمجدول فقط.
- **لم يُلمس شيء قائم:** `main.py`/01.33/كل ملفات `bridge_refactor/` كما هي (p57 يثبّت البصمات)؛ مكتبات قياسية فقط. إن بقيت مهام Task Scheduler القديمة فعّالة **عطّلها** حتى لا تتضاعف الدورات.

### منظومة النظافة الشاملة — `clean_disk_garbage()` داخل `main_upgrade.py` (MAINT-8/D55–D61، فويسات 143–147)
- **لماذا:** 01.33 يحتفظ بآخر 3 `checkpoints/hot/` فقط (L5440) لكنه **لا يحذف أبداً** `archive/<id>.tar.gz` ولا `reports/<id>.json` ⇒ تراكم جيجابايتات. المالك: «طالما عدت ساعة يتمسح — رفع ما رفعش، مفيش استثناء» (فويس 144).
- **متى:** عند إقلاع المشغل قبل انطلاق البوت (D58 تطهير استرجاعي لكل المشاريع القديمة — حتى مشاريع أجهزة أخرى، فويس 143) ثم كل 60 دقيقة داخل `tick`. يُعيد سطراً واحداً في `logs/main_upgrade.log`: «حُذف N | قُصّ N لوج | حُرّر X MB | طازج N | محمي N | أخطاء N | مشاريع N».
- **ماذا يُمسح (>60 دقيقة):** في كل `project_registry/<key>/`: `archive/*.tar.gz` (+ `*.tar.tmp` اليتيمة من انهيار أثناء الكتابة L5211) — D55 | `checkpoints/hot/<id>/` عبر `rmtree` — D56 | `reports/*.json` — D57. وفي مجلد البوت: `extracted_webapp/<pid>/`، `extracted_push_temp/*` (الاسم من كارت الوكيل — لا يظهر في أي كود؛ احتياطي لا-ضرر)، و`webapp*.tar.gz*` **بنمط مقيّد** (لا `*.tar.gz` عام — نسخك الاحتياطية بأمان) — D60.
- **العمر:** الأقدم بين الطابع الزمني في الاسم (`YYYYMMDDTHHMMSS…Z` بتوقيت UTC — 01.33 L5340) و`mtime`؛ للمجلد يُؤخذ أحدث ابن مباشر (تنزيل جارٍ داخل مجلد قديم الشكل لا يُمسح). «حتى لو ملوش تاريخ» (فويس 143) ⇒ المعرّف القديم يُمسح حتى لو `copy2` أبقى mtime طازجاً.
- **اللوجات (D59 + فويس 145):** `bridge_bot.log` و`logs/*.log` فوق 10MB تُقصّ **في مكانها** مع إبقاء آخر 2MB من أول سطر كامل — نفس الملف/نفس inode، لا حذف ولا إعادة تسمية ⇒ `FileHandler` المفتوح في 01.33 (L76، وضع append) يكمل الكتابة في النهاية الجديدة على ويندوز ولينكس. `logs/*.log` الخاملة >30 يوماً تُحذف؛ `bridge_bot.log` لا يُحذف أبداً (قصّ فقط).
- **اكتشاف `project_registry`:** يعكس `resolve_shared_path` في 01.33 (L140–157): بجوار البوت ثم المجلد الأب (فويس 141)، ويُنظَّف كلاهما إن وُجدا؛ `BRIDGE_HOME` يُحترم (runtime.py L26).
- **محرَّم (D61):** `manifest.json`/`manifest.bak`/`queue.json`/`secrets.local.json`/`registry.json` — المنظّف لا يدخل جذر المشروع أصلاً، ولو وصله اسم محمي يتخطاه ويعدّه. كل حذف داخل `try/except OSError` (قفل ويندوز WinError 32 ⇒ تخطٍّ + سطر تحذير، لا انهيار)، وفوقها شبكة أمان في `Supervisor.clean` حتى لا يُسقط أي خطأ المشغل.
- **العاقبة المقبولة بقرار المالك (فويس 144):** بعد ساعة تفقد أزرار «آخر 3 checkpoints / آخر Archive / تقرير الملفات» تفاصيلها (تعرض `UNKNOWN` / «موجود الآن: لا» / «لا يوجد record صالح» — L6419/6436/6474 تنخفض بأمان). ومهمة رفع عالقة >60 دقيقة (توكن/ريبو خاطئ) ستُعلَّم `synced` صورياً عند محاولتها التالية بصفر ملفات (`CHECKPOINT_RECORD_MISSING` L4893 ⇒ L5157) — المالك قَبِل «رفع ما رفعش» صراحة. الـ`.gitignore` لا يغطي `project_registry/` و`logs/` (ليست متتبَّعة؛ لا أثر على Git).

## الأقفال والتزامن (D33 R-A/R-B)
- **داخل 01.33:** الأساسي + المعزل تحت `FILE_LOCK`؛ السجل تحت `ACCOUNT_LOG_LOCK` وحده ويُكتب **بعد** الخروج من `FILE_LOCK` — لا deadlock.
- **بين العمليتين (R-B):** ملف قفل `accounts_cooldown.json.lock` عبر `os.open(O_CREAT|O_EXCL|O_WRONLY)` — الاسم والثوابت نفسها في الملفين: مهلة **30s** (`COOLDOWN_VAULT_LOCK_TIMEOUT_S`)، قفل أقدم من **60s** يُعدّ يتيماً ويُتجاوز بتحذير (`COOLDOWN_VAULT_LOCK_ORPHAN_S`). 01.33: `_with_vault_lock(lock_path, fn) -> (acquired, result)`؛ 05.02: `_with_vault_lock(self, lock_path, fn)` بالعقد نفسه.
- **إعادة القراءة قبل الحفظ (R-A):** 05.02 يُعيد تحميل المعزل **تحت القفل** داخل `_commit_moves` ويحذف المنقولين فقط — أي حساب أضافه 01.33 أثناء الفحص يبقى سليماً. تعذر القفل خلال 30s ⇒ `{"error": "vault_lock_busy", "revived": 0}` ⇒ خروج 1 — لا كتابة.

## المفاتيح (01.33 p03 بعد `mark_account_cooldown`)
- `COOLDOWN_VAULT_FILENAME` · `COOLDOWN_VAULT_LOCK_FILENAME` · `COOLDOWN_VAULT_LOCK_TIMEOUT_S` · `COOLDOWN_VAULT_LOCK_ORPHAN_S` · `ACCOUNT_LOG_FILENAME` · `ACCOUNT_LOG_FIELDS` · `COOLDOWN_VAULT_REASONS` · `BALANCE_UNREADABLE_BREAKER_N`.
- **محذوف نهائياً (D27/C2):** `COOLDOWN_VAULT_HOURS`, `FORBIDDEN_MOVE_AFTER_N`, `FORBIDDEN_HITS_WINDOW_HOURS`, `register_forbidden_hit`, `cooldown_until_ts`, `cooldown_hours`. لا تُعِدها.

## الاختبارات (المقارنة بالأسماء لا بالعدد — 19 فشلاً معروفاً في الخط الأساسي)
- `tests/test_p50_dec07_breaker.py` — صمام DEC-07 + عقد الاحتياطي.
- `tests/test_p51_forbidden_isolation.py` (01.33، 18 اختباراً، ملفات مؤقتة حقيقية + `FILE_LOCK` الحقيقي) — النقل الأعمى، السجل jsonl الكامل، غياب العتبة.
- `tests/test_p52_revival_routing.py` (05.02 `run_revival`، 10 اختبارات، بلا شبكة).
- `tests/test_p53_vault_hardening.py` (35–49) — N=1، LOGIN_FAILED، D27، D35، jsonl، R-A/R-B بالقفل الحقيقي، D34 `NETWORK_DOWN`، D37 `git check-ignore`، D38/D39، نقاء CRLF/LF.
- `tests/test_refactor_parity.py` — تطابق `bridge_refactor/**` مع 01.33 بعد تحديث حدود PARTS.
