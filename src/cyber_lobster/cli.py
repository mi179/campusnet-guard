"""cyber-lobster CLI 主入口（argparse）。"""

import argparse
import json
import sys
import time
import getpass
from typing import NoReturn

from cyber_lobster import __version__
from cyber_lobster.logger import info, warn, error, success, notify_win32
from cyber_lobster.config import (
    load as load_config,
    save as save_config,
    config_path,
    default_config_path,
    reset_config_path,
    set_config_path,
    storage_pointer_path,
    ENV_CONFIG_PATH,
    GlobalConfig,
    AccountConfig,
)
from cyber_lobster.help_text import print_user_guide
from cyber_lobster.system import (
    get_cpu_temp,
    get_all_temp_sensors,
    get_memory_info,
    format_memory,
)
from cyber_lobster.network import check_gateways, check_connectivity

# ── 常量 ──
SERVICE_NAMES = {"DX": "电信", "YD": "移动", "LT": "联通", "校园网": "校园网"}
VALID_SERVICES = {"DX", "YD", "LT", "校园网"}
WATCH_INTERVAL = 10
CHECK_TIMEOUT = 3.0
DEFAULT_HOST = "172.16.54.18"  # 历史兼容示例值，不保证适用于所有校园网
DEFAULT_SERVICE = "DX"


# ═══════════════════════════════════════════════
#  CLI 解析器
# ═══════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cyber-lobster",
        description="cyber-lobster 校园网自动重连工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "普通用户常用命令:\n"
            "  cyber-lobster              打开主菜单\n"
            "  cyber-lobster add          添加账号\n"
            "  cyber-lobster start        启动守护模式\n"
            "  cyber-lobster list         查看账号\n"
            "  cyber-lobster test         验证当前账号\n"
            "  cyber-lobster doctor       检查配置和网络状态\n"
            "  cyber-lobster help         查看内置帮助文档\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"cyber-lobster {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    # ── 普通用户入口 ──
    sub.add_parser("menu", help="打开交互主菜单")
    sub.add_parser("help", aliases=["guide"], help="查看内置帮助文档")

    # ── setup ──
    sub.add_parser("setup", aliases=["add"], help="交互式配置向导（添加/修改账号）")

    # ── accounts / switch / verify ──
    sub.add_parser("accounts", aliases=["list"], help="列出已保存账号")

    p_switch = sub.add_parser("switch", help="切换当前激活的默认账号")
    p_switch.add_argument("user_id", nargs="?", help="要切换到的账号 ID")
    p_switch.add_argument("--login", action="store_true", help="切换后立即登录新账号")
    p_switch.add_argument("--no-logout", action="store_true", help="切换前不注销当前账号")

    p_verify = sub.add_parser("verify", aliases=["test"], help="验证当前或指定账号能否登录")
    p_verify.add_argument("user_id", nargs="?", help="要验证的账号 ID，默认当前账号")

    sub.add_parser("doctor", help="检查配置、密码存储和网络状态")

    p_storage = sub.add_parser("storage", help="查看或自定义账号配置保存位置")
    p_storage.add_argument("path", nargs="?", help="新的配置文件或文件夹路径；省略则只查看")
    p_storage.add_argument("--reset", action="store_true", help="恢复默认保存位置")

    # ── logout ──
    p_logout = sub.add_parser("logout", help="发送 ePortal 注销请求")
    p_logout.add_argument("--host", default=DEFAULT_HOST, help="认证服务器地址")

    # ── watch ──
    p_watch = sub.add_parser("watch", aliases=["start"], help="断网自动重连监控")
    p_watch.add_argument("--interval", type=int, default=WATCH_INTERVAL,
                         help=f"检测间隔秒数（默认 {WATCH_INTERVAL}）")
    p_watch.add_argument("--timeout", type=float, default=CHECK_TIMEOUT,
                         help=f"检测超时秒数（默认 {CHECK_TIMEOUT}）")

    # ── autostart ──
    p_autostart = sub.add_parser("autostart", help="查看、开启或关闭开机自动守护")
    p_autostart.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["status", "enable", "disable", "on", "off"],
        help="status=查看，enable/on=开启，disable/off=关闭",
    )
    p_autostart.add_argument(
        "--mode",
        choices=["gui", "cli"],
        default="gui",
        help="开机启动 GUI 无感守护，或启动 CLI watch；默认 gui",
    )

    # ── status / ping / check / login（保留）──
    p_status = sub.add_parser("status", help="查看本机系统状态（CPU 温度 / 内存）")
    p_status.add_argument("--all-sensors", action="store_true",
                          help="显示所有 thermal 传感器")

    sub.add_parser("ping", help="Ping 检测已配置的网关")

    sub.add_parser("check", help="系统状态 + 网关连通性一并检查")

    p_login = sub.add_parser("login", help="手动执行一次 ePortal 登录")
    p_login.add_argument("user_id", nargs="?", default="", help="学号")
    p_login.add_argument("--host", default=DEFAULT_HOST, help="认证服务器地址")
    p_login.add_argument("--service", default=DEFAULT_SERVICE, choices=["DX", "YD", "LT", "校园网"],
                         help="运营商")
    p_login.add_argument("--current", action="store_true",
                         help="使用当前配置的默认账号登录")

    return parser


# ═══════════════════════════════════════════════
#  setup — 交互式配置向导
# ═══════════════════════════════════════════════

def _prompt_nonempty(label: str) -> str:
    while True:
        val = input(f"  {label}: ").strip()
        if val:
            return val
        print("  此项不能为空。")


def _prompt_choice(label: str, choices: set[str], default: str) -> str:
    while True:
        val = input(f"  {label} [{default}]: ").strip().upper()
        if not val:
            return default
        if val in choices:
            return val
        print(f"  仅支持 {', '.join(sorted(choices))}")


def _password_required(account: AccountConfig) -> bool:
    if account.password:
        return True
    error(f"账号 {account.user_id} 的密码不可用，请重新运行 cyber-lobster setup 更新该账号")
    return False


def _login_account(account: AccountConfig, label: str = "登录") -> int:
    """执行一次账号登录/验证。"""
    from cyber_lobster.network_login import (
        PortalCredentials,
        login_with_session_retry,
        parse_login_response,
    )

    if not _password_required(account):
        return 1

    creds = PortalCredentials(
        user_id=account.user_id,
        password=account.password,
        service=account.service,
        query_string=account.query_string,
    )
    info(f"{label} {account.host} - {account.user_id} ({SERVICE_NAMES.get(account.service, account.service)})")
    result = login_with_session_retry(
        creds,
        host=account.host,
        max_session_attempts=1,
        request_retries=2,
    )
    if result.success:
        msg = parse_login_response(result.body)
        success(f"{label}成功")
        if msg:
            print("  ", json.dumps(msg, ensure_ascii=False, indent=2)[:300])
        return 0

    error(f"{label}失败: {result.error or result.body[:100]}")
    return 1


def _select_account_id(cfg: GlobalConfig, requested: str = "") -> str:
    ids = cfg.account_ids()
    if requested:
        return requested

    print()
    print("  已保存的账号：")
    print("  -----------------------")
    for i, uid in enumerate(ids, 1):
        marker = " <- 当前" if uid == cfg.current_user_id else ""
        print(f"  {i}. {uid}{marker}")
    print()

    while True:
        try:
            choice = input(f"  选择账号 (1-{len(ids)}): ").strip()
            if not choice:
                return ""
            idx = int(choice) - 1
            if 0 <= idx < len(ids):
                return ids[idx]
        except ValueError:
            pass
        print(f"  输入无效，请输入 1-{len(ids)}")


def cmd_menu(args: argparse.Namespace) -> int:
    """打开交互主菜单。"""
    from exe_main import main as menu_main
    return menu_main()


def cmd_help(args: argparse.Namespace) -> int:
    """显示内置帮助。"""
    print_user_guide()
    return 0


def cmd_storage(args: argparse.Namespace) -> int:
    """查看或设置配置保存位置。"""
    if getattr(args, "reset", False):
        path = reset_config_path()
        success(f"已恢复默认保存位置: {path}")
        return 0

    new_path = getattr(args, "path", "") or ""
    if new_path:
        try:
            path = set_config_path(new_path)
        except OSError as exc:
            error(f"设置保存位置失败: {exc}")
            return 1
        success(f"账号配置保存位置已设置为: {path}")
        info("已有配置会复制到新位置；密码仍由当前系统用户保护。")
        return 0

    print("账号配置保存位置")
    print("=" * 40)
    print(f"当前: {config_path()}")
    print(f"默认: {default_config_path()}")
    print(f"位置指针: {storage_pointer_path()}")
    print(f"环境变量覆盖: {ENV_CONFIG_PATH}")
    print()
    print("普通用户无需修改。高级用户可运行:")
    print("  cyber-lobster storage D:\\MyData\\cyber-lobster")
    print("  cyber-lobster storage --reset")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    """交互式配置向导。"""
    from cyber_lobster.network_login import (
        PortalCredentials,
        login_with_session_retry,
        parse_login_response,
    )

    print()
    print("cyber-lobster 配置向导")
    print("═" * 40)
    print(f"  配置将保存到: {config_path()}")
    print()

    print("  请选择运营商:")
    print("    1. 电信 (DX)")
    print("    2. 移动 (YD)")
    print("    3. 联通 (LT)")
    print("    4. 校园网")
    while True:
        c = input("  请选择 [1]: ").strip()
        if not c or c in ("1", "2", "3", "4"):
            service = {"1": "DX", "2": "YD", "3": "LT", "4": "校园网"}.get(c, "DX")
            break
        print("  输入无效，请选 1/2/3/4")

    user_id = _prompt_nonempty("学号")
    password = getpass.getpass("  密码（输入时不显示，正常敲回车即可）: ")
    while not password:
        password = getpass.getpass("  密码不能为空: ")
    host = input(f"  认证服务器 [{DEFAULT_HOST}]: ").strip() or DEFAULT_HOST

    print()
    svc_name = SERVICE_NAMES.get(service, service)
    info(f"确认: {svc_name}({service}) / {user_id}")
    info("正在验证登录...")

    creds = PortalCredentials(user_id=user_id, password=password, service=service)
    result = login_with_session_retry(creds, host=host, max_session_attempts=1, request_retries=2)

    if not result.success:
        err = result.error or result.body[:100]
        error(f"登录失败: {err}")
        return 1

    resp = parse_login_response(result.body)
    msg = resp.get("message", "") or resp.get("result", "")
    success(f"登录成功: {msg[:80]}")

    # 保存到配置
    cfg = load_config()
    try:
        cfg.upsert_account(AccountConfig(
            user_id=user_id, password=password, service=service, host=host,
        ))
    except Exception as exc:
        error(f"保存密码失败: {type(exc).__name__}: {exc}")
        return 1
    if not save_config(cfg):
        return 1
    success(f"配置已保存 -> {config_path()}")
    return 0


# ═══════════════════════════════════════════════
#  accounts / switch / verify — 多账号管理
# ═══════════════════════════════════════════════

def cmd_accounts(args: argparse.Namespace) -> int:
    """列出已保存账号。"""
    cfg = load_config()
    ids = cfg.account_ids()
    if not ids:
        warn("没有已保存的账号，请先运行 cyber-lobster setup")
        return 1

    print()
    print("  已保存账号：")
    print("  -----------------------------------------")
    for uid in ids:
        raw = cfg.accounts.get(uid, {})
        marker = " <- 当前" if uid == cfg.current_user_id else ""
        service = SERVICE_NAMES.get(raw.get("service", "DX"), raw.get("service", "DX"))
        host = raw.get("host", DEFAULT_HOST)
        scheme = raw.get("password_scheme") or ("legacy-plain" if raw.get("password") else "missing")
        print(f"  {uid}{marker}")
        print(f"    运营商: {service}  |  认证服务器: {host}  |  密码存储: {scheme}")
    print()
    return 0


def cmd_switch(args: argparse.Namespace) -> int:
    """切换当前默认账号。"""
    cfg = load_config()
    ids = cfg.account_ids()

    if not ids:
        warn("没有已保存的账号，请先运行 cyber-lobster setup")
        return 1

    current = cfg.current_user_id
    new_id = _select_account_id(cfg, getattr(args, "user_id", "") or "")
    if not new_id:
        return 0

    if new_id not in cfg.accounts:
        error(f"账号不存在: {new_id}")
        return 1

    if new_id == current:
        info(f"已经是当前账号: {new_id}")
        if getattr(args, "login", False):
            account = cfg.get_account(new_id)
            return _login_account(account, label="验证") if account else 1
        return 0

    old_account = cfg.get_current_account()
    if old_account and not getattr(args, "no_logout", False):
        from cyber_lobster.network_login import logout as eportal_logout

        info(f"正在注销旧账号: {old_account.user_id}...")
        result = eportal_logout(host=old_account.host)
        if result.success:
            success("旧账号已下线")
        else:
            warn(f"注销旧账号失败（继续切换）: {result.error}")

    cfg.current_user_id = new_id
    if not save_config(cfg):
        return 1
    success(f"已切换到账号: {new_id}")

    if getattr(args, "login", False):
        account = cfg.get_account(new_id)
        return _login_account(account, label="登录") if account else 1

    info("如需立即上线新账号，可运行: cyber-lobster switch <账号ID> --login")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """验证当前或指定账号能否登录。"""
    cfg = load_config()
    user_id = getattr(args, "user_id", "") or cfg.current_user_id
    if not user_id:
        warn("没有当前账号，请先运行 cyber-lobster setup")
        return 1

    account = cfg.get_account(user_id)
    if not account:
        error(f"账号不存在: {user_id}")
        return 1

    return _login_account(account, label="验证")


# ═══════════════════════════════════════════════
#  logout — 注销下线
# ═══════════════════════════════════════════════

def cmd_logout(args: argparse.Namespace) -> int:
    """发送注销请求。"""
    from cyber_lobster.network_login import logout as eportal_logout, parse_login_response

    info(f"正在向 {args.host} 发送注销请求...")
    result = eportal_logout(host=args.host)
    if result.success:
        msg = parse_login_response(result.body)
        success(f"注销成功: {msg.get('message', '') or msg.get('result', 'ok')}")
        return 0
    else:
        error(f"注销失败: {result.error}")
        return 1


# ═══════════════════════════════════════════════
#  watch — 断网自动重连
# ═══════════════════════════════════════════════

def cmd_watch(args: argparse.Namespace) -> int:
    """断网自动重连监控守护模式。"""
    cfg = load_config()
    account = cfg.get_current_account()

    if not account:
        warn("配置中没有有效账号，请先运行 cyber-lobster setup")
        return 1
    if not _password_required(account):
        return 1

    from cyber_lobster.network_login import PortalCredentials, login_with_session_retry

    interval = args.interval
    timeout = args.timeout
    creds = PortalCredentials(
        user_id=account.user_id,
        password=account.password,
        service=account.service,
        query_string=account.query_string,
    )

    info(f"监控启动 - {account.user_id} ({SERVICE_NAMES.get(account.service, account.service)})")
    info(f"间隔: {interval}s  |  超时: {timeout}s  |  按 Ctrl+C 退出")
    print()

    fail_count = 0

    try:
        while True:
            try:
                online = check_connectivity(timeout=timeout)
            except Exception:
                online = False

            if online:
                if fail_count > 0:
                    success(f"网络已恢复（之前断连 {fail_count} 次）")
                    notify_win32("cyber-lobster", "校园网已自动重新连通！")
                    fail_count = 0
                else:
                    info("网络正常")
            else:
                fail_count += 1
                warn(f"断连 ({fail_count})，正在重连...")

                try:
                    result = login_with_session_retry(
                        creds, host=account.host,
                        max_session_attempts=1, request_retries=2,
                    )
                    if result.success:
                        success("重连成功")
                        notify_win32("cyber-lobster", "校园网已自动重新连通！")
                        fail_count = 0
                    else:
                        err = (result.error or result.body[:60]).replace("\n", " ")
                        warn(f"重连失败: {err}")
                except Exception as exc:
                    warn(f"重连异常: {type(exc).__name__}: {exc}")

            time.sleep(interval)

    except KeyboardInterrupt:
        info("监控已停止。")
        return 0
    except Exception as exc:
        error(f"意外错误: {type(exc).__name__}: {exc}")
        return 1


# ═══════════════════════════════════════════════
#  autostart — 开机自启设置
# ═══════════════════════════════════════════════

def cmd_autostart(args: argparse.Namespace) -> int:
    """查看、开启或关闭开机自动守护。"""
    from cyber_lobster.startup import (
        StartupError,
        disable_startup,
        enable_startup,
        get_startup_status,
    )

    action = getattr(args, "action", "status")
    if action == "on":
        action = "enable"
    elif action == "off":
        action = "disable"

    if action == "status":
        try:
            status = get_startup_status()
        except StartupError as exc:
            error(str(exc))
            return 1
        print("cyber-lobster 开机自动守护")
        print("=" * 40)
        if not status.supported:
            print(f"状态: 不支持")
            print(f"原因: {status.reason}")
            return 1
        print(f"状态: {'已开启' if status.enabled else '未开启'}")
        print(f"位置: {status.location}")
        if status.command:
            print(f"命令: {status.command}")
        print()
        print("开启: cyber-lobster autostart enable")
        print("关闭: cyber-lobster autostart disable")
        return 0

    if action == "enable":
        try:
            status = enable_startup(mode=getattr(args, "mode", "gui"))
        except StartupError as exc:
            error(str(exc))
            return 1
        cfg = load_config()
        cfg.auto_start = True
        cfg.auto_auth = True
        save_config(cfg)
        success("开机自动守护已开启")
        info(f"位置: {status.location}")
        info(f"命令: {status.command}")
        return 0

    if action == "disable":
        try:
            status = disable_startup()
        except StartupError as exc:
            error(str(exc))
            return 1
        cfg = load_config()
        cfg.auto_start = False
        save_config(cfg)
        success("开机自动守护已关闭")
        info(f"位置: {status.location}")
        return 0

    error(f"未知 autostart 操作: {action}")
    return 1

# ═══════════════════════════════════════════════
#  保留子命令：status / ping / check / login
# ═══════════════════════════════════════════════

def cmd_status(args: argparse.Namespace) -> int:
    print("cyber-lobster - 系统状态")
    print("=" * 40)

    temp = get_cpu_temp()
    if temp is not None:
        print(f"CPU 封装温度:  {temp:.1f} C")
        if temp > 80:
            print("   [WARN] 温度偏高")
    else:
        print("CPU 温度:      无法读取（非 Linux 或无传感器）")

    if hasattr(args, 'all_sensors') and args.all_sensors:
        sensors = get_all_temp_sensors()
        if sensors:
            print("\n   -- 全部传感器 --")
            for name, val in sensors.items():
                mark = " [WARN]" if val > 80 else ""
                print(f"     {name:20s}: {val:.1f} C{mark}")

    mem = get_memory_info()
    if mem:
        print(f"内存使用:      {format_memory(mem)}")
        st = mem.get("SwapTotal", 0)
        sf = mem.get("SwapFree", 0)
        if st:
            su = st - sf
            print(f"   Swap:          {su // 1024} MiB / {st // 1024} MiB ({su / st * 100:.1f}%)")
    print()
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    cfg = load_config()
    # 兼容旧格式：从 cfg 读取 gateways
    gateways = getattr(cfg, "gateways", getattr(cfg, "_gateways", ["10.0.0.1"]))
    # 用默认值
    gw_list = ["10.0.0.1", "192.168.1.1", "1.1.1.1"]
    count = 3

    print(f"cyber-lobster - Ping 检测 ({count} 次)")
    print("=" * 40)
    results = check_gateways(gw_list, count=count)
    for r in results:
        icon = "[OK]" if r.alive else "[FAIL]"
        extra = ""
        if r.alive and r.avg_rtt is not None:
            extra = f"  -> {r.min_rtt:.1f}/{r.avg_rtt:.1f}/{r.max_rtt:.1f} ms  丢包 {r.loss_pct:.0f}%"
        elif not r.alive:
            extra = "  无法连通"
        print(f"{icon} {r.target}{extra}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    code1 = cmd_status(args)
    code2 = cmd_ping(args)
    return code1 or code2


def cmd_doctor(args: argparse.Namespace) -> int:
    """普通用户诊断：不登录，只检查配置和网络状态。"""
    print("cyber-lobster - 诊断")
    print("=" * 40)

    cfg = load_config()
    print(f"配置文件: {config_path()}")
    print(f"默认位置: {default_config_path()}")

    ids = cfg.account_ids()
    if not ids:
        print("账号: [失败] 未添加账号")
        print("下一步: 运行 cyber-lobster add")
        return 1

    print(f"账号数量: {len(ids)}")
    print(f"当前账号: {cfg.current_user_id or '未设置'}")

    account = cfg.get_current_account()
    if not account:
        print("当前账号: [失败] 配置中找不到当前账号")
        print("下一步: 运行 cyber-lobster list 查看账号，或 cyber-lobster add 重新添加")
        return 1

    print(f"运营商: {SERVICE_NAMES.get(account.service, account.service)}")
    print(f"认证服务器: {account.host}")
    if account.password:
        print("密码存储: [正常] 可读取（未明文显示）")
    else:
        print("密码存储: [失败] 不可读取")
        print("下一步: 运行 cyber-lobster add 重新添加该账号")
        return 1

    try:
        online = check_connectivity(timeout=2.0)
    except Exception as exc:
        print(f"外网检测: [失败] 检测异常 ({type(exc).__name__})")
        online = False

    if online:
        print("外网状态: [正常] 已连通")
        print("建议: 可运行 cyber-lobster start 进入守护模式")
    else:
        print("外网状态: [断开] 未连通或被认证页拦截")
        print("建议: 可运行 cyber-lobster test 验证登录，或 cyber-lobster start 自动重连")

    return 0


def cmd_login(args: argparse.Namespace) -> int:
    if args.current:
        cfg = load_config()
        acct = cfg.get_current_account()
        if not acct:
            warn("配置中没有有效账号，请先运行 cyber-lobster setup")
            return 1
        if not _password_required(acct):
            return 1
        from cyber_lobster.network_login import (
            PortalCredentials,
            login_with_session_retry,
            parse_login_response,
        )

        creds = PortalCredentials(
            user_id=acct.user_id, password=acct.password,
            service=acct.service, query_string=acct.query_string,
        )
        host = acct.host
    elif args.user_id:
        password = getpass.getpass("  密码（输入时不显示）: ")
        while not password:
            password = getpass.getpass("  密码不能为空: ")
        from cyber_lobster.network_login import (
            PortalCredentials,
            login_with_session_retry,
            parse_login_response,
        )

        creds = PortalCredentials(
            user_id=args.user_id, password=password,
            service=args.service,
        )
        host = args.host
    else:
        print("用法: cyber-lobster login <学号>")
        print("  或: cyber-lobster login --current")
        return 1

    info(f"登录 {host} - {creds.user_id} ({SERVICE_NAMES.get(creds.service, creds.service)})")
    result = login_with_session_retry(creds, host=host)
    if result.success:
        msg = parse_login_response(result.body)
        success("登录成功")
        if msg:
            print("  ", json.dumps(msg, ensure_ascii=False, indent=2)[:300])
        return 0
    else:
        error(f"登录失败: {result.error or result.body[:100]}")
        return 1


# ═══════════════════════════════════════════════
#  命令注册
# ═══════════════════════════════════════════════

COMMANDS = {
    "menu": cmd_menu,
    "help": cmd_help,
    "guide": cmd_help,
    "storage": cmd_storage,
    "accounts": cmd_accounts,
    "list": cmd_accounts,
    "setup": cmd_setup,
    "add": cmd_setup,
    "switch": cmd_switch,
    "verify": cmd_verify,
    "test": cmd_verify,
    "doctor": cmd_doctor,
    "logout": cmd_logout,
    "watch": cmd_watch,
    "start": cmd_watch,
    "autostart": cmd_autostart,
    "status": cmd_status,
    "ping": cmd_ping,
    "check": cmd_check,
    "login": cmd_login,
}


def main(argv: list[str] | None = None) -> NoReturn:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        from exe_main import main as menu_main
        sys.exit(menu_main())

    parser = build_parser()
    args = parser.parse_args(argv)

    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        sys.exit(handler(args))
    except KeyboardInterrupt:
        print()
        info("已取消")
        sys.exit(130)
