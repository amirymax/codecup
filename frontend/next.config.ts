import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone-сборка для Docker: сервер и только нужные зависимости.
  output: "standalone",
  /* config options here */
};

export default nextConfig;
