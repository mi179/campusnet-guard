"""Network environment diagnostics for proxy, VPN, and TUN compatibility.

The checks in this module are intentionally read-only. CampusNet Guard should
not disable proxies, VPN clients, TUN adapters, or system routing for users.
Instead, it reports likely causes in plain language so authentication failures
are easier to understand.
"""

from __future__ import annotations

import os
import platform as platform_module
import re
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
)

RISK_PROXY_ENV_KEYS = {
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
}

SUSPICIOUS_INTERFACE_KEYWORDS = (
    "tun",
    "tap",
    "wintun",
    "utun",
    "vpn",
    "wireguard",
    "openvpn",
    "tailscale",
    "zerotier",
    "clash",
    "mihomo",
    "sing-box",
    "singbox",
    "xray",
    "v2ray",
    "warp",
    "cloudflare",
)

VIRTUAL_INTERFACE_KEYWORDS = (
    "vmware",
    "virtualbox",
    "hyper-v",
    "loopback",
)


@dataclass(frozen=True)
class SystemProxyStatus:
    enabled: bool | None
    detail: str = ""


@dataclass(frozen=True)
class NetworkEnvironmentReport:
    system_proxy: SystemProxyStatus
    env_proxy_vars: dict[str, str] = field(default_factory=dict)
    suspicious_interfaces: tuple[str, ...] = ()

    @property
    def has_proxy_risk(self) -> bool:
        return bool(
            self.system_proxy.enabled
            or any(key in RISK_PROXY_ENV_KEYS for key in self.env_proxy_vars)
            or self.suspicious_interfaces
        )


def redact_proxy_value(value: str) -> str:
    """Return a display-safe proxy value without username/password."""
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "<已设置>"

    if not parsed.scheme or not parsed.netloc:
        return _redact_plain_proxy_value(value)

    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{hostname}{port}" if hostname else "<已设置>"
    return urlunsplit((parsed.scheme, netloc, "", "", ""))


def _redact_plain_proxy_value(value: str) -> str:
    """Redact ProxyServer-style values such as host:port or http=host:port."""
    cleaned_parts: list[str] = []
    for part in value.split(";"):
        part = part.strip()
        if not part:
            continue
        prefix = ""
        target = part
        if "=" in part:
            prefix, target = part.split("=", 1)
            prefix = f"{prefix.strip()}="
            target = target.strip()
        if "@" in target:
            target = target.rsplit("@", 1)[1]
        if not re.fullmatch(r"[\w.\-:\[\]]+", target):
            return "<已设置>"
        cleaned_parts.append(f"{prefix}{target}")
    return ";".join(cleaned_parts) if cleaned_parts else "<已设置>"


def collect_env_proxy_vars(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environ is None else environ
    found: dict[str, str] = {}
    for key in PROXY_ENV_KEYS:
        value = env.get(key)
        if value:
            found[key] = redact_proxy_value(value)
    return found


def get_windows_system_proxy_status() -> SystemProxyStatus:
    if platform_module.system().lower() != "windows":
        return SystemProxyStatus(enabled=None, detail="仅 Windows 系统代理可读取")

    try:
        import winreg

        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            try:
                proxy_enable = int(winreg.QueryValueEx(key, "ProxyEnable")[0])
            except OSError:
                proxy_enable = 0
            try:
                proxy_server = str(winreg.QueryValueEx(key, "ProxyServer")[0])
            except OSError:
                proxy_server = ""
            try:
                auto_config = str(winreg.QueryValueEx(key, "AutoConfigURL")[0])
            except OSError:
                auto_config = ""
    except OSError as exc:
        return SystemProxyStatus(enabled=None, detail=f"读取失败: {exc}")

    if proxy_enable:
        detail = proxy_server or "已开启但未读取到代理地址"
        return SystemProxyStatus(enabled=True, detail=redact_proxy_value(detail))
    if auto_config:
        return SystemProxyStatus(enabled=True, detail=f"自动配置脚本: {auto_config}")
    return SystemProxyStatus(enabled=False, detail="未开启")


def _default_runner(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=3,
        check=False,
    )
    return "\n".join(part for part in (completed.stdout, completed.stderr) if part)


def _interface_commands(system_name: str) -> list[list[str]]:
    if system_name == "windows":
        return [["netsh", "interface", "show", "interface"], ["ipconfig", "/all"]]
    if system_name == "darwin":
        return [["ifconfig", "-a"]]
    return [["ip", "-o", "link", "show"], ["ifconfig", "-a"]]


def _candidate_interface_lines(output: str) -> list[str]:
    lines: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        if set(line) <= {"-", "=", " "}:
            continue
        if "admin state" in lowered or "state" == lowered:
            continue
        lines.append(line)
    return lines


def _looks_suspicious_interface(line: str) -> bool:
    lowered = line.lower()
    if any(word in lowered for word in SUSPICIOUS_INTERFACE_KEYWORDS):
        return True
    if any(word in lowered for word in VIRTUAL_INTERFACE_KEYWORDS):
        return False
    return False


def _clean_interface_label(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line[:120]


def find_suspicious_interfaces(
    runner: Callable[[Sequence[str]], str] | None = None,
    system_name: str | None = None,
) -> tuple[str, ...]:
    run = _default_runner if runner is None else runner
    system = (system_name or platform_module.system()).lower()
    found: list[str] = []

    for command in _interface_commands(system):
        try:
            output = run(command)
        except (OSError, subprocess.SubprocessError, TimeoutError):
            continue
        for line in _candidate_interface_lines(output):
            if _looks_suspicious_interface(line):
                label = _clean_interface_label(line)
                if label not in found:
                    found.append(label)

    return tuple(found)


def collect_network_environment_report(
    environ: Mapping[str, str] | None = None,
    runner: Callable[[Sequence[str]], str] | None = None,
    system_name: str | None = None,
) -> NetworkEnvironmentReport:
    system = (system_name or platform_module.system()).lower()
    if system == "windows":
        system_proxy = get_windows_system_proxy_status()
    else:
        system_proxy = SystemProxyStatus(enabled=None, detail="仅 Windows 系统代理可读取")
    return NetworkEnvironmentReport(
        system_proxy=system_proxy,
        env_proxy_vars=collect_env_proxy_vars(environ),
        suspicious_interfaces=find_suspicious_interfaces(runner=runner, system_name=system),
    )


def format_network_environment_lines(report: NetworkEnvironmentReport) -> list[str]:
    lines: list[str] = []

    if report.system_proxy.enabled is True:
        lines.append(f"系统代理: [提示] 已开启（{report.system_proxy.detail}）")
    elif report.system_proxy.enabled is False:
        lines.append("系统代理: [正常] 未开启")
    else:
        detail = f"（{report.system_proxy.detail}）" if report.system_proxy.detail else ""
        lines.append(f"系统代理: [未知] 无法确认{detail}")

    risky_env = [key for key in report.env_proxy_vars if key in RISK_PROXY_ENV_KEYS]
    if risky_env:
        joined = ", ".join(f"{key}={report.env_proxy_vars[key]}" for key in risky_env)
        lines.append(f"环境代理: [提示] 已设置 {joined}")
    elif report.env_proxy_vars:
        joined = ", ".join(report.env_proxy_vars)
        lines.append(f"环境代理: [正常] 仅发现 {joined}")
    else:
        lines.append("环境代理: [正常] 未设置")

    if report.suspicious_interfaces:
        lines.append("可疑 VPN/TUN 网卡: [提示] " + "；".join(report.suspicious_interfaces[:5]))
    else:
        lines.append("可疑 VPN/TUN 网卡: [正常] 未发现")

    if report.has_proxy_risk:
        lines.append("建议: 认证失败时先暂停代理/VPN/TUN，或把认证服务器地址加入直连规则后重试。")
    else:
        lines.append("建议: 未发现明显代理/VPN/TUN 干扰。")

    return lines
