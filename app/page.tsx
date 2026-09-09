import Link from 'next/link';
import { Card, Cards } from 'fumadocs-ui/components/card';
import { YaakButton } from '@/components/yaak-button';

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col justify-center px-4 py-16 text-center">
      <h1 className="mb-4 text-4xl font-bold">mnapis</h1>
      <p className="text-fd-muted-foreground mb-8">
        MarginNote 本地 Bridge HTTP 接口文档 · Bridge API v0.39-draft
      </p>
      <div className="mx-auto w-full max-w-3xl text-left">
        <Cards>
          <Card title="连接与鉴权" href="/docs/guide/auth-discovery" />
          <Card title="标准工作流" href="/docs/guide/workflows" />
          <Card title="交互式 API 参考" href="/docs/api" />
          <Card title="运行时能力" href="/docs/contract/capabilities" />
        </Cards>
      </div>
      <p className="text-fd-muted-foreground mt-8 text-sm">
        Base URL <code>http://127.0.0.1:{'{port}'}/bridge/v1</code> · 除公开端点外 Bearer
        鉴权 · 请求不带 Origin 头
      </p>
      <div className="mt-4 flex justify-center">
        <YaakButton />
      </div>
      <p className="mt-2 text-sm">
        <Link href="/docs" className="font-medium underline">
          进入文档 →
        </Link>
      </p>
    </main>
  );
}
