"""CLI 入口行为测试。"""

import importlib
import sys
from types import ModuleType
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from cyber_lobster.config import GlobalConfig


class FakePortalCredentials:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def import_cli():
    sys.modules.pop("cyber_lobster.cli", None)
    return importlib.import_module("cyber_lobster.cli")


def fake_network_login(**overrides):
    module = SimpleNamespace(
        PortalCredentials=FakePortalCredentials,
        login_with_session_retry=lambda *args, **kwargs: None,
        logout=lambda *args, **kwargs: None,
        parse_login_response=lambda *args, **kwargs: {},
        DEFAULT_HOST="172.16.54.18",
        DEFAULT_SERVICE="DX",
    )
    for name, value in overrides.items():
        setattr(module, name, value)
    return module


class TestCliMain(TestCase):
    def test_friendly_aliases_are_registered(self):
        cli = import_cli()
        for command in ("menu", "add", "list", "start", "test", "doctor", "help", "storage", "autostart"):
            self.assertIn(command, cli.COMMANDS)

    def test_parser_accepts_friendly_aliases(self):
        cli = import_cli()
        parser = cli.build_parser()
        for command in ("menu", "add", "list", "start", "test", "doctor", "help", "storage", "autostart"):
            args = parser.parse_args([command])
            self.assertEqual(args.command, command)

    def test_parser_accepts_autostart_actions(self):
        cli = import_cli()
        parser = cli.build_parser()
        args = parser.parse_args(["autostart", "enable", "--mode", "gui"])
        self.assertEqual(args.command, "autostart")
        self.assertEqual(args.action, "enable")
        self.assertEqual(args.mode, "gui")

    def test_parser_accepts_campus_network_service(self):
        cli = import_cli()
        parser = cli.build_parser()
        args = parser.parse_args(["login", "u1", "--service", "校园网"])
        self.assertEqual(args.service, "校园网")

    def test_no_args_enters_menu_entry(self):
        cli = import_cli()
        fake_menu = SimpleNamespace(main=lambda: 23)
        with patch.dict(sys.modules, {"cyber_lobster.menu": fake_menu}):
            with self.assertRaises(SystemExit) as raised:
                cli.main([])

        self.assertEqual(raised.exception.code, 23)

    def test_no_args_does_not_import_legacy_exe_main(self):
        cli = import_cli()
        sys.modules.pop("exe_main", None)
        fake_menu = SimpleNamespace(main=lambda: 0)

        with patch.dict(sys.modules, {"cyber_lobster.menu": fake_menu}):
            with self.assertRaises(SystemExit):
                cli.main([])

        self.assertNotIn("exe_main", sys.modules)

    def test_switch_with_login_logs_out_and_verifies_new_account(self):
        cli = import_cli()
        cfg = GlobalConfig(
            current_user_id="old",
            accounts={
                "old": {"password": "oldpw", "service": "DX", "host": "portal"},
                "new": {"password": "newpw", "service": "LT", "host": "portal"},
            },
        )
        args = SimpleNamespace(user_id="new", login=True, no_logout=False)
        login_result = SimpleNamespace(success=True, body='{"result": "ok"}', error="")
        logout_result = SimpleNamespace(success=True, body="", error="")
        logout = Mock(return_value=logout_result)
        login = Mock(return_value=login_result)
        network_login = fake_network_login(
            logout=logout,
            login_with_session_retry=login,
        )

        with patch.dict(sys.modules, {"cyber_lobster.network_login": network_login}):
            with patch.object(cli, "load_config", return_value=cfg):
                with patch.object(cli, "save_config", return_value=True) as save:
                    code = cli.cmd_switch(args)

        self.assertEqual(code, 0)
        self.assertEqual(cfg.current_user_id, "new")
        save.assert_called_once_with(cfg)
        logout.assert_called_once_with(host="portal")
        login.assert_called_once()

    def test_switch_no_logout_skips_old_account_logout(self):
        cli = import_cli()
        cfg = GlobalConfig(
            current_user_id="old",
            accounts={
                "old": {"password": "oldpw", "service": "DX", "host": "portal"},
                "new": {"password": "newpw", "service": "LT", "host": "portal"},
            },
        )
        args = SimpleNamespace(user_id="new", login=False, no_logout=True)

        with patch.object(cli, "logout_host") as logout:
            with patch.object(cli, "load_config", return_value=cfg):
                with patch.object(cli, "save_config", return_value=True):
                    code = cli.cmd_switch(args)

        self.assertEqual(code, 0)
        self.assertEqual(cfg.current_user_id, "new")
        logout.assert_not_called()

    def test_doctor_without_accounts_guides_user_to_add(self):
        cli = import_cli()
        cfg = GlobalConfig()

        with patch.object(cli, "load_config", return_value=cfg):
            code = cli.cmd_doctor(SimpleNamespace())

        self.assertEqual(code, 1)

    def test_help_command_prints_builtin_guide(self):
        cli = import_cli()
        code = cli.cmd_help(SimpleNamespace())
        self.assertEqual(code, 0)

    def test_autostart_enable_updates_system_and_config(self):
        cli = import_cli()
        cfg = GlobalConfig(auto_start=False, auto_auth=False)
        startup_module = ModuleType("cyber_lobster.startup")
        startup_module.StartupError = RuntimeError
        startup_module.enable_startup = Mock(
            return_value=SimpleNamespace(
                supported=True,
                enabled=True,
                command='"app.exe" --autostart',
                location="HKCU\\Run\\CyberLobster",
            )
        )
        startup_module.disable_startup = Mock()
        startup_module.get_startup_status = Mock()

        with patch.dict(sys.modules, {"cyber_lobster.startup": startup_module}):
            with patch.object(cli, "load_config", return_value=cfg):
                with patch.object(cli, "save_config", return_value=True) as save:
                    code = cli.cmd_autostart(SimpleNamespace(action="enable", mode="gui"))

        self.assertEqual(code, 0)
        self.assertTrue(cfg.auto_start)
        self.assertTrue(cfg.auto_auth)
        startup_module.enable_startup.assert_called_once_with(mode="gui")
        save.assert_called_once_with(cfg)

    def test_autostart_disable_updates_system_and_config(self):
        cli = import_cli()
        cfg = GlobalConfig(auto_start=True, auto_auth=True)
        startup_module = ModuleType("cyber_lobster.startup")
        startup_module.StartupError = RuntimeError
        startup_module.enable_startup = Mock()
        startup_module.disable_startup = Mock(
            return_value=SimpleNamespace(
                supported=True,
                enabled=False,
                command="",
                location="HKCU\\Run\\CyberLobster",
            )
        )
        startup_module.get_startup_status = Mock()

        with patch.dict(sys.modules, {"cyber_lobster.startup": startup_module}):
            with patch.object(cli, "load_config", return_value=cfg):
                with patch.object(cli, "save_config", return_value=True) as save:
                    code = cli.cmd_autostart(SimpleNamespace(action="disable", mode="gui"))

        self.assertEqual(code, 0)
        self.assertFalse(cfg.auto_start)
        self.assertTrue(cfg.auto_auth)
        startup_module.disable_startup.assert_called_once_with()
        save.assert_called_once_with(cfg)

    def test_logout_uses_network_logout(self):
        cli = import_cli()
        logout_result = SimpleNamespace(success=True, body='{"result": "ok"}', error="")
        logout = Mock(return_value=logout_result)
        network_login = fake_network_login(logout=logout)

        with patch.dict(sys.modules, {"cyber_lobster.network_login": network_login}):
            code = cli.cmd_logout(SimpleNamespace(host="portal"))

        self.assertEqual(code, 0)
        logout.assert_called_once_with(host="portal")

    def test_login_current_uses_saved_account(self):
        cli = import_cli()
        cfg = GlobalConfig(
            current_user_id="u1",
            accounts={"u1": {"password": "secret", "service": "DX", "host": "portal"}},
        )
        login_result = SimpleNamespace(success=True, body='{"result": "ok"}', error="")
        login = Mock(return_value=login_result)
        network_login = fake_network_login(login_with_session_retry=login)

        with patch.dict(sys.modules, {"cyber_lobster.network_login": network_login}):
            with patch.object(cli, "load_config", return_value=cfg):
                code = cli.cmd_login(SimpleNamespace(current=True, user_id="", password="", service="DX", host="portal"))

        self.assertEqual(code, 0)
        login.assert_called_once()

    def test_login_manual_prompts_password_and_calls_login_service(self):
        cli = import_cli()
        login_result = SimpleNamespace(success=True, body='{"result": "ok"}', error="")

        with patch.object(cli.getpass, "getpass", return_value="hidden") as getpass:
            with patch.object(cli, "login_plain", return_value=login_result) as login:
                with patch.object(cli, "parse_response", return_value={"result": "ok"}):
                    code = cli.cmd_login(
                        SimpleNamespace(
                            current=False,
                            user_id="u1",
                            service="LT",
                            host="portal",
                        )
                    )

        self.assertEqual(code, 0)
        getpass.assert_called_once()
        login.assert_called_once_with(
            "u1",
            "hidden",
            "LT",
            "portal",
            max_session_attempts=3,
            request_retries=3,
        )

    def test_login_without_args_prints_usage_without_network_dependency(self):
        cli = import_cli()
        sys.modules.pop("cyber_lobster.network_login", None)
        code = cli.cmd_login(SimpleNamespace(current=False, user_id="", password="", service="DX", host="portal"))

        self.assertEqual(code, 1)
        self.assertNotIn("cyber_lobster.network_login", sys.modules)

    def test_verify_missing_password_does_not_attempt_network_login(self):
        cli = import_cli()
        cfg = GlobalConfig(
            current_user_id="u1",
            accounts={"u1": {"password": "", "service": "DX", "host": "portal"}},
        )

        with patch.object(cli, "load_config", return_value=cfg):
            with patch.object(cli, "login_account") as login:
                code = cli.cmd_verify(SimpleNamespace(user_id=""))

        self.assertEqual(code, 1)
        login.assert_not_called()

    def test_watch_without_accounts_returns_error(self):
        cli = import_cli()
        with patch.object(cli, "load_config", return_value=GlobalConfig()):
            code = cli.cmd_watch(SimpleNamespace(interval=1, timeout=0.1))

        self.assertEqual(code, 1)
