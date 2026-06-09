# 官方页面方案

CampusNet Guard（校园网守护）适配 Ruijie ePortal 的校园网自动认证与断网重连工具。

> 内部命令和安装包文件名仍为 `cyber-lobster`，后续版本可能统一重命名。

## 技术选型

使用 **Cloudflare Pages** 托管静态官方页面。

### 为什么选 Cloudflare Pages

- **静态托管**：HTML/Markdown，不需要服务器
- **免费额度**：个人项目完全够用
- **自定义域名**：可以绑定自己的域名
- **全球 CDN**：访问速度不错
- **自动部署**：推送到 Git 仓库自动更新

## 页面内容

官方页面应包含以下内容：

### 首页
- 项目名称和一句话介绍
- 下载按钮（Windows EXE）
- 功能特性列表
- 截图/演示

### 下载页
- GitHub Releases 主链接
- 备用下载渠道说明
- 各平台下载说明

### 教程页
- Windows 快速开始（图文）
- Linux 安装指南
- 常见问题解答

### 免责声明页
- 使用范围和限制
- 用户责任
- 安全说明

### 关于页
- GitHub 项目链接
- Issue 反馈入口
- 版本历史

## 下载渠道设计

### 主渠道：GitHub Releases

- 作为源头，版本记录最完整
- 所有其他渠道都应链接回 GitHub Releases

### 备用渠道

| 渠道 | 说明 | 适用场景 | 状态 |
|------|------|---------|------|
| Cloudflare Pages 官方页面 | 中转说明 + 备用链接入口 | 国内用户 | 计划中 |
| Cloudflare R2 + 自定义域名 | exe/zip 直链 | 国内下载 | 计划中 |
| GitHub Release 文件代理 | 临时备用 | 临时 | 可用性不稳定 |
| 个人博客页面 | 多个下载入口汇总 | 国内用户 | 计划中 |

### Cloudflare R2 方案

R2 是 Cloudflare 的对象存储服务，适合放 exe/zip 文件：

- 免费额度：10 GB 存储 + 1000 万次读取/月
- 可以绑定自定义域名
- 国内访问速度尚可
- 适合放发布包的直链

使用方式：
1. 上传 exe/zip 到 R2 存储桶
2. 绑定自定义域名（如 `dl.cyber-lobster.example.com`）
3. 在官方页面提供直链下载

## 域名方案

建议域名（待注册）：

- `cyber-lobster.pages.dev`（Cloudflare Pages 默认域名）
- `cyber-lobster.example.com`（自定义域名，如果有）

## 部署步骤

1. 创建 Cloudflare Pages 项目
2. 连接 GitHub 仓库（或单独的 pages 仓库）
3. 配置自定义域名（可选）
4. 推送代码自动部署

## 安全提醒

在所有下载页面都要提醒：

> ⚠️ 请只从 GitHub Releases 或官方页面下载，不要使用来路不明的 exe 文件。
