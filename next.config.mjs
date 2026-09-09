import { createMDX } from 'fumadocs-mdx/next';

/**
 * 纯静态导出（Cloudflare Pages 免费无限量）：
 * - 所有文档页 / llms 路由构建时预渲染；
 * - /api/search 为静态 JSON 索引，客户端 staticClient 直读；
 * - 无 Try-it Playground，接口调试走 Yaak 一键导入，
 *   见 components/yaak-button.tsx；
 * - redirects() 与静态导出不兼容，重定向走 public/_redirects（Pages 原生支持）。
 */
const config = {
  output: 'export',
  reactStrictMode: true,
};

const withMDX = createMDX();

export default withMDX(config);
