import { defineCloudflareConfig } from '@opennextjs/cloudflare';

export default defineCloudflareConfig({
  // 默认缓存即可（全站静态预渲染 + 两个动态 API 路由，无需 R2 增量缓存）
});
