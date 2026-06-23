"""Per-user startup management.

Windows uses HKCU Run so enabling startup does not require administrator
permissions and does not create a visible console window for the GUI build.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "CyberLobster"
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class StartupError(RuntimeError):
    """Raised when startup settings cannot be changed."""


@dataclass(frozen=True)
class StartupStatus:
    supported: bool
    enabled: bool
    command: str = ""
    location: str = ""
    reason: str = ""


def build_startup_command(mode: str = "gui") -> str:
    """Build the command stored in the OS startup location."""
    mode = (mode or "gui").lower()
    if mode not in {"gui", "cli"}:
        raise ValueError("mode must be 'gui' or 'cli'")

    executable = _current_executable()
    if _is_frozen():
        target = _sibling_executable(executable, mode)
        args = [str(target)]
    else:
        module = "cyber_lobster.gui" if mode == "gui" else "cyber_lobster.cli"
        args = [sys.executable, "-m", module]

    args.append("--autostart" if mode == "gui" else "watch")
    return subprocess.list2cmdline(args)


def get_startup_status() -> StartupStatus:
    if sys.platform != "win32":
        return StartupStatus(
            supported=False,
            enabled=False,
            location="",
            reason="当前只支持在 Windows 图形界面中直接设置开机自启动。",
        )

    try:
        command = _get_windows_run_value()
    except OSError as exc:
        raise StartupError(f"读取开机自启动状态失败: {exc}") from exc

    return StartupStatus(
        supported=True,
        enabled=bool(command),
        command=command,
        location=rf"HKCU\{WINDOWS_RUN_KEY}\{APP_NAME}",
    )


def enable_startup(command: str | None = None, mode: str = "gui") -> StartupStatus:
    if sys.platform != "win32":
        raise StartupError("当前系统暂不支持在程序内直接开启开机自启动。")

    startup_command = command or build_startup_command(mode=mode)
    try:
        _set_windows_run_value(startup_command)
    except OSError as exc:
        raise StartupError(f"开启开机自启动失败: {exc}") from exc

    return StartupStatus(
        supported=True,
        enabled=True,
        command=startup_command,
        location=rf"HKCU\{WINDOWS_RUN_KEY}\{APP_NAME}",
    )


def disable_startup() -> StartupStatus:
    if sys.platform != "win32":
        raise StartupError("当前系统暂不支持在程序内直接关闭开机自启动。")

    try:
        _delete_windows_run_value()
    except OSError as exc:
        raise StartupError(f"关闭开机自启动失败: {exc}") from exc

    return StartupStatus(
        supported=True,
        enabled=False,
        command="",
        location=rf"HKCU\{WINDOWS_RUN_KEY}\{APP_NAME}",
    )


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _current_executable() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def _sibling_executable(current: Path, mode: str) -> Path:
    if sys.platform != "win32":
        return current

    wanted = "campusnet-guard-gui.exe" if mode == "gui" else "campusnet-guard-cli.exe"
    sibling = current.with_name(wanted)
    if sibling.exists():
        return sibling
    return current


def _get_windows_run_value() -> str:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _kind = winreg.QueryValueEx(key, APP_NAME)
            return str(value)
    except FileNotFoundError:
        return ""


def _set_windows_run_value(command: str) -> None:
    import winreg

    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)


def _delete_windows_run_value() -> None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
