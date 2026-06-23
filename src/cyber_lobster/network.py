"""网络连通性检测（基于 ping / HTTP）。"""

import subprocess
import re
import statistics
import sys
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass
class PingResult:
    target: str
    alive: bool
    sent: int = 0
    received: int = 0
    loss_pct: float = 100.0
    rtt_ms: list[float] = field(default_factory=list)

    @property
    def avg_rtt(self) -> Optional[float]:
        return statistics.mean(self.rtt_ms) if self.rtt_ms else None

    @property
    def max_rtt(self) -> Optional[float]:
        return max(self.rtt_ms) if self.rtt_ms else None

    @property
    def min_rtt(self) -> Optional[float]:
        return min(self.rtt_ms) if self.rtt_ms else None


# Linux: 64 bytes from 10.0.0.1: icmp_seq=1 ttl=64 time=1.23 ms
# Windows EN/ZH: Reply from 1.1.1.1: bytes=32 time<1ms TTL=57 / 时间=18ms
RE_PING = re.compile(r"(?:time|时间)\s*([=<])\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)
RE_SUMMARY_POSIX = re.compile(
    r"(\d+)\s+packets transmitted, (\d+)\s+(?:received|packets received)"
)
RE_SUMMARY_WINDOWS = re.compile(
    r"(?:Packets:|数据包:)\s*"
    r"(?:Sent|已发送)\s*=\s*(\d+)\s*[,，]\s*"
    r"(?:Received|已接收|接收)\s*=\s*(\d+)",
    re.IGNORECASE,
)


def _parse_rtts(output: str) -> list[float]:
    rtts: list[float] = []
    for operator, value in RE_PING.findall(output):
        rtt = float(value)
        if operator == "<" and rtt <= 1:
            rtt = 0.5
        rtts.append(rtt)
    return rtts


def _parse_ping_summary(output: str, default_sent: int) -> tuple[int, int] | None:
    for regex in (RE_SUMMARY_POSIX, RE_SUMMARY_WINDOWS):
        match = regex.search(output)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


def ping_host(host: str, count: int = 3, timeout: int = 5) -> PingResult:
    """对单个 host 执行 ping，返回 PingResult。自动适配 Linux / Windows。"""
    if sys.platform == "win32":
        # Windows: -n 次数, -w 超时(毫秒)
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:
        # Linux / macOS
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * (timeout + 1) + 2,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return PingResult(target=host, alive=False)

    stdout = proc.stdout
    rtts = _parse_rtts(stdout)

    transmitted = count
    received = len(rtts)
    summary = _parse_ping_summary(stdout, default_sent=count)
    if summary:
        transmitted, received = summary
    elif proc.returncode == 0 and received == 0:
        received = count

    loss_pct = ((transmitted - received) / transmitted * 100) if transmitted else 100

    return PingResult(
        target=host,
        alive=received > 0,
        sent=transmitted,
        received=received,
        loss_pct=loss_pct,
        rtt_ms=rtts,
    )


def check_gateways(
    gateways: list[str], count: int = 3, timeout: int = 5
) -> list[PingResult]:
    """依次检测多个网关。"""
    results: list[PingResult] = []
    for gw in gateways:
        results.append(ping_host(gw, count=count, timeout=timeout))
    return results


# ---- HTTP 连通性检测 ----

@dataclass(frozen=True)
class ConnectivityProbe:
    url: str
    expected_status: int
    body_contains: str = ""


CHECK_PROBES = [
    ConnectivityProbe("http://connect.rom.miui.com/generate_204", 204),
    ConnectivityProbe("http://www.gstatic.com/generate_204", 204),
    ConnectivityProbe(
        "http://www.msftconnecttest.com/connecttest.txt",
        200,
        "Microsoft Connect Test",
    ),
    ConnectivityProbe(
        "http://captive.apple.com/hotspot-detect.html",
        200,
        "Success",
    ),
]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _probe_connectivity(probe: ConnectivityProbe, timeout: float) -> bool:
    request = Request(
        probe.url,
        headers={
            "User-Agent": "campusnet-guard/1.0",
            "Cache-Control": "no-cache",
        },
    )
    opener = build_opener(_NoRedirect)

    try:
        with opener.open(request, timeout=timeout) as response:
            if response.getcode() != probe.expected_status:
                return False
            if not probe.body_contains:
                return True
            body = response.read(1024).decode("utf-8", errors="ignore")
            return probe.body_contains in body
    except HTTPError:
        # Captive portals usually redirect probes to a login page. Treat that
        # as offline so the caller can trigger ePortal login.
        return False
    except (OSError, TimeoutError, URLError, ValueError):
        return False


def check_connectivity(timeout: float = 3.0) -> bool:
    """尝试 HTTP GET 检测外网连通性。

    使用明确的 204/固定正文探针，避免校园网认证页重定向被误判为外网可用。
    """
    for probe in CHECK_PROBES:
        if _probe_connectivity(probe, timeout=timeout):
            return True

    return False
