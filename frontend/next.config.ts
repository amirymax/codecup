import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone-сборка для Docker: сервер и только нужные зависимости.
  output: "standalone",
  // Значок Next.js в углу экрана. В продакшне его и так нет, но он мешает
  // смотреть вёрстку при разработке.
  devIndicators: false,
  /* config options here */
};

export default nextConfig;
