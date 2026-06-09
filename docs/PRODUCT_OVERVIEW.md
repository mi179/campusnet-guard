# CampusNet Guard 产品定位

## 产品信息

- **产品名**：CampusNet Guard（校园网守护）
- **技术描述**：适配 Ruijie ePortal 的校园网自动认证与断网重连工具
- **内部命令/包名**：cyber-lobster（后续版本可能统一重命名）
- **开源协议**：MIT

## 推荐路线：公益开源

当前阶段推荐走**公益开源路线**：

- 不商业化
- 不收集遥测/密码/cookie/token
- 明确免责声明
- 接受 Issue，但要求脱敏日志
- 不保证所有 Ruijie ePortal 版本兼容

## 用户分层

### Windows 普通用户

- 下载 zip → 解压 → 双击 GUI → 添加账号 → 开启守护
- 不需要 Python、不需要命令行、不需要安装
- 可选开机自启动

### Linux 高级用户

- 源码安装，CLI 为主路径
- 适合 NAS/软路由/小主机/服务器
- 可配合 tmux/screen/systemd 后台运行

### 高级设备用户

- NAS、软路由、工控机、小主机
- 需要长期守护、非交互运行
- 适合 tmux/screen 后台模式

## 平台支持

| 平台 | 状态 | 说明 |
|------|------|------|
| Windows | ✅ 支持 | GUI + CLI，推荐 GUI |
| Linux | ✅ 支持 | CLI，源码安装 |
| macOS | ⚠️ 未验证 | 不作为当前支持平台 |

## 安全边界

- ✅ 密码加密存储（DPAPI / local-key + HMAC）
- ✅ 配置文件权限 600
- ✅ 不收集遥测
- ✅ 不收集密码/cookie/token
- ✅ 不绕过认证系统
- ✅ 不破解、不共享账号
- ✅ 不突破在线数量限制

## 当前版本（v0.1.0）该做

- ✅ Windows GUI 文档
- ✅ Linux CLI 文档
- ✅ 免责声明
- ✅ 下载渠道说明
- ✅ CampusNet Guard 品牌统一
- ✅ 认证服务器地址公众化

## 当前版本不该做

- ❌ macOS 支持
- ❌ 商业化
- ❌ 代码签名
- ❌ 自动更新机制
- ❌ 遥测收集
- ❌ 改 Python 包名/命令名

## 下一版本路线图

### v0.10.0

- `campusnet` CLI 别名
- CLI `stop` 子命令
- `--no-interactive` 后台模式
- `account remove` 子命令
- systemd user service

### v1.0.0

- CLI 极简化（account/config 子命令组）
- JSON 输出
- macOS 支持（如果验证通过）
- 考虑重命名 CLI 命令和 EXE

## 下载渠道

| 渠道 | 说明 | 优先级 |
|------|------|--------|
| GitHub Releases | 源头，版本记录最完整 | 主 |
| Cloudflare Pages 官方页面 | 项目介绍 + 下载入口 | 备用（计划中） |
| Cloudflare R2 | exe/zip 直链，CDN 加速 | 备用（计划中） |

## 免责声明要点

- 仅用于用户自己的校园网账号自动认证和断网重连
- 不绕过认证、不破解、不共享账号
- 不突破在线设备数量限制
- 学校/运营商策略由网络系统决定
- 不保证适配所有 Ruijie ePortal 版本
- 不建议在公共电脑保存账号
- 使用者自行承担账号安全和网络合规责任
