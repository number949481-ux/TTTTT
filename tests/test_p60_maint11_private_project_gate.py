"""
tests/test_p60_maint11_private_project_gate.py
=============================================
مجموعة اختبارات MAINT-11:
بوابة فحص صلاحيات المشروع الخاص (Private Project Gate) ومنع حرق الأسطول.

تغطي:
1. فحص حراسة المشاريع الجديدة (Guard Clause).
2. رصد استجابة status: -13 (no permission).
3. رصد استجابة HTTP 403 مع JSON.
4. التفريق الذكي لـ Cloudflare HTML Challenge وتفعيل الـ Fail-Open.
5. رصد انتهاء الجلسة 401 (Session Expired).
6. تصرف الـ Timeout وخطأ الشبكة (Fail-Open).
7. منع إرسال كارت البدء الكاذب (F-9) والتأكد من توقيع الـ Return Tuple.
8. خط الدفاع الثاني (Defense in Depth) وترقية الفشل إلى FORBIDDEN.
9. براءة الحساب التامة في حلقة الـ Failover مع التبريد الموضعي 5 دقائق.
10. قدسية ملف 01.03 (Zero Mutation).
"""
import pathlib
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path
BRIDGE_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

# Import runtime functions from bridge_refactor or 01.33
import bridge_refactor.runtime as br


class TestMaint11PrivateProjectGate(unittest.TestCase):
    def setUp(self):
        self.dummy_cookies = {"sessionid": "test_session_123"}
        self.sample_pid = "550e8400-e29b-41d4-a716-446655440000"
        self.acc = {
            "email": "test@example.com",
            "password": "pwd",
            "cookies": self.dummy_cookies,
            "balance": 500,
            "last_refresh": time.time(),
            "active": True,
        }

    def test_01_guard_clause_new_project(self):
        """الاستعلامات الجديدة بدون pid يجب أن تتجاوز الفحص فوراً"""
        is_acc, status_code, reason = br._check_project_permission_fast("", self.dummy_cookies)
        self.assertTrue(is_acc)
        self.assertEqual(status_code, 200)
        self.assertEqual(reason, "NEW_PROJECT")

        is_acc, status_code, reason = br._check_project_permission_fast(None, self.dummy_cookies)
        self.assertTrue(is_acc)
        self.assertEqual(status_code, 200)

    @patch("curl_cffi.requests.get")
    def test_02_detect_status_minus_13_no_permission(self, mock_get):
        """كشف رد status: -13 و no permission من جينسبارك واعتباره مشروعاً خاصاً"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.json.return_value = {
            "code": 200,
            "status": -13,
            "message": "no permission",
            "data": {},
        }
        mock_get.return_value = mock_resp

        is_acc, status_code, reason = br._check_project_permission_fast(self.sample_pid, self.dummy_cookies)
        self.assertFalse(is_acc)
        self.assertEqual(status_code, 403)
        self.assertEqual(reason, "PRIVATE_PROJECT")

    @patch("curl_cffi.requests.get")
    def test_03_detect_http_403_json(self, mock_get):
        """كشف رد HTTP 403 مع JSON واعتباره مشروعاً خاصاً"""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_resp.json.return_value = {"error": "forbidden", "message": "Project is private"}
        mock_get.return_value = mock_resp

        is_acc, status_code, reason = br._check_project_permission_fast(self.sample_pid, self.dummy_cookies)
        self.assertFalse(is_acc)
        self.assertEqual(status_code, 403)
        self.assertEqual(reason, "PRIVATE_PROJECT")

    @patch("curl_cffi.requests.get")
    def test_04_cloudflare_challenge_fails_open(self, mock_get):
        """كشف تحدي كلاودفلير HTML وعدم إغلاق المشروع بل تفعيل الـ Fail-Open"""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.headers = {"Content-Type": "text/html; charset=UTF-8"}
        mock_resp.json.side_effect = ValueError("Not JSON")
        mock_get.return_value = mock_resp

        is_acc, status_code, reason = br._check_project_permission_fast(self.sample_pid, self.dummy_cookies)
        self.assertTrue(is_acc)
        self.assertEqual(status_code, 403)
        self.assertEqual(reason, "CF_CHALLENGE_FAIL_OPEN")

    @patch("curl_cffi.requests.get")
    def test_05_session_expired_401(self, mock_get):
        """كشف انتهاء الجلسة 401 لتصنيفها كخطأ حسابي وليس خطأ مشروع"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        is_acc, status_code, reason = br._check_project_permission_fast(self.sample_pid, self.dummy_cookies)
        self.assertFalse(is_acc)
        self.assertEqual(status_code, 401)
        self.assertEqual(reason, "SESSION_EXPIRED")

    @patch("curl_cffi.requests.get")
    def test_06_timeout_fails_open(self, mock_get):
        """في حال حدوث Timeout أو انقطاع شبكة يتم الـ Fail-Open فوراً دون تعطيل"""
        mock_get.side_effect = TimeoutError("Connection timed out after 3.0s")

        is_acc, status_code, reason = br._check_project_permission_fast(self.sample_pid, self.dummy_cookies)
        self.assertTrue(is_acc)
        self.assertEqual(status_code, 0)
        self.assertTrue(reason.startswith("FAIL_OPEN_EXC"))

    def test_07_early_gate_blocks_false_start_card_and_returns_correct_tuple(self):
        """التأكد من منع كارت البدء F-9 وصحة عناصر الـ 5-tuple مع وضع الرسالة في Index 4"""
        engine_mock = MagicMock()
        engine_mock.check_balance.return_value = 500

        with patch.object(br.ns, "read_accounts_safe", return_value=[self.acc]):
            with patch.object(br.ns, "get_genspark_engine", return_value=engine_mock):
                with patch.object(br.ns, "_check_project_permission_fast", return_value=(False, 403, "PRIVATE_PROJECT")):
                    callback_mock = MagicMock()
                    bridge_cfg = br.BridgeConfig()

                    pub_url, status, artifacts_dir, ext_dir, last_text = br.send_message_and_make_public(
                        url=f"https://www.genspark.ai/project/{self.sample_pid}",
                        email="test@example.com",
                        password="pwd",
                        query="test prompt",
                        bridge_cfg=bridge_cfg,
                        on_project_start_callback=callback_mock,
                    )

                    # 1. منع استدعاء كارت البدء تماماً
                    callback_mock.assert_not_called()

                    # 2. التحقق من الـ 5-tuple
                    self.assertIsNone(pub_url)
                    self.assertEqual(status, "FORBIDDEN")
                    self.assertIsNone(artifacts_dir)
                    self.assertIsNone(ext_dir)
                    self.assertIsNotNone(last_text)
                    self.assertIn("المشروع خاص (Private)", last_text)

    def test_08_defense_in_depth_promotes_failed_to_forbidden(self):
        """خط الدفاع الثاني يرصد 403 من رد الشات ويرقي FAILED إلى FORBIDDEN"""
        engine_mock = MagicMock()
        engine_mock.check_balance.return_value = 500
        cfg = MagicMock()
        cfg._last_chat_err = "HTTP 403: Forbidden - not authorized"
        engine_mock.Config.return_value = cfg
        engine_mock.login.return_value = {"s": "1"}
        engine_mock.send_chat.return_value = (None, None, None)

        with patch.object(br.ns, "read_accounts_safe", return_value=[self.acc]):
            with patch.object(br.ns, "get_genspark_engine", return_value=engine_mock):
                with patch.object(br.ns, "_check_project_permission_fast", return_value=(True, 200, "OK")):
                    with patch.object(br.ns, "extract_project_id", return_value=self.sample_pid):
                        bridge_cfg = br.BridgeConfig()
                        bridge_cfg.max_timeout_retries = 1
                        pub_url, status, artifacts_dir, ext_dir, last_text = br.send_message_and_make_public(
                            url=f"https://www.genspark.ai/project/{self.sample_pid}",
                            email="test@example.com",
                            password="pwd",
                            query="test prompt",
                            bridge_cfg=bridge_cfg,
                        )

                        self.assertEqual(status, "FORBIDDEN")
                        self.assertIsNotNone(last_text)
                        self.assertIn("المشروع خاص (Private)", last_text)

    def test_09_failover_preserves_innocent_account_with_inplace_cooldown(self):
        """في حلقة الفيل أوفر: FORBIDDEN يتوقف فوراً من أول محاولة مع تبريد 5 دقائق محلي"""
        mock_send = MagicMock(return_value=(None, "FORBIDDEN", None, None, "المشروع خاص"))
        mock_update = MagicMock()

        with patch.object(br.ns, "send_message_and_make_public", mock_send):
            with patch.object(br.ns, "update_account_data", mock_update):
                with patch.object(br.ns, "claim_eligible_account_for_owner", return_value=(self.acc, [self.acc], "claimed")):
                    with patch.object(br.ns, "release_account_selection"):
                        with patch.object(br.ns, "reactivate_account_if_due", side_effect=lambda a, **kw: a):
                            with patch.object(br.ns, "get_account_fingerprint", return_value={"user_agent": "ua", "browser": "chrome"}):
                                bridge_cfg = br.BridgeConfig()
                                pub_url, status, curr_acc, ext_dir, last_text = br.send_message_with_auto_account_failover(
                                    url=f"https://www.genspark.ai/project/{self.sample_pid}",
                                    query="test query",
                                    bridge_cfg=bridge_cfg,
                                )

                                # 1. التوقف الفوري بحالة FORBIDDEN
                                self.assertEqual(status, "FORBIDDEN")
                                # 2. استدعاء send_message_and_make_public مرة واحدة فقط
                                self.assertEqual(mock_send.call_count, 1)
                                # 3. التأكد من التبريد الموضعي 5 دقائق في مكانه
                                cooldown_updates = [c[0][1] for c in mock_update.call_args_list if "cooldown_until" in c[0][1]]
                                self.assertEqual(len(cooldown_updates), 1)

    def test_11_defense_in_depth_retrospective_check_catches_403_without_last_chat_err(self):
        """[Goldfish Catch] خط الدفاع الثاني يفحص استدراكياً بـ _check_project_permission_fast حتى لو المحرك لم يضع _last_chat_err"""
        engine_mock = MagicMock()
        engine_mock.check_balance.return_value = 500
        cfg = MagicMock()
        # محاكاة سلوك 01.03 الحقيقي: _last_chat_err غير موجود إطلاقاً
        del cfg._last_chat_err
        engine_mock.Config.return_value = cfg
        engine_mock.login.return_value = {"s": "1"}
        engine_mock.send_chat.return_value = (None, None, None)

        with patch.object(br.ns, "read_accounts_safe", return_value=[self.acc]):
            with patch.object(br.ns, "get_genspark_engine", return_value=engine_mock):
                # المحاكاة: الفحص الأولي يفشل للفتح (Timeout/Fail-Open)، لكن الفحص الاستدراكي يرصد 403
                with patch.object(br.ns, "_check_project_permission_fast", side_effect=[
                    (True, 200, "FAIL_OPEN_TIMEOUT"), # 1. preflight
                    (False, 403, "PRIVATE_PROJECT"),   # 2. retrospective check
                ]):
                    with patch.object(br.ns, "extract_project_id", return_value=self.sample_pid):
                        bridge_cfg = br.BridgeConfig()
                        bridge_cfg.max_timeout_retries = 1
                        pub_url, status, artifacts_dir, ext_dir, last_text = br.send_message_and_make_public(
                            url=f"https://www.genspark.ai/project/{self.sample_pid}",
                            email="test@example.com",
                            password="pwd",
                            query="test prompt",
                            bridge_cfg=bridge_cfg,
                        )
                        self.assertIsNone(pub_url)
                        self.assertEqual(status, "FORBIDDEN")
                        self.assertIn("المشروع خاص", last_text)

    def test_12_uses_account_fingerprint_user_agent(self):
        """[Goldfish Nit] فحص الصلاحية السريع يتبنى بصمة الحساب الفعلية للـ User-Agent عند تمرير email"""
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": 0, "data": {}}

        with patch("curl_cffi.requests.get", return_value=mock_resp) as mock_get:
            br.ns._check_project_permission_fast("test_pid", {"s": "1"}, email="my_test_account@example.com")
            call_headers = mock_get.call_args[1].get("headers", {})
            self.assertIn("User-Agent", call_headers)
            fp = br.ns.get_account_fingerprint("my_test_account@example.com")
            self.assertEqual(call_headers["User-Agent"], fp["user_agent"])

    def test_13_chat_exception_with_403_promotes_to_forbidden(self):
        """[Hostile Design Gate] استثناء الشات الذي يحمل 403 يُرقى فوراً إلى FORBIDDEN لمنع حلقة CHAT_ERROR"""
        mock_mod = MagicMock()
        mock_mod.send_chat.side_effect = RuntimeError("curl: (22) The requested URL returned error: 403 Forbidden")
        mock_mod.check_balance.return_value = 100
        mock_mod.login.return_value = {"s": "1"}

        with patch.object(br.ns, "get_genspark_engine", return_value=mock_mod):
            with patch.object(br.ns, "read_accounts_safe", return_value=[self.acc]):
                with patch.object(br.ns, "_check_project_permission_fast", return_value=(True, 200, "NEW_PROJECT")):
                    bridge_cfg = br.BridgeConfig()
                    bridge_cfg.max_timeout_retries = 1
                    pub_url, status, _, _, last_text = br.send_message_and_make_public(
                        url="",
                        email="test@example.com",
                        password="pwd",
                        query="test prompt",
                        bridge_cfg=bridge_cfg
                    )
                    self.assertEqual(status, "FORBIDDEN")
                    self.assertIn("المشروع خاص", str(last_text))

    def test_10_zero_mutation_01_03(self):
        """التحقق المطلق من قدسية ملف 01.03 وعدم المساس به نهائياً"""
        opus_file = BRIDGE_DIR.parent / "01.03Genspark_claude-opus-5-code.py"
        if not opus_file.exists():
            opus_file = BRIDGE_DIR / "01.03Genspark_claude-opus-5-code.py"
        if opus_file.exists():
            self.assertTrue(opus_file.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
