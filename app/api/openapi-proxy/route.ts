/**
 * 站内 OpenAPI 代理：让 API Playground 的 Try-it 真实调用本机 Bridge。
 *
 * 为什么需要它：
 * - 浏览器跨域 fetch 会自动带 Origin 头，而 Bridge 见到 Origin 直接 403（FORBIDDEN_ORIGIN）；
 * - 服务端转发不带 Origin，鉴权只看 Authorization，天然绕过该限制。
 *
 * 协议（与 fumadocs-openapi playground fetcher 约定一致）：
 * - `?url=<目标完整 URL>`，原方法 / 请求头 / Body 原样转发；
 * - 仅允许 loopback 目标（127.0.0.1 / localhost / ::1），防止被当成开放代理。
 */
const LOOPBACK = new Set(['127.0.0.1', 'localhost', '::1']);

function pickResponseHeaders(upstream: Headers): Headers {
  const out = new Headers();
  const pass = ['content-type', 'content-length', 'cache-control'];
  for (const key of pass) {
    const value = upstream.get(key);
    if (value) out.set(key, value);
  }
  return out;
}

async function proxy(req: Request): Promise<Response> {
  const target = new URL(req.url).searchParams.get('url');
  if (!target) {
    return Response.json({ error: 'missing ?url=' }, { status: 400 });
  }

  let parsed: URL;
  try {
    parsed = new URL(target);
  } catch {
    return Response.json({ error: 'invalid url' }, { status: 400 });
  }
  if (!LOOPBACK.has(parsed.hostname)) {
    return Response.json({ error: 'only loopback targets are allowed' }, { status: 403 });
  }

  const headers = new Headers(req.headers);
  headers.delete('host');
  headers.delete('origin');
  headers.delete('referer');
  headers.delete('cookie');
  headers.delete('content-length');

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: req.method === 'GET' || req.method === 'HEAD' ? undefined : await req.arrayBuffer(),
    });
  } catch (e) {
    const message = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
    return Response.json(
      { error: `cannot reach Bridge at ${parsed.host}（MarginNote 是否在前台运行？）: ${message}` },
      { status: 502 },
    );
  }

  return new Response(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: pickResponseHeaders(upstream.headers),
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
