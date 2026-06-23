"""配置文件加载管理。

配置默认存储在系统用户数据目录，和程序/EXE 所在目录分离。
Windows: %APPDATA%\\cyber-lobster\\config.json
Linux:   ~/.config/cyber-lobster/config.json

高级用户可通过 `campusnet storage <路径>` 自定义位置。
支持多账号，结构如下:

{
  "current_user_id": "20240000000",
  "accounts": {
    "20240000000": {
      "password_scheme": "win-dpapi",
      "password_protected": "...",
      "service": "DX",
      "host": "172.16.54.18",
      "query_string": ""
    }
  }
}
"""

import json
import os
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from cyber_lobster.credential_store import (
    CredentialError,
    has_legacy_plaintext,
    protect_password,
    unprotect_password,
)

# ── 路径常量（默认和程序目录分离）──
APP_DIR_NAME = "cyber-lobster"
CONFIG_FILENAME = "config.json"
LEGACY_CONFIG_FILENAME = ".cyber_lobster_config.json"
CONFIG_POINTER_FILENAME = "config-location.txt"
ENV_CONFIG_PATH = "CYBER_LOBSTER_CONFIG"

# 测试或嵌入场景可临时覆盖；正常运行保持 None。
CONFIG_PATH: Path | None = None


@dataclass
class AccountConfig:
    """单个账号的认证配置。"""
    user_id: str = ""
    password: str = ""           # 仅运行时解密使用，不以明文写入配置
    service: str = "DX"          # 运营商: DX / YD / LT / 校园网
    host: str = "172.16.54.18"   # 历史兼容示例值，不保证适用于所有校园网
    query_string: str = ""       # 重定向 queryString（可选）


@dataclass
class GlobalConfig:
    """全局配置（对应 JSON 文件）。"""
    current_user_id: str = ""
    accounts: dict[str, dict] = field(default_factory=dict)
    auto_auth: bool = True       # 开机/启动时是否自动认证
    auto_start: bool = False     # 是否 Windows 开机自启
    auto_start_id: str = ""      # 开机自启时自动使用的账号（空=不自动进入watch）
    current_skin: str = "random"            # 当前皮肤: "random" 或皮肤名
    custom_skins: dict[str, str] = field(default_factory=dict)  # 用户自定义皮肤 {"名字": "ASCII"}

    # ── 便捷方法 ──

    def get_current_account(self) -> Optional[AccountConfig]:
        """获取当前激活的账号配置，无则返回 None。"""
        return self.get_account(self.current_user_id)

    def get_account(self, user_id: str) -> Optional[AccountConfig]:
        """按账号 ID 获取账号配置，无则返回 None。"""
        raw = self.accounts.get(user_id)
        if not raw:
            return None
        try:
            password = unprotect_password(user_id, raw)
        except CredentialError as exc:
            print(f"[config] [ERROR] 无法读取账号 {user_id} 的密码: {exc}", file=sys.stderr)
            password = ""
        return AccountConfig(
            user_id=raw.get("user_id", user_id),
            password=password,
            service=raw.get("service", "DX"),
            host=raw.get("host", "172.16.54.18"),
            query_string=raw.get("query_string", ""),
        )

    def upsert_account(self, account: AccountConfig) -> None:
        """添加或更新一个账号，并设为当前账号。"""
        protected = protect_password(account.user_id, account.password)
        self.accounts[account.user_id] = {
            **protected,
            "service": account.service,
            "host": account.host,
            "query_string": account.query_string,
        }
        self.current_user_id = account.user_id

    def has_accounts(self) -> bool:
        return len(self.accounts) > 0

    def account_ids(self) -> list[str]:
        return list(self.accounts.keys())

    def remove_account(self, user_id: str) -> bool:
        if user_id in self.accounts:
            del self.accounts[user_id]
            if self.current_user_id == user_id:
                self.current_user_id = next(iter(self.accounts)) if self.accounts else ""
            return True
        return False


# ═══════════════════════════════════════════════
#  读写接口
# ═══════════════════════════════════════════════


def load() -> GlobalConfig:
    """从家目录加载配置，文件不存在时返回全默认值。"""
    path = _resolve_config_path()
    _migrate_legacy_config(path)

    if not path.is_file():
        return GlobalConfig()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print(f"[config] [WARN] 配置文件损坏 ({path})，使用默认值", file=sys.stderr)
        return GlobalConfig()

    accounts, migrated = _protect_legacy_accounts(raw.get("accounts", {}))

    cfg = GlobalConfig(
        current_user_id=raw.get("current_user_id", ""),
        accounts=accounts,
        auto_auth=raw.get("auto_auth", True),
        auto_start=raw.get("auto_start", False),
        auto_start_id=raw.get("auto_start_id", ""),
        current_skin=raw.get("current_skin", "random"),
        custom_skins=raw.get("custom_skins", {}),
    )

    if migrated:
        save(cfg)

    return cfg


def save(cfg: GlobalConfig) -> bool:
    """保存配置到用户数据目录或自定义位置，设置 600 权限。"""
    try:
        path = _resolve_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        accounts, _ = _protect_legacy_accounts(cfg.accounts)
        path.write_text(
            json.dumps({
                "current_user_id": cfg.current_user_id,
                "accounts": accounts,
                "auto_auth": cfg.auto_auth,
                "auto_start": cfg.auto_start,
                "auto_start_id": cfg.auto_start_id,
                "current_skin": cfg.current_skin,
                "custom_skins": cfg.custom_skins,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        cfg.accounts = accounts
        # Unix 权限：仅 owner 可读写
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return True
    except CredentialError as exc:
        print(f"[config] [ERROR] 密码保护失败: {exc}", file=sys.stderr)
        return False
    except OSError as exc:
        print(f"[config] [ERROR] 保存失败: {exc}", file=sys.stderr)
        return False


def config_path() -> str:
    return str(_resolve_config_path())


def default_config_path() -> Path:
    return _default_app_data_dir() / CONFIG_FILENAME


def storage_pointer_path() -> Path:
    return _default_app_data_dir() / CONFIG_POINTER_FILENAME


def legacy_config_path() -> Path:
    return Path.home() / LEGACY_CONFIG_FILENAME


def set_config_path(path: str | Path, copy_existing: bool = True) -> Path:
    """设置自定义配置位置，返回规范化后的路径。"""
    target = Path(path).expanduser()
    if target.is_dir() or not target.suffix:
        target = target / CONFIG_FILENAME
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    current = _resolve_config_path(ignore_pointer=True)
    _migrate_legacy_config(current)
    if copy_existing and current.is_file() and current.resolve() != target:
        shutil.copy2(current, target)
    elif not target.exists():
        target.write_text(
            json.dumps({
                "current_user_id": "",
                "accounts": {},
                "auto_auth": True,
                "auto_start": False,
                "auto_start_id": "",
                "current_skin": "random",
                "custom_skins": {},
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            target.chmod(0o600)
        except OSError:
            pass

    pointer = storage_pointer_path()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(target), encoding="utf-8")
    return target


def reset_config_path() -> Path:
    """清除自定义配置位置，恢复默认用户数据目录。"""
    pointer = storage_pointer_path()
    try:
        pointer.unlink()
    except FileNotFoundError:
        pass
    return default_config_path()


def _default_app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME

    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / APP_DIR_NAME
    return Path.home() / ".config" / APP_DIR_NAME


def _resolve_config_path(ignore_pointer: bool = False) -> Path:
    if CONFIG_PATH is not None:
        return Path(CONFIG_PATH).expanduser()

    env_path = os.environ.get(ENV_CONFIG_PATH)
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_dir() or not path.suffix:
            path = path / CONFIG_FILENAME
        return path

    pointer = storage_pointer_path()
    if not ignore_pointer and pointer.is_file():
        try:
            raw = pointer.read_text(encoding="utf-8").strip()
            if raw:
                path = Path(raw).expanduser()
                if path.is_dir() or not path.suffix:
                    path = path / CONFIG_FILENAME
                return path
        except OSError:
            pass

    return default_config_path()


def _migrate_legacy_config(target: Path) -> None:
    legacy = legacy_config_path()
    if target.exists() or not legacy.is_file() or legacy.resolve() == target.resolve():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, target)
        try:
            target.chmod(0o600)
        except OSError:
            pass
        print(f"[config] 已迁移旧配置到: {target}")
    except OSError as exc:
        print(f"[config] [WARN] 旧配置迁移失败: {exc}", file=sys.stderr)


def _protect_legacy_accounts(accounts: dict[str, dict]) -> tuple[dict[str, dict], bool]:
    """把旧版明文字段迁移为本机保护字段。"""
    result: dict[str, dict] = {}
    migrated = False
    for user_id, raw in accounts.items():
        item = dict(raw)
        if has_legacy_plaintext(item):
            password = item.pop("password")
            item.update(protect_password(user_id, password))
            migrated = True
        result[user_id] = item
    return result, migrated
