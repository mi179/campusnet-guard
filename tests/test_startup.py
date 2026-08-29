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

                command = r'"C:\Apps\campusnet-guard-gui.exe" --autostart'
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
            current = Path(tmp) / "campusnet-guard-cli.exe"
            gui = Path(tmp) / "campusnet-guard-gui.exe"
            current.write_text("", encoding="utf-8")
            gui.write_text("", encoding="utf-8")

            with patch.object(startup.sys, "platform", "win32"):
                with patch.object(startup.sys, "executable", str(current)):
                    with patch.object(startup.sys, "frozen", True, create=True):
                        command = startup.build_startup_command("gui")

        self.assertIn("campusnet-guard-gui.exe", command)
        self.assertIn("--autostart", command)

    def test_linux_enable_status_disable(self):
        with TemporaryDirectory() as tmp:
            with patch.object(startup.sys, "platform", "linux"):
                with patch.dict(startup.os.environ, {"XDG_CONFIG_HOME": tmp}):
                    status = startup.get_startup_status()
                    self.assertTrue(status.supported)
                    self.assertFalse(status.enabled)

                    command = "/usr/bin/campusnet-gui --autostart"
                    enabled = startup.enable_startup(command=command)
                    self.assertTrue(enabled.enabled)
                    self.assertEqual(enabled.command, command)

                    desktop_file = Path(tmp) / "autostart" / startup.LINUX_AUTOSTART_FILENAME
                    self.assertTrue(desktop_file.exists())
                    self.assertIn(f"Exec={command}", desktop_file.read_text(encoding="utf-8"))

                    status = startup.get_startup_status()
                    self.assertTrue(status.enabled)
                    self.assertEqual(status.command, command)

                    disabled = startup.disable_startup()
                    self.assertFalse(disabled.enabled)
                    self.assertFalse(desktop_file.exists())

    def test_macos_enable_status_disable(self):
        with TemporaryDirectory() as tmp:
            launch_agent = Path(tmp) / "Library" / "LaunchAgents" / "campusnet.plist"
            with patch.object(startup.sys, "platform", "darwin"):
                with patch.object(startup, "_macos_launch_agent_path", return_value=launch_agent):
                    status = startup.get_startup_status()
                    self.assertTrue(status.supported)
                    self.assertFalse(status.enabled)

                    command = "'/Applications/CampusNet Guard.app/Contents/MacOS/CampusNet Guard' --autostart"
                    enabled = startup.enable_startup(command=command)
                    self.assertTrue(enabled.enabled)
                    self.assertTrue(launch_agent.exists())

                    status = startup.get_startup_status()
                    self.assertTrue(status.enabled)
                    self.assertIn("CampusNet Guard.app", status.command)
                    self.assertIn("--autostart", status.command)

                    disabled = startup.disable_startup()
                    self.assertFalse(disabled.enabled)
                    self.assertFalse(launch_agent.exists())
