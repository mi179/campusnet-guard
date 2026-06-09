<div align="center">

# 🛡️ CampusNet Guard

**校园网守护 · 适配 Ruijie ePortal 的校园网自动认证与断网重连工具**

*Ruijie ePortal campus network auto-login and reconnect tool*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)]()

> 内部命令和安装包文件名仍为 `cyber-lobster`，后续版本可能统一重命名。

</div>

---

## 一句话介绍

CampusNet Guard（校园网守护）是适配 Ruijie ePortal 的校园网自动认证与断网重连工具，覆盖宿舍、教室、实验室、办公室、图书馆、机房、NAS、软路由、小主机等需要保持校园网在线的场景。

---

## 适用场景

| 场景 | 说明 |
|------|------|
| 宿舍电脑 | 个人笔记本、台式机，断网自动重连 |
| 教室/实验室 | 工位机、教学设备，保持在线 |
| 办公室 | 办公电脑，避免频繁认证 |
| 图书馆 | 公共区域设备（不建议保存账号） |
| 机房 | 批量设备，长期在线 |
| NAS | 群晖/威联通等，7x24 在线 |
| 软路由 | OpenWrt/爱快等，网关级守护 |
| 小主机 | 树莓派、工控机、迷你主机 |
| 个人电脑 | 任何需要保持校园网在线的设备 |

---

## ⬇️ 下载

**Windows 普通用户**：下载 `cyber-lobster-windows.zip`，解压后双击 `cyber-lobster-gui.exe` 即可使用，不需要安装 Python。

> 内部命令和安装包文件名仍为 `cyber-lobster`，后续版本可能统一重命名。

### 主渠道

👉 [GitHub Releases 下载页](https://github.com/mi179/campusnet-guard/releases/latest)

### 国内备用渠道

如果 GitHub 直连下载慢，可以通过以下方式获取：

- **官方页面**：项目介绍、下载入口、教程、FAQ（计划中，参见 [官方页面方案](#官方页面方案)）
- **GitHub 代理下载**：参见下方 [GitHub 下载慢怎么办](#q-github-下载慢怎么办)

> ⚠️ **安全提醒**：请只从 GitHub Releases 或官方页面下载，不要使用来路不明的 exe 文件。

---

## 🚀 快速开始（Windows）

### 第 1 步：下载并解压

从 [Releases 页面](https://github.com/mi179/campusnet-guard/releases/latest) 下载 `cyber-lobster-windows.zip`，解压到任意文件夹。

### 第 2 步：双击运行

双击 `cyber-lobster-gui.exe`。

> **首次运行提示**：Windows 可能弹出"Windows 已保护你的电脑"（SmartScreen）或"未知发布者"提示。这是因为程序没有购买代码签名证书。点击 **"更多信息"** → **"仍要运行"** 即可。详见 [Windows 安全提示说明](#windows-安全提示)。

### 第 3 步：添加账号

打开 GUI 的 **高级** 页，点击 **添加账号**：

1. 选择运营商（电信/移动/联通/校园网）
2. 输入学号
3. 输入密码（输入时不会显示）
4. 确认认证服务器地址（不同学校可能不同）
5. 点击 **保存并验证**

验证成功后账号自动保存。密码不会明文保存，由 Windows DPAPI 加密保护。

### 第 4 步：开启守护

回到 **主页**，点击 **开始守护**。程序会每 10 秒检测一次网络，断网时自动重新认证。

### 第 5 步（可选）：开机自启动

打开 **设置** 页，勾选 **开机后自动运行并守护校园网**。以后电脑开机后会自动启动并进入守护模式。

---

## 🖥️ GUI 页面说明

| 页面 | 功能 |
|------|------|
| **主页** | 开始守护、停止守护、注销下线、检测网络、实时日志 |
| **高级** | 添加账号、多账号切换、测试登录、删除账号 |
| **设置** | 检测间隔、开机自动守护、配置保存位置 |
| **帮助** | 内置使用说明 |

---

## Windows 安全提示

### "未知发布者" / SmartScreen 拦截

程序没有购买代码签名证书（个人项目，证书年费数千元），所以 Windows 会弹出安全提示。这是正常现象，**不代表程序有病毒**。

处理方式：
1. 弹出蓝色窗口 → 点击 **"更多信息"** → **"仍要运行"**
2. 弹出黄色窗口 → 点击 **"更多信息"** → **"仍要运行"**

### 为什么不使用 UPX 压缩

UPX 是可执行文件压缩工具，但会被 Windows Defender 误报为病毒。本项目不使用 UPX，所以文件较大（约 15 MB），但不会触发杀毒软件误报。

---

## 🔒 账号与密码安全

- **密码不明文落盘**
  - Windows：使用 DPAPI 加密，绑定当前系统用户，换用户/换电脑后需重新输入
  - Linux：使用本地密钥 + HMAC-SHA256 加密
- **配置文件权限**：`chmod 600`，仅当前用户可读写
- **配置路径**：
  - Windows：`%APPDATA%\cyber-lobster\config.json`
  - Linux：`~/.config/cyber-lobster/config.json`
- **配置与程序分离**：EXE 放在哪里都不影响配置文件位置
- **不收集遥测**：不收集任何日志、密码、cookie、token

---

## 🐧 Linux 使用

Linux 用户通过源码运行，不提供 Linux EXE。

### 安装

```bash
git clone https://github.com/mi179/campusnet-guard.git
cd campusnet-guard
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 使用

```bash
# 添加账号（密码隐藏输入，自动加密保存）
cyber-lobster add

# 启动断网自动重连
cyber-lobster start

# 诊断配置和网络状态
cyber-lobster doctor

# 查看已保存账号
cyber-lobster list
```

### 后台运行

```bash
# tmux 后台运行
tmux new -s campusnet
cyber-lobster start
# Ctrl+B D 退出 tmux，程序继续运行
# tmux attach -t campusnet 重新连接

# screen 后台运行
screen -S campusnet
cyber-lobster start
# Ctrl+A D 退出 screen
# screen -r campusnet 重新连接
```

### systemd user service（后续计划）

当前版本不内置 systemd service。高级用户可手动配置：

```ini
# ~/.config/systemd/user/cyber-lobster.service
[Unit]
Description=CampusNet Guard 校园网自动认证守护
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.venv/bin/cyber-lobster start
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

### 详细说明

参见 [docs/LINUX_USAGE.md](docs/LINUX_USAGE.md)。

---

## 🔧 CLI 命令（排障/高级用户）

**普通用户推荐使用 GUI，不需要 CLI。** CLI 主要用于排障和高级场景。

| 命令 | 用途 |
|------|------|
| `cyber-lobster add` | 添加账号 |
| `cyber-lobster start` | 启动守护 |
| `cyber-lobster list` | 查看账号 |
| `cyber-lobster test` | 验证登录 |
| `cyber-lobster doctor` | 诊断 |
| `cyber-lobster logout` | 注销下线 |
| `cyber-lobster autostart enable` | 开启开机自启 |
| `cyber-lobster autostart disable` | 关闭开机自启 |

完整命令列表：`cyber-lobster --help`

---

## ❓ 常见问题

### Q: 登录失败怎么办？

1. **运营商选错** — 电信选 DX，移动选 YD，联通 LT；校内直连选"校园网"
2. **账号或密码错误** — 确认学号和密码正确
3. **认证服务器地址不对** — 不同学校的认证服务器地址可能不同，示例 `172.16.54.18`，联系学校网络中心确认
4. **queryString 过期** — 重新添加账号，或从浏览器登录页复制

### Q: 教室/图书馆不弹认证页？

不同区域的认证服务器可能不同。尝试在添加账号时修改认证服务器地址。部分教室/网络环境不弹认证页，可能是学校网络策略限制。

### Q: 在线设备数量限制？

学校网络系统可能限制同时在线设备数量。如果超出限制，其他设备会被踢下线。这取决于学校策略，本工具无法改变。

### Q: GitHub 下载慢怎么办？

GitHub 在国内访问可能较慢。以下是一些解决方案：

**方法 1：使用可信的 GitHub 代理/镜像**

> ⚠️ 只使用可信的代理服务，不要使用来路不明的下载链接。

- 搜索 "GitHub 加速" 或 "GitHub 镜像"，选择可信的服务
- 使用方式：将 `https://github.com/` 替换为代理地址

**方法 2：使用 Git 克隆**

```bash
git clone https://github.com/mi179/campusnet-guard.git
```

**方法 3：让朋友帮忙**

让能访问 GitHub 的同学帮忙下载，通过微信/U盘/局域网传给你。

**方法 4：使用备用下载渠道**

项目计划提供 Cloudflare Pages 托管的官方页面，提供备用下载入口。参见 [官方页面方案](#官方页面方案)。

> ⚠️ **安全提醒**：不要从搜索引擎随便找的下载站下载 exe 文件，可能被篡改。只从 GitHub Releases 或官方页面下载。

### Q: 换电脑后密码不可用？

Windows DPAPI 加密的密码绑定当前系统用户，换电脑/换用户后需要重新运行 `cyber-lobster add` 输入密码。

### Q: 开机自启动找不到？

开机自启动的程序不会在桌面显示图标。它在后台运行，只在任务栏右下角（系统托盘）有图标。如果找不到，按 `Ctrl+Shift+Esc` 打开任务管理器，查看"启动"选项卡。

### Q: 如何卸载？

1. 删除下载的程序文件夹
2. 删除配置文件：
   - Windows：`%APPDATA%\cyber-lobster\`
   - Linux：`~/.config/cyber-lobster/`

---

## ⚠️ 免责声明

- 本工具仅用于**用户自己的校园网账号自动认证和断网重连**
- 本工具**不绕过认证、不破解、不共享账号、不突破在线数量限制**
- 本工具**只自动提交用户自己的账号**，模拟正常的登录流程
- 学校/运营商的**认证策略、在线设备数量、教室是否弹认证页**，由网络系统决定，本工具无法控制
- 部分教室/网络环境**不弹认证页、无法认证、在线数满**，可能不是软件问题
- **不保证适配所有 Ruijie ePortal 版本**
- **不建议在公共电脑保存账号**
- 使用者应**遵守学校网络管理规定**
- 下载请以 **GitHub Releases 或官方页面**为准，不要使用来路不明的 exe
- **使用者自行承担**账号安全和网络合规责任

详见 [docs/DISCLAIMER.md](docs/DISCLAIMER.md)。

---

## 📦 发布包说明

| 文件 | 用途 |
|------|------|
| `cyber-lobster-windows.zip` | Windows 用户下载包 |
| `cyber-lobster-gui.exe` | 图形界面版（推荐） |
| `cyber-lobster-cli.exe` | 命令行版（排障用） |

- **不需要安装 Python** — EXE 已包含 Python 运行时
- **不需要安装 PyInstaller** — 这是开发工具，普通用户不需要
- **Linux 用户**：通过源码安装，参见上方 Linux 使用说明
- **macOS**：暂未验证，不作为当前支持平台

---

## 📄 License

[MIT](LICENSE)

---

## 官方页面方案

计划使用 Cloudflare Pages 托管静态官方页面，提供以下内容：

- **项目介绍**：功能说明、截图、下载按钮
- **下载入口**：GitHub Releases 主链接 + 备用下载渠道
- **快速教程**：Windows 快速开始、Linux 安装指南
- **常见问题**：FAQ 页面
- **免责声明**：使用条款和责任说明
- **GitHub 链接**：指向项目仓库

### 为什么用 Cloudflare Pages

- 静态 HTML/Markdown，不需要服务器
- 免费额度足够个人项目使用
- 可以绑定自定义域名
- 全球 CDN，国内访问速度尚可

### 备用下载渠道设计

| 渠道 | 说明 | 优先级 |
|------|------|--------|
| GitHub Releases | 源头，版本记录最完整 | 主 |
| Cloudflare Pages 官方页面 | 中转说明 + 备用链接入口 | 备用 |
| Cloudflare R2 + 自定义域名 | exe/zip 直链，适合国内下载 | 备用（计划中） |
| GitHub Release 文件代理 | 临时备用，可用性不稳定 | 备用（临时） |
| 个人博客页面 | 多个下载入口汇总 | 备用（计划中） |

> ⚠️ **安全提醒**：无论从哪个渠道下载，都请验证文件来源。优先从 GitHub Releases 或官方页面下载，避免来路不明的 exe 文件。

---

<div align="center">
  Made with ❤️ · CampusNet Guard 守护着你的校园网<br>
  <sub>有问题请提交 Issue → https://github.com/mi179/campusnet-guard/issues</sub>
</div>
