/** @type {import('next').NextConfig} */
const backendPort = process.env.BACKEND_PORT || '8000';
const backendHost = process.env.BACKEND_HOST || '127.0.0.1';

const nextConfig = {
  output: 'standalone',
  // Pinggy tunnel opens Mini App from a different host than localhost
  allowedDevOrigins: ['*.run.pinggy-free.link'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `http://${backendHost}:${backendPort}/api/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
      { protocol: 'http', hostname: '127.0.0.1' },
      { protocol: 'http', hostname: 'localhost' },
    ],
  },
};

module.exports = nextConfig;
