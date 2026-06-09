# Linux 使用说明

CampusNet Guard（校园网守护）Linux 用户通过源码运行，不提供 Linux EXE。

> 内部命令仍为 `cyber-lobster`，后续版本可能添加 `campusnet` 别名。

## 适用场景

- NAS（群晖/威联通等）：7x24 在线
- 软路由（OpenWrt/爱快等）：网关级守护
- 小主机（树莓派/工控机/迷你主机）：长期在线
- 实验室/办公室 Linux 工位：保持校园网在线
- 服务器/开发机：保持网络连通

## 系统要求

- Python 3.10+
- pip
- 终端（用于交互式输入密码）

## 安装

### 方式一：一键安装脚本

```bash
git clone https://github.com/mi179/campusnet-guard.git
cd campusnet-guard
bash scripts/linux/install.sh
```

### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/mi179/campusnet-guard.git
cd campusnet-guard

# 2. 创建虚拟环境
python3 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 安装依赖
pip install -e .
```

## 添加账号

```bash
cyber-lobster setup
```

按提示选择运营商、输入学号和密码。密码输入时不会显示，这是正常的。

> `cyber-lobster add` 是 `setup` 的别名，效果相同。

**认证服务器地址**：不同学校的认证服务器地址可能不同。添加账号时会提示确认，示例 `172.16.54.18`，请以学校网络中心提供的地址为准。

密码会自动加密保存到 `~/.config/cyber-lobster/config.json`，使用本地密钥 + HMAC-SHA256 保护。

## 查看账号

```bash
cyber-lobster list
```

## 验证登录

```bash
cyber-lobster test
```

## 诊断

```bash
cyber-lobster doctor
```

输出配置文件位置、账号状态、密码可读性、外网连通性。

或使用诊断脚本：

```bash
bash scripts/linux/doctor.sh
```

## 启动守护

```bash
cyber-lobster start
```

程序会每 10 秒检测一次网络，断网时自动重新认证。

或使用启动脚本：

```bash
bash scripts/linux/start.sh
```

### 自定义参数

```bash
# 修改检测间隔为 30 秒
cyber-lobster start --interval 30

# 修改超时为 5 秒
cyber-lobster start --timeout 5
```

### 停止守护

按 `Ctrl+C` 停止。

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

## systemd user service（高级用户）

当前版本不内置 systemd service。高级用户可手动配置：

### 1. 复制模板

```bash
mkdir -p ~/.config/systemd/user
cp scripts/linux/systemd-user/campusnet-guard.service ~/.config/systemd/user/
```

### 2. 修改路径

编辑 `~/.config/systemd/user/campusnet-guard.service`，将 `/path/to/campusnet-guard` 替换为实际路径：

```ini
WorkingDirectory=/home/你的用户名/campusnet-guard
ExecStart=/home/你的用户名/campusnet-guard/.venv/bin/cyber-lobster start --interval 10
```

### 3. 启用

```bash
systemctl --user daemon-reload
systemctl --user enable campusnet-guard
systemctl --user start campusnet-guard
```

### 4. 查看状态和日志

```bash
# 查看状态
systemctl --user status campusnet-guard

# 查看日志（实时）
journalctl --user -u campusnet-guard -f

# 查看最近日志
journalctl --user -u campusnet-guard -n 50
```

### 5. 停止和禁用

```bash
systemctl --user stop campusnet-guard
systemctl --user disable campusnet-guard
```

## 注销下线

```bash
cyber-lobster logout
```

## 查看所有命令

```bash
cyber-lobster --help
```

## 密码存储

Linux 下密码使用本地密钥 + HMAC-SHA256 加密：

- 密钥文件：`~/.cyber_lobster_key`（32 字节随机密钥，权限 600）
- 配置文件：`~/.config/cyber-lobster/config.json`（权限 600）
- 安全性：密钥在同一用户下可读，对个人使用足够

## 卸载

1. 停止守护进程（Ctrl+C 或 systemctl stop）
2. 删除项目目录：`rm -rf campusnet-guard`
3. 删除配置文件：`rm -rf ~/.config/cyber-lobster`
4. 删除密钥文件：`rm -f ~/.cyber_lobster_key`

## 平台差异

| 功能 | Windows | Linux |
|------|---------|-------|
| 密码存储 | DPAPI | local-key + HMAC |
| 弹窗通知 | ✅ ctypes.MessageBoxW | ❌ 不支持 |
| 开机自启 | ✅ HKCU Run | ⚠️ 需手动配置 systemd |
| GUI | ✅ 内置 tkinter | ❌ 不提供 |
| CLI | ✅ 完整支持 | ✅ 完整支持 |

## 常见问题

### Q: 提示 "externally-managed-environment"

Debian/Ubuntu 22.04+ 的系统 Python 不允许直接 pip install。必须使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Q: 提示 "No module named 'cyber_lobster'"

确保已激活虚拟环境：

```bash
source .venv/bin/activate
```

### Q: 如何在 NAS/软路由上运行？

1. 安装 Python 3.10+
2. 按上述步骤安装
3. 使用 tmux 或 screen 后台运行
4. 如需开机自启，配置 systemd user service

### Q: 认证服务器地址是多少？

不同学校不同。添加账号时会提示确认。示例 `172.16.54.18`，请以学校网络中心提供的地址为准。
