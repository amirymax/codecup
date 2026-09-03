import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import { Logo } from "@/components/Logo";
import { LogoutButton } from "@/components/LogoutButton";
import { MobileNav, type NavLink } from "@/components/MobileNav";
import { nav } from "@/messages/ru";
import { cn } from "@/lib/utils";
import type { User } from "@/lib/api/types";

type Active = "contests" | "profile" | "admin" | "";

/**
 * Шапка сайта в трёх вариантах: гость, участник, администратор.
 * Вариант выбирается по пользователю, а не приходит параметром, — так
 * страница не может нарисовать админское меню обычному участнику.
 */
export function Navbar({ user, active = "" }: { user: User | null; active?: Active }) {
  const links: NavLink[] = [
    { label: nav.contests, href: "/", key: "contests" },
  ];

  if (user) {
    links.push({ label: nav.mySubmissions, href: "/profile", key: "profile" });
  }
  if (user?.is_admin) {
    links.push({ label: nav.dashboard, href: "/admin", key: "admin" });
  }

  return (
    <nav
      className="sticky top-0 z-50 flex h-16 items-center justify-between gap-3 border-b
                 border-line bg-ink/85 px-4 backdrop-blur-md sm:gap-4 sm:px-6 lg:px-10"
    >
      <Logo />

      {/* Полная шапка требует ~745px: логотип, три ссылки, имя и «Выйти».
          Ниже этого они наезжают друг на друга, поэтому уходят в меню. */}
      <div className="hidden min-w-0 flex-1 items-center justify-center gap-1 lg:flex">
        {links.map((link) => (
          <Link
            key={link.key}
            href={link.href}
            className={cn(
              "rounded-[7px] px-3.5 py-2 text-sm font-medium whitespace-nowrap no-underline",
              "transition-colors hover:bg-surface-3 hover:text-text",
              active === link.key ? "bg-surface-3 text-text" : "text-muted",
            )}
          >
            {link.label}
          </Link>
        ))}
      </div>

      <div className="flex shrink-0 items-center gap-2 lg:gap-2.5">
        {user ? (
          <>
            <Link
              href="/profile"
              className="flex items-center gap-2.5 rounded-full border border-line-2 py-1.5
                         pr-1.5 pl-1.5 no-underline transition-colors hover:border-line-3
                         hover:bg-surface-3 lg:pr-3"
            >
              <Avatar name={user.display_name} />
              <span className="hidden text-[13px] font-medium text-text-2 lg:inline">
                {user.display_name}
              </span>
            </Link>
            <div className="hidden lg:block">
              <LogoutButton />
            </div>
            <MobileNav links={links} active={active} />
          </>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-2 rounded-lg bg-blue px-4 py-2.5 text-sm
                       font-semibold text-white no-underline transition-colors
                       hover:bg-blue-dark"
          >
            <TelegramIcon />
            {nav.login}
          </Link>
        )}
      </div>
    </nav>
  );
}

function TelegramIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M21.5 3.5L2.5 11l6 2.3m13-9.8l-4 17-6.7-5.2m10.7-11.8l-10.7 11.8m0 0L9.3 20"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
