"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { logout } from "@/lib/api/auth";
import { cn } from "@/lib/utils";
import { nav } from "@/messages/ru";

export function LogoutButton({ className }: { className?: string }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  async function handleClick() {
    await logout();
    // refresh(), а не push(): серверные компоненты должны перечитать
    // пользователя, иначе шапка останется в виде «вошёл».
    startTransition(() => {
      router.refresh();
      router.push("/");
    });
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      className={cn(
        "rounded-lg border border-line-2 px-3 py-2 text-[13px] font-medium text-muted",
        "transition-colors hover:border-line-3 hover:text-text disabled:opacity-50",
        className,
      )}
    >
      {nav.logout}
    </button>
  );
}
