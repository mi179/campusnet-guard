"""Startup management tests."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from cyber_lobster import startup


class FakeKey:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.values = {}

    def OpenKey(self, *_args):
        return FakeKey()

    def CreateKeyEx(self, *_args):
        return FakeKey()

    def QueryValueEx(self, _key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], self.REG_SZ

    def SetValueEx(self, _key, name, _reserved, _kind, value):
        self.values[name] = value

    def DeleteValue(self, _key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]


class TestStartup(TestCase):
    def test_windows_enable_status_disable(self):
        fake_winreg = FakeWinreg()

        with patch.object(startup.sys, "platform", "win32"):
            with patch.dict(sys.modules, {"winreg": fake_winreg}):
                status = startup.get_startup_status()
                self.assertFalse(status.enabled)

                command = r'"C:\Apps\cyber-lobster-gui.exe" --autostart'
                enabled = startup.enable_startup(command=command)
                self.assertTrue(enabled.enabled)
                self.assertEqual(fake_winreg.values[startup.APP_NAME], command)

                status = startup.get_startup_status()
                self.assertTrue(status.enabled)
                self.assertEqual(status.command, command)

                disabled = startup.disable_startup()
                self.assertFalse(disabled.enabled)
                self.assertNotIn(startup.APP_NAME, fake_winreg.values)

    def test_build_startup_command_prefers_gui_sibling_when_frozen(self):
        with TemporaryDirectory() as tmp:
            current = Path(tmp) / "cyber-lobster-cli.exe"
            gui = Path(tmp) / "cyber-lobster-gui.exe"
            current.write_text("", encoding="utf-8")
            gui.write_text("", encoding="utf-8")

            with patch.object(startup.sys, "platform", "win32"):
                with patch.object(startup.sys, "executable", str(current)):
                    with patch.object(startup.sys, "frozen", True, create=True):
                        command = startup.build_startup_command("gui")

        self.assertIn("cyber-lobster-gui.exe", command)
        self.assertIn("--autostart", command)
