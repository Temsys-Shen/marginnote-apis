import { loader } from 'fumadocs-core/source';
import { lucideIconsPlugin } from 'fumadocs-core/source/lucide-icons';
import { docsContentRoute, docsRoute } from './shared';
import { defineDocs } from 'fumadocs-mdx/macro';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';
import { openapi } from './openapi';

const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    schema: pageSchema,
    postprocess: {
      includeProcessedMarkdown: true,
    },
  },
  meta: {
    schema: metaSchema,
  },
});

// 手写 MDX（guides / reference / contract）+ OpenAPI 虚拟页面（groupBy tag）合并为同一 source
export const source = loader(
  {
    docs: docs.toFumadocsSource(),
    openapi: await openapi.staticSource({
      groupBy: 'tag',
    }),
  },
  {
    baseUrl: docsRoute,
    plugins: [openapi.loaderPlugin(), lucideIconsPlugin()],
  },
);

type AnyPage = ReturnType<typeof source.getPage> extends infer T ? T : never;

export function getPageMarkdownUrl(page: NonNullable<AnyPage>) {
  const segments = [...page.slugs, 'content.md'];
  return {
    segments,
    url: `/${docsContentRoute.split('/').filter(Boolean).join('/')}/${segments.join('/')}`,
  };
}

export async function getLLMText(page: NonNullable<AnyPage>): Promise<string> {
  const data = page.data as { title?: string; description?: string; getText?: (key: string) => Promise<string> };
  try {
    const processed = await data.getText?.('processed');
    if (processed) return `# ${page.data.title} (${page.url})\n\n${processed}`;
  } catch {
    // OpenAPI 虚拟页面没有 processed 文本，降级为标题 + 描述
  }
  return `# ${page.data.title} (${page.url})\n\n${data.description ?? ''}`;
}
