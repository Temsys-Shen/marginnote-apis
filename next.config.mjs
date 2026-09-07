import { createMDX } from 'fumadocs-mdx/next';

/**
 * 纯静态导出（Cloudflare Pages 免费无限量）：
 * - 所有文档页 / llms 路由构建时预渲染；
 * - /api/search 为静态 JSON 索引（staticGET），客户端 staticClient 直读；
 * - 无动态路由：openapi-proxy 已移除（云上本来也连不到本机 Bridge），
 *   Playground 一并关闭，Try-it 只在本地 `next dev` + 直连 Bridge 时可用（见 contract/openapi）。
 * - redirects() 与静态导出不兼容，重定向走 public/_redirects（Pages 原生支持）。
 */
const config = {
  output: 'export',
  reactStrictMode: true,
};

const withMDX = createMDX();

export default withMDX(config);
