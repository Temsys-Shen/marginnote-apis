import { createOpenAPI } from 'fumadocs-openapi/server';
import type { Document } from 'fumadocs-openapi';
import spec from '../openapi/openapi.json';

/**
 * OpenAPI 数据源：`openapi/openapi.json`（由 openapi.yaml 转换而来，
 * 见 scripts/yaml-to-json.mjs）。
 *
 * 注意：必须用静态 import + 函数式 input，把 spec 打进构建产物。
 * 若传文件路径字符串，fumadocs-openapi 会在**运行时**读文件系统，
 * 纯静态托管（Cloudflare Pages）下没有可读的 fs。
 */
export const openapi = createOpenAPI({
  input: { bridge: () => spec as unknown as Document },
});
