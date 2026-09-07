import { openapi } from '../../lib/openapi';

/**
 * Bridge Try-it 官方代理（fumadocs-openapi 原生 `createProxy`，零自造）：
 * 浏览器 fetch 自带 Origin 头会被 Bridge 直接 403，
 * 由该同源函数经服务端转发，转发请求不带浏览器 Origin。
 *
 * 安全：只允许本机回环目标 + `/bridge/v1` 路径，防止被当开放代理（SSRF）。
 *
 * 形态说明：本站是 `output: 'export'` 纯静态导出，Next Route Handler
 * 会破坏构建，因此代理落在 Cloudflare Pages Function（随 `out/` 一起部署），
 * 本地用 `pnpm preview`（wrangler pages dev）联调，云上部署直接可用。
 */
/**
 * Workers 运行时兼容处理：fumadocs-openapi 的 createProxy 内部会用
 * `new Request(url, { cache: 'no-cache', … })`，但 Workers 的 Request
 * 不支持 `no-cache` 这种写法，构造时直接抛错。下面只是在调用官方代理之前，
 * 把这种写法去掉（代理本来就不缓存，去掉后行为不变）。
 * 代理逻辑本身仍全部走官方 createProxy，这里没有自己写转发。
 */
const NativeRequest = globalThis.Request;
class CompatibleRequest extends NativeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    if (init && 'cache' in init) {
      const { cache: _removed, ...rest } = init;
      init = rest;
    }
    super(input as RequestInfo, init);
  }
}
globalThis.Request = CompatibleRequest as typeof Request;

const proxy = openapi.createProxy({
  allowedOrigins: [/^http:\/\/127\.0\.0\.1:\d+$/, /^http:\/\/localhost:\d+$/],
  filterRequest: (request) => {
    const url = new URL(request.url);
    return url.pathname.startsWith('/bridge/v1/');
  },
});

export function onRequest(context: { request: Request }): Promise<Response> {
  return proxy.handle(context.request);
}
