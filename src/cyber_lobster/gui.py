"""Tkinter 图形界面入口。"""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import argparse

from cyber_lobster import __version__
from cyber_lobster.config import (
    AccountConfig,
    config_path,
    default_config_path,
    load as load_config,
    reset_config_path,
    save as save_config,
    set_config_path,
)
from cyber_lobster.auth_service import (
    error_text,
    login_account,
    login_plain,
    logout_host,
    parse_response,
    password_available,
)
from cyber_lobster.constants import DEFAULT_HOST, SERVICE_NAMES, SERVICE_VALUES
from cyber_lobster.network import check_connectivity
from cyber_lobster.network_environment import (
    collect_network_environment_report,
    format_network_environment_lines,
)
from cyber_lobster.startup import (
    StartupError,
    disable_startup,
    enable_startup,
    get_startup_status,
)


class CyberLobsterGUI(tk.Tk):
    def __init__(self, autostart: bool = False) -> None:
        super().__init__()
        self.title(f"CampusNet Guard {__version__}")
        self.geometry("860x560")
        self.minsize(780, 500)

        self.autostart_mode = autostart
        self.cfg = load_config()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.watch_thread: threading.Thread | None = None
        self.worker_busy = False

        self.status_var = tk.StringVar(value="状态: 等待检测")
        self.account_var = tk.StringVar(value="")
        self.current_account_var = tk.StringVar(value="未添加账号")
        self.interval_var = tk.IntVar(value=10)
        self.timeout_var = tk.DoubleVar(value=3.0)
        self.storage_var = tk.StringVar(value=config_path())
        self.auto_auth_var = tk.BooleanVar(value=bool(self.cfg.auto_auth))
        self.startup_var = tk.BooleanVar(value=False)
        self.startup_status_var = tk.StringVar(value="正在读取开机自启动状态...")

        self._build_ui()
        self._refresh_accounts()
        self._refresh_startup_state()
        startup_account = self.cfg.get_current_account()
        if self.autostart_mode and self.cfg.auto_auth and startup_account and startup_account.password:
            self.after(0, self.iconify)
        if self.autostart_mode:
            self._log("开机自启动模式：正在自动检测配置和网络状态。")
        else:
            self._log("程序已启动。首次使用请到“高级”页添加账号。")
        self.after(200, self._drain_events)
        self.after(300, self._initial_check)
        self.after(900, self._maybe_autostart_watch)

    # ----- UI -----

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(14, 12, 14, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="CampusNet Guard 校园网守护",
            font=("Microsoft YaHei UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_var).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        self._build_home_tab()
        self._build_accounts_tab()
        self._build_settings_tab()
        self._build_help_tab()

    def _build_home_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(tab, text="主页")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        top = ttk.LabelFrame(tab, text="当前账号", padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="账号").grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.current_account_var, font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(10, 0),
        )

        actions = ttk.Frame(tab)
        actions.grid(row=1, column=0, sticky="ew", pady=12)
        for i in range(4):
            actions.columnconfigure(i, weight=1)

        self.start_button = ttk.Button(actions, text="开始守护", command=self._start_watch)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=4)
        self.stop_button = ttk.Button(actions, text="停止守护", command=self._stop_watch, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(actions, text="注销下线", command=self._logout_current).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(actions, text="检测网络", command=self._check_network_async).grid(row=0, column=3, sticky="ew", padx=4)

        log_frame = ttk.LabelFrame(tab, text="运行日志", padding=8)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=14, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

    def _build_accounts_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(tab, text="高级")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        ttk.Label(
            tab,
            text="账号与高级设置：首次使用在这里添加账号；普通用户通常只需要保留一个账号。",
            wraplength=680,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.accounts_tree = ttk.Treeview(
            tab,
            columns=("user_id", "service", "host", "storage"),
            show="headings",
            selectmode="browse",
        )
        self.accounts_tree.heading("user_id", text="账号")
        self.accounts_tree.heading("service", text="运营商")
        self.accounts_tree.heading("host", text="认证服务器")
        self.accounts_tree.heading("storage", text="密码存储")
        self.accounts_tree.column("user_id", width=170)
        self.accounts_tree.column("service", width=90, anchor="center")
        self.accounts_tree.column("host", width=180)
        self.accounts_tree.column("storage", width=140, anchor="center")
        self.accounts_tree.grid(row=1, column=0, sticky="nsew")

        buttons = ttk.Frame(tab)
        buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(buttons, text="添加账号", command=self._open_add_account).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="设为当前", command=self._set_tree_current).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="测试登录", command=self._verify_tree_account).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="删除账号", command=self._delete_tree_account).pack(side="left")

    def _build_settings_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(tab, text="设置")
        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="检测间隔（秒）").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Spinbox(tab, from_=3, to=300, textvariable=self.interval_var, width=10).grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(tab, text="检测超时（秒）").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Spinbox(tab, from_=1, to=30, increment=0.5, textvariable=self.timeout_var, width=10).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Separator(tab).grid(row=2, column=0, columnspan=3, sticky="ew", pady=12)

        ttk.Label(tab, text="自动运行").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Checkbutton(
            tab,
            text="程序启动后自动开始守护",
            variable=self.auto_auth_var,
            command=self._toggle_auto_auth,
        ).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=6)

        self.startup_check = ttk.Checkbutton(
            tab,
            text="开机后自动运行并守护校园网",
            variable=self.startup_var,
            command=self._toggle_startup,
        )
        self.startup_check.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=6)
        ttk.Label(tab, textvariable=self.startup_status_var, wraplength=560).grid(
            row=5,
            column=1,
            columnspan=2,
            sticky="w",
            padx=(10, 0),
            pady=(0, 6),
        )

        ttk.Separator(tab).grid(row=6, column=0, columnspan=3, sticky="ew", pady=12)

        ttk.Label(tab, text="账号配置位置").grid(row=7, column=0, sticky="w", pady=6)
        ttk.Entry(tab, textvariable=self.storage_var, state="readonly").grid(row=7, column=1, sticky="ew", padx=(10, 8), pady=6)
        ttk.Button(tab, text="选择位置", command=self._choose_storage).grid(row=7, column=2, pady=6)
        ttk.Button(tab, text="恢复默认位置", command=self._reset_storage).grid(row=8, column=1, sticky="w", padx=(10, 0), pady=6)

        note = (
            "普通用户无需修改保存位置。账号信息默认和程序位置分离，"
            "密码由当前系统用户保护，换电脑后需要重新输入密码。"
        )
        ttk.Label(tab, text=note, wraplength=620).grid(row=9, column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _build_help_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(tab, text="帮助")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        text = tk.Text(
            tab,
            wrap="word",
            state="normal",
            padx=18,
            pady=14,
            borderwidth=0,
            font=("Microsoft YaHei UI", 10),
        )
        text.tag_configure("title", font=("Microsoft YaHei UI", 16, "bold"), spacing3=10)
        text.tag_configure("section", font=("Microsoft YaHei UI", 12, "bold"), spacing1=10, spacing3=6)
        self._insert_help(text)
        text.configure(state="disabled")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(tab, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)

    # ----- Accounts -----

    def _insert_help(self, text: tk.Text) -> None:
        sections = [
            ("title", "CampusNet Guard 使用说明\n"),
            ("section", "第一次使用，只做三件事\n"),
            ("body", "1. 打开“高级”页，点击“添加账号”。\n"),
            ("body", "2. 选择运营商，输入学号和密码，点击“保存并验证”。\n"),
            ("body", "3. 回到“主页”，点击“开始守护”。之后断网会自动重连。\n\n"),
            ("body", "想开机后无感运行：打开“设置”页，勾选“开机后自动运行并守护校园网”。配置正常时会自动守护，配置缺失时才弹出窗口提醒。\n\n"),
            ("section", "主页按钮是什么意思\n"),
            ("body", "开始守护：开启后台检测，断网后自动登录。\n"),
            ("body", "停止守护：暂停自动检测，不再自动重连。\n"),
            ("body", "注销下线：主动向校园网发送下线请求。\n"),
            ("body", "检测网络：只检查外网状态，不会登录账号。\n\n"),
            ("section", "账号为什么在高级页\n"),
            ("body", "大多数人只有一个校园网账号，不需要频繁切换。添加、切换、删除、测试登录都放在“高级”页，主页保持简单。\n\n"),
            ("section", "账号和密码保存在哪里\n"),
            ("body", "账号配置默认保存在当前 Windows 用户的数据目录，不跟着 EXE 走。\n"),
            ("body", "密码不会明文保存；Windows 下使用 DPAPI，只能由当前系统用户读取。\n"),
            ("body", "需要改保存位置时，打开“设置”页选择文件夹。普通用户一般不用改。\n\n"),
            ("section", "出问题先看这里\n"),
            ("body", "日志提示“外网未连通”：可以直接点“开始守护”。\n"),
            ("body", "日志提示“设备未注册”：通常是认证服务器或 portal 参数不一致，先确认学校登录页是否变了。\n"),
            ("body", "换电脑后不能读取密码：这是正常的安全保护，重新添加账号即可。\n"),
        ]
        for tag, content in sections:
            text.insert("end", content, tag if tag != "body" else None)

    def _refresh_accounts(self) -> None:
        ids = self.cfg.account_ids()
        if self.cfg.current_user_id in ids:
            self.account_var.set(self.cfg.current_user_id)
        elif ids:
            self.account_var.set(ids[0])
            self.cfg.current_user_id = ids[0]
            save_config(self.cfg)
        else:
            self.account_var.set("")

        current = self.cfg.get_current_account()
        if current:
            service = SERVICE_NAMES.get(current.service, current.service)
            self.current_account_var.set(f"{current.user_id}（{service}）")
        else:
            self.current_account_var.set("未添加账号")

        for row in self.accounts_tree.get_children():
            self.accounts_tree.delete(row)
        for uid in ids:
            raw = self.cfg.accounts.get(uid, {})
            service = SERVICE_NAMES.get(raw.get("service", "DX"), raw.get("service", "DX"))
            storage = raw.get("password_scheme") or ("旧版明文" if raw.get("password") else "缺失")
            label = f"{uid}（当前）" if uid == self.cfg.current_user_id else uid
            self.accounts_tree.insert(
                "",
                "end",
                iid=uid,
                values=(label, service, raw.get("host", DEFAULT_HOST), storage),
            )
        self.storage_var.set(config_path())

    def _on_account_selected(self, _event=None) -> None:
        self._switch_selected_account()

    def _switch_selected_account(self) -> None:
        uid = self.account_var.get().strip()
        if not uid:
            return
        if uid not in self.cfg.accounts:
            messagebox.showerror("账号不存在", "请选择有效账号。")
            return
        self.cfg.current_user_id = uid
        save_config(self.cfg)
        self._refresh_accounts()
        self._log(f"已切换当前账号: {uid}")

    def _selected_tree_user_id(self) -> str:
        selection = self.accounts_tree.selection()
        return selection[0] if selection else ""

    def _set_tree_current(self) -> None:
        uid = self._selected_tree_user_id()
        if not uid:
            messagebox.showinfo("请选择账号", "请先在账号列表中选择一个账号。")
            return
        self.account_var.set(uid)
        self._switch_selected_account()

    def _verify_tree_account(self) -> None:
        uid = self._selected_tree_user_id()
        if not uid:
            messagebox.showinfo("请选择账号", "请先在账号列表中选择一个账号。")
            return
        self._verify_account(uid)

    def _delete_tree_account(self) -> None:
        uid = self._selected_tree_user_id()
        if not uid:
            messagebox.showinfo("请选择账号", "请先在账号列表中选择一个账号。")
            return
        if not messagebox.askyesno("删除账号", f"确定删除账号 {uid} 吗？"):
            return
        self.cfg.remove_account(uid)
        save_config(self.cfg)
        self._refresh_accounts()
        self._log(f"已删除账号: {uid}")

    def _open_add_account(self) -> None:
        AddAccountDialog(self, self._save_new_account)

    def _save_new_account(self, account: AccountConfig, dialog: "AddAccountDialog") -> None:
        if self.worker_busy:
            messagebox.showinfo("请稍候", "已有任务正在运行。")
            return
        dialog.set_busy(True)
        self.worker_busy = True

        def work() -> None:
            try:
                self._put_log(f"正在验证账号 {account.user_id}...")
                result = login_plain(
                    account.user_id,
                    account.password,
                    account.service,
                    account.host,
                    max_session_attempts=1,
                    request_retries=2,
                )
                if not result.success:
                    self.events.put(("account_failed", (dialog, error_text(result))))
                    return
                self.cfg.upsert_account(account)
                save_config(self.cfg)
                self.events.put(("account_saved", dialog))
            except Exception as exc:
                self.events.put(("account_failed", (dialog, f"{type(exc).__name__}: {exc}")))
            finally:
                self.worker_busy = False

        threading.Thread(target=work, daemon=True).start()

    # ----- Actions -----

    def _maybe_autostart_watch(self) -> None:
        if not self.autostart_mode:
            return

        if not self.cfg.auto_auth:
            self._log("已开机启动，但自动守护未开启。")
            self.iconify()
            return

        account = self.cfg.get_current_account()
        if not account or not password_available(account):
            self.notebook.select(1)
            self.deiconify()
            self.lift()
            self._log("开机自动守护未启动：账号配置不可用，请先在“高级”页添加或更新账号。")
            return

        self._start_watch()
        self.iconify()

    def _initial_check(self) -> None:
        if not self.cfg.account_ids():
            self.status_var.set("状态: 未添加账号")
            self.notebook.select(1)
            if self.autostart_mode:
                self.deiconify()
                self.lift()
            self._log("请在“高级”页点击“添加账号”，保存验证后再回到主页开始守护。")
            return
        self._check_network_async()

    def _current_account(self) -> AccountConfig | None:
        account = self.cfg.get_current_account()
        if not account:
            messagebox.showinfo("没有账号", "请先添加账号。")
            return None
        if not password_available(account):
            messagebox.showerror("密码不可读取", "该账号密码不可读取，请重新添加账号。")
            return None
        return account

    def _check_network_async(self) -> None:
        def work() -> None:
            online = check_connectivity(timeout=float(self.timeout_var.get()))
            report = collect_network_environment_report()
            self.events.put(("network", (online, report)))

        threading.Thread(target=work, daemon=True).start()

    def _verify_current(self) -> None:
        account = self._current_account()
        if account:
            self._verify_account(account.user_id)

    def _verify_account(self, user_id: str) -> None:
        account = self.cfg.get_account(user_id)
        if not account or not password_available(account):
            messagebox.showerror("账号不可用", "账号不存在或密码不可读取。")
            return
        self._run_login(account, label="验证")

    def _logout_current(self) -> None:
        account = self._current_account()
        if not account:
            return

        def work() -> None:
            self._put_log(f"正在注销账号 {account.user_id}...")
            result = logout_host(account.host)
            self.events.put(("logout", result))

        threading.Thread(target=work, daemon=True).start()

    def _run_login(self, account: AccountConfig, label: str = "登录") -> None:
        if self.worker_busy:
            messagebox.showinfo("请稍候", "已有任务正在运行。")
            return
        self.worker_busy = True

        def work() -> None:
            try:
                self._put_log(f"{label}账号 {account.user_id}...")
                result = login_account(account, max_session_attempts=1, request_retries=2)
                self.events.put(("login", (label, result)))
            finally:
                self.worker_busy = False

        threading.Thread(target=work, daemon=True).start()

    def _start_watch(self) -> None:
        account = self._current_account()
        if not account:
            return
        if self.watch_thread and self.watch_thread.is_alive():
            return

        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("状态: 守护中")
        self._log("守护模式已启动。")

        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

    def _stop_watch(self) -> None:
        self.stop_event.set()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_var.set("状态: 已停止")
        self._log("守护模式已停止。")

    def _watch_loop(self) -> None:
        while not self.stop_event.is_set():
            account = self.cfg.get_current_account()
            if not account or not password_available(account):
                self.events.put(("watch_error", "账号不可用，请重新添加账号。"))
                break

            online = check_connectivity(timeout=float(self.timeout_var.get()))
            if online:
                self.events.put(("watch_log", "网络正常。"))
            else:
                self.events.put(("watch_log", "检测到断网，正在重连..."))
                result = login_account(account, max_session_attempts=1, request_retries=2)
                if result.success:
                    self.events.put(("watch_log", "重连成功。"))
                else:
                    self.events.put(("watch_log", f"重连失败: {error_text(result, 80)}"))

            wait = max(3, int(self.interval_var.get()))
            for _ in range(wait):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

        self.events.put(("watch_stopped", None))

    # ----- Settings -----

    def _refresh_startup_state(self) -> None:
        try:
            status = get_startup_status()
        except StartupError as exc:
            self.startup_var.set(False)
            self.startup_status_var.set(str(exc))
            return

        if not status.supported:
            self.startup_var.set(False)
            self.startup_status_var.set(status.reason)
            if hasattr(self, "startup_check"):
                self.startup_check.configure(state="disabled")
            return

        self.startup_var.set(status.enabled)
        self.cfg.auto_start = status.enabled
        save_config(self.cfg)
        if status.enabled:
            self.startup_status_var.set("已开启。下次开机会自动启动并按配置守护校园网。")
        else:
            self.startup_status_var.set("未开启。需要时可勾选开机自动守护。")

    def _toggle_auto_auth(self) -> None:
        self.cfg.auto_auth = bool(self.auto_auth_var.get())
        save_config(self.cfg)
        if self.cfg.auto_auth:
            self._log("已开启：程序启动后自动开始守护。")
        else:
            self._log("已关闭：程序启动后不自动开始守护。")

    def _toggle_startup(self) -> None:
        enable = bool(self.startup_var.get())
        try:
            if enable:
                status = enable_startup(mode="gui")
                self.cfg.auto_start = True
                self.cfg.auto_auth = True
                self.auto_auth_var.set(True)
                save_config(self.cfg)
                self.startup_status_var.set("已开启。下次开机会自动启动并按配置守护校园网。")
                self._log(f"开机自动守护已开启: {status.location}")
            else:
                disable_startup()
                self.cfg.auto_start = False
                save_config(self.cfg)
                self.startup_status_var.set("未开启。需要时可勾选开机自动守护。")
                self._log("开机自动守护已关闭。")
        except StartupError as exc:
            self.startup_var.set(not enable)
            messagebox.showerror("开机自启动设置失败", str(exc))
            self._refresh_startup_state()

    def _choose_storage(self) -> None:
        directory = filedialog.askdirectory(title="选择账号配置保存文件夹")
        if not directory:
            return
        try:
            path = set_config_path(directory)
            self.storage_var.set(str(path))
            self.cfg = load_config()
            self._refresh_accounts()
            self._log(f"账号配置保存位置已设置为: {path}")
            messagebox.showinfo("保存位置已设置", f"账号配置将保存到:\n{path}")
        except Exception as exc:
            messagebox.showerror("设置失败", str(exc))

    def _reset_storage(self) -> None:
        path = reset_config_path()
        self.storage_var.set(str(path))
        self.cfg = load_config()
        self._refresh_accounts()
        self._log(f"已恢复默认保存位置: {path}")

    # ----- Event/log -----

    def _put_log(self, message: str) -> None:
        self.events.put(("log", message))

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "log":
                    self._log(str(payload))
                elif event == "network":
                    if isinstance(payload, tuple):
                        online, report = payload
                    else:
                        online, report = bool(payload), None
                    self.status_var.set("状态: 外网已连通" if online else "状态: 外网未连通")
                    self._log("外网已连通。" if online else "外网未连通或被认证页拦截。")
                    if report is not None:
                        self._log("代理/VPN 兼容性检查：")
                        for line in format_network_environment_lines(report):
                            self._log(line)
                elif event == "login":
                    label, result = payload
                    if result.success:
                        msg = parse_response(result.body)
                        self.status_var.set(f"状态: {label}成功")
                        self._log(f"{label}成功。{msg.get('message', '') if msg else ''}")
                    else:
                        self.status_var.set(f"状态: {label}失败")
                        self._log(f"{label}失败: {error_text(result)}")
                elif event == "logout":
                    result = payload
                    if result.success:
                        self._log("注销成功。")
                        self.status_var.set("状态: 已注销")
                    else:
                        self._log(f"注销失败: {result.error}")
                elif event == "watch_log":
                    self._log(str(payload))
                elif event == "watch_error":
                    self._log(str(payload))
                    self._stop_watch()
                elif event == "watch_stopped":
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                elif event == "account_saved":
                    dialog = payload
                    dialog.destroy()
                    self.cfg = load_config()
                    self._refresh_accounts()
                    self._log("账号已验证并保存。")
                    self.notebook.select(0)
                elif event == "account_failed":
                    dialog, error = payload
                    dialog.set_busy(False)
                    messagebox.showerror("账号验证失败", str(error))
                    self._log(f"账号验证失败: {error}")
        except queue.Empty:
            pass
        self.after(200, self._drain_events)


class AddAccountDialog(tk.Toplevel):
    def __init__(self, parent: CyberLobsterGUI, on_save) -> None:
        super().__init__(parent)
        self.title("添加账号")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.on_save = on_save

        self.service_var = tk.StringVar(value="电信")
        self.user_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        self.save_button: ttk.Button | None = None

        self._build()
        self.user_entry.focus_set()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="运营商").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Combobox(
            frame,
            textvariable=self.service_var,
            values=list(SERVICE_VALUES.keys()),
            state="readonly",
            width=24,
        ).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="学号").grid(row=1, column=0, sticky="w", pady=6)
        self.user_entry = ttk.Entry(frame, textvariable=self.user_var, width=28)
        self.user_entry.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="密码").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=28).grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(frame, text="认证服务器").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.host_var, width=28).grid(row=3, column=1, sticky="ew", pady=6)

        note = "保存前会先验证登录；密码不会明文保存。"
        ttk.Label(frame, text=note, wraplength=280).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 12))

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="取消", command=self.destroy).pack(side="right")
        self.save_button = ttk.Button(buttons, text="保存并验证", command=self._save)
        self.save_button.pack(side="right", padx=(0, 8))

    def _save(self) -> None:
        user_id = self.user_var.get().strip()
        password = self.password_var.get()
        host = self.host_var.get().strip() or DEFAULT_HOST
        service = SERVICE_VALUES.get(self.service_var.get(), "DX")

        if not user_id:
            messagebox.showinfo("缺少学号", "请输入学号。")
            return
        if not password:
            messagebox.showinfo("缺少密码", "请输入密码。")
            return

        account = AccountConfig(user_id=user_id, password=password, service=service, host=host)
        self.on_save(account, self)

    def set_busy(self, busy: bool) -> None:
        if self.save_button:
            self.save_button.configure(state="disabled" if busy else "normal")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--autostart", action="store_true")
    args, _unknown = parser.parse_known_args()
    app = CyberLobsterGUI(autostart=args.autostart)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
