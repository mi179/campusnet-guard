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

    def test_error_text_prefers_error_and_flattens_newlines(self):
        result = SimpleNamespace(error="bad\nthing", body="fallback")

        self.assertEqual(auth_service.error_text(result), "bad thing")

    def test_response_message_prefers_message_then_result(self):
        parse = Mock(return_value={"result": "ok"})
        network_login = fake_network_login(parse_login_response=parse)

        with patch.dict("sys.modules", {"cyber_lobster.network_login": network_login}):
            message = auth_service.response_message("{}")

        self.assertEqual(message, "ok")
