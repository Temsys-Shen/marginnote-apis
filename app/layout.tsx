import { RootProvider } from 'fumadocs-ui/provider/next';
import StaticSearchDialog from '@/components/search-dialog';
import './global.css';

export const metadata = {
  title: {
    template: '%s | mnapis',
    default: 'mnapis',
  },
  description: 'MarginNote 本地 Bridge HTTP 接口文档',
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider
          search={{
            SearchDialog: StaticSearchDialog,
          }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
