import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';

export const metadata = {
  title: {
    template: '%s | MarginNote Agent Bridge',
    default: 'MarginNote Agent Bridge HTTP API',
  },
  description: 'MarginNote 4 本地 Agent Bridge 完整 HTTP 接口文档（Bridge API v0.49 / 72 路由）',
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
