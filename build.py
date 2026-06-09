#!/usr/bin/env python3
"""
cyber-lobster 打包脚本 —— 编译 GUI/CLI 单文件 EXE。

用法:
    pip install pyinstaller
    python build.py

输出：
  dist/cyber-lobster-gui.exe  普通用户图形界面
  dist/cyber-lobster-cli.exe  排障用命令行
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def find_pyinstaller() -> list[str]:
    """查找可用的 PyInstaller 命令。

    优先使用当前 Python 的 -m PyInstaller，
    若失败则依次尝试 pyinstaller / pyinstaller3.12 等命令。
    返回 argv 列表。
    """
    # 先用 sys.executable 跑 -m PyInstaller --version 验证
    try:
        r = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return [sys.executable, "-m", "PyInstaller"]
    except (OSError, subprocess.TimeoutExpired):
        pass

    # 回退：直接找 pyinstaller 命令
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
        "--onefile",                    # 单文件 exe
        "--clean",                      # 清理缓存
        "--noconfirm",                  # 覆盖不询问
        "--noupx",                      # 不使用 UPX 压缩
        "--paths", "src",               # 让 PyInstaller 找到 src/cyber_lobster
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

    print(f"[BUILD] {name} 打包中...")
    print(f"    命令: {' '.join(args)}")
    print()

    result = subprocess.run(args, cwd=project_root)
    if result.returncode != 0:
        print(f"\n[ERROR] {name} 打包失败 (exit {result.returncode})")
        sys.exit(1)

    if sys.platform == "win32":
        exe_path = project_root / "dist" / f"{name}.exe"
    else:
        exe_path = project_root / "dist" / name

    if not exe_path.is_file():
        print(f"\n[ERROR] 未找到输出文件: {exe_path}")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] {name} 打包成功: {exe_path} ({size_mb:.1f} MB)")
    return exe_path


def main():
    project_root = Path(__file__).parent.resolve()
    os.chdir(project_root)

    # ── 找 PyInstaller ──
    pyi_cmd = find_pyinstaller()
    if not pyi_cmd:
        print("[ERROR] 找不到 PyInstaller。请安装:  pip install pyinstaller")
        print()
        print("   如果已安装但仍找不到，尝试:  python -m pip install pyinstaller")
        sys.exit(1)

    # ── 清理旧构建 ──
    for p in ["build", "dist"]:
        shutil.rmtree(p, ignore_errors=True)
    for spec in project_root.glob("*.spec"):
        spec.unlink(missing_ok=True)

    outputs = [
        _build_target(pyi_cmd, project_root, "cyber-lobster-gui", "gui_main.py", windowed=True),
        _build_target(pyi_cmd, project_root, "cyber-lobster-cli", "exe_main.py", windowed=False),
    ]

    print("\n[OK] 全部打包完成。普通用户请使用:")
    print(f"   {outputs[0]}")


if __name__ == "__main__":
    main()
