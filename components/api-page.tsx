'use client';
import { createOpenAPIPage } from 'fumadocs-openapi/ui';

/**
 * OpenAPI 交互页面，渲染参数、请求体、响应 Schema 与多语言代码示例。
 * Playground 已关闭，调试走 Yaak 一键导入，见 components/yaak-button.tsx，
 * 挂载在每页头部。
 */
export const OpenAPIPage = createOpenAPIPage({
  playground: {
    enabled: false,
  },
});
