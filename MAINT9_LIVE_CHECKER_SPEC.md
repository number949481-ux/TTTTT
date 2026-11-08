# MAINT-9 — وثيقة المواصفات الهندسية وخطة التنفيذ الجراحية
## منظومة فحص وتنشيط الحسابات لايف عبر بوت التيليجرام 31 (Live Account Verification & Refresh Engine)

**MODE:** `PLAN_SPECIFICATION_ONLY` — هذه الوثيقة تخطيط فقط. **لا يُلمس أي سطر كود قبل كلمة «GO» الحرفية من المالك.**
**BASE:** `genspark_ai_developer @ 5cb67c5` (porcelain 0) · 01.33 sha `fe039f0f…` · 05.02 `63a5bfee…` · main_upgrade `d4c0ed01…` · rebuild_refactor `dd28c701…`
**المصدر:** Gist الرئيسي `6ad6deb3…` (2590 سطراً) — كارت التكليف L2484–2524 + فويسات 158–184 · RESUME §3.22 (المراجعة 360° + المراجعة الثانية)
**الترقيم المعتمد (S3):** D62–D70 (D61 محجوز لـ MAINT-8)

---

## 0) الخلاصة التنفيذية (7 أسطر)

1. **خمسة ملفات** تُمس عند GO: `01.33` (p09 + p12)، `scripts/rebuild_refactor.py` (جدول PARTS فقط)، `05.02` (خُطّافان اختياريان في `run_quarantine`)، `bridge_refactor/main_upgrade.py` (فحص علامة «مشغول»)، ملف جديد `bridge_refactor/live_account_checker.py` + اختبار جديد `tests/test_p58_live_checker.py` + تحديث بصمتين في p56/p57 + `.gitignore`.
2. **الماكينة = 05.02 نفسها** (`run_quarantine` + `RotationCheckpoint` + `_activate_for_bot31`). المشغّل لا يكتب في أي ملف حسابات مباشرة — كل كتابة تمر عبر 05.02 تحت القفل المشترك (S6).
3. **النسخ لا القصّ (S2/فويس 181):** «النسخة» = **طابور فحص** (`live_check_queue.json`: بصمات sha256 للبريد + الترتيب — بلا أسرار). بيانات الحسابات تُقرأ وتُكتب **في الأساسي في مكانها** عبر 05.02. الأساسي لا يُمسح ولا يُفرغ ولا يُنقل. (§3.2 يشرح لماذا هذا هو «النسخ» الآمن الوحيد المتوافق مع DRY.)
4. **الإيقاف بملف** `live_check.stop` (S4) · **علامة مشغول** `live_check.busy` بنمط R-B (S5) · **حالة الرسالة اللايف** `live_check_state.json` — الثلاثة بجوار `accounts_genspark.json` في الأب.
5. **بوابات الأخضر/الأحمر (D70)** في 4 محطات — آلة حالات §5 بـ 9 callbacks بنمط المشروع `lc_*`.
6. **جدول PARTS** يُعاد حسابه بمعادلة واحدة (§4.3): كل ما بعد p09 يزحف بـ A، وp12 ينتهي عند `10076 + A + B`؛ المولّد يتحقق تلقائياً من التغطية (rebuild_refactor L235–240).
7. **التراجع:** commit واحد قابل للعكس بـ `git revert`؛ بصمات p56/p57 تعود تلقائياً؛ لا migration ولا تغيير في شكل أي ملف حسابات.

---

## 1) القرارات الملزِمة (كما وردت في كارت التكليف) وتفسيرها التنفيذي

| القرار | النص الملزم | الترجمة التنفيذية | الدليل في الكود الحالي |
|---|---|---|---|
| **S1 / D62** | الزر في 01.33 + تحديث PARTS + إعادة التوليد + تحديث sha p56/p57 | صف أخير في `build_dashboard_keyboard` بـ `style:"primary"`؛ معالجات في p12 | L6881–6894، L6339، PARTS L35–47، p56 L421، p57 L142 |
| **S2 / D63** | نَسخ لا قَصّ؛ الأساسي عذراء؛ الفحص على «نسخة طابور»؛ المشحون ≥100 يُحدَّث في الأساسي فوراً؛ التصفير = تصفير الـ Checkpoint فقط | طابور = بصمات؛ البيانات في مكانها؛ «من الصفر» = `RotationCheckpoint._fresh` | `RotationCheckpoint` L300–362، `_activate_for_bot31` L826–853 |
| **D64** | Subprocess مستقل | `subprocess.Popen([sys.executable, live_account_checker.py, …])` من p12 | `import subprocess` موجود L38؛ نموذج Popen في main_upgrade L372/L387 |
| **D65** | رسالة لايف واحدة ≤4000 حرف تُحدَّث بـ editMessageText مع «X من Y (%) \| المتبقي» | المشغّل يرسل بـ `urllib.request` (stdlib) — **لا يستورد 01.33** | آثار استيراد 01.33 الجانبية: L76 FileHandler، L196 token، L4301 EXECUTOR |
| **D66 / D71** | رسالة جديدة بصوت لكل حساب ≥100 + لقطة التقرير + الإيميل كاملاً | `sendMessage` بلا `disable_notification`؛ الإيميل عبر `html.escape` | — |
| **D67** | حفظ لحظي تحت `accounts_cooldown.json.lock` | **منفَّذ أصلاً** في 05.02 `save_checkpoint` L583→L635 + `rotation.mark` L691–694 | لا كود جديد |
| **S4 / D68** | إيقاف بملف `live_check.stop` يُستطلع بين الحسابات | خُطّاف `stop_flag` في `run_quarantine` (§3.4) | `IS_RUNNING` L644/L722 |
| **S5 / D69** | علامة مشغول يفحصها Supervisor قبل `--sweep` | `live_check.busy` + فحص في `Supervisor.start_job` | `start_job` L377–391، `tick` L421–430 |
| **S6** | القفل المشترك لكل العمليات | المشغّل لا يكتب ملفات حسابات؛ 05.02 يكتب تحت القفل | `_with_vault_lock` 05.02 L757 |
| **S7** | `on_account=None, stop_flag=None` في `run_quarantine`؛ CLI بلا تغيير | 4 نقاط لمس فقط (§3.4) | L510–511 التوقيع |
| **D70** | بوابات أخضر/أحمر في 4 محطات | آلة الحالات §5 | `ALLOWED_BUTTON_STYLES` L6339 = primary/success/danger ✓ |
| **تايم آوت (كارت D68 القديم)** | يبقى في مكانه + سطر في `account_log.jsonl` + عداد | AUTH_FAILED يبقى أصلاً L686–689؛ **السطر في اللوج جديد** (داخل الخُطّاف — لا تعديل في 05.02) | `ACCOUNT_LOG_FILENAME` 01.33 L1318 / 05.02 `_log_move` L792 |

---

## 2) ما **لن** تفعله هذه الخطة (صريحاً)

- لا تغيير في الجدول الدوري (06/18 `--sweep` ≤20، 12/00 `--revive`) — 7.11/D48 سليم.
- لا فحص لـ `accounts_failed.json` أو `accounts_delayed_gifts_credits.json` — أبداً.
- لا تعديل في `update_account_data` (B14 مؤجل بقرار S6 — خطر مقبول موثق §8).
- لا نسخ لبيانات الحسابات (باسورد/كوكيز) إلى أي ملف جديد.
- لا `asyncio`، لا خيوط إضافية في 01.33، لا استيراد 01.33 داخل المشغّل.
- لا لمس لـ `01.03…`، `genspark_verifier_engine.py`، `bridge_refactor/parts/**` يدوياً (تُولَّد فقط)، `git/github_bulk_sync.py`.
- لا push/gh/ZIP — حفظ محلي ومزامنة المالك.

---

## 3) المعمارية التفصيلية

### 3.1 الملفات والمسارات (كلها بجوار `accounts_genspark.json` في الأب — عبر `resolve_file_path` من 05.02 L259–296)

| الملف | من يكتبه | من يقرأه | المحتوى | .gitignore |
|---|---|---|---|---|
| `genspark_rotation_checkpoint.json` | 05.02 (`rotation.mark`) | المشغّل + البوت (للاستئناف) | قائم — بصمات sha256 | قائم L18 |
| `live_check_queue.json` | المشغّل عند البدء | المشغّل/البوت (Y الكلي) | `{cycle_id, created_at, total, order:[sha256…]}` — بلا أسرار | **جديد** |
| `live_check_state.json` | المشغّل (بعد كل حساب) | البوت | `{pid, chat_id, message_id, mode, started_at, heartbeat, counters{checked,total,active,cooldown,stale,dead,net_err,hunted}, last_email_hash}` | **جديد** |
| `live_check.busy` | المشغّل (`O_CREAT\|O_EXCL`) | Supervisor + البوت | pid + ISO time؛ mtime يُحدَّث كل حساب (heartbeat) | **جديد** (`*.busy`) |
| `live_check.stop` | البوت (زر الإيقاف المؤكَّد) | المشغّل بين الحسابات | فارغ | **جديد** |
| `logs/live_check.log` | المشغّل | المالك | stdout/stderr (تحت تقليم MAINT-8 ✓) | قائم (`logs/`) |

**يتيم:** `live_check.busy` بعمر mtime > 15 دقيقة = يتيم ⇒ يُتجاوز بتحذير (نمط `COOLDOWN_VAULT_LOCK_ORPHAN_S` L1316 لكن بمهلة أطول لأن الحساب الواحد قد يستغرق 5.5 دقيقة حداً أقصى: 45s×2 login + 25s×5 + 300s فاصل).

### 3.2 لماذا «النسخة» = طابور بصمات لا نسخة بيانات (قرار يحتاج تأكيد المالك — Q-GO-1)

فويس 181: «نسخ فقط… مش فارق». كارت التكليف: «نسخة طابور… المشحون يُحدَّث ويُعاد فوراً للأساسي». الطريقتان:

| | (أ) نسخة بيانات كاملة `accounts_live_copy.json` | (ب) **طابور بصمات + فحص في مكانه** (الموصى به) |
|---|---|---|
| DRY | ✗ 05.02 يكتب نتائجه في `primary_path` الممرَّر؛ لو مرّرنا النسخة تذهب النتائج للنسخة ⇒ طبقة دمج جديدة (`_merge_by_email` L855 لكل حساب) | ✓ 05.02 يعمل على الأساسي كما في `--sweep` اليوم |
| الأسرار | ✗ ملف ثانٍ يحوي باسورد/كوكيز (مغطّى بـ `accounts*.json` في .gitignore لكن 7.14: محرك المزامنة يتجاوزه) | ✓ لا أسرار جديدة |
| التزامن | ✗ كتابتان لكل حساب (نسخة + أساسي) + سباق مع 01.33 | ✓ كتابة واحدة تحت القفل كما اليوم |
| «الأساسي عذراء» | الأساسي يُحدَّث أيضاً (المشحون يُعاد إليه) — فلا فرق جوهري | الأساسي يُحدَّث في مكانه فقط لحقول الحالة (MERGE_FIELDS L580–581) |
| «من الصفر» | إعادة النسخ | `RotationCheckpoint._fresh` + طابور جديد |

**التوصية:** (ب). الطابور هو «الكوبي» الذي طلبه المالك (تحديد الكل → لصق في طابور الفحص)، والبوت لا يتوقف ثانية. إن أصرّ المالك على (أ) تُضاف مرحلة دمج (+~60 سطراً، +4 اختبارات) وتُوثَّق كاستثناء.

### 3.3 المشغّل `bridge_refactor/live_account_checker.py` (ملف مالك جديد — ~260 سطراً)

**argv:** `--chat-id <int> --message-id <int> --mode fresh|resume [--delay-min 60] [--delay-max 300] [--token-file <path>]`
**الاستيراد:** `importlib.util.spec_from_file_location("gifts_manager", <ROOT>/05.02_genspark_delayed_gifts_manager.py)` (الاسم يبدأ برقم) — الاستيراد يشغّل `signal.signal(SIGINT)` L88 (آثار مقبولة) ويحتاج `genspark_master_account_manager` من الأب (L63–69) — **NOT-VERIFIED في الـ sandbox؛ موجود على جهاز المالك (فويس 178/كارت 2-6)**؛ الاختبارات تحقنه stub كما p56 L41–44.
**التوكن:** `TELEGRAM_BOT_TOKEN` من البيئة ثم `telegram_bot_token.txt` محلي ثم الأب (نفس ترتيب 01.33 L179–196) — لا يُطبع أبداً.
**الحلقة:**
1. احجز `live_check.busy` (`O_EXCL`)؛ فشل ⇒ لو mtime حديث: رسالة «فحص آخر يعمل» ثم exit 2؛ لو يتيم: استبدال بتحذير.
2. احذف `live_check.stop` القديم إن وُجد.
3. `mode=fresh` ⇒ اكتب checkpoint جديد (`_fresh(cycle+1)`)؛ `resume` ⇒ اترك.
4. ابنِ الطابور: `remaining = rotation.begin_cycle(primary_emails)` ⇒ اكتب `live_check_queue.json` (Y = len(primary)، المتبقي = len(remaining)).
5. `manager = MasterDelayedGiftsManager(primary, quarantine=delayed, failed, dead, threshold, sort, auto_relogin=True, min_delay=60, max_delay=300)`.
6. `manager.run_quarantine(scan_mode="first_n", limit=len(remaining), dry_run=False, rotation=rotation, on_account=_on_account, stop_flag=STOP_FILE)`.
7. `_on_account(email, status, bal, diag)`: حدّث العدادات + `live_check_state.json` + heartbeat الـ busy + `editMessageText` (≤1/حساب) + لو `status=="HEALTHY" and bal>=100` ⇒ `sendMessage` صيد (إيميل كامل + الرصيد + لقطة العدادات) + لو `AUTH_FAILED` ⇒ سطر JSON في `account_log.jsonl` `{ts, event:"live_check_net_error", email, reason}` (D28: سطر كامل).
8. عند الانتهاء/الإيقاف: رسالة ختامية (edit)، حذف `busy` و`stop`، exit 0 (مكتمل) / 3 (أُوقف) / 1 (خطأ).
**تيليجرام (urllib):** 429 ⇒ نوم `retry_after+1` ومحاولة واحدة (كما 01.33 L1620–1639)؛ «message is not modified» ⇒ نجاح؛ «message to edit not found» ⇒ `sendMessage` جديدة وتحديث `message_id` في state.
**قاطع شبكة (جديد — تحصين):** 5 AUTH_FAILED متتالية ⇒ توقف مؤقت 10 دقائق + تنبيه؛ 3 دورات توقف متتالية ⇒ إيقاف ذاتي exit 4 (05.02 بلا قاطع؛ 01.33 لديه D34 L1322).

### 3.4 خُطّافا 05.02 (S7) — 4 نقاط لمس بالضبط، CLI بلا تغيير

| # | الموضع الحالي | التعديل |
|---|---|---|
| 1 | L510–511 التوقيع | `+ on_account: Optional[Callable[[str, str, Optional[int], str], None]] = None, stop_flag: Optional[Path] = None` (+`Callable` في typing L39) |
| 2 | L644 `if not IS_RUNNING:` | `if not IS_RUNNING or (stop_flag is not None and stop_flag.exists()):` |
| 3 | بعد L694 (`rotation.mark(email)`) | `if on_account is not None: try: on_account(email, status, bal, diag_msg or "") except Exception: print(تحذير)` — **بعد** الحفظ الذري حتى لا يسبق الإشعارُ الحقيقة |
| 4 | L722–724 الفاصل | `time.sleep(delay_sec)` ⇒ نوم مجزّأ بثانية واحدة يفحص `stop_flag` (الإيقاف لا ينتظر 5 دقائق) |

**لا يتغير:** `main()`، الحارس `--allow-primary-scan`، سقف `-l ≤20` مع `--sweep` (حارس CLI في main L1006–1011 — المشغّل يستدعي `run_quarantine` مباشرة ⇒ **Q-GO-2** أدناه).

### 3.5 Supervisor (`main_upgrade.py`) — S5

- ثابت `LIVE_BUSY_FILE = ACCOUNTS_FILE.parent / "live_check.busy"` و`LIVE_BUSY_ORPHAN_S = 900`.
- في `start_job(kind)` قبل Popen (L377–391): لو `LIVE_BUSY_FILE` موجود وmtime حديث ⇒ `log.warning("تخطي %s: فحص لايف يعمل (pid …)")` و`return False`؛ يتيم ⇒ تحذير + متابعة.
- يسري على `sweep` **و** `revive` (كلاهما يشارك القفل والشبكة) — **Q-GO-3**.
- **لا** يقتل المشغّل عند الإغلاق (D53): المشغّل ليس ابنه؛ يُترك يكمل (يُوثَّق). stdlib فقط (p57 whitelist L40 ✓ — `pathlib/os/time` كافية).

### 3.6 البوت 01.33 — p09 (لوحات) وp12 (معالجات)

**p09 — بعد `build_dashboard_keyboard` L6894 (A ≈ 55 سطراً):**
- تعديل L6887 قبل `]`؟ **لا** — الصف يُضاف **بعد** حلقة المشاريع (L6893) قبل `return` L6894: `rows.append([{"text": "🔍 فحص وتنشيط الحسابات لايف ⚡", "callback_data": "cmd:live_check", "style": "primary"}])` (صف بزر واحد = عرض كامل).
- `build_live_check_confirm_keyboard(kind)` ⇒ `kind ∈ {fresh, resume, reset}`: `[🟢 … success | 🔴 إلغاء danger]` بأسماء `lc_go:<kind>` / `lc_cancel`.
- `build_live_check_choice_keyboard()` ⇒ `[🔄 استئناف lc_pick:resume] [🆕 من الصفر lc_pick:reset] / [🔴 رجوع lc_cancel]`.
- `build_live_check_running_keyboard()` ⇒ `[🛑 إيقاف الفحص lc_stop danger]`؛ `build_live_check_stop_confirm_keyboard()` ⇒ `[🔴 نعم أوقف lc_stop_yes danger] [🟢 لا، استمر lc_stop_no success]`.
- `render_live_check_prompt_text(kind, snapshot)` نصوص المحطات (≤4000).

**p12 — قبل `handle_telegram_update` L8672 (B ≈ 140 سطراً):**
- `live_check_paths()` (بجوار `get_accounts_file_path` L1036 ⇒ الأب)، `read_live_check_state()`, `is_live_check_running()` (busy موجود وحديث)، `live_check_remaining()` (أساسي − checkpoint بـ `hashlib.sha256(email.strip().lower())` — نفس `RotationCheckpoint.key` L319–321؛ `hashlib` مستورد L27)، `launch_live_checker(chat_id, mode)` (يرسل رسالة اللايف الأولى أولاً ليحصل على `message_id` ثم Popen بـ `cwd=SCRIPT_DIR`، stdout إلى `logs/live_check.log`، على win32 `creationflags=CREATE_NO_WINDOW`).
- كتلة معزولة مبكرة (نمط P25 L8689) `if data == "cmd:live_check" or data.startswith("lc_"):` … `return` — **قبل** السلسلة الرئيسية L8857 لتجنب أي تداخل.

**ملاحظة سباق (D-UX):** شاشة تأكيد الإيقاف تُرسل كرسالة **جديدة** صغيرة لا بتعديل رسالة اللايف (المشغّل يعيد كتابة اللايف كل حساب فيمسح أزرار التأكيد). بعد القرار تُحذف/تُعدَّل رسالة التأكيد.

---

## 4) جدول PARTS المحدَّث — المعادلة

### 4.1 الحالي (rebuild_refactor L35–47، مجموع 10076)
p01 1–197 · p02 198–531 · p03 532–1596 · p04 1597–2152 · p05 2153–2705 · p06 2706–4297 · p07 4298–5480 · p08 5481–6045 · **p09 6046–7672** · p10 7673–7987 · p11 7988–8522 · **p12 8523–10076**

### 4.2 المتغيّران
- **A** = عدد الأسطر المضافة داخل p09 (كلها بعد L6894 وقبل L7672) — تقدير 55.
- **B** = عدد الأسطر المضافة داخل p12 (كلها بين L8523 وL10076) — تقدير 140.
- لا سطر يُضاف في p01–p08 (لا ثوابت جديدة في p02/p03؛ المسارات تُحسب داخل p12).

### 4.3 الجدول الجديد (صيغة عامة)
| الجزء | البداية | النهاية |
|---|---|---|
| p01…p08 | كما هي | كما هي |
| p09 | 6046 | 7672 **+ A** |
| p10 | 7673 **+ A** | 7987 **+ A** |
| p11 | 7988 **+ A** | 8522 **+ A** |
| p12 | 8523 **+ A** | 10076 **+ A + B** |

**التحقق الآلي:** `main()` في المولّد يؤكد التغطية بلا فجوة/تداخل (L235–240) ويفشل بصوت عالٍ عند أي خطأ؛ وحدود البداية يجب أن تبقى على `def`/تعليق top-level (L34) — نقاط الإدراج المختارة لا تمس أسطر الحدود (L7673 `_is_fresh_artifact`، L7988 `format_active_account_line`، L8523 تعليق) لأن كل الإضافة **داخل** p09/p12 لا عند أطرافها.
**بعد التوليد:** `bridge_refactor/parts/p09…p12` + `telegram/ui.py`/`handlers.py` (قوائم `__all__`) تتغير — تُلتزم مع نفس الـ commit (اختبار `test_m4_generated_tree_matches_committed_tree`). CRLF نقي إلزامي (parity L241–242؛ `GENERATED_NEWLINE="\r\n"`).

### 4.4 البصمات
- `tests/test_p56_rotation_sweep.py` L421 و`tests/test_p57_main_upgrade_supervisor.py` L142: تحديث البادئة إلى sha الجديد لـ 01.33 (يُحسب بعد التعديل مباشرة بـ `sha256sum`).
- `bridge_refactor/main.py` sha يتغير (قالب ثابت لكنه يُعاد كتابته) — لا اختبار يثبّته بالقيمة.

---

## 5) آلة الحالات — شاشات الأخضر/الأحمر (D70)

```
[Dashboard] --cmd:live_check--> (running?) 
   ├─ yes ──> S_RUNNING_INFO: «فحص يعمل منذ … (X من Y)» [🛑 إيقاف lc_stop] [⬅️ رجوع lc_cancel]
   └─ no ──> (remaining>0 && checked>0 ?)
        ├─ yes ──> S_CHOICE: [🔄 استئناف lc_pick:resume] [🆕 من الصفر lc_pick:reset] / [🔴 رجوع lc_cancel]
        │       lc_pick:resume ──> S_CONFIRM(resume): «استئناف من الحساب k (المتبقي m)؟» [🟢 lc_go:resume] [🔴 lc_cancel]
        │       lc_pick:reset  ──> S_CONFIRM(reset):  «تصفير العداد وفحص Y بالكامل؟»   [🟢 lc_go:reset]  [🔴 lc_cancel]
        └─ no  ──> S_CONFIRM(fresh): «بدء فحص Y حساباً في الخلفية؟» [🟢 lc_go:fresh] [🔴 lc_cancel]

lc_go:<kind> ──> launch_live_checker(mode = resume|fresh) ──> S_LIVE (رسالة اللايف + [🛑 lc_stop])
S_LIVE --lc_stop--> S_STOP_CONFIRM (رسالة جديدة): [🔴 نعم أوقف lc_stop_yes] [🟢 لا، استمر lc_stop_no]
   lc_stop_yes ──> كتابة live_check.stop ──> «سيتوقف بعد الحساب الجاري (≤ 5.5 دقيقة)»
   lc_stop_no  ──> حذف رسالة التأكيد
lc_cancel ──> رسالة «تم الإلغاء» + get_main_keyboard
```
**الثوابت:** 9 callbacks (`cmd:live_check`, `lc_pick:resume`, `lc_pick:reset`, `lc_go:fresh|resume|reset`, `lc_stop`, `lc_stop_yes`, `lc_stop_no`, `lc_cancel`) — كلها < 64 بايت. **الحالة لا تُحفظ في `user_state`** (البوت عديم الحالة هنا؛ الحقيقة في الملفات) ⇒ ضغطة قديمة على زر منتهٍ تُجاب بـ «انتهت» كما P25 L8693–8698.
**الحارس ضد الضغط المزدوج على `lc_go`:** قبل Popen يُعاد فحص `busy`؛ لو ظهر ⇒ «فحص يعمل بالفعل».

---

## 6) خطة التنفيذ الجراحية (بعد GO — بالترتيب، لا تخطّي)

| # | الخطوة | المُدخل | المُخرج | معيار القبول | الحجم |
|---|---|---|---|---|---|
| 0 | Layer A + sha الأربعة + `/tmp` نسخة W-0 | HEAD | تقرير HEAD/dirty | dirty=0، sha مطابقة | — |
| 1 | `.gitignore`: `live_check*.json`, `*.busy`, `live_check.stop` | — | diff سطرين | `git check-ignore -v` يطابق | 3 أسطر |
| 2 | 05.02: الخُطّافان (4 نقاط §3.4) | L510/644/694/722 | diff ≤ 25 سطراً | `py_compile`؛ LF نقي؛ p54–p56 خضراء بلا تغيير | 25 |
| 3 | `main_upgrade.py`: `LIVE_BUSY_FILE` + فحص في `start_job` | L377–391 | diff ≤ 25 | p57 33/33 + 2 اختبار جديد (busy حديث ⇒ تخطّ؛ يتيم ⇒ متابعة) | 25 |
| 4 | `bridge_refactor/live_account_checker.py` (جديد) | §3.3 | ملف ~260 LF | `py_compile`؛ stdlib + importlib فقط؛ لا استيراد 01.33 | 260 |
| 5 | 01.33 p09: الصف + 4 لوحات + نصوص | بعد L6894 | A سطر CRLF | p25/p27/p32 خضراء؛ الصف الأخير `cmd:live_check` | ~55 |
| 6 | 01.33 p12: helpers + كتلة `lc_*` المعزولة | قبل L8672 | B سطر CRLF | `py_compile`؛ `grep -c $'\r$'` = `wc -l` | ~140 |
| 7 | `rebuild_refactor.py`: جدول PARTS بالمعادلة §4.3 | A, B الفعليان | 4 صفوف | تشغيل المولّد ينجح (L241 «✅») | 4 أسطر |
| 8 | تشغيل المولّد + التزام parts/facades المولَّدة | — | شجرة جديدة | `test_refactor_parity` كاملاً أخضر | — |
| 9 | تحديث sha في p56 L421 / p57 L142 | sha الجديد | سطران | p56/p57 خضراء | 2 |
| 10 | `tests/test_p58_live_checker.py` (جديد) | §7 | ~18 اختباراً | كلها خضراء؛ لا شبكة؛ stub للماستر مانجر | ~350 |
| 11 | الحزمة الكاملة بالأسماء | — | 19 فشل معروف + 0 جديد | قائمة `^FAILED` مطابقة للخط الأساسي | — |
| 12 | الوثائق: README_COOLDOWN_VAULT (قسم المشغّل)، RESUME §3.23 + §4 D62–D70، PROGRESS `[x]`، recovery، كارت §14 | — | verify_docs Exit 0 | الميثاق بايتياً متطابق | — |

**الاعتماديات:** 2 قبل 4 (المشغّل يستدعي التوقيع الجديد)؛ 5–6 قبل 7–8؛ 8 قبل 9؛ كل شيء قبل 11.

---

## 7) خطة الاختبار `tests/test_p58_live_checker.py` (بلا شبكة، بلا ملفات حقيقية، `tmp_path`)

1. الداشبورد: الصف الأخير يحوي `cmd:live_check` بـ `style=primary` وحده في صفه؛ العدّ `proj:` ما زال 3 (توافق p27).
2. `is_live_check_running`: busy حديث ⇒ True؛ busy بعمر 16 دقيقة ⇒ False.
3. `live_check_remaining`: checkpoint ببصمتين من 5 ⇒ 3 متبقية؛ بصمة يتيمة تُهمل.
4. آلة الحالات: 9 callbacks × الحالات (running/choice/fresh) عبر monkeypatch لـ `send_telegram_message`/`edit_*`/`subprocess.Popen` — التحقق من النص واللوحة ومن أن Popen لا يُستدعى إلا بعد `lc_go` ومن argv (`--mode`, `--chat-id`, `--message-id`).
5. `lc_stop_yes` يكتب `live_check.stop`؛ `lc_stop_no` لا يكتبه.
6. 05.02: `run_quarantine(stop_flag=موجود)` يتوقف قبل الحساب الأول؛ `on_account` يُستدعى بعد `rotation.mark` (ترتيب) ومرة لكل حساب؛ استثناء داخل `on_account` لا يوقف الحلقة؛ بلا الخُطّافين السلوك بايتياً كما p56.
7. المشغّل: حجز busy ناجح/فاشل/يتيم؛ `fresh` يصفّر الـ checkpoint؛ `resume` لا؛ `_on_account` HEALTHY/150 ⇒ `sendMessage` واحدة + edit واحدة؛ AUTH_FAILED ⇒ سطر في `account_log.jsonl`؛ 429 ⇒ نوم ومحاولة؛ not-found ⇒ رسالة جديدة وتحديث state؛ القاطع 5 متتالية.
8. Supervisor: `start_job("sweep")` مع busy حديث ⇒ False + تحذير؛ يتيم ⇒ True.
9. المولّد: جدول PARTS يغطي الملف بلا فجوات (يُغطَّى بـ parity).
**الخط الأساسي:** 19 فشلاً بالأسماء (auto_compact×5، credit_completion_recovery×3، p17×2، p20، p26، p2×2، p32، p33، p3، p46، p47) — أي اسم جديد = توقف.

---

## 8) المخاطر والعواقب (مع الدرجة) وخطة التراجع

| # | الخطر | الدرجة | التخفيف |
|---|---|---|---|
| R1 | خطأ في A/B ⇒ المولّد يفشل أو جزء غير سليم نحوياً | S1 | المولّد يفشل بصوت (L237/L262)؛ الخطوة 8 لا تُتجاوز |
| R2 | sha 01.33 يتغير ⇒ p56/p57 حمراء حتى الخطوة 9 | S2 متوقع | تحديث في نفس الـ commit |
| R3 | `genspark_master_account_manager` غائب على جهاز جديد ⇒ المشغّل exit 1 فوراً | S2 | رسالة تيليجرام صريحة «الماستر مانجر غير موجود» + exit 1؛ الاختبارات stub |
| R4 | B14: `update_account_data` (01.33 L1073) خارج القفل المشترك ⇒ Lost Update نادر أثناء `_commit` 05.02 (L593→629) — التعرض يرتفع من 2×/يوم إلى ساعات | S1 **مقبول بقرار المالك S6** | يُوثَّق؛ النافذة ميلي-ثوانٍ لكل حساب؛ يبقى B14 مفتوحاً في BACKLOG |
| R5 | المشغّل يستدعي `run_quarantine` مباشرة ⇒ سقف ≤20 (Q-24) لا يسري ⇒ 85 حساباً في جلسة واحدة | قرار | **Q-GO-2**: الفحص اليدوي استثناء ثالث من 7.11 بفاصل 60–300s إلزامي |
| R6 | ريستارت البوت أثناء الفحص | S3 | المشغّل عملية مستقلة تكمل؛ البوت الجديد يرى busy/state ويعرض «يعمل» |
| R7 | ريستارت الجهاز أثناء الفحص | S3 | busy يتيم بعد 15 دقيقة؛ checkpoint محفوظ بعد كل حساب؛ خسارة حساب واحد بحد أقصى |
| R8 | حذف المالك لرسالة اللايف | S3 | not-found ⇒ رسالة جديدة |
| R9 | كل الكوكيز منتهية | S2 | القاطع §3.3 (5 متتالية ⇒ توقف 10 دقائق؛ 3 مرات ⇒ إيقاف ذاتي) |
| R10 | `resolve_shared_path` في main_upgrade يرجع الأب افتراضياً (L64) بينما 01.33 المحلي (L173) | SUSPECTED | المشغّل يستخدم `resolve_file_path` من 05.02 حصراً؛ البوت يستخدم `get_accounts_file_path` — كلاهما يصل للأب عندما يوجد الملف هناك |
| R11 | ويندوز: `CREATE_NO_WINDOW` فقط؛ لا إشارات | — | الإيقاف بالملف فقط؛ `_long_path` عند الحاجة |

**التراجع (Rollback):** كل خطوات 1–10 في **commit واحد** على `genspark_ai_developer` (مزامنة المالك). التراجع = `git revert <sha>` ⇒ 01.33 يعود إلى `fe039f0f…` فتعود بصمات p56/p57 صحيحة تلقائياً، وparts المولَّدة تعود، ولا أثر على أي ملف حسابات (المشغّل لا يغيّر شكل البيانات). تراجع تشغيلي فوري بلا git: حذف `live_check.busy` + إنشاء `live_check.stop` ⇒ المشغّل يتوقف خلال ≤5.5 دقيقة، والزر يبقى بلا أثر جانبي.

---

## 9) أسئلة بوابة GO (يُجاب عليها بالرقم قبل أي كود)

- **Q-GO-1:** «النسخة» = طابور بصمات + فحص في مكانه **(ب — الموصى به)** أم نسخة بيانات كاملة + دمج (أ)؟
- **Q-GO-2:** اعتماد الفحص اليدوي كاستثناء ثالث من 7.11/D48 (كل الأساسي في جلسة واحدة، فاصل 60–300s) — نعم/لا؟
- **Q-GO-3:** علامة «مشغول» تُؤجّل `--revive` 12/00 أيضاً لا `--sweep` فقط — نعم/لا؟
- **Q-GO-4:** القاطع (5 AUTH_FAILED متتالية ⇒ توقف 10 دقائق؛ 3 مرات ⇒ إيقاف ذاتي) — نعم أو أرقام أخرى؟
- **Q-GO-5:** شاشة تأكيد الإيقاف كرسالة جديدة (لا بتعديل رسالة اللايف) — نعم/لا؟
- **Q-GO-6:** نطاق A5 لـ 05.02 يُوسَّع صراحة ليشمل `run_quarantine` (4 نقاط §3.4) — نعم/لا؟

**بعد «GO» + الإجابات:** تُنفَّذ الخطوات 0–12 بالترتيب، بكارت مراجعة FULL بعد كل محطة، وبلا push.
