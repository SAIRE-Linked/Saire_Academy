/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  trailingSlash: true,
  poweredByHeader: false,
  async headers() {
    return [{source: '/python-runtime/:path*', headers: [
      {key:'Access-Control-Allow-Origin', value:'*'},
      {key:'Cross-Origin-Resource-Policy', value:'cross-origin'},
      {key:'Cache-Control', value:'public, max-age=31536000, immutable'},
      {key:'X-Content-Type-Options', value:'nosniff'},
    ]}];
  },
  async rewrites() {
    const backend = (process.env.LMS_BACKEND_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
    return [
      { source: '/api/v1/:path*/', destination: `${backend}/api/v1/:path*/` },
      { source: '/accounts/:path*/', destination: `${backend}/accounts/:path*/` },
    ];
  },
};
export default nextConfig;
