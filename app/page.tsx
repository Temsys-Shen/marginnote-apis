import Link from 'next/link';
import { Card, Cards } from 'fumadocs-ui/components/card';

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col justify-center px-4 py-16 text-center">
      <h1 className="mb-4 text-4xl font-bold">mnapis</h1>
      <p className="text-fd-muted-foreground mb-8">
        MarginNote HTTP 接口文档 · Bridge API v0.49 · App 4.5.0 · 72 路由
      </p>
      <div className="mx-auto w-full max-w-3xl text-left">
        <Cards>
          <Card title="快速开始：连接与鉴权" href="/docs/guide/auth-discovery" />
          <Card title="标准工作流：拆书 / 目录 / 整理" href="/docs/guide/workflows" />
          <Card title="交互式 API 参考（72 路由）" href="/docs/api" />
          <Card title="运行时能力契约" href="/docs/contract/capabilities" />
        </Cards>
      </div>
      <p className="text-fd-muted-foreground mt-8 text-sm">
        Base URL <code>http://127.0.0.1:{'{port}'}/bridge/v1</code> · 除{' '}
        <code>GET /status</code> 外一律 Bearer 鉴权 · 不要带 Origin 头
      </p>
      <p className="mt-2 text-sm">
        <Link href="/docs" className="font-medium underline">
          进入文档 →
        </Link>
      </p>
    </main>
  );
}
