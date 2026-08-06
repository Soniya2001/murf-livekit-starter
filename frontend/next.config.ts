import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    // These warnings come from upstream LiveKit/AI UI components, not our code.
    ignoreDuringBuilds: true,
  },
  transpilePackages: ['streamdown', 'remark-cjk-friendly-gfm-strikethrough', 'remark-cjk-friendly'],
};

export default nextConfig;
