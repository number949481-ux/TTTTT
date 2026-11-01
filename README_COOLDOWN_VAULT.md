# معزل التبريد الموحد — `accounts_cooldown.json` + `account_log.json` (MAINT-3)

> صفحة واحدة لأي وكيل/مالك قادم. القرارات الحاكمة: `RESUME.md §3–§3.8` + جدول D1–D25. الميثاق الدائم في رأس `PROGRESS.md`.

## لماذا
- قبل MAINT-3 كان حساب يرجع **403 (FORBIDDEN)** يُوسم **نجاحاً** في `accounts_genspark.json` (`status=active`, `last_success_at`) بينما يرى المستخدم بطاقة فشل (RESUME §3.1 T5).
- الرد الفارغ (`EMPTY_STREAM_FAILED`، صمام DEC-07) كان يُبرَّد في المكان ساعةً واحدة.

## الملفات الثلاثة (كلها بجوار `accounts_genspark.json` — D6)
| الملف | الدور | من يكتب | من يقرأ |
|---|---|---|---|
| `accounts_genspark.json` | الأساسي | 01.33 + 05.02 | 01.33 + 05.02 |
| `accounts_cooldown.json` | **معزل التبريد** (قائمة مسطحة؛ سجل الحساب كاملاً + `quarantine_info`) | 01.33 (Cut&Move) + 05.02 (`--revive -q` يحذف المنقول) | 05.02 فقط (الفحص الدوري) |
| `account_log.json` | سجل تدقيق (أول عنصر `schema` دائم؛ تقليم 30 يوماً + سقف 5000 — D7) | 01.33 | بشر/أدوات مراجعة |

**لا `password`/`cookies` في `account_log.json` أبداً.** سجل المعزل يحتفظ بهما (D2) لأن `05.02 check_account_status` يحتاجها.

## متى يُنقل الحساب (01.33 — `send_message_with_auto_account_failover`)
| الحالة | السلوك | الساعات المعلوماتية `cooldown_until_ts` |
|---|---|---|
| `FORBIDDEN` أول مرة | `forbidden_hits` += 1، تبريد **5 دقائق** في المكان فقط | — |
| `FORBIDDEN` على **مشروع ثانٍ مختلف خلال 24h** (`FORBIDDEN_MOVE_AFTER_N=2` — D19) | **Cut&Move** إلى المعزل | 24h (D1) |
| `EMPTY_STREAM_FAILED` | **Cut&Move** إلى المعزل؛ إن فشل النقل ⇒ التبريد القديم 1h في المكان (D10) | 1h |
| فشل النقل لأي سبب | الحساب يبقى في الأساسي مع تبريد احتياطي؛ **لا وسم نجاح أبداً** | — |

النقل = **نسخ أولاً** إلى المعزل ثم **قصّ** من الأساسي (مع `accounts_genspark.json.cooldown_move.bak` دوّار). فشل القص ⇒ الحساب في الملفين (`move_partial` في السجل) — لا فقدان أبداً. النقل idempotent (`duplicate_detected`).

## كيف يعود الحساب (05.02 فقط — لا سكربتات موازية)
```
python 05.02_genspark_delayed_gifts_manager.py --revive -q /ABS/PATH/accounts_cooldown.json -f /ABS/PATH/accounts_genspark.json --success-file /ABS/PATH/accounts_success.json
```
- **يُجدوَل خارج المستودع** مرتين يومياً **12:00 و 00:00** (ثابت دستوري D16/D17): يفحص **هذا الملف فقط**.
- ⛔ `accounts_failed.json` و⛔ `accounts_delayed_gifts_credits.json` **لا يُمرَّران للفحص أبداً** (وجهتا كتابة فقط).
- الدورة (MAINT-3-B-1، `run_revival`): `HEALTHY` + هدية ≤3 أيام ← الأساسي والناجح · `DEAD` ← `accounts_failed.json` · `STALE` ← `accounts_delayed_gifts_credits.json` · غير المحسوم يبقى. ثم خروج فوري.
- 05.02 يحذف `quarantine_info` عند الإنعاش فيعود الحساب نظيفاً؛ `cooldown_until_ts` معلوماتي فقط (D12).
- عودة `STALE` من معزل الهدية = يدوياً/جدول المالك (D23) — لا فحص دوري لذلك الملف.

## المفاتيح (01.33 p03 بعد `mark_account_cooldown`)
- `COOLDOWN_VAULT_REASONS = ("FORBIDDEN", "EMPTY_STREAM_FAILED")` — **tuple فارغ = تعطيل كامل** (السلوك القديم حرفياً، بما فيه T5). حذف اسم واحد يعطّل سببه فقط.
- `COOLDOWN_VAULT_HOURS = {"FORBIDDEN": 24.0, "EMPTY_STREAM_FAILED": 1.0}` · `FORBIDDEN_MOVE_AFTER_N = 2` · `FORBIDDEN_HITS_WINDOW_HOURS = 24`.
- التوسع لحالة جديدة = اسم في الـtuple + ساعات في القاموس + `moved = move_account_to_cooldown_vault(...)` في فرعها.

## الأقفال والتزامن
- الأساسي + المعزل تحت `FILE_LOCK` وحده؛ السجل تحت `ACCOUNT_LOG_LOCK` وحده ويُكتب **بعد** الخروج من `FILE_LOCK` — لا تداخل، لا deadlock.
- لا قفل عبر العمليات بين 01.33 و05.02 (D15 مقبول): جدولة 12:00/00:00 + النقل idempotent يصحّح أي ازدواج.

## الاختبارات
- `tests/test_p51_forbidden_isolation.py` (01.33، 18 اختباراً، ملفات مؤقتة حقيقية + `FILE_LOCK` الحقيقي).
- `tests/test_p52_revival_routing.py` (05.02 `run_revival`، 10 اختبارات، بلا شبكة).
- `tests/test_p50_dec07_breaker.py::test_09` يثبّت عقد **الاحتياطي** (التبريد 1h عند تعذر النقل).
