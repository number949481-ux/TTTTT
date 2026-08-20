"""
test_p12_resume_same_project.py
================================
حراسة إصلاحات P12 (مشكلة اللوج المبلغة من المالك):
  «تايم اوت بسبب ملوش لزمه، ولما بيفصل بيقطع مش بيكمل نفس شات —
   بيعمل chat id جديد أصلاً»

الضمانات:
  1. المحرك 01.03: انقطاع البث لا يفقد project_id (ماركر __STREAM_INTERRUPTED__).
  2. المحرك 01.03: لا live stream للترمنال — طباعة كاملة دفعة واحدة + عدد الثواني.
  3. المحرك 01.03: timeout كـ tuple (اتصال، قراءة) = idle-timeout لا قطعاً كلياً.
  4. البريدج 01.31: carry_pid يستأنف نفس المشروع في المحاولات التالية (لا fork جديد).
  5. البريدج 01.31: __STREAM_INTERRUPTED__ يدخل حلقة المتابعة بدل الفشل.
  6. البريدج 01.31: زر المعاينة الحية يُرسل فور معرفة pid في مسار الاستئناف أيضاً.
"""
import pathlib
import re
import sys
import unittest

webapp_dir = pathlib.Path(__file__).resolve().parent.parent
if str(webapp_dir) not in sys.path:
    sys.path.insert(0, str(webapp_dir))

ENGINE_SRC = (webapp_dir / "01.03Genspark_claude-opus-5-code.py").read_text(encoding="utf-8")
BRIDGE_SRC = (webapp_dir / "01.31_telegram_gen_bridge.py").read_text(encoding="utf-8")

# عزل جسم send_chat في المحرك
_start = ENGINE_SRC.index("def send_chat(")
_next = ENGINE_SRC.index("\ndef ", _start + 10)
SEND_CHAT_SRC = ENGINE_SRC[_start:_next]

# عزل جسم send_message_and_make_public في البريدج
_bstart = BRIDGE_SRC.index("def send_message_and_make_public(")
_bnext = BRIDGE_SRC.index("\ndef ", _bstart + 10)
SMAP_SRC = BRIDGE_SRC[_bstart:_bnext]


class TestEngineStreamResilience(unittest.TestCase):
    """1-3: حراسة المحرك 01.03"""

    def test_01_stream_interrupt_returns_pid_not_new_chat(self):
        """انقطاع البث مع pid حي يجب أن يرجع __STREAM_INTERRUPTED__ + نفس الـ pid"""
        self.assertIn("stream_interrupted", SEND_CHAT_SRC)
        self.assertIn('"__STREAM_INTERRUPTED__", proj_id_new', SEND_CHAT_SRC)

    def test_02_final_except_preserves_pid(self):
        """الـ except الخارجي يجب ألا يرجع None للـ pid (كان يسبب chat id جديد)"""
        tail = SEND_CHAT_SRC[SEND_CHAT_SRC.rfind("except Exception as e:"):]
        self.assertIn("return None, proj_id_new, None", tail,
                      "الـ except الأخير يجب أن يعيد proj_id_new وليس None")
        self.assertNotIn("return None, None, None", tail,
                         "ممنوع فقدان project_id في مسار الخطأ العام")

    def test_03_no_terminal_live_stream(self):
        """لا طباعة لحظية chunk-by-chunk في الترمنال — تجميع صامت فقط"""
        self.assertNotIn('print(chunk, end="", flush=True)', SEND_CHAT_SRC,
                         "ممنوع بث chunks للترمنال — الطباعة الكاملة بعد الاكتمال فقط")
        self.assertNotIn("live_started", SEND_CHAT_SRC,
                         "آلية live_started القديمة يجب أن تكون محذوفة بالكامل")

    def test_04_full_response_printed_with_elapsed_seconds(self):
        """الطباعة الكاملة دفعة واحدة + سطر 'اخد X ثانية' بعد الاكتمال"""
        self.assertIn("اخد {_elapsed:.1f} ثانية", SEND_CHAT_SRC)
        self.assertIn("full_text.splitlines()", SEND_CHAT_SRC)

    def test_05_timeout_is_idle_tuple_not_total_cut(self):
        """timeout يجب أن يكون tuple (اتصال، قراءة) مع stream=True — لا قطع كلي"""
        m = re.search(r"^.*sess\.post\(.*ask_proxy.*$", SEND_CHAT_SRC, re.MULTILINE)
        self.assertIsNotNone(m)
        self.assertIn("timeout=(", m.group(0))
        self.assertIn("stream=True", m.group(0))

    def test_06_ticket_file_still_written_incrementally(self):
        """ملف التذكرة يبقى لحظياً (وظيفة أصلية) رغم إلغاء بث الترمنال"""
        self.assertIn("ticket_file.write(chunk)", SEND_CHAT_SRC)
        self.assertIn("ticket_file.flush()", SEND_CHAT_SRC)


class TestBridgeSameProjectResume(unittest.TestCase):
    """4-6: حراسة البريدج 01.31"""

    def test_07_carry_pid_mechanism_exists(self):
        """carry_pid يُلتقط من الـ callback ويُستأنف عليه في المحاولات التالية"""
        self.assertIn("carry_pid = None", SMAP_SRC)
        self.assertIn("_pid_capture_callback", SMAP_SRC)
        self.assertIn("if carry_pid:", SMAP_SRC)
        self.assertIn("project_id = carry_pid", SMAP_SRC)

    def test_08_carry_pid_skips_new_fork(self):
        """عند وجود carry_pid يجب تخطي مسار fork/url بالكامل (elif) — لا مشروع جديد"""
        i_carry = SMAP_SRC.index("if carry_pid:")
        i_elif = SMAP_SRC.index("elif url and isinstance(url, str)")
        self.assertLess(i_carry, i_elif, "carry_pid يجب أن يسبق مسار الـ url/fork ويحجبه")

    def test_09_pid_always_captured_after_send_chat(self):
        """بعد كل send_chat ناجح يثبت الـ pid في carry_pid للمحاولات التالية"""
        self.assertIn("carry_pid = pid", SMAP_SRC)

    def test_10_stream_interrupted_enters_polling_not_fail(self):
        """__STREAM_INTERRUPTED__ يجب أن يحول الحالة لـ RUNNING (متابعة) لا فشل"""
        self.assertIn('answer == "__STREAM_INTERRUPTED__"', SMAP_SRC)
        idx = SMAP_SRC.index('answer == "__STREAM_INTERRUPTED__"')
        window = SMAP_SRC[idx:idx + 400]
        self.assertIn('final_status = "RUNNING"', window,
                      "الانقطاع مع مشروع حي يدخل حلقة المتابعة على نفس الـ pid")

    def test_11_callback_forwarded_always(self):
        """الـ callback الداخلي يُمرر دائماً لـ send_chat (يلتقط الـ pid حتى مع عدم طلب preview)"""
        self.assertIn('"on_project_start_callback": _pid_capture_callback', SMAP_SRC)

    def test_12_live_preview_fires_on_resume_paths(self):
        """زر المعاينة يُطلق فور معرفة الـ pid في مسار الاستئناف ومسار الـ fork (P12-C)"""
        carry_block = SMAP_SRC[SMAP_SRC.index("if carry_pid:"):SMAP_SRC.index("elif url and")]
        self.assertIn("on_project_start_callback(project_id)", carry_block,
                      "مسار carry_pid يجب أن يرسل بطاقة المعاينة فوراً")
        fork_idx = SMAP_SRC.index("project_id = forked_pid or orig_pid")
        fork_block = SMAP_SRC[fork_idx:fork_idx + 500]
        self.assertIn("on_project_start_callback(project_id)", fork_block,
                      "مسار الاستئناف من URL يجب أن يرسل بطاقة المعاينة فوراً")


class TestRuntimeParityAfterP12(unittest.TestCase):
    """التأكد أن bridge_refactor أعيد توليده متزامناً مع P12"""

    def test_13_refactor_contains_p12_fixes(self):
        p06 = (webapp_dir / "bridge_refactor" / "parts" / "p06_engine_flow.py").read_text(encoding="utf-8")
        self.assertIn("carry_pid", p06)
        self.assertIn("__STREAM_INTERRUPTED__", p06)


if __name__ == "__main__":
    unittest.main()
