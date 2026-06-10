# Cloudflare Pages 部署说明

Cloudflare Pages 连接 GitHub 后，push 到指定分支会自动部署，不需要本地电脑一直开着。

## A. 产品官网

**正式域名**: https://campusnet.journeymind.blog
**备用地址**: https://campusnet-guard.pages.dev

| 参数 | 值 |
|------|-----|
| Repository | mi179/campusnet-guard |
| Production branch | main |
| Build command | exit 0 |
| Build output directory | site |
| Root directory | (仓库根目录) |

### 部署步骤

1. 登录 Cloudflare Dashboard
2. 进入 Workers & Pages
3. 点击 Create application → Pages → Import existing Git repository
4. 选择 GitHub 仓库 mi179/campusnet-guard
5. 配置构建设置（见上表）
6. 点击 Save and Deploy

### 自定义域名

后续配置。当前使用 Cloudflare 默认域名: campusnet-guard.pages.dev

## B. 博客

| 参数 | 值 |
|------|-----|
| Repository | mi179/cf-pages-blog |
| Production branch | master |
| Build command | npm ci && npm run build |
| Build output directory | public |
| Root directory | (仓库根目录) |

## 使用 GitHub Actions 部署（可选）

如果用 GitHub Actions 部署 Cloudflare Pages，需要把以下变量放在 GitHub Secrets（不要写进代码）：

- `CLOUDFLARE_API_TOKEN` — Cloudflare API Token
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare 账号 ID

## 安全提醒

- **不要把 Cloudflare API Token 写进仓库**
- **不要把 GitHub Token 写进仓库**
- Token 只放在 GitHub Secrets 或 Cloudflare Dashboard

## 国内下载镜像

后续单独做 Cloudflare R2 + 自定义域名方案。

## 文件结构

```
site/
├── index.html      # 首页
├── styles.css      # 样式
├── 404.html        # 404 页面
├── _headers        # HTTP 安全头
└── _redirects      # 重定向规则（可选）
```
