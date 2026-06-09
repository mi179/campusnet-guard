"""Interactive EXE entry point behavior tests."""

import importlib
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch


def import_exe_main():
    sys.modules.pop("exe_main", None)
    fake_network_login = SimpleNamespace(
        PortalCredentials=object,
        login_with_session_retry=lambda *args, **kwargs: None,
        parse_login_response=lambda *args, **kwargs: {},
        DEFAULT_HOST="172.16.54.18",
    )
    with patch.dict(sys.modules, {"cyber_lobster.network_login": fake_network_login}):
        return importlib.import_module("exe_main")


class TestExeEntryPoint(TestCase):
    def test_no_args_opens_menu_instead_of_direct_watch(self):
        exe_main = import_exe_main()
        menu = Mock(return_value=23)
        watch = Mock(return_value=0)

        with patch.object(exe_main.sys, "argv", ["cyber-lobster-cli.exe"]):
            with patch.object(exe_main, "main", menu):
                with patch.object(exe_main, "run_watch_loop", watch):
                    code = exe_main.entry_point()

        self.assertEqual(code, 23)
        menu.assert_called_once_with()
        watch.assert_not_called()
