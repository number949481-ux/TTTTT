#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_p11_button_styles.py
===============================
حراسة صارمة لميزة ألوان الأزرار (Telegram Bot API 9.4 — Button Styles):
1. الـ Whitelist الرسمية الوحيدة: primary / success / danger.
2. أي قيمة خارج الـ Whitelist (positive/destructive/...) تُحذف نهائياً
   لأنها ترجع 400 invalid button style من تيليجرام.
3. الحقل style يمرر فقط عندما يكون صالحاً، ولا يكسر الأزرار القديمة بدونه.
4. أزرار المعاينة الحية والإلغاء والاستئناف ملونة بالأنماط الصحيحة.
"""

import sys
import json
import pathlib
import unittest
import importlib.util

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

_spec = importlib.util.spec_from_file_location("bridge_mod_p11", webapp_dir / "01.31_telegram_gen_bridge.py")
_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bridge)

make_inline_keyboard = _bridge.make_inline_keyboard
ALLOWED_BUTTON_STYLES = _bridge.ALLOWED_BUTTON_STYLES
build_live_preview_keyboard = _bridge.build_live_preview_keyboard


class TestButtonStylesWhitelist(unittest.TestCase):
    """حراسة الـ Whitelist الرسمية لأنماط الألوان"""

    def test_01_whitelist_exact_official_values(self):
        """1. الـ Whitelist يجب أن تكون بالظبط القيم الرسمية الثلاثة في Bot API 9.4"""
        self.assertEqual(ALLOWED_BUTTON_STYLES, frozenset({"primary", "success", "danger"}))

    def test_02_valid_style_passes_through(self):
        """2. style صالح يمرر كما هو في الـ JSON النهائي"""
        kb = make_inline_keyboard([[{"text": "✅ تأكيد", "callback_data": "ok", "style": "success"}]])
        self.assertEqual(kb["inline_keyboard"][0][0]["style"], "success")

    def test_03_invalid_style_is_stripped(self):
        """3. أي style خارج الـ Whitelist يُحذف (positive/destructive ترجع 400 من تيليجرام)"""
        for bad in ("positive", "destructive", "green", "red", "blue", "SUCCESS!", "primary "):
            bad_clean = bad.strip().lower()
            kb = make_inline_keyboard([[{"text": "زر", "callback_data": "x", "style": bad}]])
            btn = kb["inline_keyboard"][0][0]
            if bad_clean in ALLOWED_BUTTON_STYLES:
                self.assertEqual(btn.get("style"), bad_clean)
            else:
                self.assertNotIn("style", btn, f"style غير صالح '{bad}' كان يجب حذفه!")

    def test_04_style_normalized_case_and_spaces(self):
        """4. التطبيع: 'Danger' و ' SUCCESS ' تتحول للقيمة الرسمية الصغيرة"""
        kb = make_inline_keyboard([[
            {"text": "أ", "callback_data": "a", "style": "Danger"},
            {"text": "ب", "callback_data": "b", "style": " SUCCESS "},
            {"text": "ج", "callback_data": "c", "style": "PRIMARY"},
        ]])
        styles = [b["style"] for b in kb["inline_keyboard"][0]]
        self.assertEqual(styles, ["danger", "success", "primary"])

    def test_05_buttons_without_style_unchanged(self):
        """5. عدم الانحدار: الأزرار القديمة بدون style تعمل كما هي بدون أي حقل زائد"""
        kb = make_inline_keyboard([[{"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"}]])
        btn = kb["inline_keyboard"][0][0]
        self.assertEqual(btn, {"text": "📁 مشاريعي", "callback_data": "cmd:list_projects"})

    def test_06_style_json_serializable(self):
        """6. الكيبورد الملون قابل للتسلسل JSON خام (مسار reply_markup المباشر بدون مكتبة)"""
        kb = make_inline_keyboard([[{"text": "🌐 فتح", "url": "https://example.com", "style": "primary"}]])
        raw = json.dumps(kb, ensure_ascii=False)
        parsed = json.loads(raw)
        self.assertEqual(parsed["inline_keyboard"][0][0]["style"], "primary")

    def test_07_no_icon_custom_emoji_leakage(self):
        """7. حظر تسريب icon_custom_emoji_id (يتطلب Premium) — لا يمرر أبداً"""
        kb = make_inline_keyboard([[{
            "text": "زر", "callback_data": "x",
            "style": "success", "icon_custom_emoji_id": "12345",
        }]])
        self.assertNotIn("icon_custom_emoji_id", kb["inline_keyboard"][0][0])


class TestColoredKeyboardsIntegration(unittest.TestCase):
    """حراسة تلوين الأزرار الرئيسية في كيبوردات البوت"""

    def test_08_live_preview_running_is_primary_blue(self):
        """8. زر المعاينة الحية أثناء البناء = أزرق (primary)"""
        kb = build_live_preview_keyboard("proj_123", status="running")
        btn = kb["inline_keyboard"][0][0]
        self.assertEqual(btn.get("style"), "primary")
        self.assertIn("url", btn)

    def test_09_live_preview_done_is_success_green(self):
        """9. زر المشروع المكتمل = أخضر (success)"""
        kb = build_live_preview_keyboard("proj_123", status="done")
        btn = kb["inline_keyboard"][0][0]
        self.assertEqual(btn.get("style"), "success")

    def test_10_source_has_no_invalid_style_literals(self):
        """10. فحص شفرة المصدر: لا توجد أي قيمة style غير رسمية مكتوبة حرفياً"""
        src = (webapp_dir / "01.31_telegram_gen_bridge.py").read_text(encoding="utf-8")
        import re
        for m in re.finditer(r'"style"\s*:\s*"([^"]+)"', src):
            val = m.group(1)
            self.assertIn(val, ("primary", "success", "danger"),
                          f"قيمة style غير رسمية في المصدر: '{val}' — سترجع 400 من تيليجرام!")


if __name__ == "__main__":
    unittest.main()
