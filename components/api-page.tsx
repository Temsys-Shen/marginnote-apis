'use client';
import { createOpenAPIPage } from 'fumadocs-openapi/ui';

/**
 * OpenAPI 交互页面：请求/响应 Schema、多语言代码示例。
 *
 * 注意：Playground（Try-it）已关闭——它需要站内代理转发（去掉浏览器自带的
 * Origin 头，否则 Bridge 直接 403），而纯静态托管没有服务端。
 * 云上调试请用 curl（见各指南页示例）；本机有 Bridge 时可用 `next dev` 模式。
 */
export const OpenAPIPage = createOpenAPIPage({
  playground: {
    enabled: false,
  },
});
