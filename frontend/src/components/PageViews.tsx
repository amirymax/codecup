"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { track } from "@/lib/analytics";

/**
 * Один просмотр на каждый переход по сайту.
 *
 * Считаем в браузере, а не на сервере: так в статистику не попадают ни боты,
 * которые не выполняют JavaScript, ни запросы самого Next.js за данными.
 */
export function PageViews() {
  const pathname = usePathname();

  useEffect(() => {
    // Хождения администратора по админке — это не трафик сайта.
    if (pathname.startsWith("/admin")) return;
    track("pageview", pathname);
  }, [pathname]);

  return null;
}
