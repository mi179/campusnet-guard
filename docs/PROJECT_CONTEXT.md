# CampusNet Guard 项目上下文

> 更新日期：2026-08-31。本文给维护者和后续开发会话使用，记录当前真实状态、关键决策、已知限制和继续工作的入口。

## 当前状态

- 当前正式版本：`v0.1.6`
- 正式发布页：<https://github.com/mi179/campusnet-guard/releases/tag/v0.1.6>
- 最新下载页：<https://github.com/mi179/campusnet-guard/releases/latest>
- 当前支持平台：Windows、Debian/Ubuntu Linux、macOS
- Python 包版本同时维护在 `pyproject.toml` 与 `src/cyber_lobster/__init__.py`
- 最近一次完整本地测试：49 项 `unittest` 通过

## 已发布安装包

| 平台 | 发布文件 | 说明 |
|------|----------|------|
| Windows | `campusnet-guard-windows.zip` | GUI EXE + CLI 排障工具 |
| Debian / Ubuntu | `campusnet-guard_all.deb` | 架构无关 DEB，包含 GUI、CLI、桌面入口和 systemd 用户服务 |
| macOS Apple Silicon | `campusnet-guard-macos-apple-silicon.dmg` / `.zip` | 原生 `arm64` 应用 |
| macOS Intel | `campusnet-guard-macos-intel.dmg` / `.zip` | 原生 `x86_64` 应用 |

Linux 一键安装：

```bash
curl -fsSL https://raw.githubusercontent.com/mi179/campusnet-guard/main/scripts/linux/install_deb.sh | bash
```

macOS 自动构建包目前是临时签名，没有 Apple Developer ID 签名与公证。首次打开可能需要在 Finder 中按住 Control 点击应用并选择“打开”。

## 构建与发布入口

| 目标 | 入口 |
|------|------|
| Windows EXE | `python build.py` |
| Linux DEB | `bash scripts/linux/build_deb.sh` |
| Linux 一键安装器 | `scripts/linux/install_deb.sh` |
| macOS APP/DMG/ZIP | `bash scripts/macos/build_app.sh`（只能在 macOS 构建） |
| macOS ICNS | `scripts/macos/create_icns.py` |
| 正式发布工作流 | `.github/workflows/release.yml` |
| main 最新包工作流 | `.github/workflows/latest-windows.yml` |

发布约定：

1. 推送 `main` 自动更新 `latest` Release。
2. 推送 `v*` 标签自动创建正式 Release。
3. 正式工作流并行构建 Windows、Linux、Apple Silicon Mac 和 Intel Mac。
4. macOS 使用 GitHub 的 `macos-15` 与 `macos-15-intel` Runner；Cairo 用于把 SVG 图标转换成 ICNS。
5. 发布前必须核对实际附件，不以工作流绿色状态代替验包。

## GUI 与启动行为

- Windows、Linux、macOS 共用 `src/cyber_lobster/gui.py`。
- Linux 高 DPI/小屏显示已经处理：窗口按屏幕尺寸适配，Treeview 行高按实际字体计算。
- Windows 开机启动使用当前用户注册表 `HKCU Run`。
- Linux 使用 `~/.config/autostart/campusnet-guard.desktop`。
- macOS 使用 `~/Library/LaunchAgents/blog.journeymind.campusnet-guard.plist`。
- Linux DEB 安装 `python3-tk`，并提供应用菜单入口 `campusnet-gui`。

## 名称与兼容性边界

- 产品名：CampusNet Guard
- 推荐 CLI：`campusnet`
- 兼容 CLI：`campusnet-guard`、`cyber-lobster`
- 内部 Python 包：`cyber_lobster`
- 历史配置目录：`cyber-lobster`

暂不直接重命名内部包和配置目录，以免破坏已有用户配置与旧命令。

## 代理、VPN 与 TUN 现状

这是当前最重要的待完善兼容性问题。

### 已完成

- ePortal 登录使用 `requests.Session`，并设置 `trust_env = False`。
- 登录请求不会继承普通 HTTP/HTTPS 环境代理。
- `doctor` 会检测代理环境变量和常见 `tun`、`utun`、Wintun、Clash、sing-box、Xray 等虚拟接口。
- 诊断只读，不会自动关闭代理、VPN、TUN，也不会修改用户路由或 DNS。

### 已知限制

- `trust_env = False` 只能绕过普通代理配置，不能保证绕过路由层 TUN。
- 当前认证 socket 没有绑定校园网物理接口。
- macOS Shadowrocket 开启 TUN 时，认证服务器流量可能进入 `utun`。
- Windows Wintun、Linux `tun0` 等环境存在同类问题。
- `src/cyber_lobster/network.py` 的联网探针使用 `urllib` 默认 opener，尚未明确禁用系统代理；代理可用时可能把“校园网未认证”误判为“外网已连通”。

### 当前用户侧建议

优先在代理客户端中把认证服务器配置为直连。默认示例：

```text
IP-CIDR,172.16.54.18/32,DIRECT,no-resolve
```

认证地址因学校而异，应以账号配置中的 `host` 为准，不应把示例地址硬编码成所有学校的规则。

macOS 可检查实际出口：

```bash
route -n get <认证服务器IP> | grep interface
```

`utun*` 通常表示被 TUN 接管；物理 Wi-Fi/以太网接口表示直连。接口名不能在程序中固定假设为 `en0`。

### 推荐的下一步实现

建议新增“校园网强制直连”能力，但保持默认安全和不修改全局设置：

1. 根据认证服务器动态查询当前路由和出口接口。
2. 识别物理接口与 TUN/VPN 接口，GUI/doctor 显示明确结论。
3. 先修复联网探针，使其明确不使用代理。
4. 认证请求按平台选择物理出口：macOS `IP_BOUND_IF`、Linux `SO_BINDTODEVICE`、Windows `IP_UNICAST_IF`。
5. 绑定失败时回退并提示用户添加 `DIRECT` 规则，不静默修改路由。
6. 为三平台分别增加可注入、无需真实改路由的单元测试。

应用级绑定不能替代代理客户端的排除路由；代理软件中的 `DIRECT` 规则仍应作为首选方案。

## 安全与产品原则

- 密码不明文落盘。
- Windows 使用 DPAPI；Linux/macOS 使用当前用户本地密钥保护。
- 不收集遥测、密码、cookie 或 token。
- 不绕过校园网认证、不破解、不共享账号、不突破在线数量限制。
- 不自动修改系统代理、VPN、TUN、路由或 DNS。
- 普通用户优先 GUI，服务器和排障场景保留 CLI。

## 后续工作优先级

1. 修复联网探针代理误判。
2. 完善认证服务器路由诊断与物理接口绑定。
3. 找真实 macOS Shadowrocket TUN 环境做验证。
4. 配置 Apple Developer ID 签名和公证。
5. 增加 Windows、Linux、macOS GUI smoke test 与发布截图。
6. 再考虑自动更新、CLI `--json` 和 GUI 首次使用向导。

