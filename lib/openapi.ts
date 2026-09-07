import { createOpenAPI } from 'fumadocs-openapi/server';
import type { Document } from 'fumadocs-openapi';
import spec from '../openapi/openapi.json';

/**
 * OpenAPI 数据源：`openapi/openapi.json`（由 openapi.yaml 转换而来，
 * 见 scripts/yaml-to-json.mjs）。
 *
 * 注意：必须用静态 import + 函数式 input，把 spec 打进构建产物。
 * 若传文件路径字符串，fumadocs-openapi 会在**运行时**读文件系统，
 * Node 下正常，但在 Cloudflare Workers（workerd）里没有 fs，所有
 * OpenAPI 页面和搜索路由都会 500。
 *
 * proxyUrl 指向站内代理 `/api/openapi-proxy`：浏览器 fetch 跨域会带 Origin，
 * 而 Bridge 见到 Origin 直接 403；走服务端代理转发则无此问题，
 * 于是 API Playground 的 Try-it 可以真实调用本机 Bridge。
 */
export const openapi = createOpenAPI({
  input: { bridge: () => spec as unknown as Document },
  proxyUrl: '/api/openapi-proxy',
});
