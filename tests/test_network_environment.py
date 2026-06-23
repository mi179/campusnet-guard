"""Proxy, VPN, and TUN compatibility diagnostics."""

from unittest import TestCase

from cyber_lobster.network_environment import (
    NetworkEnvironmentReport,
    SystemProxyStatus,
    collect_env_proxy_vars,
    collect_network_environment_report,
    find_suspicious_interfaces,
    format_network_environment_lines,
    redact_proxy_value,
)


class TestNetworkEnvironment(TestCase):
    def test_redacts_proxy_credentials_but_keeps_useful_address(self):
        self.assertEqual(
            redact_proxy_value("http://user:secret@127.0.0.1:7890"),
            "http://127.0.0.1:7890",
        )
        self.assertEqual(
            redact_proxy_value("http=127.0.0.1:1080;https=user:secret@example.com:443"),
            "http=127.0.0.1:1080;https=example.com:443",
        )

    def test_collect_env_proxy_vars_ignores_unrelated_environment(self):
        found = collect_env_proxy_vars(
            {
                "HTTP_PROXY": "http://user:secret@127.0.0.1:7890",
                "PATH": "ignored",
            }
        )

        self.assertEqual(found, {"HTTP_PROXY": "http://127.0.0.1:7890"})

    def test_find_suspicious_interfaces_detects_tun_without_flagging_wifi(self):
        def runner(command):
            if command[:3] == ["netsh", "interface", "show"]:
                return """
Admin State    State          Type             Interface Name
Enabled        Connected      Dedicated        WLAN
Enabled        Connected      Dedicated        xray-tun
"""
            return ""

        found = find_suspicious_interfaces(runner=runner, system_name="windows")

        joined = "\n".join(found).lower()
        self.assertIn("xray-tun", joined)
        self.assertFalse(any("wlan" in item.lower() for item in found))

    def test_collect_report_can_run_as_read_only_linux_check(self):
        commands = []

        def runner(command):
            commands.append(list(command))
            return ""

        report = collect_network_environment_report(
            environ={},
            runner=runner,
            system_name="linux",
        )

        self.assertIsNone(report.system_proxy.enabled)
        self.assertEqual(report.env_proxy_vars, {})
        self.assertEqual(report.suspicious_interfaces, ())
        self.assertFalse(report.has_proxy_risk)
        self.assertIn(["ip", "-o", "link", "show"], commands)

    def test_format_lines_explains_risk_and_next_step(self):
        report = NetworkEnvironmentReport(
            system_proxy=SystemProxyStatus(enabled=True, detail="127.0.0.1:1080"),
            env_proxy_vars={"HTTP_PROXY": "http://127.0.0.1:7890"},
            suspicious_interfaces=("Enabled Connected Dedicated xray-tun",),
        )

        text = "\n".join(format_network_environment_lines(report))

        self.assertIn("系统代理", text)
        self.assertIn("环境代理", text)
        self.assertIn("VPN/TUN", text)
        self.assertIn("直连规则", text)
