"""network 模块回归测试。"""

from unittest import TestCase
from unittest.mock import patch

from cyber_lobster.network import (
    _parse_ping_summary,
    _parse_rtts,
    check_connectivity,
)


class TestPingParsing(TestCase):
    def test_parse_linux_ping_summary(self):
        output = "3 packets transmitted, 2 received, 33% packet loss"
        self.assertEqual(_parse_ping_summary(output, default_sent=3), (3, 2))

    def test_parse_windows_english_ping_summary(self):
        output = "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
        self.assertEqual(_parse_ping_summary(output, default_sent=4), (4, 4))

    def test_parse_windows_chinese_ping_summary(self):
        output = "数据包: 已发送 = 4，已接收 = 3，丢失 = 1 (25% 丢失)"
        self.assertEqual(_parse_ping_summary(output, default_sent=4), (4, 3))

    def test_parse_rtts_across_platforms(self):
        output = "time=12.3 ms time<1ms 时间=18ms"
        self.assertEqual(_parse_rtts(output), [12.3, 0.5, 18.0])


class TestConnectivity(TestCase):
    def test_check_connectivity_requires_successful_probe(self):
        with patch(
            "cyber_lobster.network._probe_connectivity",
            side_effect=[False, False, False, False],
        ):
            self.assertFalse(check_connectivity())

    def test_check_connectivity_succeeds_on_first_valid_probe(self):
        with patch(
            "cyber_lobster.network._probe_connectivity",
            side_effect=[False, True],
        ) as probe:
            self.assertTrue(check_connectivity())
            self.assertEqual(probe.call_count, 2)
