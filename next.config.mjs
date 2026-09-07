import { createMDX } from 'fumadocs-mdx/next';

/**
 * 纯静态导出（Cloudflare Pages 免费无限量）：
 * - 所有文档页 / llms 路由构建时预渲染；
 * - /api/search 为静态 JSON 索引（staticGET），客户端 staticClient 直读；
 * - Try-it 代理为 Cloudflare Pages Function（functions/api/bridge-proxy.ts，
 *   fumadocs-openapi 原生 createProxy），随 out/ 一起部署，不经 Next 构建；
 *   本地用 `pnpm preview`（wrangler pages dev）联调，`pnpm dev` 无此路由；
 * - redirects() 与静态导出不兼容，重定向走 public/_redirects（Pages 原生支持）。
 */
const config = {
  output: 'export',
  reactStrictMode: true,
};

const withMDX = createMDX();

export default withMDX(config);
