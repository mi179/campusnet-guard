"""Per-user startup management for Windows and Linux."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "CyberLobster"
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
LINUX_AUTOSTART_FILENAME = "campusnet-guard.desktop"


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
    if sys.platform == "win32":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


def get_startup_status() -> StartupStatus:
    if sys.platform.startswith("linux"):
        path = _linux_autostart_path()
        command = _get_linux_autostart_command(path)
        return StartupStatus(
            supported=True,
            enabled=bool(command),
            command=command,
            location=str(path),
        )

    if sys.platform != "win32":
        return StartupStatus(
            supported=False,
            enabled=False,
            location="",
            reason="当前系统暂不支持在程序内直接设置开机自启动。",
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
    startup_command = command or build_startup_command(mode=mode)

    if sys.platform.startswith("linux"):
        path = _linux_autostart_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "\n".join(
                    [
                        "[Desktop Entry]",
                        "Type=Application",
                        "Name=CampusNet Guard",
                        "Name[zh_CN]=校园网守护",
                        f"Exec={startup_command}",
                        "Icon=campusnet-guard",
                        "Terminal=false",
                        "X-GNOME-Autostart-enabled=true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            path.chmod(0o600)
        except OSError as exc:
            raise StartupError(f"开启开机自启动失败: {exc}") from exc
        return StartupStatus(
            supported=True,
            enabled=True,
            command=startup_command,
            location=str(path),
        )

    if sys.platform != "win32":
        raise StartupError("当前系统暂不支持在程序内直接开启开机自启动。")

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
    if sys.platform.startswith("linux"):
        path = _linux_autostart_path()
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StartupError(f"关闭开机自启动失败: {exc}") from exc
        return StartupStatus(
            supported=True,
            enabled=False,
            command="",
            location=str(path),
        )

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


def _linux_autostart_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "autostart" / LINUX_AUTOSTART_FILENAME


def _get_linux_autostart_command(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except OSError as exc:
        raise StartupError(f"读取开机自启动状态失败: {exc}") from exc

    hidden = False
    command = ""
    for raw_line in content.splitlines():
        key, separator, value = raw_line.partition("=")
        if not separator:
            continue
        if key.strip().lower() == "hidden":
            hidden = value.strip().lower() == "true"
        elif key.strip().lower() == "exec":
            command = value.strip()
    return "" if hidden else command


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
