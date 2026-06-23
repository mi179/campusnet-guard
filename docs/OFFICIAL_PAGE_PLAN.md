# 官方页面与下载渠道说明

## 当前状态

CampusNet Guard 官网已部署在 Cloudflare Pages：

- 正式域名：`https://campusnet.journeymind.blog`
- Pages 备用域名：`https://campusnet-guard.pages.dev`
- 主下载：GitHub Releases latest
- 国内备用：移动云盘，见 `docs/MIRROR_DOWNLOADS.md`

官网源文件位于仓库 `site/` 目录，推送到 GitHub 后由 Cloudflare Pages 自动部署。

## 官网职责

官网不是完整文档站，当前阶段只做四件事：

1. 让普通用户知道这是什么。
2. 给出 Windows 下载入口。
3. 给出 Linux 源码安装路径。
4. 明确安全提醒和免责声明。

详细教程仍放在 README 和 `docs/` 目录，避免官网维护成本过高。

## 页面内容

### 首页

- 产品名和一句话介绍。
- Windows 下载按钮，优先指向国内快速下载。
- Linux 使用入口，指向 GitHub 仓库。
- GitHub Releases 作为可信源和版本源。
- 常见问题和免责声明。

### 暂不拆分多页面

当前 `site/` 使用单页静态 HTML。项目体量还小，暂不引入路由、构建工具或多页面文档系统。

## 下载渠道设计

| 渠道 | 说明 | 状态 |
|------|------|------|
| 蓝奏云 | 免登录，普通用户优先 | 快速下载 |
| 中国移动云盘 | 国内网盘入口 | 快速下载 |
| 天翼云盘 | 国内网盘入口 | 快速下载 |
| GitHub Releases | 源头，版本记录最完整 | 可信源 |
| Cloudflare Pages 官网 | 下载说明和入口汇总 | 已启用 |
| Cloudflare R2 | 直链对象存储 | 暂缓 |
| 个人博客 | 项目故事和教程入口 | 已启用 |

## R2 暂缓原因

Cloudflare R2 适合放 zip/exe 直链，但当前阶段先不引入：

- 多一个上传和校验流程。
- 需要维护对象命名和历史版本。
- 用户仍应以 GitHub Releases 为可信源。

等发布频率稳定后，再考虑 `dl.journeymind.blog` 或类似子域名承载 R2 下载。

## 安全提醒

所有下载页面都应保持同一口径：

> 请优先从 GitHub Releases 或官网入口下载，不要使用来路不明的 exe 文件。备用网盘可能失效，后续会补充 SHA256 校验。

## Cloudflare Pages 配置

- Repository：`mi179/campusnet-guard`
- Production branch：`main`
- Build command：`exit 0`
- Build output directory：`site`
- Root directory：仓库根目录

部署不依赖本地电脑一直开着。
