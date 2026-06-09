"""配置与密码迁移测试。"""

import json
import os
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cyber_lobster import config
from cyber_lobster.config import AccountConfig, GlobalConfig


def fake_protect(user_id: str, password: str) -> dict[str, str]:
    return {
        "password_scheme": "test",
        "password_protected": f"{user_id}:{password}",
    }


def fake_unprotect(user_id: str, raw: dict) -> str:
    if raw.get("password"):
        return raw["password"]
    return raw["password_protected"].split(":", 1)[1]


class TestConfigPasswordStorage(TestCase):
    def test_upsert_account_does_not_keep_plaintext_password(self):
        cfg = GlobalConfig()
        with patch("cyber_lobster.config.protect_password", side_effect=fake_protect):
            cfg.upsert_account(AccountConfig(user_id="u1", password="secret"))

        raw = cfg.accounts["u1"]
        self.assertNotIn("password", raw)
        self.assertEqual(raw["password_scheme"], "test")
        self.assertEqual(raw["password_protected"], "u1:secret")

    def test_load_migrates_legacy_plaintext_password(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps({
                    "current_user_id": "u1",
                    "accounts": {
                        "u1": {
                            "password": "secret",
                            "service": "DX",
                            "host": "172.16.54.18",
                        }
                    },
                }),
                encoding="utf-8",
            )

            with patch.object(config, "CONFIG_PATH", path):
                with patch("cyber_lobster.config.protect_password", side_effect=fake_protect):
                    with patch("cyber_lobster.config.unprotect_password", side_effect=fake_unprotect):
                        cfg = config.load()
                        self.assertEqual(cfg.get_current_account().password, "secret")

            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("password", raw["accounts"]["u1"])
            self.assertEqual(raw["accounts"]["u1"]["password_scheme"], "test")


class TestConfigPath(TestCase):
    def test_default_config_path_uses_appdata_on_windows(self):
        with TemporaryDirectory() as tmp:
            with patch.object(config, "CONFIG_PATH", None):
                with patch.object(config.sys, "platform", "win32"):
                    with patch.dict(os.environ, {"APPDATA": tmp}, clear=False):
                        path = config.default_config_path()

        self.assertEqual(path, Path(tmp) / "cyber-lobster" / "config.json")

    def test_set_config_path_writes_pointer_and_creates_config(self):
        with TemporaryDirectory() as appdata, TemporaryDirectory() as custom:
            target_dir = Path(custom) / "my-config"
            with patch.object(config, "CONFIG_PATH", None):
                with patch.object(config.sys, "platform", "win32"):
                    with patch.dict(os.environ, {"APPDATA": appdata}, clear=False):
                        target = config.set_config_path(target_dir, copy_existing=False)
                        resolved = Path(config.config_path())

                        self.assertEqual(target, target_dir / "config.json")
                        self.assertEqual(resolved, target)
                        self.assertTrue(target.is_file())
                        self.assertEqual(
                            (Path(appdata) / "cyber-lobster" / "config-location.txt").read_text(encoding="utf-8"),
                            str(target),
                        )
