"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { TelegramIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { exchangeLogin, pollLoginStatus, startTelegramLogin } from "@/lib/api/auth";
import { ApiRequestError } from "@/lib/api/errors";
import { login as t } from "@/messages/ru";

type View = "idle" | "waiting" | "expired" | "unavailable";

const POLL_INTERVAL_MS = 2000;

/**
 * Вход через Telegram.
 *
 * Подтверждение приходит в бот, а не в браузер, поэтому страница опрашивает
 * backend: другого способа узнать о нажатии кнопки в Telegram у неё нет.
 * Опрос прекращается сам, когда код подтверждён, отменён или просрочен.
 */
export function LoginCard({ next }: { next: string }) {
  const router = useRouter();
  const [view, setView] = useState<View>("idle");
  const session = useRef<{ nonce: string; clientSecret: string } | null>(null);

  const finish = useCallback(async () => {
    const current = session.current;
    if (!current) return;

    try {
      await exchangeLogin(current.nonce, current.clientSecret);
      // refresh() обязателен: шапка и страницы рендерятся на сервере и
      // должны перечитать пользователя по свежей куке.
      router.refresh();
      router.replace(next);
    } catch {
      setView("expired");
    }
  }, [next, router]);

  // Опрос живёт только в состоянии ожидания и убирается вместе с ним.
  useEffect(() => {
    if (view !== "waiting" || !session.current) return;

    const controller = new AbortController();
    let stopped = false;

    const timer = setInterval(async () => {
      if (stopped || !session.current) return;
      try {
        const status = await pollLoginStatus(session.current.nonce, controller.signal);
        if (status === "confirmed") {
          stopped = true;
          clearInterval(timer);
          await finish();
        } else if (status === "expired" || status === "cancelled") {
          stopped = true;
          clearInterval(timer);
          setView("expired");
        }
      } catch {
        // Разрыв сети — не повод ломать вход: следующий тик попробует снова.
      }
    }, POLL_INTERVAL_MS);

    return () => {
      stopped = true;
      clearInterval(timer);
      controller.abort();
    };
  }, [view, finish]);

  async function start() {
    try {
      const started = await startTelegramLogin();
      session.current = { nonce: started.nonce, clientSecret: started.clientSecret };
      window.open(started.deepLink, "_blank", "noopener,noreferrer");
      setView("waiting");
    } catch (error) {
      if (error instanceof ApiRequestError && error.code === "telegram_not_configured") {
        setView("unavailable");
        return;
      }
      setView("expired");
    }
  }

  if (view === "waiting") return <WaitingView onCancel={() => setView("idle")} />;
  if (view === "expired") return <ExpiredView onRetry={() => setView("idle")} />;
  if (view === "unavailable") return <UnavailableView />;

  return <IdleView onStart={start} />;
}

function IdleView({ onStart }: { onStart: () => void }) {
  return (
    <>
      <h1 className="mb-2 text-[22px] font-extrabold tracking-tight">{t.title}</h1>
      <p className="mb-7 text-sm leading-relaxed text-muted">{t.subtitle}</p>

      <Button variant="telegram" size="lg" className="mb-7 w-full" onClick={onStart}>
        <TelegramIcon size={18} />
        {t.loginBtn}
      </Button>

      <ol className="flex list-none flex-col gap-4 border-t border-line p-0 pt-6">
        {[t.step1, t.step2, t.step3].map((text, index) => (
          <li key={text} className="flex items-start gap-3">
            <span
              className="flex size-5.5 shrink-0 items-center justify-center rounded-full border
                         border-line-2 bg-surface-3 font-mono text-[11px] font-semibold text-muted-2"
            >
              {index + 1}
            </span>
            <p className="mt-0.5 text-[13.5px] leading-snug text-muted">{text}</p>
          </li>
        ))}
      </ol>
    </>
  );
}

function WaitingView({ onCancel }: { onCancel: () => void }) {
  return (
    <div className="px-0 pt-3 pb-1 text-center">
      <div
        className="mx-auto mb-6 flex size-14 items-center justify-center rounded-full border
                   border-blue/25 bg-blue/10"
        style={{ animation: "cc-pulse 1.8s infinite" }}
      >
        <TelegramIcon size={26} className="text-blue-light" />
      </div>
      <h2 className="mb-2 text-lg font-bold">{t.waitingTitle}</h2>
      <p className="mb-7 text-sm leading-relaxed text-muted">
        {t.waitingDesc1}
        <br />
        {t.waitingDesc2}
      </p>
      <div className="flex items-center justify-center gap-2.5 font-mono text-[13px] text-muted-2">
        <Spinner />
        {t.waitingSpinner}
      </div>
      <button
        type="button"
        onClick={onCancel}
        className="mt-6 cursor-pointer border-none bg-transparent text-[13px] text-muted-2 underline"
      >
        {t.cancel}
      </button>
    </div>
  );
}

function ExpiredView({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="px-0 pt-3 pb-1 text-center">
      <div
        className="mx-auto mb-6 flex size-14 items-center justify-center rounded-full border
                   border-red/25 bg-red/10"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M12 9v4m0 4h.01M10.3 3.86L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.86a2 2 0 0 0-3.4 0z"
            stroke="#f87171"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h2 className="mb-2 text-lg font-bold">{t.errorTitle}</h2>
      <p className="mb-7 text-sm leading-relaxed text-muted">{t.errorDesc}</p>
      <Button variant="telegram" className="w-full" onClick={onRetry}>
        {t.retry}
      </Button>
    </div>
  );
}

function UnavailableView() {
  return (
    <div className="px-0 pt-3 pb-1 text-center">
      <h2 className="mb-2 text-lg font-bold">{t.notConfiguredTitle}</h2>
      <p className="text-sm leading-relaxed text-muted">{t.notConfiguredDesc}</p>
    </div>
  );
}

function Spinner() {
  return (
    <span
      className="inline-block size-3.5 rounded-full border-2 border-line-2 border-t-blue"
      style={{ animation: "cc-spin 0.8s linear infinite" }}
    />
  );
}
