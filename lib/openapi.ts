import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createOpenAPI } from 'fumadocs-openapi/server';
import type { Document } from 'fumadocs-openapi';
import { parse } from 'yaml';

/**
 * OpenAPI 唯一数据源为 `openapi/openapi.yaml`（仓库 bot 从 MarginNote
 * 源代码生成）。构建期（Node）同步读入并解析为对象后传给 createOpenAPI。
 *
 * staticSource() 只在 `next build` 期间执行，读 fs 合法；运行时消费的是
 * 已生成的虚拟页面数据，纯静态托管下无 fs 依赖。
 *
 * 调试走 Yaak 一键导入，见 components/yaak-button.tsx。
 */
const spec = parse(
  readFileSync(join(process.cwd(), 'openapi', 'openapi.yaml'), 'utf8'),
) as unknown as Document;

export const openapi = createOpenAPI({
  input: { bridge: () => spec },
});
