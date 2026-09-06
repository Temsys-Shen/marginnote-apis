# MarginNote Agent Bridge HTTP 接口文档

MarginNote 4 本地 Agent Bridge（loopback HTTP）的完整 HTTP 接口文档。

- 版本：Bridge API **v0.49** / App 4.5.0 / Guide v0.49（72 路由）
- Base URL：`http://127.0.0.1:{port}/bridge/v1`（端口现查，默认 42340 起扫 20 个）
- 框架：**Fumadocs**（Next.js）+ **fumadocs-openapi**（OpenAPI 虚拟页面 + APIPage + Playground）

## 目录

```text
./
├── app/                   # Next.js 路由
│   ├── page.tsx           # 落地页
│   ├── docs/[[...slug]]/  # 文档页（手写 MDX + OpenAPI 虚拟页分支渲染）
│   ├── api/search/        # 站内搜索
│   ├── api/openapi-proxy/ # 站内代理：让 Playground 真机调用本机 Bridge
│   └── llms.txt | llms-full.txt | llms.mdx/  # LLM 友好输出
├── components/
│   ├── api-page.tsx       # createOpenAPIPage（Schema/示例/Playground）
│   └── mdx.tsx
├── content/docs/          # 手写文档（指南/参考/契约）+ meta.json 侧边栏
├── lib/
│   ├── openapi.ts         # createOpenAPI（input: openapi.yaml）
│   └── source.ts          # loader（手写源 + staticSource groupBy tag）
├── openapi/
│   └── openapi.yaml       # OpenAPI 3.1（由 scripts/build-openapi.py 生成）
├── scripts/
│   └── build-openapi.py   # capabilities → openapi 生成器
└── raw/                   # 原始响应存档（本地，不提交 token 相关文件）
```

## 快速开始

```bash
npm install
npm run dev     # 本地预览 http://localhost:3000
npm run build   # 构建验证
npm run start   # 运行构建产物
npm run types:check
```

连通性检查：

```bash
curl -s http://127.0.0.1:42340/bridge/v1/status
TOKEN=$(cat ~/.config/mn-bridge/token)
curl -s http://127.0.0.1:42340/bridge/v1/capabilities -H "Authorization: Bearer $TOKEN" | head -c 300
```

令牌获取：MarginNote 设置 → Lab →「Copy Agent Setup Command」，粘进终端执行（安装码 10 分钟有效、只能用一次）。

## 用到的 Fumadocs 特性

- **fumadocs-openapi 全套**：`createOpenAPI` + `staticSource({ groupBy: 'tag' })` 虚拟页面（72 操作 → 67 路径页，12 组）、`createOpenAPIPage`（参数/响应 Schema、多语言代码示例、API Playground）、侧边栏方法徽标（loader plugin）、`fumadocs-openapi/css/preset.css`
- **Playground 真机调试**：浏览器跨域自带 Origin 会被 Bridge 403，本站 `/api/openapi-proxy` 在服务端转发（去 Origin、仅放行 loopback），Try-it 可真实调用本机 Bridge（含 120s 超时适配同步大包）
- **搜索**：`createFromSource`，全文 + 面包屑 + 高亮
- **LLM 输出**：`/llms.txt`（索引）、`/llms-full.txt`（全量）、每页 `MarkdownCopyButton` + `/llms.mdx/...` 原文（含 OpenAPI 页降级文本）
- **MDX 组件**：Cards/Card（落地页/索引）、Tabs/Tab（同机/跨设备）、Steps/Step（拆书/对账流程）、Callout（纪律警告）、Accordion（错误清单折叠）
- **OpenAPI 契约再生**：`python3 scripts/build-openapi.py`（输入 `raw/capabilities.json`；已修复同 path 多 method 合并，避免 YAML 重复键）

## 阅读顺序

1. `/docs` → 指南：连接鉴权 → 标准工作流 → 错误纪律
2. 侧边栏「交互式 API」：12 组 67 页交互式参考（Schema + 示例 + Try-it）
3. 契约：capabilities 附录、OpenAPI 说明、版本与来源

权威顺序：**运行时 `/capabilities` ＞ 运行时 `GET /guide` ＞ 本站**。
