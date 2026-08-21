# 🔄 بروتوكول استئناف الجلسات واستعادة السياق (V3_RESUME_SESSION.md)

> **الهدف:** توفير دليل سريع وواضح لأي وكيل AI أو مهندس برمجي لاستعادة الحالة المعمارية للمشروع فوراً ومتابعة العمل بدون أي فجوات سياقية.

---

## ⚡ 1. خطوات استعادة السياق في 30 ثانية (Fast Resume Checklist)

1. **قراءة سجل التقدم الرئيسي:**
   * افتح [PROGRESS.md](PROGRESS.md) لمعرفة المراحل المكتملة والمرحلة الجارية.
2. **فحص سجل الجلسات:**
   * افتح `docs/engineering/SESSION_LOG.md` لمعرفة آخر جلسة وآخر مهمة نُفذت.
3. **التحقق من سلامة الاختبارات الشاملة:**
   * شغل الأمر: `python scripts/hadith_sijil.py` وتأكد من اجتياز 297/297 اختبار بـ Exit Code 0.
4. **معرفة الملفات النشطة المعتمدة:**
   * ملف البوت النشط: `01.33_telegram_gen_bridge.py`.
   * محرك كوين المستقل: `qwen_engine.py` (يستورده `04_upload_to_Fable_github.py` + `01.33` للكوميت الذكي P24).
   * ملف المحرك المعتمد: `01.03Genspark_claude-opus-5-code.py` (بث SSE حقيقي: `stream=True` + `iter_lines()` — ممنوع `r.text`).
   * الأساس المجمّد: `01.32_telegram_gen_bridge.py` + `01.31_telegram_gen_bridge.py` + `01.30_telegram_gen_bridge.py` (baseline) + `01.29` + `01.28` + `01.27` + `01.26` + `01.02Genspark_claude-opus-5-code.py` (Golden Baselines — ملفات مرجعية فقط، ممنوع تعديلها).

---

## 🛡️ 2. القواعد المعمارية الإلزامية غير القابلة للكسر (Non-Negotiable Rules)
* **Single-File Doctrine:** ممنوع تشتيت الاعتماديات؛ التعديل يتم داخل الملفات المعتمدة فقط.
* **Test-Before-Talk:** ممنوع إبلاغ المستخدم بنجاح أي تعديل دون تشغيل `py_compile` واختبارات الوحدة الـ 297 والتأكد من خروج Exit Code 0.
* **REST-Only Upload (S39/P20):** الرفع لـ GitHub يتم حصرياً عبر Contents REST API داخل `_default_github_uploader` — ممنوع إعادة أي مسار git native (clone/push/init) أو إرجاع `_git_native_sync_uploader`/`_generate_ai_commit_message` (محروس بـ 8 اختبارات في `tests/test_p20_rest_only_data_retention.py`).
* **DATA_RETENTION Failover (S39/P20):** خطأ "requires AI Data Retention" يُكشف أولاً في `detect_response_status` ويُعامل كنفاد رصيد: تبريد 29h + حساب تالٍ + إعادة إرسال **نفس آخر رسالة** (ممنوع التحويل لبرومبت الاستئناف) + تنبيه مميز `data-retention-blocked` (محروس بـ 16 اختباراً في `tests/test_p20_rest_only_data_retention.py`).
* **True SSE Streaming (S29):** طلب `ask_proxy` يجب أن يبقى `stream=True` والقراءة عبر `iter_lines()` — الرجوع لـ `r.text` يؤخر زر المعاينة الحية حتى اكتمال التوليد (محروس باختبارات 8–10).
* **Button Styles Whitelist (S30):** حقل `style` في أزرار Inline يقبل فقط `primary`/`success`/`danger` (Bot API 9.4) — أي قيمة أخرى تُحذف مركزياً في `make_inline_keyboard` لتجنب `400 invalid button style` (محروس بـ 10 اختبارات في `tests/test_p11_button_styles.py`).
* **Same-Project Resume (S31/P12):** انقطاع بث SSE مع project_id حي يجب أن يرجع `__STREAM_INTERRUPTED__` + الـ pid، والبوت يتابع polling على **نفس المشروع** عبر `carry_pid` — ممنوع fork/شات جديد بعد الانقطاع (محروس بـ 13 اختباراً في `tests/test_p12_resume_same_project.py`).
* **Pre-Flight Balance Gate (S32/P13):** قبل أي إرسال أو fork يُفحص الرصيد؛ رصيد فعلي < `min_preflight_balance` (100) = `mark_account_cooldown(29h)` فوري + إرجاع `LOW_BALANCE` + تخطٍ **صامت** للحساب التالي في الـ failover — فشل الشبكة (-1) لا يُعاقَب (محروس بـ 14 اختباراً في `tests/test_p13_preflight_balance.py`).
* **GitHub Upsert Sync (S33/P14):** في `04_upload_to_Fable_github.py`: الملف الموجود في الريبو يُقارن بالمحتوى قبل النسخ (بايت + CRLF→LF) — المطابق لا يُلمس والمختلف يظهر `✏️ M` وليس `➕ A`؛ حذف مرآتي يتجاوز 50% من ملفات الريبو = أرشيف جزئي ➔ إلغاء الحذف بالكامل؛ كشف الجذر Repo-Anchored بعد `git clone` وليس قبله (محروس بـ 16 اختباراً في `tests/test_p14_upsert_sync.py`).
* **Qwen Engine Module (S34/P15):** منظومة ومحرك كوين (Qwen.ai Direct) تعيش حصرياً في `qwen_engine.py` — ممنوع إعادة تعريف أي دالة/ثابت منها داخل `04_upload_to_Fable_github.py` (يستورد فقط). حقن اللوجر يتم عبر `qwen_engine.configure(log_func=log_message)`، وحالة الفائز الحية تُقرأ دائماً كـ `qwen_engine.LAST_AI_*` (صفة موديول) — ممنوع from-import لها لأنه يجمّد قيمتها (محروس بـ 16 اختباراً في `tests/test_p15_qwen_engine.py`).
* **Early Make-Public (S35/P16):** فور التقاط أول project id في أي مسار (بث SSE / استئناف carry_pid / fork بالـ URL) يُستدعى `make_public` بخيط daemon منفصل مع dedup لكل pid وتجاهل sentinels — زر المعاينة الحية يجب ألا يعطي 404 أبداً (محروس بـ 9 اختبارات في `tests/test_p16_early_public.py`).
* **Operational Hardening (S36/P17):** جلسة منتهية أثناء الشات = تجديد فوري (لا حرق محاولة)؛ نفاد الرصيد يُكشف داخل حلقة polling أيضاً؛ الجروبات (chat ids سالبة) مدعومة في `is_chat_allowed`؛ `.pytest_cache/` و `bridge_bot.log` ممنوع تتبعهما في git (محروس بـ 27 اختباراً في `tests/test_p17_hardening.py`).
* **Copy Project Settings (S38/P19):** زر «📋 نسخ إعدادات من مشروع آخر» في لوحة المشروع غير المحفوظ — `generate_sequential_project_name` (اسم تسلسلي تلقائي: «الحج 1» ➔ «الحج 2») + `copy_project_settings_to_new_project` (نسخ GitHub repo/branch/token من مخزن المشروع السري فقط `allow_env_fallback=False` + الموديل + برومبت الاستئناف) — التوكن ممنوع يتسرب من env fallback (محروس بـ 24 اختباراً في `tests/test_p19_copy_settings.py`).
* **Qwen Commit Bridge (S44/P24):** رسائل كوميت الرفع REST تُسبَق بملخص ذكي من `qwen_engine.generate_ai_summary()` عبر `ProjectRegistry._qwen_commit_prefix_for_job` — استدعاء **واحد فقط لكل job** قبل حلقة PUT؛ أي فشل = prefix فارغ = **نفس الرسالة القديمة حرفياً** (ممنوع أن يكسر كوين الرفع أبداً). `accounts_qwen.json` مركزي عبر `resolve_shared_path` داخل `qwen_engine.py`، وقرار المالك `AI_RACE_ACCOUNTS = 0` (الكل يتسابق) + مهلة 30ث/مرحلة بلا تغيير (محروس بـ 17 اختباراً في `tests/test_p24_qwen_commit_bridge.py`).
* **Shared Secrets Auto-Discovery (S42/P23):** الملفات المشتركة (`telegram_bot_token.txt` + `project_registry/` + `projects_tree.json` + `accounts_genspark.json`) تُلتقط حصرياً عبر `resolve_shared_path` — محلي أولاً ثم الفولدر الأب `W___webapp/` ثم المحلي للإنشاء؛ ممنوع الرجوع لمسار `SCRIPT_DIR /` مباشر لهذه الملفات أو hardcode أي توكن، واليافطة المركزية تعيش في `AGENTS.md`/`GEMINI.md` (محروس بـ 17 اختباراً في `tests/test_p23_shared_paths.py`).
* **Interactive Cancellation Flow (S45/P25):** إلغاء البناء الجاري يتم حصرياً عبر مسجل أحداث الإلغاء (`register_cancel_event`/`trigger_cancel`/`unregister_cancel_event` — توكن 12-hex لأن callback_data ≤ 64 بايت) + حقن `cfg.cancel_event` (threading.Event): المحرك `01.03` يفحصه كأول سطر داخل `r.iter_lines()` ➔ `break` ➔ `r.close()` ➔ `__USER_CANCELLED__` **بأولوية قبل** تصنيف الرصيد. ممنوع: إلغاء بضغطة واحدة (خطوتا أمان إلزاميتان `cancel_prompt:` ➔ `cancel_exec:`)، معاقبة/تبريد الحساب عند حالة `CANCELLED` (الإلغاء قرار مستخدم وليس فشل حساب)، أو ترك التوكن مسجلاً بلا `unregister_cancel_event` في `finally` (Zero Leaks). نوم حلقات المتابعة يجب أن يبقى `Event.wait(timeout=5)` وليس sleep (محروس بـ 42 اختباراً في `tests/test_p25_interactive_cancel.py` — ومنها حارسا S46: رسالة الإلغاء النهائية ترفق لوحة التحكم الكاملة `build_dashboard_keyboard` وممنوع الزر اليتيم).
* **Activity-Stop (S37/P18 — حي في 01.30) — قاعدة المالك النصية:** أثناء حلقة polling يُراقب مؤشر Deep Thinking / Tasks Remaining كل دورة؛ **أي تغيّر** (زيادة أو نقصان المهام، تقلّب Deep Thinking، اختفاء المؤشر بعد نشاط) = **وقف فوري `break` بلا أي تكملة** — «لو غيرت مهام وقف مش تكمل». فشل جلب المؤشر (None) يُتجاهل ولا يوقف (محروس بـ 20 اختباراً في `tests/test_p18_activity_stop.py`).
* **بروتوكول «حدث سجل»:** عند استلام كلمة السر «حدث سجل»، يتم فحص التعديلات ➔ تشغيل الاختبارات ➔ تحديث `docs/engineering/PROGRESS.md` و `docs/` ودفاتر الذاكرة.

