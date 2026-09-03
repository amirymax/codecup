"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { LogoutButton } from "@/components/LogoutButton";
import { nav as t } from "@/messages/ru";
import { cn } from "@/lib/utils";

export interface NavLink {
  label: string;
  href: string;
  key: string;
}

/**
 * Меню для узких экранов.
 *
 * На телефоне логотип, три ссылки, имя и «Выйти» в одну строку не помещаются:
 * ссылки не сжимаются и наезжают на соседей. Поэтому здесь они уходят под
 * кнопку, а в шапке остаются только логотип и аватар.
 */
export function MobileNav({ links, active }: { links: NavLink[]; active: string }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const container = useRef<HTMLDivElement>(null);

  // Переход по ссылке не размонтирует шапку, поэтому закрываем меню сами.
  useEffect(() => setOpen(false), [pathname]);

  // Тап мимо меню закрывает его — как и ожидается на телефоне.
  //
  // Слушатель на документе, а не затемняющая подложка: у шапки backdrop-blur,
  // а такой элемент становится точкой отсчёта для position: fixed внутри
  // себя, и подложка схлопывалась в полоску нулевой высоты.
  useEffect(() => {
    if (!open) return;

    function closeOnOutsideTap(event: PointerEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    }

    document.addEventListener("pointerdown", closeOnOutsideTap);
    return () => document.removeEventListener("pointerdown", closeOnOutsideTap);
  }, [open]);

  return (
    <div ref={container} className="lg:hidden">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={open ? t.menuClose : t.menuOpen}
        className="flex size-9 items-center justify-center rounded-lg border border-line-2
                   text-muted transition-colors hover:border-line-3 hover:text-text"
      >
        <MenuIcon open={open} />
      </button>

      {open && (
        <div
          className="absolute inset-x-0 top-16 z-50 flex flex-col gap-1 border-b border-line
                     bg-ink px-4 py-3 shadow-lg shadow-black/40"
        >
          {links.map((link) => (
            <Link
              key={link.key}
              href={link.href}
              className={cn(
                "rounded-lg px-3 py-2.5 text-[15px] font-medium no-underline",
                active === link.key ? "bg-surface-3 text-text" : "text-muted",
              )}
            >
              {link.label}
            </Link>
          ))}
          <div className="mt-1 border-t border-line pt-3">
            <LogoutButton className="w-full" />
          </div>
        </div>
      )}
    </div>
  );
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      {open ? (
        <path
          d="M6 6l12 12M18 6L6 18"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      ) : (
        <path
          d="M4 7h16M4 12h16M4 17h16"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}
