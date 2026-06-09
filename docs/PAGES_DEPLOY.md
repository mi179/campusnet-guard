# Cloudflare Pages 部署说明

## 仓库信息

- GitHub 仓库: mi179/campusnet-guard
- 静态文件目录: site/

## 部署步骤

1. 登录 Cloudflare Dashboard
2. 进入 Workers & Pages
3. 点击 Create application → Pages → Import existing Git repository
4. 选择 GitHub 仓库 mi179/campusnet-guard
5. 配置构建设置:
   - Production branch: main
   - Build command: exit 0
   - Build output directory: site
   - Root directory: (留空，使用仓库根目录)
6. 点击 Save and Deploy

## 部署参数

| 参数 | 值 |
|------|-----|
| 项目名 | campusnet-guard |
| Production branch | main |
| Build command | exit 0 |
| Build output directory | site |
| Root directory | (仓库根目录) |

## 自定义域名

后续配置。当前使用 Cloudflare 默认域名: campusnet-guard.pages.dev

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
