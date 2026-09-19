/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Local development may proxy the private sandbox API through the same
  // origin. This avoids exposing a browser directly to an arbitrary local
  // backend port. Production remains direct unless an operator explicitly
  // configures AGENTOS_API_PROXY_TARGET at deployment time.
  async rewrites() {
    const target = process.env.AGENTOS_API_PROXY_TARGET;
    if (!target) return [];
    return [{ source: "/agentos-api/:path*", destination: `${target}/:path*` }];
  },
};

export default nextConfig;
