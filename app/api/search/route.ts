import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

// 静态模式：构建时把全量索引导出为静态 JSON，客户端 staticClient 直接读取，
// 无需服务端（见 components/search-dialog.tsx）。Cloudflare Pages 纯静态即可。
export const revalidate = false;
export const { staticGET: GET } = createFromSource(source);
