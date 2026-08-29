#  ⚡️ MASTER RESUME PROTOCOL — RESUME, DO NOT RESTART
 
# 🔄 PROTOCOL SELF-UPDATE — الوكيل يحدّث البروتوكول بنفسه
# هذا الملف (00_MASTER_RESUME_PROTOCOL.md) هو المصدر الوحيد
# لبرومبت الاستئناف. إذا اكتشفت أثناء الجلسة أن محتواه لم يعد
# مطابقاً للواقع — مثلاً:
#   - البند 0 يشير لمهمة/Phase انتهت أو تغيّرت،
#   - Baseline أو SPEC_DOC أو DEC أصبحت قديمة،
#   - نقطة الاستئناف الفعلية اختلفت عما يصفه،
# فنفّذ فوراً بهذا الترتيب:
# 1. حدِّث في الملف البيانات المتغيّرة فقط: بلوك ## 0
#    (المهمة/SPEC_DOC/DEC/Baseline) وسطر نقطة الاستئناف.
#    ⛔ ممنوع منعاً باتاً تعديل القواعد الثابتة (البنود 1–6
#    وهذا البلوك) — إن رأيت أن قاعدة نفسها تحتاج تغييراً
#    فاقترحه نصاً في تقريرك ولا تنفّذه.
# 2. أنهِ الخطوة الذرية الجارية (أو ارجع عنها) واترك الشجرة
#    نظيفة، ثم Commit برسالة تبدأ بـ:
#    "protocol: self-update — <سبب التحديث>"
# 3. توقف عن العمل وقدّم تقريراً مصغّراً بصيغة:
#    PROTOCOL-UPDATED: <ما تغيّر ولماذا> + <آخر خطوة مكتملة>
#    + "انسخ النسخة الجديدة من 00_MASTER_RESUME_PROTOCOL.md
#    واستأنف بها" — ثم انتظر ولا تستأنف من تلقاء نفسك.

## 0. CURRENT OWNER TASK ← [الجزء الوحيد المتغيّر لكل مهمة]
⏸️ BLOCKED-ON-OWNER — بانتظار مهمة جديدة من المالك (S78+)
آخر مرحلة مكتملة: PHASE 44 — RESUME PIPELINE INTEGRITY (DEC-040)
✅ مُقفلة S72–S78 (CP0–CP9 كلها [x] — أرشيف 7.7-ج في
Deep_Thinking_Tasks_Remaining.TXT — لا يُعاد فتحها).
SPEC_DOC المؤرشفة: 18_COT_CLEANUP_AND_DYNAMIC_RESUME_PROMPT.MD
(كل Checkboxes محسومة).
آخر Baseline معتمد (S78 Terminal فعلي): 974/974 PASS (+12 subtests)
+ hadith_sijil Exit 0 + Parity 11/11 + شجرة نظيفة | الملف النشط:
01.33 (8585 سطراً) | Scope Freeze الدائم: جسم detect_response_status
/ P35 / P40 / دلالات P18 تغليف فقط + المحرك 01.03 READ-ONLY.
نقطة الاستئناف: لا توجد — انتظر مهمة جديدة من المالك (أي جلسة
تُفتح بلا مهمة جديدة ➔ STOP + BLOCKED-ON-OWNER).

## 1. LOCATE (قراءة لتحديد الحالة فقط — بلا فحص جنائي جديد)
اقرأ: الدستور (البند 7) → docs/engineering/PROGRESS.md
(current-task/next-action) → SPEC_DOC إن وُجدت، وإن لم تُنشأ
بعد فقائمة Checkpoints البند 7 هي المرجع → SESSION_LOG.md →
آخر Commits. الريبو مرجع فقط:
https://github.com/number949481-ux/TTTTT
كل [x] مُصدَّقة افتراضياً ولا تُعاد — التحقق (بدليل واحد سريع)
فقط عند تعارض صريح بين الملفات، والأقل تقدماً يفوز.
أول [ ] = نقطة البدء الوحيدة لهذه الجلسة.

## 2. UNBLOCK RULE
هذا البرومبت هو توجيه المالك: أي BLOCKED-ON-OWNER من نوع
"بانتظار مهمة جديدة" يُعتبر ملغياً — حدّثه وابدأ فوراً.
أما Blocker تقني حي: عالجه إن كان ضرورياً لإنجاز المهمة،
وإلا وثّقه وتوقف وأبلغ.

## 3. SANITY CHECK (إلزامي قبل أي كود — دقيقتان لا أكثر)
pytest -q  ← يطابق الـ Baseline أعلاه أو أعلى
python scripts/hadith_sijil.py  ← Exit Code 0
فشل متعلق بالمهمة → أصلحه بدليل أولاً. فشل Pre-existing غير
متعلق → وثّقه وواصل — لا تتحول لجلسة إصلاح شاملة.

## 4. EXECUTE
نفّذ CURRENT OWNER TASK فقط، Checkpoint تلو الأخرى:
تنفيذ → دليل Terminal → تحديث Checkbox و next-action فوراً →
Commit لكل Checkpoint مكتملة.
ممنوع: إعادة عمل مكتمل، Refactor أو تحسينات خارج النص، لمس
المسارات المجمّدة (Scope Freeze)، تغيير سلوك قائم بلا ضرورة،
أو Mutation بلا تأكيد حيثما تنص المهمة
(Confirmation before ANY Mutation).

## 5. TASK CHANGE GUARD
إذا وجدت البند 7 يحمل مهمة مختلفة عن البند 0 أعلاه →
STOP IMMEDIATELY: سجّل BLOCKED-ON-OWNER واطلب توجيه المالك —
لا تنفّذ القديمة ولا الجديدة.
⚠️ استثناء 1: تحديثات الـ Checkboxes والحالة الناتجة عن تنفيذك
أنت للمهمة الحالية لا تُعتبر "تغييراً للمهمة".
⚠️ استثناء 2: إن كان الاختلاف مجرد بيانات قديمة في هذا الملف
(البند 0 لم يُحدَّث بعد إنجاز سابق) → طبّق بلوك SELF-UPDATE
أعلاه بدلاً من التوقف الأعمى.

## 6. CLOSE (من الدستور حرفياً — لا إعادة صياغة)
عند اكتمال آخر Checkpoint:
- بوابات الجودة كاملة كما في البند 5 من الدستور
  (pytest 100% بلا Skip جديد + hadith_sijil Exit 0 + Parity).
- التوثيق الكامل كما في البند 6: PROGRESS + SESSION_LOG (DEC
  أعلاه) + SPEC_DOC مكتملة + تحديث البند 7 بالمهمة التالية
  + تحديث بلوك ## 0 في 00_MASTER_RESUME_PROTOCOL.md بالمهمة
  التالية (Phase/SPEC_DOC/DEC/Baseline الجديد) — كل ذلك في
  نفس الـ Commit، بحيث يصبح برومبت الاستئناف القادم جاهزاً
  في الريبو دون أي تدخل يدوي + Git tree نظيفة.
- التقرير النهائي بعناوين البند 8 من الدستور الاثني عشر
  حرفياً وبالترتيب (STATUS → CAUSE → EVIDENCE → CALL PATH →
  FIX DESIGN → CHANGES → TESTS → PARITY → QUALITY GATE →
  GIT → REMAINING RISK → NEXT RESUME POINT).

## FINAL RULE
Evidence-First: أي "تم" بلا مخرجات Terminal حقيقية = غير منجز.
هذه جلسة RESUME — ليست RESTART ولا إعادة تدقيق شاملة.
ابدأ الآن: LOCATE → SANITY → EXECUTE → VERIFY → CLOSE
