# CampusNet Guard v0.9.0 发布说明

适配 Ruijie ePortal 的校园网自动认证与断网重连工具。

> 内部命令和安装包文件名仍为 `cyber-lobster`，后续版本可能统一重命名。

## 新增功能

### GUI 图形界面
- 全新 Tkinter 图形界面，普通用户不需要使用命令行
- 主页：开始守护、停止守护、注销下线、检测网络
- 高级：添加账号、多账号切换、测试登录、删除账号
- 设置：检测间隔、开机自动守护、配置保存位置
- 帮助：内置使用说明

### 密码安全存储
- Windows：使用 DPAPI 加密，绑定当前系统用户
- Linux：使用本地密钥 + HMAC-SHA256 加密
- 密码不明文落盘
- 配置文件权限 `chmod 600`

### 开机自启动
- Windows：HKCU Run 注册表，不需要管理员权限
- GUI 设置页一键开启/关闭
- 支持 GUI 和 CLI 两种启动模式

### 校园网运营商选项
- 支持电信（DX）、移动（YD）、联通（LT）、校园网
- 添加账号时可选择运营商

## 安全修复

### CLI 安全修复
- 移除 `login <学号> <密码>` 参数（密码会进 shell 历史）
- 密码只允许隐藏输入（`getpass`）
- 移除 `inject_cookies` 中的明文密码 Cookie
- 移除硬编码学院名 Cookie
- README 不再出现明文密码配置示例

### GitHub Actions 权限最小化
- 添加 `permissions: contents: write`

## 打包修复

### PyInstaller 修复
- 添加 `--paths src` 解决模块找不到问题
- 添加 `--collect-submodules cyber_lobster` 收集所有子模块
- 添加 `--noupx` 避免 Defender 误报
- 构建产物从 11 MB 增加到 15 MB（模块完整打包）

## 下载

从 [Releases 页面](https://github.com/mi179/campusnet-guard/releases/latest) 下载：

- `cyber-lobster-windows.zip` — Windows 用户下载包
  - `cyber-lobster-gui.exe` — 图形界面版（推荐）
  - `cyber-lobster-cli.exe` — 命令行版（排障用）

不需要安装 Python，不需要安装 PyInstaller。

### 备用下载渠道

如果 GitHub 下载慢，可以使用以下备用渠道：

- **官方页面**（计划中）：Cloudflare Pages 托管，提供备用下载入口
- **GitHub 代理**：搜索 "GitHub 加速"，将下载链接替换为代理地址
- **同学帮忙**：让能访问 GitHub 的同学帮你下载

> ⚠️ 请只从 GitHub Releases 或官方页面下载，不要使用来路不明的 exe 文件。

详见 [官方页面方案](OFFICIAL_PAGE_PLAN.md)。

## 已知限制

- Windows SmartScreen 可能拦截（无代码签名证书，需手动允许）
- Linux 不支持 Windows 弹窗通知
- Linux 开机自启需手动配置 systemd（后续版本内置）
- GUI 依赖 tkinter（Linux 需手动安装 `python3-tk`）
- 换电脑/换用户后需重新输入密码（DPAPI 绑定）

## 更新日志

- 新增 GUI 图形界面
- 新增密码安全存储（DPAPI / local-key + HMAC）
- 新增开机自启动
- 新增校园网运营商选项
- 修复 CLI 安全问题（移除明文密码参数、Cookie）
- 修复 PyInstaller 打包问题（模块完整打包）
- 修复 GitHub Actions 权限（最小化）
- 新增 Windows 快速使用指南
- 新增 Linux 使用说明
- 新增免责声明
