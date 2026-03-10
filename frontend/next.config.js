/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
import "./src/env.js";

// Backend URL for API proxy.
// NEXT_PUBLIC_BACKEND_BASE_URL must be available at *build* time (Docker build arg or
// baked in). Falls back to the Railway backend domain so local dev still works.
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL ||
  "https://backend-production-3b9f.up.railway.app";

/** @type {import("next").NextConfig} */
const config = {
  devIndicators: false,

  // Proxy /api/* (except /api/auth which is a real Next.js route) and /mock/api/*
  // to the DeerFlow backend.
  // Uses afterFiles so /api/auth/[...all] (a real Next.js route) is matched first.
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [
        {
          source: "/api/:path*",
          destination: `${BACKEND_URL}/api/:path*`,
        },
        // NOTE: /mock/api/* is intentionally NOT proxied — those are Next.js API route
        // handlers that serve static demo thread JSON from public/demo/threads/.
      ],
      fallback: [],
    };
  },
};

export default config;
