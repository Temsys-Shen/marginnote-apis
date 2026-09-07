'use client';
import { createOpenAPIPage } from 'fumadocs-openapi/ui';

/**
 * OpenAPI 交互页面：参数/请求体/响应 Schema、多语言代码示例、Playground。
 *
 * Playground（Try-it）走 fumadocs-openapi 原生能力：auth（Bearer）输入框、
 * 参数/请求体表单、发送与响应展示，token 由 fumadocs 存 localStorage。
 * 浏览器自带 Origin 头会被 Bridge 直接 403，因此发送统一走同源官方代理
 * （`openapi.createProxy`，见 functions/api/bridge-proxy.ts），由服务端转发、
 * 不带浏览器 Origin。代理 allowlist 只放本机回环 + bridge 路径，防 SSRF。
 */
export const OpenAPIPage = createOpenAPIPage({
  playground: {
    enabled: true,
  },
});
