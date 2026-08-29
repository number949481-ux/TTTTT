# 🤖 GEMINI.md — تعليمات النموذج (مرآة AGENTS.md)

> اقرأ `AGENTS.md` بالكامل — هذا الملف تذكير مختصر بنفس القواعد الإلزامية.

## 📌 قاعدة مركزية [P23]

ملفات الحسابات (`telegram_bot_token.txt`, `accounts_genspark.json`, `.env`,
`project_registry/`, `projects_tree.json`) مكانها الرئيسي الموحد في الفولدر
الكبير (`W___webapp/`) وكل النسخ تقرأ منها تلقائياً عبر `resolve_shared_path`
(محلي أولاً ثم الأب) — **بدون تكرار أو نسخ يدوي**.

## 🛡️ إلزامي

- الملف المعتمد الوحيد: `01.33_telegram_gen_bridge.py` — النسخ الأقدم مرجعية فقط.
- بوابة الجودة قبل أي إغلاق: pytest كامل 100% + `scripts/hadith_sijil.py` Exit 0.
- نقطة الاستئناف الوحيدة المعتمدة: `PROGRESS.md` الجذري.
- التفاصيل الكاملة: `AGENTS.md` + `docs/engineering/V3_RESUME_SESSION.md`.
