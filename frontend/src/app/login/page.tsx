import { redirect } from "next/navigation";

import { Logo } from "@/components/Logo";
import { getCurrentUser } from "@/lib/api/server";

import { LoginCard } from "./LoginCard";

interface Props {
  searchParams: Promise<{ next?: string }>;
}

export default async function LoginPage({ searchParams }: Props) {
  const { next } = await searchParams;
  const user = await getCurrentUser();

  // Уже вошедшему на странице входа делать нечего.
  if (user) redirect(safeNext(next));

  return (
    <div
      className="flex min-h-screen flex-col bg-ink text-text"
      style={{
        background:
          "radial-gradient(circle at 50% 0%, rgba(59,130,246,0.08), transparent 55%), #09090b",
      }}
    >
      <header className="flex items-center justify-between gap-4 px-5 py-6 sm:px-8">
        <Logo />
      </header>

      <main className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-[420px] rounded-2xl border border-line-2 bg-surface p-7 sm:p-10">
          <LoginCard next={safeNext(next)} />
        </div>
      </main>
    </div>
  );
}

/**
 * Открытый редирект — классическая дыра на странице входа, поэтому наружу
 * уводить нельзя: принимаем только внутренние пути.
 */
function safeNext(next: string | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return "/";
  return next;
}
