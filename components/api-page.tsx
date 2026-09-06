'use client';
import { createOpenAPIPage } from 'fumadocs-openapi/ui';

/**
 * OpenAPI 交互页面：请求/响应 Schema、curl/Python/JS 等多语言示例、
 * API Playground（Try-it）。Playground 经站内代理真实调用本机 Bridge，
 * 超时放宽到 120s（同步 prepare 大包阻塞可达数分钟）。
 */
export const OpenAPIPage = createOpenAPIPage({
  playground: {
    enabled: true,
    fetchOptions: {
      proxyUrl: '/api/openapi-proxy',
      requestTimeout: 120,
    },
  },
});
