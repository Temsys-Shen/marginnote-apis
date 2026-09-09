import { createOpenAPI } from 'fumadocs-openapi/server';
import type { Document } from 'fumadocs-openapi';
import spec from '../openapi/openapi.json';

/**
 * OpenAPI 数据源为 `openapi/openapi.json`，由 openapi.yaml 转换而来，
 * 见 scripts/yaml-to-json.mjs。openapi.yaml 由仓库 bot 从 MarginNote
 * 源代码生成。
 *
 * 用静态 import 加函数式 input，把 spec 打进构建产物。传文件路径字符串时，
 * fumadocs-openapi 会在运行时读文件系统，纯静态托管下没有可读的 fs。
 *
 * 调试走 Yaak 一键导入，见 components/yaak-button.tsx。
 */
export const openapi = createOpenAPI({
  input: { bridge: () => spec as unknown as Document },
});
