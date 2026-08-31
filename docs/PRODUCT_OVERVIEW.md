# CampusNet Guard 产品与工程说明

当前版本、发布物、构建链路和代理/TUN 技术上下文统一记录在 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)。本文主要保留长期产品定位与路线。

## 产品定位

CampusNet Guard（校园网守护）是适配 Ruijie ePortal 的校园网自动认证与断网重连工具。

当前定位是**公益开源的小工具产品**，优先服务真实校园网用户，而不是做商业化网络管理平台。

## 用户分层

### Windows 普通用户

- 目标：下载 zip，解压，双击 GUI，添加账号，开始守护。
- 不应该要求用户理解 Python、命令行、虚拟环境、配置路径。
- 常见问题需要在 GUI 日志、README、快速指南里直接给下一步。

### Linux / NAS / 软路由用户

- 目标：源码安装，用 `campusnet setup` 和 `campusnet start` 长期运行。
- 这类用户可以接受 CLI、tmux/screen/systemd，但 CLI 必须稳定、安静、可诊断。
- Debian / Ubuntu 桌面用户使用带 GUI 的 DEB；服务器环境保留 CLI。

### macOS 用户

- Apple Silicon 与 Intel 分别提供原生 DMG/ZIP 图形包。
- 图形界面支持账号管理、断网守护和登录后自动运行。

### 维护者 / 高级用户

- 目标：能理解认证流程、配置文件、发布流程和兼容性边界。
- 需要清楚知道哪些名称是公开品牌，哪些是历史兼容。

## 名称边界

| 名称 | 用途 | 是否公开主推 |
|------|------|--------------|
| CampusNet Guard | 产品名、窗口标题、官网、Release 文件名 | 是 |
| campusnet | 推荐 CLI 入口 | 是 |
| campusnet-guard | CLI 兼容别名、仓库名、发布包名 | 是 |
| cyber-lobster | 旧版本兼容命令、Python 包名、历史配置目录 | 否，仅兼容 |

暂不重命名 Python 包 `cyber_lobster` 和配置目录 `cyber-lobster`，因为这会影响已有用户配置迁移和历史命令兼容。

## 产品原则

- 用户说的是场景、感受和目标，不一定是准确技术方案。
- 普通用户入口优先 GUI；CLI 面向服务器、高级用户和排障。
- 报错要说明“发生了什么”和“下一步做什么”，不能只暴露异常名。
- 不自动修改用户系统代理、VPN、TUN、路由、DNS 等全局设置。
- 认证请求尽量直连校园网认证服务器，避免环境代理干扰。
- 技术重构不能牺牲双击即用、开机守护、多账号切换、密码不明文这些核心体验。

## 安全边界

- 密码不明文落盘。
- Windows 使用 DPAPI 保护密码。
- Linux 使用本地密钥保护密码，配置文件权限 600。
- macOS 使用当前用户本地密钥保护密码，配置文件权限 600。
- 不收集遥测、密码、cookie、token。
- 不绕过认证、不破解、不共享账号、不突破在线数量限制。
- 不建议在公共电脑保存账号。

## 当前已完成

- Windows GUI 主路径。
- CLI Lite 主入口：`campusnet setup/start/doctor/verify/list`。
- 多账号管理与切换。
- 开机自启动。
- 配置位置与程序位置分离。
- 密码保护和旧明文配置迁移。
- Linux DEB、一键安装脚本和 systemd 模板。
- macOS Apple Silicon / Intel 原生 GUI 安装包。
- Cloudflare Pages 官网：`https://campusnet.journeymind.blog`
- GitHub Actions 云端构建 Windows、Linux 和 macOS 发布包。
- 代理/VPN/TUN 兼容性诊断。

## 下一步路线

### v0.1.x：打磨可交付版本

- 保持 GUI 和 CLI 行为稳定。
- 修正文档、官网、发布包命名不一致问题。
- 补充 Windows 真实 smoke test 和截图。
- 补充 SHA256 校验说明。

### v0.2.x：CLI Lite 工程化

- 整理 CLI 输出风格：默认安静，错误明确。
- 增加可脚本化输出，例如 `--json`。
- 明确 `setup/doctor/verify/watch/status/logout/accounts/switch` 的边界。
- 降低交互菜单在 Linux 用户路径中的存在感。

### v0.3.x：GUI 产品化

- 首页只保留日常操作和清晰状态。
- 诊断结果用“问题 + 建议”展示，而不是纯日志。
- 增加首次使用向导。
- 增加截图和普通用户教程。

## 暂不做

- Apple Developer ID 签名与公证。
- 自动更新。
- 商业化。
- 遥测收集。
- 自动修改代理/VPN/TUN 设置。
- 直接重命名 Python 包和配置目录。
