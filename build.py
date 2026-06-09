#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for CampusNet Guard -- compile GUI/CLI single-file EXE.

Usage:
    pip install pyinstaller
    python build.py

Output:
  dist/cyber-lobster-gui.exe  GUI for end users
  dist/cyber-lobster-cli.exe  CLI for troubleshooting
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def find_pyinstaller() -> list[str]:
    """Find available PyInstaller command.

    Prefer `python -m PyInstaller`, fall back to `pyinstaller` CLI.
    Returns argv list.
    """
    try:
        r = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return [sys.executable, "-m", "PyInstaller"]
    except (OSError, subprocess.TimeoutExpired):
        pass

    candidates = ["pyinstaller", "pyinstaller3.12", "pyinstaller3.11", "pyi-makespec"]
    for cmd in candidates:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return [cmd]
        except (OSError, subprocess.TimeoutExpired):
            continue

    return []


def _common_args() -> list[str]:
    return [
        "--onefile",
        "--clean",
        "--noconfirm",
        "--noupx",
        "--paths", "src",
        "--collect-submodules", "cyber_lobster",
        "--hidden-import", "cyber_lobster",
        "--hidden-import", "cyber_lobster.cli",
        "--hidden-import", "cyber_lobster.config",
        "--hidden-import", "cyber_lobster.credential_store",
        "--hidden-import", "cyber_lobster.gui",
        "--hidden-import", "cyber_lobster.help_text",
        "--hidden-import", "cyber_lobster.logger",
        "--hidden-import", "cyber_lobster.network",
        "--hidden-import", "cyber_lobster.network_login",
        "--hidden-import", "cyber_lobster.startup",
        "--hidden-import", "cyber_lobster.system",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "requests",
        "--hidden-import", "urllib3",
        "--hidden-import", "charset_normalizer",
        "--hidden-import", "certifi",
        "--hidden-import", "idna",
        "--hidden-import", "msvcrt",
    ]


def _build_target(
    pyi_cmd: list[str],
    project_root: Path,
    name: str,
    entry: str,
    windowed: bool,
) -> Path:
    args = pyi_cmd + _common_args() + [
        "--name", name,
        "--windowed" if windowed else "--console",
        entry,
    ]

    print(f"[BUILD] {name} ...")
    print(f"    cmd: {' '.join(args)}")
    print()

    result = subprocess.run(args, cwd=project_root)
    if result.returncode != 0:
        print(f"\n[ERROR] {name} failed (exit {result.returncode})")
        sys.exit(1)

    if sys.platform == "win32":
        exe_path = project_root / "dist" / f"{name}.exe"
    else:
        exe_path = project_root / "dist" / name

    if not exe_path.is_file():
        print(f"\n[ERROR] output not found: {exe_path}")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] {name}: {exe_path} ({size_mb:.1f} MB)")
    return exe_path


def main():
    project_root = Path(__file__).parent.resolve()
    os.chdir(project_root)

    pyi_cmd = find_pyinstaller()
    if not pyi_cmd:
        print("[ERROR] PyInstaller not found. Install: pip install pyinstaller")
        sys.exit(1)

    for p in ["build", "dist"]:
        shutil.rmtree(p, ignore_errors=True)
    for spec in project_root.glob("*.spec"):
        spec.unlink(missing_ok=True)

    outputs = [
        _build_target(pyi_cmd, project_root, "cyber-lobster-gui", "gui_main.py", windowed=True),
        _build_target(pyi_cmd, project_root, "cyber-lobster-cli", "exe_main.py", windowed=False),
    ]

    print(f"\n[OK] Build complete. Output:")
    print(f"   {outputs[0]}")


if __name__ == "__main__":
    main()
