import { createMDX } from 'fumadocs-mdx/next';

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: '/docs/api',
        destination: '/docs/system/get-status',
        permanent: false,
      },
    ];
  },
};

const withMDX = createMDX();

export default withMDX(config);
