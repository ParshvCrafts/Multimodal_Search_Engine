import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.asos-media.com' },
      { protocol: 'https', hostname: '**.asos-media.com' },
      { protocol: 'https', hostname: 'img.asos-media.com' },
    ],
  },
}

export default nextConfig
