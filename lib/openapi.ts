import { createOpenAPI } from 'fumadocs-openapi/server';

/**
 * OpenAPI 数据源：`openapi/openapi.yaml`（72 路由，由 scripts/build-openapi.py 生成）。
 *
 * proxyUrl 指向站内代理 `/api/openapi-proxy`：浏览器 fetch 跨域会带 Origin，
 * 而 Bridge 见到 Origin 直接 403；走服务端代理转发则无此问题，
 * 于是 API Playground 的 Try-it 可以真实调用本机 Bridge。
 */
export const openapi = createOpenAPI({
  input: ['./openapi/openapi.yaml'],
  proxyUrl: '/api/openapi-proxy',
});
