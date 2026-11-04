# MAINT-10_MASTER_PLAN.md — المرجع التنفيذي الوحيد لـ MAINT-10 (دورة حياة الحساب والبوابة الصفرية)

> **MODE:** `ALIGNMENT_AND_SPEC_ONLY` — هذه الوثيقة **خطة** لا تنفيذ. صفر كود مُعدَّل، صفر اختبار مُشغَّل، صفر مهمة تنفيذية بدأت.
> **BASE المحلي:** `genspark_ai_developer @ 2dd78ae` (dirty 0). الكارت يسمّي BASE `6c35602` — أرقام السطور طُوبقت مع HEAD المحلي بـ`grep -n` (مبدأ 7.28b) وكلها متطابقة.
> **المصادر المُراجَعة (أُعيد جلبها في هذه الجلسة — 7.28a):**
> | Gist | الأسطر | sha256[:16] | التغيّر منذ آخر جلسة |
> |---|---|---|---|
> | `093e9661…` «خريطة دورة حياة الحساب» (محادثات/اتفاقات) | 5394 | `f1895f25187931a4` | بلا تغيير |
> | `db5d6f65…` «كارت» (كروت ومراجعات الوكلاء) | 216 | `d4389d2e6c3bcf90` | بلا تغيير |
> | `97327cc1…` الرئيسي | 2877 | `1028f77c9b74dc06` | بلا تغيير (آخر جلسة) |
>
> **اسم الملف:** أمر المالك الأخير يطلب `MASTER_PLAN.md` (مثال: `MAINT-10_PLAN.md`). الـGists تطلب ثلاثة أسماء أخرى (`MAINT10_LIFECYCLE_SPEC.md` @093e L2268/L4246، `MAINT10_SPECIFICATION.md` @db5d L130، `MAINT10_GATE0_SPEC.md` @093e L4398/L4428). اعتُمد اسم أمر المالك الأحدث؛ الأسماء الثلاثة تُعتبر مُستبدَلة بهذا الملف (انظر U-9).
> **قاعدة التنفيذ:** لا يُنفَّذ أي بند قبل كلمة **GO** صريحة؛ وكل مهمة (T1…T8) تُنفَّذ منفردة وبترتيبها.
> **الخصوصية:** لا يُذكر أي بريد/كلمة سر/توكن في هذه الوثيقة — أرقام سطور فقط.

---

## فهرس
1. [القرارات النهائية](#1-القرارات-النهائية) — معتمد / معتمد بشرط / مرفوض / معلّق
2. [خطة التنفيذ](#2-خطة-التنفيذ) — المراحل T0…T8 + الاعتماديات + معايير القبول
3. [التعديلات التفصيلية](#3-التعديلات-التفصيلية) — مسار + سطر حقيقي + BEFORE (حقيقي) ← AFTER (مقترح غير منفَّذ) + السبب + الاختبارات
4. [نطاق التغيير المغلق](#4-نطاق-التغيير-المغلق)
5. [التوثيق](#5-التوثيق)
6. [نقاط عدم اليقين والتعارضات](#6-نقاط-عدم-اليقين-والتعارضات-تحتاج-قرار-المالك) — U-1…U-12

---

## 0) خريطة الواقع (الكود الحالي = مرجع الحقيقة)

### 0.1 تحويل أرقام السطور parts ↔ الأم
| الجزء | نطاق PARTS في `scripts/rebuild_refactor.py` | معادلة التحويل (رأس 5 أسطر في كل part) | تحقق |
|---|---|---|---|
| `bridge_refactor/parts/p03_engine_accounts.py` | (532, 1596) | **الأم = p03 + 526** | p03:L733 `is_account_ready` ⇒ الأم L1259 ✓؛ p03:L760 `mark_account_cooldown` ⇒ الأم L1286 ✓ |
| `bridge_refactor/parts/p06_engine_flow.py` | (2706, 4297) | **الأم = p06 + 2700** | p06:L800 `return None, "LOW_BALANCE"` ⇒ الأم L3500 ✓؛ p06:L1240 FORBIDDEN ⇒ الأم L3940 ✓؛ p06:L1564 COMPLETED ⇒ الأم L4264 ✓ |

> **ملاحظة تصحيحية (7.28c):** كروت الـGist تستشهد بملف `bridge_refactor/p03_constants.py` (093e L2344/L2404/L2636/L2765/L2945/L2955/L3021/L4208/L4210). **هذا الملف غير موجود** (`ls bridge_refactor/p03_constants.py` = لا شيء). الدوال المقصودة (`get_eligible_accounts` L724–757، `reactivate_account_if_due` L623–642، `refresh_cookies_on_401` L967–1068) موجودة في `bridge_refactor/parts/p03_engine_accounts.py`. أرقام السطور في الكروت صحيحة؛ اسم الملف فقط خاطئ.

### 0.2 الحالة الفعلية للمسارات الستة (ما يفعله الكود اليوم)
| المسار | الملف:السطر | السلوك الحالي |
|---|---|---|
| بوابة الرصيد القبلية (P13) | p06:L770–805 | `bal_check = mod.check_balance(cookies)` L778؛ −1 ⇒ نقل للمعزل `BALANCE_UNREADABLE` L782–788 (D26 M3)؛ `0 ≤ bal < _min_balance` ⇒ `mark_account_cooldown(…29h)` L799 ثم `return None, "LOW_BALANCE"` L800 **قبل** كتابة الرصيد؛ الكتابة `{"balance": int(bal_check)}` L803 تحدث فقط لرصيد ≥ 100 |
| إعادة الفحص بعد تجديد 401 | p06:L809–822 | نفس النمط: L821 تبريد ثم L822 `return LOW_BALANCE` بلا كتابة رصيد |
| إعادة الفحص بعد 401 أثناء الشات | p06:L944–951 | نفس النمط: L950 تبريد ثم L951 `return LOW_BALANCE` بلا كتابة رصيد (**غير مذكور في أي كارت** — انظر U-5) |
| اختيار الحساب | p03:L724–757 | `is_account_ready` L733 + P48 طزاجة الهدية L741–757؛ **لا قراءة لحقل `balance` إطلاقاً** |
| فك التبريد | p03:L623–642 | يكتب `status/active/cooldown_until/cooldown_released_at` L632–637؛ **لا يكتب `balance`** |
| التبريد 29h | p03:L760–771 | يكتب `cooldown_until/last_used/last_credit_exhausted(_at)/status=cooldown/active=False`؛ **لا يكتب `balance`** |
| 403 FORBIDDEN في الـfailover | p06:L1240–1257 | نقل أعمى N=1 للمعزل `move_account_to_cooldown_vault(reason="FORBIDDEN")` L1248؛ احتياطي 5 دقائق إن فشل النقل L1254؛ `continue` L1257 ⇒ يجرّب الحساب التالي (حتى 50 محاولة L1074) |
| إلغاء المستخدم (P25) | 01.03:L2298–2302 + L2479؛ p06:L965–969 + L1161–1170 | يُعيد `"__USER_CANCELLED__", proj_id_new, asst_msg_id`؛ الـfailover يكتب `{"last_used", "status": "active"}` L1169 ويُنهي؛ **لا تمييز قبل/بعد أول chunk** |
| نجاح COMPLETED | p06:L1564–1578 | يكتب `{"last_used","status":"active","active":True,"cooldown_until":0,"last_success_at"}` ويُرجع؛ **لا تبريد ولا تصفير** |
| CREDIT_EXHAUSTED | p06:L1376, L1457 | `mark_account_cooldown(…29h)` — بلا `balance` |
| مصدر الحقيقة الخارجي للرصيد | 05.02:L459–460 | `account["balance"] = real_balance` (الفاحص الدوري يكتب الرصيد الحي) |

### 0.3 عقود الاختبارات التي تلمس هذه المسارات (يجب أن تبقى خضراء أو تُحدَّث صراحةً ضمن النطاق)
| الملف | الاختبار | العقد الحرفي | أثر MAINT-10 |
|---|---|---|---|
| `tests/test_p51_forbidden_isolation.py` | test_11 | أول 403 ينقل فوراً للمعزل | **يُكسر بـQ1** ⇒ يُعاد كتابته |
| 〃 | test_12 | سجل النقل/اللوج لـFORBIDDEN | **يُكسر بـQ1** |
| 〃 | test_13 | فشل النقل ⇒ 5 دقائق | يُعاد صياغته (5 دقائق تصبح السلوك الأساسي لا الاحتياطي) |
| 〃 | test_14 | تعطيل FORBIDDEN من `COOLDOWN_VAULT_REASONS` يعيد السلوك القديم | **يُكسر بـQ1** |
| 〃 | test_18 L360 | `body.count('status == "FORBIDDEN"') == 1` | يبقى (فرع واحد) |
| 〃 | test_18 L365 | `P44_STRUCTURED_STATUSES == ("CREDIT_EXHAUSTED","DATA_RETENTION","SESSION_EXPIRED","FORBIDDEN")` | **لا يُمس** (p05:L165) |
| 〃 | test_18 L373 | `COOLDOWN_VAULT_REASONS[:2] == ("FORBIDDEN","EMPTY_STREAM_FAILED")` | انظر U-2 (هل يبقى FORBIDDEN في الـtuple؟) |
| 〃 | test_18 L376/378 | 01.33 CRLF نقي؛ 05.02 LF نقي | يبقى |
| `tests/test_p53_vault_hardening.py` | test_35 | أول 403 ينقل بلا كاش | **يُكسر بـQ1** |
| 〃 | test_36 L216–223 | FORBIDDEN ضمن `COOLDOWN_VAULT_REASONS`؛ فرع FORBIDDEN واحد وقبل `if pub_url or status == "COMPLETED"` | انظر U-2 |
| 〃 | test_47 | حسابان متتاليان `BALANCE_UNREADABLE` ⇒ `NETWORK_DOWN` (D34) | يبقى — **يتعارض مع `NETWORK_TRANSIENT` في الكارت المقفول** (U-4) |
| `tests/test_p13_preflight_balance.py` | test_04 L71 | النص `mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours` داخل البوابة | يبقى إن أُضيفت الـkwarg **بعد** `cooldown_hours` |
| 〃 | test_07 | `bal_check >= 0` و `0 <= bal_recheck` | يبقى |
| 〃 | test_08 | النص `{"balance": int(bal_check)}` موجود | يبقى (يزداد تكراره) |
| 〃 | test_10 | أول توجيه بعد `status == "LOW_BALANCE"` هو `continue` | يبقى |
| 〃 | test_11 | LOW_BALANCE قبل CREDIT_EXHAUSTED | يبقى |
| `tests/test_p17_hardening.py` | L70 | نفس نص الاستدعاء في كتلة 401 | يبقى بنفس الشرط |
| `tests/test_p25_interactive_cancel.py` | test_05 | `if status == CANCELLED_STATUS:` قبل `if status == "LOW_BALANCE":` | يبقى |
| 〃 | test_06/07 | أنماط regex لفحص الإلغاء قبل المحاولة وعلامة المحرك | تبقى |
| `tests/test_p48_gift_preflight.py` | TestEligible test_01/02 | STALE يُستبعد؛ FRESH/GRACE ثم UNKNOWN | يبقى — الفلتر الأوفلاين يُدرج **قبل** P48 |
| `tests/test_p56_rotation_sweep.py` L421 / `tests/test_p57_main_upgrade_supervisor.py` L142 | حارس sha | `e5c165bf9dfc4929` | **يُحدَّث** بعد إعادة التوليد (D-07) |
| `tests/test_refactor_parity.py` | 16/16 | parts == الأم | يبقى بإعادة التوليد |

---

## 1) القرارات النهائية

> **منهج الاعتماد:** قرار المالك المكتوب بصيغة «RATIFIED/معتمد» في كارت المالك (`db5d6f65…` L115–121؛ `093e9661…` L3275–3282) = **معتمد**. ما ورد في كروت الوكلاء فقط (الكارت المقفول v1.0 @093e L4146–4262) بلا نص مالك مطابق = **مقترح وكيل** يحتاج تأكيداً. ما يتعارض مع قرار مالك سابق **مُنفَّذ** (D26) يُسجَّل معتمداً **بشرط** تأكيد الإلغاء الصريح (7.28e) — وهو موجود نصّياً في Q1 («إلغاء القرار القديم D26 تماماً»)، فالشرط مستوفى لحالة 403 فقط.

### 1.A معتمد (Approved) — نص مالك صريح
| # | القرار | السبب (من نص المالك) | الدليل الدقيق | حالة الاعتماد |
|---|---|---|---|---|
| **A-1 (Q1)** | 403 ⇒ **إلغاء D26 لحالة 403 فقط**: لا نقل للمعزل؛ الحساب يبقى `active:true` برصيده؛ تبريد احترازي **5 دقائق** في مكانه؛ **كسر** حلقة الـfailover فوراً (لا `continue` إلى حساب آخر)؛ إشعار تيليجرام «اجعل المشروع Public»؛ **ممنوع** إنشاء مشروع جديد | منع حرق 50 حساباً على مشروع مقفول؛ الحساب بريء | db5d L116؛ 093e L3276؛ فويس 193 (093e) | **معتمد** — يلغي D26 لحالة FORBIDDEN فقط؛ بقية أسباب المعزل (`EMPTY_STREAM_FAILED/LOGIN_FAILED/BALANCE_UNREADABLE/ZERO_BALANCE_STALE_GIFT`) **بلا تغيير** |
| **A-2 (Q2-a)** | فلتر الرصيد الأوفلاين في `get_eligible_accounts`: استبعاد الحساب الذي حقل `balance` فيه **رقم صريح < 100**؛ `None`/غير رقمي ⇒ Fail-Open (يدخل الطابور) | منع `MAX_ATTEMPTS_EXHAUSTED` بسبب حسابات صفرية تحتل الطابور | db5d L117؛ 093e L3277، L4180، L4208، L4227–4229 (Fail-Open) | **معتمد** |
| **A-3 (Q2-b)** | «Live Check Overrides»: الفحص الحي (P13 في p06 / 05.02) هو الحقيقة؛ أي قيمة مكتوبة أوفلاين (بما فيها 100 الافتراضية) تُستبدل بالقيمة الحية عند قراءتها | سيادة الواقع الميداني | db5d L117؛ 093e L4179 | **معتمد** (هو بالفعل سلوك p06:L803 لرصيد ≥100 و05.02:L460؛ يتوسع بـA-4) |
| **A-4 (Q3-a / D-03)** | كتابة الرصيد الفعلي `int(bal_check)` في JSON **قبل** `return LOW_BALANCE` في p06:L800 وL822 | سد ثغرة هروب الـreturn بلا توثيق الرصيد؛ تمكين الفلتر الأوفلاين | db5d L118؛ 093e L3278، L4207 | **معتمد** |
| **A-5 (Q3-b / D-02)** | `balance: 0` عند `CREDIT_EXHAUSTED` (نفاد حقيقي أثناء التوليد) | الرصيد نفد فعلاً | db5d L118؛ 093e L3278 | **معتمد** |
| **A-6 (Q3-c)** | الأعطال المؤقتة/فشل الشبكة (−1)/403 **لا** تصفّر الرصيد ولا تغيّره | لا دليل على استهلاك | db5d L118؛ 093e L3278 | **معتمد** (الكود الحالي لا يكتب balance في هذه المسارات — يُحفظ كقيد اختبار) |
| **A-7 (Q4 — المبدأ)** | الحد الفاصل للإلغاء = **أول chunk من البث** (01.03:L2298 `for _raw_line in r.iter_lines()`): قبله ⇒ الحساب سليم `active:true`؛ بعده ⇒ `balance:0` + تبريد 29h | ما بعد أول chunk = استهلاك على السيرفر | db5d L119؛ 093e L3279، L4188–4190 | **معتمد كمبدأ** — **آلية الكشف معلّقة** (انظر P-2/U-1): لا توجد راية «أول chunk» في 01.03 المحمي |
| **A-8 (Q5)** | الخيار (ب): `genspark_verifier_engine.py` و`01.03` **READ-ONLY** (Zero Edits)؛ fallback `do_login` 01.03:L1060؛ ممنوع استيراد ملفات خارج المستودع (`genspark_master_account_manager.py` غائب) | تثبيت الوضع القائم | db5d L120؛ 093e L3280، L4192–4196، L4235 | **معتمد** — يُقيّد A-7 (لا راية داخل 01.03) |
| **A-9 (Q6)** | MAINT-10 هو المهمة الحاكمة الوحيدة؛ الكارت (B) MAINT-9 مغلق | — | db5d L121؛ 093e L3281، L4198–4199 | **معتمد** |
| **A-10 (D-07)** | كل تعديل في الأم `01.33` + تحديث PARTS + إعادة توليد parts + تحديث sha في p56:L421/p57:L142 + ثبات 19/1402 بالأسماء | عقد البنية | db5d L93–95؛ 093e L4238–4240 | **معتمد** (عقد قائم) |

### 1.B معتمد بشرط (Approved-Conditional) — نص مالك موجود لكنه يحتاج حسم تفصيلة قبل التنفيذ
| # | القرار | الدليل | الشرط المعلّق |
|---|---|---|---|
| **C-1 (D-01)** | `reactivate_account_if_due` (p03:L632) يكتب `balance: 100` عند فك التبريد بعد 29h | 093e L4178، L4210؛ RESUME §4 صف D-01 (فويس 187/188 «قرار سيادي بمسؤولية المالك») | **غير مذكور في كارت RATIFIED Q1–Q6** (db5d L115–121) — ورد في كارت الوكيل المقفول وفي سرد سابق. يحتاج تأكيد المالك بكلمة (U-3). أثره الجانبي: الحساب الذي استيقظ برصيد 100 «افتراضي» يمرّ من الفلتر الأوفلاين ويُفحص حيّاً — وهو مقصود (A-3). |
| **C-2 (D-06)** | `COMPLETED` ⇒ `balance:0` + تبريد 29h بلا فحص إضافي (p06:L1564–1578) | 093e L4185، L4211؛ RESUME §4 D-06 (فويس 190) | **غير مذكور في كارت RATIFIED Q1–Q6**. ويتعارض مع A-3 (Live Overrides): التصفير الأعمى بعد نجاح قد يُسقط حساباً لا يزال فيه رصيد (مثال: المهمة استهلكت 40 من 100). ويلمس `_declined` (p06:L1005 — رفض النموذج يُحتسب COMPLETED) فيبرّد حساباً لم يستهلك شيئاً. يحتاج قرار المالك (U-6). |

### 1.C مرفوض / مُلغى (Rejected)
| # | البند | لماذا مرفوض | الدليل |
|---|---|---|---|
| **R-1** | D26 لحالة **403** (نقل أعمى N=1 للمعزل + `continue`) | ألغاه المالك صراحةً في Q1 | db5d L116؛ 093e L3276 — ينفَّذ كـA-1. **D26 لبقية الأسباب يبقى** |
| **R-2** | إنشاء مشروع جديد تلقائياً عند 403 | محظور قطعياً | db5d L92؛ 093e L4237 |
| **R-3** | أي تعديل في `genspark_verifier_engine.py` أو `01.03Genspark_claude-opus-5-code.py` | Q5 (ب) + حظر صريح | 093e L4194، L4235 |
| **R-4** | اتصالات شبكية داخل `get_eligible_accounts` | الفلتر أوفلاين 100% | 093e L4236 |
| **R-5** | استيراد `genspark_master_account_manager.py` أو أي ملف خارج المستودع | غائب عن المستودع | 093e L4195 |
| **R-6** | الاستشهاد بـ`bridge_refactor/p03_constants.py` | الملف غير موجود (grep/ls = 0) — هلوسة وكيل | هذه الوثيقة §0.1 |

### 1.D معلّق (Pending) — لا يُنفَّذ قبل قرار المالك
| # | البند | الحالة |
|---|---|---|
| **P-1** | هل يبقى `"FORBIDDEN"` داخل `COOLDOWN_VAULT_REASONS` (p03:L794) بعد Q1؟ | معلّق — U-2 |
| **P-2** | آلية كشف «أول chunk» دون لمس 01.03 (الخياران موصوفان في §3 T6) | معلّق — U-1 |
| **P-3** | −1 (`BALANCE_UNREADABLE`): الكارت المقفول يقول «5 دقائق `NETWORK_TRANSIENT` بلا عزل» (093e L4220) بينما الكود والاختبار p53 test_47 يطبّقان D26 M3 (نقل للمعزل) + D34 | معلّق — U-4؛ **خارج نص RATIFIED**؛ الافتراضي = لا تغيير |
| **P-4** | هل يشمل A-4 المسار الثالث p06:L951 (401 أثناء الشات)؟ | معلّق — U-5؛ التوصية: نعم (نفس الثغرة) |
| **P-5** | C-1 و C-2 أعلاه | معلّق — U-3 / U-6 |
| **P-6** | نص إشعار تيليجرام لحالة 403 (p10:L306–309 الحالي: «توقفت المهمة بسبب رفض الوصول للمشروع») — هل يُعدَّل ليقول «اجعل المشروع Public»؟ | معلّق — U-7 |
| **P-7** | 5 دقائق 403: تُكتب كـ`cooldown_until = now+300` فقط (بلا `status=cooldown`) كما في الاحتياطي الحالي L1254، أم مع `status`؟ | معلّق — U-8؛ التوصية: `cooldown_until` فقط لإبقاء `active:true` حرفياً كما طلب المالك |

---

## 2) خطة التنفيذ

> **قواعد عامة:** (1) كل مهمة تنتظر GO منفرداً. (2) التعديل يُكتب في **الأم `01.33`** (CRLF) ثم يُحدَّث جدول `PARTS` في `scripts/rebuild_refactor.py` (L35–47) ثم يُعاد التوليد؛ الحكم النهائي = parity 16/16 (`tests/test_refactor_parity.py`). (3) الاختبارات تُشغَّل بـ`-p no:cacheprovider` وتُقارن **بالأسماء** مع خط الأساس 19 (7.27b). (4) أي فشل جديد = إيقاف المهمة، لا تعديل الاختبار إلا إذا كان منصوصاً عليه في §3.

| المهمة | المحتوى | يعتمد على | الملفات | معيار القبول القابل للتحقق |
|---|---|---|---|---|
| **T0 — تثبيت الحسم** | المالك يجيب U-1…U-12 (§6) أو يكتب «الافتراضي» لكل نقطة؛ ثم GO | — | لا ملفات | رسالة مالك صريحة تحوي GO + الإجابات؛ تُدوَّن في RESUME §4 كـD-08… |
| **T1 — خط الأساس** | `pytest -q -p no:cacheprovider` على HEAD نظيف **قبل** أي تعديل؛ حفظ أسماء الفاشلين في `/tmp` | T0 | قراءة فقط | 19 فاشلاً بالأسماء المعروفة حرفياً / 1402 ناجحاً؛ `git status --porcelain` فارغ |
| **T2 — A-4 (+P-4) سد ثغرة الهروب** | `update_account_data(email, {"balance": int(…)})` قبل كل `return LOW_BALANCE` | T1 | الأم 01.33 (L3500، L3522، [L3651])؛ p06 (L800، L822، [L951]) | p13 test_04/07/08/10/11 خضراء؛ عدد `{"balance": int(` في p06 = 3 (أو 4 مع U-5)؛ parity 16/16؛ 0 فشل جديد |
| **T3 — A-5 `balance:0` عند CREDIT_EXHAUSTED** | kwarg اختيارية `balance=None` في `mark_account_cooldown` (p03:L760) تُمرَّر `0` في استدعاءي CREDIT_EXHAUSTED فقط | T2 | الأم 01.33 (L1286–1297، L4076، L4157)؛ p03 (L760–771)؛ p06 (L1376، L1457) | نصّا الاستدعاء في p13 L71 / p17 L70 يبقيان حرفياً؛ اختبار جديد: CREDIT_EXHAUSTED ⇒ `balance==0`؛ DATA_RETENTION/EMPTY_STREAM ⇒ بلا تغيير؛ 0 فشل جديد |
| **T4 — A-2 الفلتر الأوفلاين** | شرط الرصيد بعد `is_account_ready` (p03:L733–734) وقبل P48 + ثابت `OFFLINE_MIN_BALANCE` | T2 | الأم 01.33 (L1259–1261؛ L1177–1181 للثابت)؛ p03 (L733–735؛ L651–655) | p48 TestEligible خضراء؛ جديد: 0/99 يُستبعدان، 100/None/"abc" يبقون، bool لا يُحتسب رقماً؛ لا شبكة داخل الدالة (grep) |
| **T5 — A-1 حسم 403** | استبدال كتلة L1240–1257: لا نقل، `cooldown_until=now+300`، `return` بحالة FORBIDDEN بعد محاولة واحدة | T1 | الأم 01.33 (L3937–3957)؛ p06 (L1237–1257)؛ p51 test_11/12/13/14؛ p53 test_35 (+test_36/test_18 حسب U-2)؛ [p10:L306–309 حسب U-7] | فرع `status == "FORBIDDEN"` واحد وقبل COMPLETED؛ بعد 403: `active` بلا تغيير، لا سطر في `accounts_cooldown.json` ولا JSONL، `cooldown_until≈now+300`؛ الـfailover يُرجع `"FORBIDDEN"` بعد محاولة واحدة؛ `P44_STRUCTURED_STATUSES` بلا تغيير |
| **T6 — A-7 الكنسلة الذكية** | في فرع CANCELLED (p06:L1161–1170): لو بدأ التوليد ⇒ `balance:0`+29h وإلا السلوك الحالي | T0 (U-1) + T3 | الأم 01.33 (L3861–3870)؛ p06 (L1161–1170؛ L714–724 للراية) | p25 test_05/06/07 خضراء؛ جديد: قبل الإشارة ⇒ active بلا تبريد؛ بعدها ⇒ cooldown + `balance==0` |
| **T7 — C-1 / C-2 (إن أكّدهما المالك)** | C-1: `"balance": 100` في p03:L632–641؛ C-2: COMPLETED ⇒ تصفير+تبريد | T0 + T4 | الأم (L1158–1167؛ L4264–4278)؛ p03؛ p06 | C-1: فك التبريد يكتب 100؛ C-2: المعيار يُحدَّد بعد U-6 |
| **T8 — إغلاق D-07** | إعادة التوليد؛ parity؛ sha الجديد في p56:L421/p57:L142؛ خط الأساس؛ وثائق §5؛ كارت المراجعة | T2…T7 | `scripts/rebuild_refactor.py` PARTS؛ p56/p57؛ PROGRESS/RESUME/recovery/UNIVERSAL_REVIEW_CARD | parity 16/16؛ 01.33 CRLF نقي؛ 05.02 بلا لمس (`e1216b51…`)؛ 19 بالأسماء + 0 جديد؛ `verify_docs_integrity.py` Exit 0 |

**الترتيب:** T0 → T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8. (T5 مستقلة فنياً لكنها الأعلى مخاطرة على الاختبارات فتُؤخَّر بعد استقرار المسار المالي.)

---

## 3) التعديلات التفصيلية

> **BEFORE** = نص حقيقي من HEAD (أرقام parts؛ الأم = p03+526 / p06+2700). **AFTER** = اقتراح **غير منفَّذ** يُراجَع عند GO.

### T2 — سد ثغرة الهروب (A-4 + P-4) — `bridge_refactor/parts/p06_engine_flow.py` / `send_message_and_make_public`
**(أ) p06:L798–800 (الأم L3498–3500) — BEFORE:**
```python
                    log_event("warning", f"💰 رصيد منخفض ({int(bal_check)} < {_min_balance}) — تبريد 29h وتخطٍ صامت بدون أي إرسال", email=email)
                    mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                    return None, "LOW_BALANCE", None, None, None
```
**AFTER:**
```python
                    log_event("warning", f"💰 رصيد منخفض ({int(bal_check)} < {_min_balance}) — تبريد 29h وتخطٍ صامت بدون أي إرسال", email=email)
                    try:  # [MAINT-10/A-4] توثيق الرصيد الفعلي قبل الخروج — يغذّي الفلتر الأوفلاين (A-2)
                        update_account_data(email, {"balance": int(bal_check)}, json_path=json_path)
                    except Exception:
                        pass
                    mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                    return None, "LOW_BALANCE", None, None, None
```
**(ب) p06:L820–822 (الأم L3520–3522) — BEFORE:**
```python
                        log_event("warning", f"💰 رصيد منخفض بعد تجديد الجلسة ({int(bal_recheck)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                        mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                        return None, "LOW_BALANCE", None, None, None
```
**AFTER:** نفس النمط بـ`{"balance": int(bal_recheck)}`.

**(ج) p06:L949–951 (الأم L3649–3651) — مشروط بـU-5 — BEFORE:**
```python
                                log_event("warning", f"💰 رصيد منخفض بعد تجديد 401 أثناء الشات ({int(bal_mid)} < {_min_balance}) — تبريد 29h وتخطٍ صامت", email=email)
                                mark_account_cooldown(email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)
                                return None, "LOW_BALANCE", None, None, None
```
**AFTER:** نفس النمط بـ`{"balance": int(bal_mid)}`.

**السبب:** A-4/D-03. **الاختبارات:** p13 test_04 (نص الاستدعاء يبقى حرفياً)، test_07، test_08، test_10، test_11؛ p17 L70؛ جديد في `tests/test_p59_maint10_lifecycle.py`: `check_balance`⇒40 ⇒ JSON يحمل `balance==40` و`status=="cooldown"`.

### T3 — `balance: 0` عند CREDIT_EXHAUSTED (A-5) — `bridge_refactor/parts/p03_engine_accounts.py`
**p03:L760–771 (الأم L1286–1297) — BEFORE:**
```python
def mark_account_cooldown(email: str, cooldown_hours: float = 29.0, json_path: str | None = None) -> bool:
    """تسجيل نفاد الكريدت وتعيين cooldown_until = الآن + 29h مع active=False، وتستعاد تلقائياً بـ is_account_ready"""
    now = time.time()
    cd_until_ts = now + (cooldown_hours * 3600)
    return update_account_data(email, {
        "cooldown_until": cd_until_ts,
        "last_used": now,
        "last_credit_exhausted": now,
        "last_credit_exhausted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "cooldown",
        "active": False
    }, json_path=json_path)
```
**AFTER:**
```python
def mark_account_cooldown(email: str, cooldown_hours: float = 29.0, json_path: str | None = None,
                          balance: int | None = None) -> bool:
    """… [MAINT-10/A-5] balance يُكتب فقط إذا مُرِّر صراحةً (0 عند CREDIT_EXHAUSTED)؛ الأعطال المؤقتة لا تمرّره (A-6)"""
    now = time.time()
    cd_until_ts = now + (cooldown_hours * 3600)
    _fields = {
        "cooldown_until": cd_until_ts,
        "last_used": now,
        "last_credit_exhausted": now,
        "last_credit_exhausted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "cooldown",
        "active": False
    }
    if balance is not None:
        _fields["balance"] = int(balance)
    return update_account_data(email, _fields, json_path=json_path)
```
**مواضع الاستدعاء (p06 — BEFORE حقيقي، كلاهما):** `mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path)` في L1376 (داخل `if status == "CREDIT_EXHAUSTED":` L1374؛ الأم L4076) وL1457 (داخل L1449؛ الأم L4157). **AFTER:** `…, json_path=json_path, balance=0)`.
**لا تُمرَّر** في L799/L821/L950 (الرصيد الفعلي كُتب في T2)، L1184 (COMPACT)، L1218 (DEC07 ساعة)، L1297 (DATA_RETENTION) — A-6.
**الاختبارات:** جديد كما في الجدول؛ `test_credit_completion_recovery.py` (3 فاشلة أساساً — تُقارن بالأسماء).

### T4 — الفلتر الأوفلاين (A-2) — `p03_engine_accounts.py` / `get_eligible_accounts`
**p03:L727–735 (الأم L1253–1261) — BEFORE:**
```python
    for acc in all_accounts:
        if not isinstance(acc, dict):
            continue
        em = acc.get("email")
        if not em or em in tried_emails or not is_valid_email(em):
            continue
        if not is_account_ready(acc):
            continue
        eligible.append(acc)
```
**AFTER:**
```python
    for acc in all_accounts:
        if not isinstance(acc, dict):
            continue
        em = acc.get("email")
        if not em or em in tried_emails or not is_valid_email(em):
            continue
        if not is_account_ready(acc):
            continue
        # [MAINT-10/A-2] فلتر الرصيد الأوفلاين: رقم صريح < الحد ⇒ استبعاد بلا شبكة/كتابة؛ None/غير رقمي ⇒ Fail-Open
        _bal = acc.get("balance")
        if isinstance(_bal, (int, float)) and not isinstance(_bal, bool) and _bal < OFFLINE_MIN_BALANCE:
            log_event("info", f"[OFFLINE_BALANCE] تخطي حساب رصيده المسجل {int(_bal)} < {OFFLINE_MIN_BALANCE}", email=str(em))
            continue
        eligible.append(acc)
```
+ ثابت بجوار كتلة P48 (p03:L651–655): `OFFLINE_MIN_BALANCE: int = 100  # [MAINT-10/A-2] مطابق لافتراضي min_preflight_balance (p06:L773)`.
> قيود: الدالة لا تملك `bridge_cfg` ⇒ الحد ثابت (U-10)؛ الفلتر قبل P48 فلا يغيّر ترتيب FRESH/GRACE/UNKNOWN؛ الحساب قيد التنفيذ لا يتأثر (الفلتر عند الاختيار فقط).
**الاختبارات:** p48 TestEligible؛ جديد كما في الجدول؛ grep لا `check_balance`/`requests` داخل الدالة.

### T5 — حسم 403 (A-1) — `p06_engine_flow.py` / `send_message_with_auto_account_failover`
**p06:L1237–1257 (الأم L3937–3957) — BEFORE:**
```python
            # 🧊 [MAINT-4-B/D26 M1] 403 صريح → لا وسم نجاح أبداً (إصلاح T5) + نقل أعمى فوري N=1 إلى accounts_cooldown.json
            # بلا كاش ضربات وبلا انتظار (D19 مُلغى). احتياطي 5 دقائق فقط إن فشل النقل نفسه (منع الحلقة الساخنة).
            # تعطيل الآلية (COOLDOWN_VAULT_REASONS بلا FORBIDDEN) يعيد السلوك القديم حرفياً.
            if status == "FORBIDDEN" and "FORBIDDEN" in COOLDOWN_VAULT_REASONS:
                notify_account_selection_observer(
                    bridge_cfg,
                    "forbidden-isolate",
                    status="FORBIDDEN",
                    max_attempts=max_attempts,
                )
                _pid_403 = extract_project_id(pub_url or active_url or "")
                moved = move_account_to_cooldown_vault(
                    curr_email, reason="FORBIDDEN", json_path=json_path,
                    meta={"http_status": 403, "project_key": str(getattr(bridge_cfg, "selection_project_key", "") or ""),
                          "pid": _pid_403},
                )
                if not moved:
                    update_account_data(curr_email, {"cooldown_until": time.time() + 300}, json_path=json_path)
                _403_action = "نُقل للمعزل فوراً (N=1)" if moved else "تبريد 5 دقائق (فشل النقل)"
                log_event("warning", f"[MAINT-4-B] FORBIDDEN — {_403_action} والانتقال للحساب التالي", email=curr_email)
                continue   # active_url/active_query بلا تغيير — عقد LOW_BALANCE
```
**AFTER:**
```python
            # 🛑 [MAINT-10/A-1 — يلغي D26 لحالة 403 فقط] المشروع Private ⇒ الحساب بريء: لا معزل، لا تصفير، active بلا تغيير.
            # تبريد احترازي 5 دقائق في مكانه (منع الحلقة الساخنة) + إيقاف المهمة فوراً (لا حساب آخر) + إشعار المستخدم.
            if status == "FORBIDDEN":
                notify_account_selection_observer(
                    bridge_cfg,
                    "forbidden-stop",
                    status="FORBIDDEN",
                    max_attempts=max_attempts,
                )
                update_account_data(curr_email, {"cooldown_until": time.time() + 300}, json_path=json_path)
                log_event("warning", "[MAINT-10] FORBIDDEN (403) — المشروع Private؛ تبريد 5 دقائق في مكانه وإيقاف المهمة بلا محاولة حساب آخر", email=curr_email)
                return pub_url, "FORBIDDEN", curr_acc, ext_dir, last_text
```
> - `return` لا `break`: الخروج بـ`break` يصل إلى L1595 فيُرجع `MAX_ATTEMPTS_EXHAUSTED` ويُضلّل المستخدم؛ `return "FORBIDDEN"` يُسلّم الحالة إلى p10 (`NON_ACTIONABLE_PROGRESS_STATUSES` L70 + رسالة L306–309). الحساب يُحرَّر في `finally` L1591–1594.
> - الإشعار «اجعل المشروع Public» يتطلب تعديل نص p10:L306–309 — مشروط بـU-7.
> - `"FORBIDDEN"` في `COOLDOWN_VAULT_REASONS` (p03:L794) — U-2.
**الاختبارات (تعديل مطلوب):** p51 test_11 («أول 403 **لا** ينقل»)، test_12 (لا سجل/لوج)، test_13 (5 دقائق هي الأصل)، test_14 (يُحذف/يُعاد تعريفه)؛ p53 test_35؛ test_18 L373/test_36 L216 حسب U-2. **تبقى:** test_18 L360، test_36 L222–223، P44 (p05:L165)، p50 test_08c.

### T6 — الكنسلة الذكية (A-7) — بعد حسم U-1
**p06:L1161–1170 (الأم L3861–3870) — BEFORE:**
```python
            if status == CANCELLED_STATUS:
                notify_account_selection_observer(
                    bridge_cfg,
                    "user-cancelled",
                    status=CANCELLED_STATUS,
                    max_attempts=max_attempts,
                )
                log_event("warning", "🛑 [P25] أُلغيت المهمة بواسطة المستخدم — تحرير الحساب فوراً وإنهاء الـ failover", email=curr_email)
                update_account_data(curr_email, {"last_used": time.time(), "status": "active"}, json_path=json_path)
                return pub_url, CANCELLED_STATUS, curr_acc, ext_dir, last_text
```
**AFTER (هيكل):**
```python
            if status == CANCELLED_STATUS:
                notify_account_selection_observer(bridge_cfg, "user-cancelled", status=CANCELLED_STATUS, max_attempts=max_attempts)
                if _generation_started:   # [MAINT-10/A-7] بعد أول إشارة بث ⇒ استُهلك على السيرفر
                    log_event("warning", "🛑 [P25/MAINT-10] إلغاء بعد بدء التوليد — تبريد 29h ورصيد 0", email=curr_email)
                    mark_account_cooldown(curr_email, cooldown_hours=bridge_cfg.cooldown_hours, json_path=json_path, balance=0)
                else:
                    log_event("warning", "🛑 [P25] أُلغيت المهمة بواسطة المستخدم — تحرير الحساب فوراً وإنهاء الـ failover", email=curr_email)
                    update_account_data(curr_email, {"last_used": time.time(), "status": "active"}, json_path=json_path)
                return pub_url, CANCELLED_STATUS, curr_acc, ext_dir, last_text
```
**مصدر `_generation_started` — خياران بلا لمس 01.03:**
- **(أ) إشارة `project_start`** عبر `_pid_capture_callback` (p06:L714–724): راية تُرفع عند أول pid حقيقي. **الدليل:** 01.03:L2432–2437 يستدعي الـcallback عند حدث `project_start` داخل حلقة `iter_lines` (L2298) أي بعد أول سطر بث. في مسار resume (`carry_pid` L838) الراية صحيحة من البداية — سليم دلالياً.
- **(ب) `proj_id_new` المُرجَع مع `__USER_CANCELLED__`** (01.03:L2479): p06:L928 يستقبل `pid` ثم L965–969 يُسقطه؛ يمكن تمريره في الخانة الخامسة. تحفّظ: `asst_msg_id` يُولَّد محلياً (L2286) فلا يصلح كإشارة؛ `proj_id_new` يصلح (L2433/L2442 من الخادم).
> **التوصية:** (أ). **كلاهما** يقيس «أول حدث project» لا «أول chunk دلتا» (L2340/2353) حرفياً — فارق أجزاء ثانية داخل نفس البث؛ قبول هذا التقريب قرار مالك (U-1).
**الاختبارات:** p25 test_05/06/07 تبقى (الأنماط لا تتغير)؛ جديد: إلغاء قبل/بعد.

### T7 — C-1 / C-2 (مشروطان)
**C-1 — p03:L632–637 (الأم L1158–1163) — BEFORE:**
```python
        update_account_data(email, {
            "status": "active",
            "active": True,
            "cooldown_until": 0,
            "cooldown_released_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, json_path=json_path)
```
**AFTER (إن أُكِّد U-3):** `"balance": 100,  # [MAINT-10/C-1] افتراضي بعد 29h — A-3 يصحّحه حيّاً` + `acc["balance"] = 100` في L638–641.

**C-2 — p06:L1564–1578 (الأم L4264–4278) — BEFORE:**
```python
            if pub_url or status == "COMPLETED":
                notify_account_selection_observer(
                    bridge_cfg,
                    "attempt-succeeded",
                    status=str(status or "COMPLETED"),
                    public_url=str(pub_url or ""),
                )
                update_account_data(curr_email, {
                    "last_used": time.time(),
                    "status": "active",
                    "active": True,
                    "cooldown_until": 0,
                    "last_success_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }, json_path=json_path)
                return pub_url, status, curr_acc, ext_dir, last_text
```
**AFTER:** **لا يُكتب قبل حسم U-6** — الشرط `pub_url or status == "COMPLETED"` يشمل `_declined` (L1005) وحالات بـ`pub_url` بلا COMPLETED؛ والكارت المقفول (093e L4211) يطلب تصفيراً أعمى؛ و`last_success_at` مرتبط بعقود p51 L293–314 / p53 L209–231.

### T8 — إغلاق D-07
- `scripts/rebuild_refactor.py` PARTS (L35–47): تحريك حدود p03 (532,1596) وp06 (2706,4297) وكل ما بعدهما بعدد الأسطر المضافة.
- `tests/test_p56_rotation_sweep.py` L421 + `tests/test_p57_main_upgrade_supervisor.py` L142: استبدال `e5c165bf9dfc4929`.
- `tests/test_p59_maint10_lifecycle.py` **جديد** يجمع اختبارات T2–T7.

---

## 4) نطاق التغيير المغلق

> كل ما ليس في هذه القائمة **محظور**. أي حاجة لملف/تعديل غير مذكور ⇒ إيقاف + سؤال المالك + تحديث هذه الوثيقة قبل أي لمس.

### 4.1 ملفات كود مسموح تعديلها (فقط بالمواضع المذكورة)
| الملف | المواضع المسموحة | المهمة |
|---|---|---|
| `01.33_telegram_gen_bridge.py` (الأم، CRLF) | L1158–1163 (C-1 مشروط)؛ L1177–1181 (ثابت `OFFLINE_MIN_BALANCE`)؛ L1253–1261 (فلتر)؛ L1286–1297 (`mark_account_cooldown` kwarg)؛ L3498–3500، L3520–3522، [L3649–3651] (كتابة الرصيد)؛ L3861–3870 (+ L3414–3424 للراية) (الكنسلة)؛ L3937–3957 (403)؛ L4076، L4157 (`balance=0`)؛ [L4264–4278 C-2 مشروط] | T2–T7 |
| `bridge_refactor/parts/p03_engine_accounts.py` | **مولَّد** — يُعاد توليده من الأم؛ لا تحرير يدوي (رأس الملف L4) | T8 |
| `bridge_refactor/parts/p06_engine_flow.py` | **مولَّد** — نفس الحكم | T8 |
| `bridge_refactor/parts/p07…p12` | **مولَّدة** — تتغير آلياً بإزاحة PARTS فقط | T8 |
| `scripts/rebuild_refactor.py` | جدول `PARTS` L35–47 فقط (حدود p03/p06 وما بعدهما) | T8 |
| `bridge_refactor/parts/p10_progress_credit.py` ⇐ الأم L8088–8091 تقريباً (نص رسالة FORBIDDEN) | **مشروط بـU-7 فقط** | T5 |

### 4.2 اختبارات مسموح تعديلها/إنشاؤها
| الملف | المسموح |
|---|---|
| `tests/test_p59_maint10_lifecycle.py` | **إنشاء** — كل اختبارات MAINT-10 الجديدة |
| `tests/test_p51_forbidden_isolation.py` | test_11، test_12، test_13، test_14 (إعادة كتابة لعقد A-1)؛ test_18 L373 **فقط إن** حُسم U-2 بالحذف |
| `tests/test_p53_vault_hardening.py` | test_35 (إعادة كتابة)؛ test_36 L216 **فقط إن** حُسم U-2 بالحذف |
| `tests/test_p56_rotation_sweep.py` | L421 sha فقط |
| `tests/test_p57_main_upgrade_supervisor.py` | L142 sha فقط |

### 4.3 ملفات توثيق مسموح تحديثها (غير وظيفية)
`PROGRESS.md`، `RESUME.md`، `UNIVERSAL_REVIEW_CARD.md`، `genspark/recovery_state.json`، `MAINT-10_MASTER_PLAN.md` (هذه)، `README.md` (فقرة دورة الحياة إن وُجدت — T8).

### 4.4 محظور قطعياً (READ-ONLY)
| الملف/البند | السبب |
|---|---|
| `01.03Genspark_claude-opus-5-code.py` | Q5/R-3 — محمي |
| `genspark_verifier_engine.py` | Q5 Zero Edits |
| `05.02_genspark_delayed_gifts_manager.py` | خارج النطاق؛ sha `e1216b51…` يجب أن يبقى |
| `bridge_refactor/main_upgrade.py`، `bridge_refactor/live_account_checker.py`، `bridge_refactor/git/github_bulk_sync.py` | OWNER_PRESERVED (rebuild L31) — خارج النطاق |
| `P44_STRUCTURED_STATUSES` (p05:L165 / الأم L2312) | عقد test_18 L365 |
| `is_account_ready` (p03:L578–620) | عقد p51 «Untouched» (L26) |
| آلية D26 لغير 403 (`EMPTY_STREAM_FAILED/LOGIN_FAILED/BALANCE_UNREADABLE/ZERO_BALANCE_STALE_GIFT`) + D34 | لا نص مالك يلغيها (U-4) |
| `move_account_to_cooldown_vault`، JSONL، القفل المشترك | خارج النطاق |
| إنشاء مشروع جديد عند 403 / أي اتصال شبكي داخل `get_eligible_accounts` / أي import خارجي | R-2/R-4/R-5 |
| تعديل توقيع الإرجاع الخماسي لـ`send_message_and_make_public` / `send_message_with_auto_account_failover` | يكسر مستدعين كثر؛ الخيار (ب) في T6 يستخدم الخانة الخامسة الموجودة فقط |

---

## 5) التوثيق

| الملف | التغيير المقترح | السبب | التوقيت |
|---|---|---|---|
| `PROGRESS.md` L140 | تحديث صف MAINT-10: «الخطة الحاكمة = `MAINT-10_MASTER_PLAN.md`؛ ينتظر T0 (U-1…U-12) + GO» | ربط TASK بالمرجع التنفيذي الوحيد | **الآن** (هذه الجلسة — غير وظيفي) |
| `RESUME.md` §3.25 (جديد قبل `## 4)`) | ملخص جلسة MASTER AUDIT: ما فُحص/ما حُدّث/ما تعذّر؛ إشارة إلى الخطة | استمرارية | **الآن** |
| `RESUME.md` L25 صف MODE | «MAINT-10 PLAN مكتوب (§3.25 + `MAINT-10_MASTER_PLAN.md`) — ينتظر GO؛ MODE ⇒ ALIGNMENT_ONLY» | قانون MODE | **الآن** |
| `RESUME.md` §4 صف `D-01–D-07` | إضافة إشارة «مصنَّفة في الخطة: A-1…A-10 / C-1، C-2 / P-1…P-7» | ربط القرارات | **الآن** |
| `genspark/recovery_state.json` | مفتاح `maint10_plan_2026_11_04` + تحديث `next` | استعادة بعد ريستارت | **الآن** |
| `UNIVERSAL_REVIEW_CARD.md` | صف §14 جديد 1.15 + مبدأ 7.29 إن ظهر درس جديد (انظر الكارت أدناه) | دستور المراجعة | **الآن** إن وُجد درس جديد |
| `PROGRESS.md` / `RESUME.md` / `recovery_state` | بعد كل Tn: `[x]` جزئي + sha + أسماء الاختبارات | عقد D-07 | أثناء T2–T8 |
| `README.md` | فقرة «دورة حياة الحساب بعد MAINT-10» (403 بريء، فلتر أوفلاين، balance) | توثيق المستخدم | T8 |
| `tests/test_p51_forbidden_isolation.py` docstring L1–30 | تحديث سرد D26 ⇒ «D26 لغير 403؛ 403 = A-1» | دقة العقد | T5 |

---

## 6) نقاط عدم اليقين والتعارضات (تحتاج قرار المالك)

| # | النقطة | القراءتان / الخيارات (7.26) | الدليل | توصيتي (ليست قراراً) |
|---|---|---|---|---|
| **U-1** | تعريف «أول chunk» تقنياً بلا لمس 01.03 | (أ) حدث `project_start` عبر callback (p06:L714–724 ← 01.03:L2432–2437) — تقريب بأجزاء ثانية؛ (ب) `proj_id_new` المُرجَع مع `__USER_CANCELLED__` (01.03:L2479) عبر الخانة الخامسة؛ (ج) تعديل 01.03 لإضافة راية — **مرفوض بـQ5** | لا توجد راية «first chunk» في 01.03 (grep=0) | (أ) |
| **U-2** | `"FORBIDDEN"` في `COOLDOWN_VAULT_REASONS` (p03:L794) بعد A-1 | (أ) إبقاؤه كـdead-config لحماية test_18 L373/test_36 L216؛ (ب) حذفه + تعديل الاختبارين | الكود بعد T5 لن يقرأه | (ب) — لا ثوابت ميتة؛ لكن (أ) أقل مخاطرة على الاختبارات |
| **U-3** | C-1 `balance:100` عند فك التبريد | غير مذكور في RATIFIED Q1–Q6؛ موجود في الكارت المقفول (093e L4178/L4210) وفويس 187/188 | db5d L115–121 لا يحويه | تأكيد بكلمة أو تأجيل؛ إن أُكِّد فمع A-3 صراحةً |
| **U-4** | −1 (`BALANCE_UNREADABLE`): الكارت المقفول يقول «5 دقائق `NETWORK_TRANSIENT` بلا عزل» (093e L4220) | الكود الحالي: نقل للمعزل D26 M3 (p06:L782–788) + قاطع D34 (L1261–1274)؛ اختبار p53 test_47 يحمي ذلك | **خارج نص RATIFIED** | لا تغيير (خارج النطاق) ما لم يكتب المالك إلغاء D26 M3 صراحةً |
| **U-5** | شمول A-4 للمسار الثالث p06:L949–951 (401 أثناء الشات) | الكروت ذكرت L800 وL822 فقط | نفس الثغرة حرفياً | نعم — تضمينه |
| **U-6** | C-2 `COMPLETED ⇒ 0 + 29h` | يتعارض مع A-3 (Live Overrides) ومع عدم استهلاك كامل الرصيد في كل مهمة؛ الشرط `pub_url or COMPLETED` يشمل `_declined` (L1005)؛ يلمس `last_success_at` (p51/p53) | 093e L4185/L4211؛ فويس 190 | **تأجيل** C-2 أو استبداله بـ«فحص حي بعد COMPLETED ثم كتابة القيمة الحقيقية» (A-3) — يحتاج قرار |
| **U-7** | نص إشعار 403 لتيليجرام | الحالي p10:L306–309 لا يقول «اجعل المشروع Public» | A-1 يطلب الإشعار | تعديل النص ضمن T5 (سطران) |
| **U-8** | شكل تبريد الـ5 دقائق لـ403 | (أ) `cooldown_until` فقط (كما L1254) ⇒ `active:true` يبقى حرفياً؛ (ب) `status=cooldown` أيضاً | A-1: «يظل active:true» | (أ) |
| **U-9** | اسم ملف الخطة | أمر المالك: `MASTER_PLAN.md`؛ الـGists: `MAINT10_LIFECYCLE_SPEC.md` / `MAINT10_SPECIFICATION.md` / `MAINT10_GATE0_SPEC.md` | — | اعتُمد `MAINT-10_MASTER_PLAN.md`؛ لا ملفات أخرى تُنشأ |
| **U-10** | حد الفلتر الأوفلاين ثابت 100 بينما البوابة الحية تقرأ `bridge_cfg.min_preflight_balance` (p06:L773) | (أ) ثابت 100؛ (ب) تمرير الحد كمعامل اختياري لـ`get_eligible_accounts` (يغيّر التوقيع — مستدعون في p06:L1095 ومسارات أخرى) | — | (أ) الآن؛ (ب) إن غيّر المالك الحد يوماً |
| **U-11** | الكارت المقفول يصف `bridge_refactor/p03_constants.py` | غير موجود — المقصود `parts/p03_engine_accounts.py` | ls=0 | تصحيح الاسم في أي كارت لاحق |
| **U-12** | ترتيب التنفيذ: مهمة واحدة لكل GO أم GO واحد لـT2–T8 | أمر المالك: «كل مهمة تُنفَّذ منفردة» | — | GO لكل Tn (أو GO مجمَّع صريح بالأسماء) |

> **ما تعذّر الوصول إليه:** جهاز المالك/لوجاته (B15 يبقى «مُبلَّغ غير متحقَّق» 7.28f)؛ مجلد `bridge_refactor_36` المذكور في الـGist (مسار محلي عند المالك `d:/SMS/…` — غير موجود في الـsandbox؛ الأرقام طُوبقت مع المستودع).
