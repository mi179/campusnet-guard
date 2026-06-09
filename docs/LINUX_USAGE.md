# Linux 使用说明

CampusNet Guard（校园网守护）Linux 用户通过源码运行，不提供 Linux EXE。

> 内部命令仍为 `cyber-lobster`，后续版本可能添加 `campusnet` 别名。

## 系统要求

- Python 3.10+
- pip
- 终端（用于交互式输入密码）

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/mi179/campusnet-guard.git
cd campusnet-guard

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -e .
```

## 添加账号

```bash
cyber-lobster add
```

按提示选择运营商、输入学号和密码。密码输入时不会显示，这是正常的。

密码会自动加密保存到 `~/.config/cyber-lobster/config.json`，使用本地密钥 + HMAC-SHA256 保护。

**认证服务器地址**：不同学校的认证服务器地址可能不同。添加账号时会提示确认，示例 `172.16.54.18`，请以学校网络中心提供的地址为准。

## 启动守护

```bash
cyber-lobster start
```

程序会每 10 秒检测一次网络，断网时自动重新认证。按 `Ctrl+C` 停止。

### 自定义参数

```bash
# 修改检测间隔为 30 秒
cyber-lobster start --interval 30

# 修改超时为 5 秒
cyber-lobster start --timeout 5
```

## 后台运行

### tmux

```bash
# 创建会话
tmux new -s campusnet

# 在 tmux 中启动守护
cyber-lobster start

# 退出 tmux（程序继续运行）
# 按 Ctrl+B，然后按 D

# 重新连接
tmux attach -t campusnet

# 查看所有会话
tmux ls
```

### screen

```bash
# 创建会话
screen -S campusnet

# 在 screen 中启动守护
cyber-lobster start

# 退出 screen（程序继续运行）
# 按 Ctrl+A，然后按 D

# 重新连接
screen -r campusnet

# 查看所有会话
screen -ls
```

## 诊断

```bash
cyber-lobster doctor
```

输出配置文件位置、账号状态、密码可读性、外网连通性。

## 其他命令

```bash
# 查看已保存账号
cyber-lobster list

# 验证当前账号能否登录
cyber-lobster test

# 手动注销
cyber-lobster logout

# 查看所有命令
cyber-lobster --help
```

## 密码存储

Linux 下密码使用本地密钥 + HMAC-SHA256 加密：

- 密钥文件：`~/.cyber_lobster_key`（32 字节随机密钥，权限 600）
- 配置文件：`~/.config/cyber-lobster/config.json`（权限 600）
- 安全性：密钥在同一用户下可读，对个人使用足够

## GUI（可选）

如果需要图形界面，需要安装 tkinter：

```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

然后运行：

```bash
python3 gui_main.py
```

## systemd user service（后续计划）

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

启用方式：

```bash
mkdir -p ~/.config/systemd/user
cp cyber-lobster.service ~/.config/systemd/user/
systemctl --user enable cyber-lobster
systemctl --user start cyber-lobster
```

## 适用场景

- NAS（群晖/威联通等）：7x24 在线，配合 tmux/screen 后台运行
- 软路由（OpenWrt/爱快等）：网关级守护
- 小主机（树莓派/工控机/迷你主机）：长期在线
- 实验室/办公室 Linux 工位：保持校园网在线
- 服务器/开发机：保持网络连通

## 平台差异

| 功能 | Windows | Linux |
|------|---------|-------|
| 密码存储 | DPAPI | local-key + HMAC |
| 弹窗通知 | ✅ ctypes.MessageBoxW | ❌ 不支持 |
| 开机自启 | ✅ HKCU Run | ⚠️ 需手动配置 systemd |
| GUI | ✅ 内置 tkinter | ⚠️ 需安装 python3-tk |
| CLI | ✅ 完整支持 | ✅ 完整支持 |
