# mnapis

MarginNote HTTP 接口文档站（本地 Agent Bridge，Bridge API v0.49 / App 4.5.0 / 72 路由）。

- 版本：Bridge API **v0.49** / App 4.5.0 / Guide v0.49（72 路由）
- Base URL：`http://127.0.0.1:{port}/bridge/v1`（端口现查，默认 42340 起扫 20 个）
- 框架：**Fumadocs**（Next.js）+ **fumadocs-openapi**（OpenAPI 虚拟页面 + APIPage）

## 目录

```text
./
├── app/                   # Next.js 路由
│   ├── page.tsx           # 落地页
│   ├── docs/[[...slug]]/  # 文档页（手写 MDX + OpenAPI 虚拟页分支渲染）
│   ├── api/search/        # 站内搜索（构建时导出静态索引）
│   └── llms.txt | llms-full.txt | llms.mdx/  # LLM 友好输出
├── components/
│   ├── api-page.tsx       # createOpenAPIPage（Schema/示例，Playground 已关闭）
│   ├── search-dialog.tsx  # 静态搜索对话框（staticClient）
│   └── mdx.tsx
├── content/docs/          # 手写文档（指南/参考/契约）+ meta.json 侧边栏
├── lib/
│   ├── openapi.ts         # createOpenAPI（静态 import openapi.json，函数式 input）
│   └── source.ts          # loader（手写源 + staticSource groupBy tag）
├── openapi/
│   ├── openapi.yaml       # OpenAPI 3.1（由 scripts/build-openapi.py 生成）
│   └── openapi.json       # 同上转 JSON（构建时静态 import，见 scripts/yaml-to-json.mjs）
├── scripts/
│   ├── build-openapi.py   # capabilities → openapi.yaml 生成器
│   └── yaml-to-json.mjs   # openapi.yaml → openapi.json
└── raw/                   # 原始响应存档（本地，不提交 token 相关文件）
```

## 快速开始

```bash
npm install
npm run dev     # 本地预览 http://localhost:3000
npm run build   # 构建验证（纯静态导出到 out/）
npm run start   # 运行构建产物
npm run types:check
```

## 部署（Cloudflare Pages，免费无限量）

本站是纯静态导出，无需服务端：

```bash
npm run deploy   # next build + wrangler pages deploy out --project-name=mnapis
```

或在 Cloudflare 面板接 GitHub 自动部署（Production branch `main`）：

- **Root directory**：留空
- **Build command**：`npm run build`
- **Output directory**：`out`
- **Environment variables**：`NODE_VERSION=22`

搜索是构建时导出的静态索引（`app/api/search` → `out/api/search`，客户端直读），
Try-it 已关闭（纯静态无服务端转发 Origin，云上本来也连不到本机 Bridge）。

连通性检查：

```bash
curl -s http://127.0.0.1:42340/bridge/v1/status
TOKEN=$(cat ~/.config/mn-bridge/token)
curl -s http://127.0.0.1:42340/bridge/v1/capabilities -H "Authorization: Bearer $TOKEN" | head -c 300
```

令牌获取：MarginNote 设置 → Lab →「Copy Agent Setup Command」，粘进终端执行（安装码 10 分钟有效、只能用一次）。

## 用到的 Fumadocs 特性

- **fumadocs-openapi 全套**：`createOpenAPI` + `staticSource({ groupBy: 'tag' })` 虚拟页面（72 操作 → 67 路径页，12 组）、`createOpenAPIPage`（参数/响应 Schema、多语言代码示例）、侧边栏方法徽标（loader plugin）、`fumadocs-openapi/css/preset.css`
- **搜索**：构建时静态导出索引 + 客户端 `staticClient`，全文 + 面包屑 + 高亮，纯静态即可
- **LLM 输出**：`/llms.txt`（索引）、`/llms-full.txt`（全量）、每页 `MarkdownCopyButton` + `/llms.mdx/...` 原文（含 OpenAPI 页降级文本）
- **MDX 组件**：Cards/Card（落地页/索引）、Tabs/Tab（同机/跨设备）、Steps/Step（拆书/对账流程）、Callout（纪律警告）、Accordion（错误清单折叠）
- **OpenAPI 契约再生**：`python3 scripts/build-openapi.py`（输入 `raw/capabilities.json`；已修复同 path 多 method 合并，避免 YAML 重复键）

## 阅读顺序

1. `/docs` → 指南：连接鉴权 → 标准工作流 → 错误纪律
2. 侧边栏「交互式 API」：12 组 67 页交互式参考（Schema + 多语言示例）
3. 契约：capabilities 附录、OpenAPI 说明、版本与来源

权威顺序：**运行时 `/capabilities` ＞ 运行时 `GET /guide` ＞ 本站**。
