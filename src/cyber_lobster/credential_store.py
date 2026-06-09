"""本机凭据保护工具。"""

from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wt
import hashlib
import hmac
import os
import sys
from pathlib import Path


SCHEME_WIN_DPAPI = "win-dpapi"
SCHEME_LOCAL_KEY = "local-key-v1"
LOCAL_KEY_FILENAME = ".cyber_lobster_key"


class CredentialError(RuntimeError):
    """凭据加解密失败。"""


def protect_password(user_id: str, password: str) -> dict[str, str]:
    """保护密码，返回可写入配置文件的字段。"""
    if not password:
        return {"password_scheme": "", "password_protected": ""}

    context = _context(user_id)
    if sys.platform == "win32":
        blob = _dpapi_protect(password.encode("utf-8"), context)
        return {
            "password_scheme": SCHEME_WIN_DPAPI,
            "password_protected": base64.b64encode(blob).decode("ascii"),
        }

    token = _local_key_protect(password.encode("utf-8"), context)
    return {
        "password_scheme": SCHEME_LOCAL_KEY,
        "password_protected": token,
    }


def unprotect_password(user_id: str, raw: dict) -> str:
    """从账号配置中读取密码；兼容旧版明文字段。"""
    legacy_password = raw.get("password", "")
    if legacy_password:
        return legacy_password

    scheme = raw.get("password_scheme", "")
    protected = raw.get("password_protected", "")
    if not protected:
        return ""

    context = _context(user_id)
    if scheme == SCHEME_WIN_DPAPI:
        if sys.platform != "win32":
            raise CredentialError("该密码由 Windows DPAPI 保护，只能在原 Windows 用户下读取")
        blob = base64.b64decode(protected.encode("ascii"))
        return _dpapi_unprotect(blob, context).decode("utf-8")

    if scheme == SCHEME_LOCAL_KEY:
        return _local_key_unprotect(protected, context).decode("utf-8")

    raise CredentialError(f"未知密码保护方案: {scheme or '(empty)'}")


def has_legacy_plaintext(raw: dict) -> bool:
    return bool(raw.get("password"))


def _context(user_id: str) -> bytes:
    return f"cyber-lobster:{user_id}".encode("utf-8")


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wt.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _bytes_to_blob(data: bytes) -> tuple[_DATA_BLOB, ctypes.Array]:
    buf = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf


def _load_dpapi():
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        wt.LPCWSTR,
        ctypes.POINTER(_DATA_BLOB),
        wt.LPVOID,
        wt.LPVOID,
        wt.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wt.BOOL

    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        ctypes.POINTER(wt.LPWSTR),
        ctypes.POINTER(_DATA_BLOB),
        wt.LPVOID,
        wt.LPVOID,
        wt.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wt.BOOL

    kernel32.LocalFree.argtypes = [wt.HLOCAL]
    kernel32.LocalFree.restype = wt.HLOCAL
    return crypt32, kernel32


def _dpapi_protect(data: bytes, entropy: bytes) -> bytes:
    crypt32, kernel32 = _load_dpapi()
    in_blob, in_buf = _bytes_to_blob(data)
    entropy_blob, entropy_buf = _bytes_to_blob(entropy)
    out_blob = _DATA_BLOB()

    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "cyber-lobster",
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    _ = (in_buf, entropy_buf)
    if not ok:
        raise CredentialError(f"DPAPI 加密失败: {ctypes.WinError(ctypes.get_last_error())}")

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out_blob.pbData, wt.HLOCAL))


def _dpapi_unprotect(blob: bytes, entropy: bytes) -> bytes:
    crypt32, kernel32 = _load_dpapi()
    in_blob, in_buf = _bytes_to_blob(blob)
    entropy_blob, entropy_buf = _bytes_to_blob(entropy)
    out_blob = _DATA_BLOB()

    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    _ = (in_buf, entropy_buf)
    if not ok:
        raise CredentialError(f"DPAPI 解密失败: {ctypes.WinError(ctypes.get_last_error())}")

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out_blob.pbData, wt.HLOCAL))


def _local_key_path() -> Path:
    return Path.home() / LOCAL_KEY_FILENAME


def _load_or_create_local_key() -> bytes:
    path = _local_key_path()
    if path.is_file():
        try:
            return base64.b64decode(path.read_text(encoding="ascii"))
        except (OSError, ValueError) as exc:
            raise CredentialError(f"本机密钥读取失败: {exc}") from exc

    key = os.urandom(32)
    try:
        path.write_text(base64.b64encode(key).decode("ascii"), encoding="ascii")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except OSError as exc:
        raise CredentialError(f"本机密钥创建失败: {exc}") from exc
    return key


def _keystream(key: bytes, context: bytes, nonce: bytes, length: int) -> bytes:
    output = b""
    counter = 0
    while len(output) < length:
        block = hmac.new(
            key,
            b"stream" + context + nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        output += block
        counter += 1
    return output[:length]


def _local_key_protect(data: bytes, context: bytes) -> str:
    key = _load_or_create_local_key()
    nonce = os.urandom(16)
    stream = _keystream(key, context, nonce, len(data))
    cipher = bytes(a ^ b for a, b in zip(data, stream))
    tag = hmac.new(key, b"tag" + context + nonce + cipher, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(nonce + tag + cipher).decode("ascii")


def _local_key_unprotect(token: str, context: bytes) -> bytes:
    key = _load_or_create_local_key()
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
    except ValueError as exc:
        raise CredentialError(f"本机密文格式无效: {exc}") from exc

    if len(raw) < 48:
        raise CredentialError("本机密文格式无效")

    nonce = raw[:16]
    tag = raw[16:48]
    cipher = raw[48:]
    expected = hmac.new(key, b"tag" + context + nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise CredentialError("本机密文校验失败")

    stream = _keystream(key, context, nonce, len(cipher))
    return bytes(a ^ b for a, b in zip(cipher, stream))
