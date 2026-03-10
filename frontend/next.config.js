/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
import "./src/env.js";

// Backend URL — can be overridden at build time via NEXT_PUBLIC_BACKEND_BASE_URL.
// Falls back to Railway proxy rewrites (afterFiles) so the app works without
// baking the URL into the bundle.
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "";

/** @type {import("next").NextConfig} */
const config = {
  devIndicators: false,

  // Proxy /api/* (except /api/auth which is a real Next.js route) and /mock/api/*
  // to the DeerFlow backend. This lets the frontend work without build-time env vars.
  async rewrites() {
    if (!BACKEND_URL) {
      // No backend URL — rewrites disabled (dev or static-only mode)
      return [];
    }
    return {
      beforeFiles: [],
      // afterFiles: checked AFTER static files and Next.js routes.
      // /api/auth/[...all] exists as a real route so it wins; everything else proxies.
      afterFiles: [
        {
          source: "/api/:path*",
          destination: `${BACKEND_URL}/api/:path*`,
        },
        {
          source: "/mock/api/:path*",
          destination: `${BACKEND_URL}/mock/api/:path*`,
        },
      ],
      fallback: [],
    };
  },
};

export default config;
