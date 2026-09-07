#!/usr/bin/env node
// openapi.yaml -> openapi.json（给 lib/openapi.ts 做静态 import 用，
// 避免 workerd 运行时读文件系统）。
import { readFile, writeFile } from 'node:fs/promises';
import { parse } from 'yaml';

const src = new URL('../openapi/openapi.yaml', import.meta.url);
const dst = new URL('../openapi/openapi.json', import.meta.url);

const text = await readFile(src, 'utf8');
const doc = parse(text);
await writeFile(dst, JSON.stringify(doc, null, 2) + '\n');
console.log(`wrote ${dst.pathname}`);
