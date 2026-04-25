import { PHASE_DEVELOPMENT_SERVER } from "next/constants.js";

export default function nextConfig(phase) {
  const isDevelopmentServer = phase === PHASE_DEVELOPMENT_SERVER;

  /** @type {import("next").NextConfig} */
  const config = {
    // Keep development on Next's default `.next` path on Windows.
    // Production build/start still uses a dedicated output folder so validation
    // builds do not collide with an active local dev server.
    distDir: isDevelopmentServer ? ".next" : ".next-build",
    reactStrictMode: true,
  };

  return config;
}
