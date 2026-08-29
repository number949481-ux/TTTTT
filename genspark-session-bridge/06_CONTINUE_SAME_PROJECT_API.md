# 🔗 06_CONTINUE_SAME_PROJECT_API — الدوال الفعلية لتكملة نفس المشروع من رابط
> موثّق: 2026-08-29 — إجابة رسالة المالك الثالثة في SESSION-GSB-001

## سؤال المالك:
"عاوز الدوال اللي أقدر أخليها تكمل بنفس المشروع — ومثال زي
`genspark.ai/autopilotagent_viewer?id=***` صح ولا غلط؟"

## الجواب المختصر:
✅ الرابط صح **كمصدر للـ Project ID** — لكن التكملة نفسها بتتم بتمرير
الـ PID المستخرج لـ `send_chat(project_id=PID)`. الرابط لوحده مش بيكمّل.

## السلسلة الكاملة (كل الدوال من كود المالك نفسه):

### 1) استخراج + تحقق + تصنيف (01.33_telegram_gen_bridge.py)
| الدالة | السطر | الوظيفة |
|---|---|---|
| `extract_project_id(url_or_id)` | ~2025 | تطلع UUID من `id=` أو من أي UUID في النص — تفهم `agents?id=` و `autopilotagent_viewer?id=` |
| `is_probable_project_id(pid)` | ~4307 | تحقق fullmatch لصيغة UUID 8-4-4-4-12 |
| `parse_project_locator(text)` | ~2050 | SSOT: تصنيف أي نص ➔ `pid` / `malformed` / `none` |
| `detect_context_collision(state, text)` | ~2071 | حارس ضد تنفيذ رابط مشروع (B) كبرومبت على مشروع نشط (A) |

### 2) التكملة المباشرة — نفس الحساب (Fork=False)
`send_chat(...)` في 01.03Genspark_claude-opus-5-code.py سطر ~1761:
```python
answer, live_pid, msg_id = send_chat(
    cookies=cookies,
    question="كمّل...",
    project_id=pid,   # ⬅️ نفس المشروع بتاريخه — Fork=False
    cfg=cfg,
)
```
- داخلياً: `_is_continue = bool(project_id or fork_project_id)` (سطر ~1797)
- مع `cli_history_max == -1` + تكملة ➔ بيلغي history المحلي تماماً
  ويعتمد على سيرفر Genspark (توفير رصيد) = نفس آلية Fetch & Forward.
- فيه كمان باراميتر `fork_project_id=` لو عايز الإرسال نفسه يبدأ بفورك.

### 3) التكملة من حساب تاني (Fork=True)
```python
ensure_public(pid, owner_cookies, cfg)                 # 01.03 سطر ~739
new_pid = create_forked_project(pid, new_cookies, cfg) # 01.03 سطر ~1661
send_chat(new_cookies, question, project_id=new_pid)
```
- `create_forked_project` بيضرب `GET /api/continue_conversation?id=OLD_PID`
  ➔ السيرفر ينشئ فرع كامل (ملفات+سجل) ويرجّع 307 والـ NEW_PID في
  Location header (`/agents?id=NEW_PID`).
- النتيجة: مشروع جديد `Root Project ID = OLD_PID`.

### 4) الالتقاط الحي أثناء البث — carry_pid (01.33 سطر ~2416)
- أي `project_start` أو رجوع من `send_chat` ➔ `carry_pid = live_pid`
- أي retry بعدها ➔ `project_id = carry_pid` (استئناف نفس المشروع، لا شات جديد).

## صيغ الروابط المقبولة (كلها extract_project_id بتفهمها):
```
https://www.genspark.ai/agents?id=<UUID>                 ← رابط الاستئناف (خاص)
https://www.genspark.ai/autopilotagent_viewer?id=<UUID>  ← العارض العام ✅ مثال المالك
<UUID> خام مباشرة                                        ← مقبول برضه
```
⚠️ شرط: الـ id لازم يكون UUID بصيغة 8-4-4-4-12 — لو الرابط من غير UUID
صالح بيتصنّف `malformed` ويترفض.

## خريطة القرار:
```
رابط/نص وارد
  └─ parse_project_locator ➔ kind == "pid"؟
       ├─ نفس الحساب صاحب المشروع؟
       │    └─ نعم ➔ send_chat(project_id=pid)            [Fork=False]
       └─ حساب مختلف؟
            └─ ensure_public ➔ create_forked_project ➔
               send_chat(project_id=new_pid)               [Fork=True]
```
