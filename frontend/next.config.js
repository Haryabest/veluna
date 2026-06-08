/** @type {import('next').NextConfig} */
const fs = require('fs');
const path = require('path');

function resolveBackendPort() {
  if (process.env.BACKEND_PORT) return process.env.BACKEND_PORT;
  const envLocal = path.join(__dirname, '.env.local');
  if (fs.existsSync(envLocal)) {
    const m = fs.readFileSync(envLocal, 'utf8').match(/^BACKEND_PORT=(.+)$/m);
    if (m) return m[1].trim();
  }
  // Docker maps host 8020 -> container 8000
  return '8020';
}

const backendPort = resolveBackendPort();
const backendHost = process.env.BACKEND_HOST || '127.0.0.1';
const minioHost = process.env.MINIO_HOST || backendHost;
const minioPort = process.env.MINIO_PORT || '9000';

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
      {
        source: '/media/:path*',
        destination: `http://${minioHost}:${minioPort}/veluna/:path*`,
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
