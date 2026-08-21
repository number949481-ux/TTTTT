import sys
import pathlib
import importlib.util

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

# SSOT: استيراد عقود الموديلات مباشرة من الملف الأساسي 01.32 (Single-File Doctrine)
_bridge_spec = importlib.util.spec_from_file_location("bridge_mod", webapp_dir / "01.32_telegram_gen_bridge.py")
_bridge = importlib.util.module_from_spec(_bridge_spec)
_bridge_spec.loader.exec_module(_bridge)
CONTRACTS = _bridge.CONTRACTS
PROTECTED_MODELS = _bridge.PROTECTED_MODELS
ALIASES = _bridge.MODEL_ALIASES
CONTRACT_VERSION = _bridge.CONTRACT_VERSION

docs_dir = webapp_dir / "docs"
docs_dir.mkdir(exist_ok=True)
doc_file = docs_dir / "model_contracts.md"

lines = [
    "# 📜 Genspark Model Contracts Specification",
    "",
    f"> **Version:** `{CONTRACT_VERSION}`  ",
    "> **Status:** `LOCALLY_VERIFIED` ✅  ",
    "> **Last Generated:** Auto-generated from `01.32_telegram_gen_bridge.py` (SSOT)",
    "",
    "---",
    "",
    "## 🤖 Active Model Contracts",
    "",
    "| Model Slug | `models` Payload | `use_model` | `ai_chat_model` | `client_message_id` | Status |",
    "|---|---|---|---|---|---|",
]

for slug, (models, use_model, ai_chat, needs_id) in CONTRACTS.items():
    models_str = f"`{models}`"
    use_str = f"`{use_model}`" if use_model else "—"
    ai_str = f"`{ai_chat}`" if ai_chat else "—"
    id_str = "✅ Yes" if needs_id else "—"
    lines.append(f"| `{slug}` | {models_str} | {use_str} | {ai_str} | {id_str} | `LOCALLY_VERIFIED` |")

lines.extend([
    "",
    "---",
    "",
    "## 🛡️ Protected Models (Special Payload Block)",
    "",
    "| Model Slug | Description | Routing Policy |",
    "|---|---|---|",
])

for p in sorted(PROTECTED_MODELS):
    lines.append(f"| `{p}` | Special direct payload (`type: ai_chat`) | Unchanged native bypass |")

lines.extend([
    "",
    "---",
    "",
    "## 🔀 Supported Aliases & Display Names",
    "",
    "| Input Alias / Display Name | Target Canonical Slug |",
    "|---|---|",
])

for alias, target in sorted(ALIASES.items()):
    lines.append(f"| `{alias}` | `{target}` |")

doc_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Docs generated successfully at: {doc_file}")
