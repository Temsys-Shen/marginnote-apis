# mnapis

MarginNote 本地 Bridge 的 HTTP 接口文档站，Bridge API v0.39-draft。

- Base URL：`http://127.0.0.1:{port}/bridge/v1`。端口每次现查，默认从 42340 起扫 20 个。
- 框架：Fumadocs，Next.js，加 fumadocs-openapi。OpenAPI 虚拟页面加 APIPage。
- 调试：Yaak 一键导入，见 `components/yaak-button.tsx`。

## 目录

```text
./
├── app/                   # Next.js 路由
│   ├── page.tsx           # 落地页
│   ├── docs/[[...slug]]/  # 文档页，手写 MDX 与 OpenAPI 虚拟页分支渲染
│   ├── api/search/        # 站内搜索，构建时导出静态索引
│   └── llms.txt | llms-full.txt | llms.mdx/  # LLM 输出
├── components/
│   ├── api-page.tsx       # createOpenAPIPage，Schema 与示例，Playground 已关闭
│   ├── yaak-button.tsx    # Yaak 一键导入按钮，全站复用同一组件
│   ├── search-dialog.tsx  # 静态搜索对话框，staticClient
│   └── mdx.tsx
├── content/docs/          # 手写文档，指南与规范，加 meta.json 侧边栏
├── lib/
│   ├── openapi.ts         # createOpenAPI，静态 import openapi.json，函数式 input
│   └── source.ts          # loader，手写源加 staticSource groupBy tag
├── openapi/
│   ├── openapi.yaml       # OpenAPI 3.1，仓库 bot 从 MarginNote 源代码生成
│   └── openapi.json       # 同上转 JSON，构建时静态 import，见 scripts/yaml-to-json.mjs
├── scripts/
│   └── yaml-to-json.mjs   # openapi.yaml 转 openapi.json
└── raw/                   # 原始响应存档，本地保存，token 相关文件不提交
```

## 快速开始

```bash
pnpm install
pnpm dev     # 本地预览 http://localhost:3000
pnpm build   # 构建验证，纯静态导出到 out/
pnpm start   # 运行构建产物
pnpm types:check
```

## 部署

Cloudflare Pages，纯静态导出，无需服务端：

```bash
pnpm deploy:pages   # next build 加 wrangler pages deploy out --project-name=mnapis
```

或在 Cloudflare 面板接 GitHub 自动部署，Production branch `main`：

- Root directory 留空
- Build command 为 `pnpm build`
- Output directory 为 `out`
- Environment variables 加 `NODE_VERSION=22`

搜索是构建时导出的静态索引，`app/api/search` 到 `out/api/search`，客户端直读。接口调试走 Yaak 一键导入，`components/yaak-button.tsx`，Data URL 为 GitHub 上的 `openapi/openapi.yaml`。

连通性检查：

```bash
curl -s http://127.0.0.1:42340/bridge/v1/status
TOKEN=$(cat ~/.config/mn-bridge/token)
curl -s http://127.0.0.1:42340/bridge/v1/capabilities -H "Authorization: Bearer $TOKEN" | head -c 300
```

令牌获取：MarginNote 设置 → Lab →「Copy Agent Setup Command」，粘进终端执行。安装码 10 分钟有效，单次使用。

## 用到的 Fumadocs 特性

- fumadocs-openapi：`createOpenAPI` 加 `staticSource({ groupBy: 'tag' })` 虚拟页面，`createOpenAPIPage` 渲染参数与响应 Schema 加多语言代码示例，Playground 已关闭，侧边栏方法徽标走 loader plugin，样式 `fumadocs-openapi/css/preset.css`
- 搜索：构建时静态导出索引加客户端 `staticClient`，全文加面包屑加高亮，纯静态运行
- LLM 输出：`/llms.txt` 索引，`/llms-full.txt` 全量，每页 `MarkdownCopyButton` 加 `/llms.mdx/...` 原文，含 OpenAPI 页降级文本
- MDX 组件：Cards 加 Card，Tabs 加 Tab，Steps 加 Step，Callout，Accordion
- Yaak 导入：`components/yaak-button.tsx` 单一来源，官方 `yaak.app/button/run` 格式，落地页、文档索引、规范页、全部 API 页复用同一组件

## 阅读顺序

1. `/docs`，指南：连接鉴权，标准工作流，错误处理
2. 侧边栏「交互式 API」，Schema 加多语言示例加 Yaak 导入
3. 规范：capabilities，OpenAPI 说明，版本与来源

运行时 `/capabilities` 与本站不一致时，以运行时为准。
