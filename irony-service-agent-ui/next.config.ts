import type { NextConfig } from "next";

const config = {
  output: "standalone",
  basePath: "/service",
  // Add other Next.js config options here
} satisfies NextConfig;

export default config;
