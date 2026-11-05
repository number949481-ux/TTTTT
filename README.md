# 🚀 Genspark Multi-Project WebApp Bridge System (01.33)

> **Active Version:** `01.33` (`01.33_telegram_gen_bridge.py`)  
> **Core Engine:** `01.03Genspark_claude-opus-5-code.py`  
> **Active Milestone:** `Phase 44 (Resume Pipeline Integrity — سلامة خط أنابيب الاستئناف: Live Rebind + Activity Gate + Stability + Final Fetch)` ✅ shipped (DEC-040 — S72–S78 — ⏸️ BLOCKED-ON-OWNER بانتظار مهمة جديدة) — مع P43 الوضع السريع وتخطي تنزيل الملفات والـ Diff و P42 حارس النية وتدفق الإنشاء الآمن وP41 التوجيه الجنائي للروابط والإغلاق النظيف وP40 المدة المضغوطة ومسار الرفض السريع وP39 بطاقة الاكتمال المبسطة وP38 توحيد إيميل الحساب النشط وP37 بطاقة ملخص الاستئناف من زر إعادة الصياغة وP36 مسار الرفض السريع بالمحرك وP35 كشف رفض الموديل وP34 التنسيق الآمن وP33 أزرار الإجراءات السريعة وP32 استخراج باسورد الحساب وP29–P31 وP28 وP27 وP26 وP25 حيَّة  
> **Test Status:** `974/974 PASS (100% OK)` — Gate Exit Code 0  

---

## 📦 Requirements & Installation

```bash
pip install -r requirements.txt
```

---

## 📖 Architecture & Documentation (Dual-Wing Docs Suite)
* **Engineering Master Guide:** [docs/engineering/README.md](docs/engineering/README.md)
* **Living SSOT Progress Log:** [docs/engineering/PROGRESS.md](docs/engineering/PROGRESS.md)
* **Tests Master Guide & Suite:** [docs/tests/README.md](docs/tests/README.md)
* **Unit Tests Catalog (974 Tests):** [docs/tests/TEST_SUITE_CATALOG.md](docs/tests/TEST_SUITE_CATALOG.md)
* **Zero-Regression Byte Report:** [docs/tests/01.25_REGRESSION_REPORT.md](docs/tests/01.25_REGRESSION_REPORT.md)

---

## 🔄 Account Lifecycle after MAINT-10 (2026-11-04)
* **403 / Private project:** the account is innocent — no vault move, no balance change, `active` untouched; a 5-minute in-place `cooldown_until` and the task stops with `FORBIDDEN` ("make the project **Public** and resend"). No other account is tried.
* **Offline balance filter:** `get_eligible_accounts` skips accounts whose recorded `balance` is a number `< OFFLINE_MIN_BALANCE` (100); `None`/non-numeric values fail open (the live check / 05.02 corrects them).
* **Recorded balance is the real one:** every in-place `LOW_BALANCE` exit writes the actual balance first; `mark_account_cooldown(..., balance=0)` is used only for genuine consumption — `CREDIT_EXHAUSTED`, a real `COMPLETED` (model declines excluded; `last_success_at` is kept), and a user cancel **after** generation started (`BridgeConfig.generation_started`; `/compact` maintenance never raises it). Temporary faults keep the balance as-is.
* **Reactivation after 29h:** `reactivate_account_if_due` restores `active: true`, `cooldown_until: 0` and a default `balance: 100`. **LOCKOUT-FIX (2026-11-05):** an account whose cooldown has expired (`status` cooldown/auth_failed/disabled) is *exempt* from the offline balance filter so it can be claimed and reactivated — otherwise a `balance: 0` written at consumption would lock it out forever. `"FORBIDDEN"` is no longer in `COOLDOWN_VAULT_REASONS` (403 is never vaulted).
* Governing plan: `MAINT-10_MASTER_PLAN.md`; tests: `tests/test_p59_maint10_lifecycle.py`.

---

## ⚡ Quick Start & Clean-Clone Verification

```bash
# 1. Run full unit test suite (974 tests):
python -m unittest discover tests -v

# 2. Automated docs integrity & quality gate:
python scripts/hadith_sijil.py
```
