/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    // Browser calls /api/*; Next forwards to the FastAPI backend (no CORS, cookies stay first-party).
    return [{ source: "/api/:path*", destination: `${process.env.API_URL ?? "http://localhost:8000"}/:path*` }];
  },
};
export default nextConfig;
