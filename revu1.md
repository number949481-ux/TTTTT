مهمة: Feature Parity Audit + Gap Analysis + Safe Completion
لدي مشروع تم عمل Refactor له داخل:
`bridge_refactor/`
والملفات المرجعية التي تمثل النسخ العاملة الكاملة هي:
```text
01.26_telegram_gen_bridge.py
01.03Genspark_claude-opus-5-code.py
```
هذه الملفات مرجع وظيفي فقط.
الهدف من تقسيم المشروع إلى Modules هو:
سرعة أعلى
كفاءة أعلى
صيانة أفضل
فصل المسؤوليات
وليس حذف أو تغيير أو تقليل أي Feature موجودة في النسخة الأصلية.
---
OBJECTIVE
أريد منك إجراء Deep Feature Parity Audit بين:
```text
bridge_refactor/
```
وبين:
```text
01.26_telegram_gen_bridge.py
01.03Genspark_claude-opus-5-code.py
```
ثم تحديد:
ما تم نقله فعليًا.
ما تم تحسينه.
ما تغير Behavior الخاص به.
ما تم فقده.
ما تم تنفيذه بشكل ناقص.
ما أصبح موجودًا لكن غير مربوط بالـ flow.
ما أصبح يعمل بشكل مختلف عن النسخة الأصلية.
ما قد يكون موجودًا في الكود لكنه غير reachable.
ما تم استبداله ببديل لكن البديل لا يغطي نفس الوظيفة.
أي Edge Cases كانت تعمل سابقًا ولم تعد تعمل.
لا أريد مقارنة شكلية بين الملفات.
أريد مقارنة Behavior + Features + Execution Flow + Failure Handling + State + Integrations.
---
CRITICAL RULE
اعتبر:
```text
01.26_telegram_gen_bridge.py
01.03Genspark_claude-opus-5-code.py
```
هما Source of Functional Truth.
لكن لا تنسخ منهما التصميم القديم.
المطلوب هو:
> **100% Feature Parity + Architecture محسنة**
أي Feature موجودة في الملفات المرجعية يجب أن تظل موجودة في `bridge_refactor` حتى لو تم تنفيذها بطريقة مختلفة.
---
PHASE 1 — BUILD COMPLETE FEATURE INVENTORY
اقرأ الملفين المرجعيين بالكامل.
استخرج منهما جميع الوظائف الفعلية، وليس فقط أسماء الـ functions.
صنفها إلى:
```text
Telegram
Genspark
Accounts
Sessions
Authentication
Browser/HTTP
AI Providers
Captcha/Vision
Quota/Credits
Jobs
Background Execution
Git
GitHub REST
Files
Workspace
State
Retry
Fallback
Error Handling
Messaging
Notifications
Configuration
Security
Logging
Recovery
Cleanup
Edge Cases
```
لكل Feature حدد:
```text
Feature ID
Feature Name
Source File
Function / Class
Trigger
Inputs
Outputs
Dependencies
Success Behavior
Failure Behavior
Fallback Behavior
Side Effects
```
---
PHASE 2 — EXTRACT ACTUAL FEATURES
لا تعتمد على أسماء functions فقط.
مثال:
إذا كان هناك:
```python
send_message()
```
لا تعتبر Feature هي "send_message".
حلل ما يحدث فعليًا بداخلها:
formatting
retries
error handling
Telegram API behavior
reply threading
media handling
message splitting
fallback
logging
timeout
user notification
كل هذه تعتبر أجزاء من الـ Feature.
---
PHASE 3 — DECOMPOSE COMPOSED FEATURES
ابحث عن الـ Features المركبة التي تتكون من عدة خطوات.
مثال:
```text
Telegram command
→ validate URL
→ create workspace
→ reserve account
→ create session
→ execute Genspark
→ detect result
→ handle quota
→ sync files
→ git commit
→ notify Telegram
→ cleanup
```
قارن هذا الـ flow كاملًا مع `bridge_refactor`.
لا تعتبر Feature موجودة لمجرد وجود function باسم مشابه.
يجب أن يكون الـ end-to-end behavior محفوظًا.
---
PHASE 4 — AUDIT bridge_refactor
افحص `bridge_refactor/` بالكامل.
اكتشف:
A. Implemented
Feature موجودة وتعمل بنفس السلوك المطلوب.
B. Partially Implemented
Feature موجودة لكن جزء من Behavior مفقود.
C. Missing
Feature غير موجودة.
D. Dead / Disconnected
Feature موجودة في module لكن لا يتم استدعاؤها.
E. Behavior Changed
Feature موجودة لكن behavior مختلف.
F. Regression Risk
Feature تبدو موجودة لكنها معرضة للفشل في حالات معينة.
---
PHASE 5 — TRACE REAL EXECUTION
لا تكتفِ بالـ static comparison.
تتبع الـ execution flow الحقيقي.
ابدأ من:
```text
Telegram Entry
```
ثم تتبع:
```text
Handler
↓
Job
↓
Account
↓
Session
↓
Genspark
↓
Result
↓
Post-processing
↓
Git
↓
Notification
↓
Cleanup
```
حدد أين ينقطع أي Feature من النسخة الأصلية.
---
PHASE 6 — COMPARE EDGE CASES
هذه المرحلة إلزامية.
استخرج من الملفات المرجعية كل الحالات الخاصة، مثل:
invalid request
invalid GitHub URL
repository unavailable
authentication failure
session expired
account unavailable
account exhausted
quota exceeded
rate limit
timeout
malformed API response
partial response
empty response
Git failure
GitHub REST failure
duplicate execution
concurrent execution
Telegram send failure
Telegram timeout
file conflict
workspace conflict
cleanup failure
unexpected exception
provider failure
fallback transition
ثم اختبر هل `bridge_refactor` يغطي كل حالة.
---
PHASE 7 — COMPARE STATE MACHINES
قارن الـ State Management بين النسخة الأصلية والـ Refactor.
راجع:
```text
Account state
Session state
Job state
Workspace state
Git state
Provider state
Retry state
```
اكتشف أي state transition كانت موجودة واختفت.
---
PHASE 8 — COMPARE FALLBACKS
هذه نقطة حرجة.
استخرج كل Fallback من النسخ الأصلية.
لا تفترض أن fallback قديمة أو redundant.
لكل واحدة:
```text
Fallback
Trigger
Primary Path
Fallback Path
Conditions
Expected Result
```
ثم تحقق أنها موجودة في `bridge_refactor`.
---
PHASE 9 — COMPARE ERROR BEHAVIOR
ليس المطلوب فقط أن الكود لا ينهار.
المطلوب الحفاظ على:
```text
Error Detection
Error Classification
Retry
Recovery
Account Rotation
Session Recovery
Fallback
User Notification
Logging
Cleanup
```
إذا كان behavior الحالي مختلفًا، سجله حتى لو كان الكود "أكثر نظافة".
---
PHASE 10 — PERFORMANCE CHECK
بعد إثبات Feature Parity:
حدد أين حقق الـ Refactor تحسينًا حقيقيًا:
```text
Performance
Memory
Network
Concurrency
Startup
File I/O
API Calls
Git Operations
Browser Sessions
CPU
```
ولا تسمح بتحسين performance يؤدي إلى فقد Feature أو تغير behavior مهم.
---
PHASE 11 — AUTOMATED PARITY MATRIX
أنشئ Matrix مثل:
```text
| ID | Feature | Original | Refactor | Status | Evidence | Risk |
```
Status:
```text
PASS
PARTIAL
MISSING
CHANGED
DEAD
REGRESSION
```
ولا تستخدم `PASS` إلا بعد إثبات أن الـ behavior متوافق.
---
PHASE 12 — CREATE GAP REPORT
أنشئ تقرير واضح يحتوي:
```text
TOTAL FEATURES
IMPLEMENTED
PARTIAL
MISSING
CHANGED
DEAD
REGRESSION RISKS
```
ثم رتب النواقص حسب:
```text
CRITICAL
HIGH
MEDIUM
LOW
```
ولا تعتبر UI أو naming difference مشكلة.
ركز على functional parity.
---
PHASE 13 — SAFE IMPLEMENTATION
بعد اكتشاف النواقص:
لا تبدأ بإعادة كتابة المشروع.
لكل Gap:
```text
1. Identify Source Behavior
2. Locate Refactor Target
3. Determine Missing Logic
4. Implement Minimal Change
5. Preserve Modular Architecture
6. Test
7. Verify Parity
```
يمنع نقل الـ spaghetti architecture القديمة إلى modules جديدة.
خذ behavior فقط وليس التصميم القديم.
---
PHASE 14 — NO FEATURE LOSS POLICY
ممنوع:
حذف Feature
تعطيل Feature
تقليل fallback
تقليل error handling
إزالة edge case
تغيير retry semantics
إزالة account/session handling
إزالة provider support
إزالة Git behavior
إزالة Telegram behavior
إلا إذا كان هناك دليل قاطع أن الـ Feature غير مستخدمة وتم تسجيلها صراحة.
---
PHASE 15 — DO NOT TRUST FUNCTION NAMES
الأمثلة التالية لا تعني Feature Parity:
```text
old:
process_request()

new:
process_request()
```
يجب مقارنة:
```text
Inputs
Validation
State
Side Effects
API Calls
Retries
Fallback
Errors
Output
Cleanup
```
---
PHASE 16 — DO NOT MODIFY REFERENCES
الملفات:
```text
01.26_telegram_gen_bridge.py
01.03Genspark_claude-opus-5-code.py
```
Read-only Reference.
لا تعدلها.
كل الإصلاحات تكون داخل:
```text
bridge_refactor/
```
---
PHASE 17 — REGRESSION TESTING
بعد إصلاح كل مجموعة Features:
شغل:
```text
Syntax
Imports
Unit Tests
Integration Tests
Smoke Tests
End-to-End Tests
```
واختبر تحديدًا:
```text
Telegram → Job
Job → Account
Account → Session
Session → Genspark
Genspark → Result
Result → Git
Git → Telegram
```
---
PHASE 18 — CURRENT PROJECT STATE
قبل أي تعديل:
```text
DO NOT ASSUME THE REFACTOR IS INCOMPLETE.
DO NOT ASSUME THE REFACTOR IS COMPLETE.
```
اكتشف الحقيقة من الكود.
قد تكون هناك Features ناقصة غير ظاهرة.
وقد تكون بعض Features موجودة لكن موصولة بطريقة خاطئة.
---
DEVELOPMENT PROTOCOL
كل تغيير يجب أن يتبع:
```text
Inspect
→ Compare
→ Identify Gap
→ Minimal Fix
→ Test
→ Verify
→ Record
```
حدث:
`DEVELOPMENT_TASKS.md`
بعد كل مجموعة إصلاحات.
---
FIXED RESUME PROTOCOL
عند استئناف العمل بعد انقطاع الجلسة:
```text
RESUME

1. Read DEVELOPMENT_TASKS.md
2. Read latest Resume State
3. Inspect current bridge_refactor state
4. Identify LAST VERIFIED FEATURE
5. Identify CURRENT GAP
6. Never repeat verified work
7. Continue from first incomplete item
8. Validate after changes
9. Update DEVELOPMENT_TASKS.md
10. Save new Resume State
```
استخدم:
```text
SESSION:
DATE:
REFERENCE_FILES:
LAST_VERIFIED_FEATURE:
CURRENT_GAP:
FILES_CHANGED:
CHANGES:
TESTS:
RESULT:
BLOCKERS:
NEXT_EXACT_ACTION:
```
Source of Truth بالترتيب:
```text
1. Actual Files
2. Tests / Runtime Evidence
3. DEVELOPMENT_TASKS.md
4. Resume State
5. Previous Chat Context
```
---
EXECUTION RULE
لا تقم بإصلاح كل شيء عشوائيًا مرة واحدة.
ابدأ بالترتيب:
```text
1. Full Feature Inventory
2. Full Parity Matrix
3. Critical Missing Features
4. High Risk Regressions
5. Partial Features
6. Changed Behaviors
7. Edge Cases
8. Performance Optimization
9. Final Regression Test
```
---
FINAL ACCEPTANCE CRITERIA
اعتبر المشروع مكتملًا فقط عندما يتحقق:
```text
100% Feature Parity
+
No Known Functional Regression
+
All Critical/High Gaps Fixed
+
All Reachable Flows Verified
+
Fallbacks Preserved
+
Error Handling Preserved
+
Account/Session Semantics Preserved
+
Telegram Behavior Preserved
+
Git Behavior Preserved
+
Performance Improvements Preserved
+
Modular Architecture Preserved
```
وفي النهاية أخرج تقريرًا نهائيًا:
```text
FEATURE PARITY:
REGRESSIONS:
MISSING FEATURES:
PARTIAL FEATURES:
CHANGED BEHAVIORS:
FIXES APPLIED:
PERFORMANCE IMPROVEMENTS:
TEST RESULTS:
REMAINING RISKS:
FINAL STATUS:
```
المبدأ الأساسي:
> `bridge_refactor` يجب أن يكون نسخة أكثر كفاءة وتنظيمًا من النظام الأصلي، وليس نسخة أقل منه.
لا تفترض أن ميزة غير موجودة في Module معين مفقودة؛ تتبع الـ full execution path أولًا.
لا تكتفِ بـ code comparison. المطلوب Functional Equivalence.
