import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Do not let `next dev` write frontend/AGENTS.md; the root AGENTS.md covers it.
  agentRules: false,
  // A minimal server for the Docker image (see frontend/Dockerfile).
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
