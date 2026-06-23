"""Shared authentication service tests."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from cyber_lobster.config import AccountConfig
from cyber_lobster import auth_service


class FakePortalCredentials:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def fake_network_login(**overrides):
    module = SimpleNamespace(
        PortalCredentials=FakePortalCredentials,
        login_with_session_retry=Mock(),
        logout=Mock(),
        parse_login_response=Mock(return_value={}),
    )
    for name, value in overrides.items():
        setattr(module, name, value)
    return module


class TestAuthService(TestCase):
    def test_password_available_requires_decrypted_password(self):
        self.assertFalse(auth_service.password_available(AccountConfig(user_id="u1", password="")))
        self.assertTrue(auth_service.password_available(AccountConfig(user_id="u1", password="pw")))

    def test_credentials_from_account_is_lazy_and_preserves_query_string(self):
        network_login = fake_network_login()
        account = AccountConfig(
            user_id="u1",
            password="pw",
            service="校园网",
            host="portal",
            query_string="wlanuserip=1.2.3.4",
        )

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            creds = auth_service.credentials_from_account(account)

        self.assertEqual(creds.user_id, "u1")
        self.assertEqual(creds.password, "pw")
        self.assertEqual(creds.service, "校园网")
        self.assertEqual(creds.query_string, "wlanuserip=1.2.3.4")

    def test_login_account_uses_account_host_and_query_string(self):
        login = Mock(return_value=SimpleNamespace(success=True, body="{}", error=""))
        network_login = fake_network_login(login_with_session_retry=login)
        account = AccountConfig(
            user_id="u1",
            password="pw",
            service="LT",
            host="portal",
            query_string="qs",
        )

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            result = auth_service.login_account(account, max_session_attempts=1, request_retries=2)

        self.assertTrue(result.success)
        login.assert_called_once()
        creds = login.call_args.args[0]
        self.assertEqual(creds.user_id, "u1")
        self.assertEqual(creds.password, "pw")
        self.assertEqual(creds.service, "LT")
        self.assertEqual(creds.query_string, "qs")
        self.assertEqual(login.call_args.kwargs["host"], "portal")

    def test_login_plain_uses_host_and_retry_options(self):
        login = Mock(return_value=SimpleNamespace(success=True, body="{}", error=""))
        network_login = fake_network_login(login_with_session_retry=login)

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            result = auth_service.login_plain(
                "u1",
                "pw",
                "DX",
                "portal",
                max_session_attempts=3,
                request_retries=4,
            )

        self.assertTrue(result.success)
        login.assert_called_once()
        creds = login.call_args.args[0]
        self.assertEqual(creds.user_id, "u1")
        self.assertEqual(creds.password, "pw")
        self.assertEqual(creds.service, "DX")
        self.assertEqual(login.call_args.kwargs["host"], "portal")
        self.assertEqual(login.call_args.kwargs["max_session_attempts"], 3)
        self.assertEqual(login.call_args.kwargs["request_retries"], 4)

    def test_logout_host_delegates_to_network_logout(self):
        logout = Mock(return_value=SimpleNamespace(success=True, body="{}", error=""))
        network_login = fake_network_login(logout=logout)

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            result = auth_service.logout_host("portal")

        self.assertTrue(result.success)
        logout.assert_called_once_with(host="portal")

    def test_error_text_prefers_error_and_flattens_newlines(self):
        result = SimpleNamespace(error="bad\nthing", body="fallback")

        self.assertEqual(auth_service.error_text(result), "bad thing")

    def test_response_message_prefers_message_then_result(self):
        parse = Mock(return_value={"result": "ok"})
        network_login = fake_network_login(parse_login_response=parse)

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            message = auth_service.response_message("{}")

        self.assertEqual(message, "ok")
