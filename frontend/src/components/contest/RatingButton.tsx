"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { contest as t } from "@/messages/ru";

const CLASSES =
  "flex items-center gap-2 rounded-full border border-line-2 px-3.5 py-1.5 text-[13px] " +
  "font-semibold text-text-2 no-underline transition-colors hover:border-line-3 hover:bg-surface-3";

/**
 * Кнопка рейтинга над заголовком контеста.
 *
 * Пока контест идёт, работы закрыты — но кнопку не прячем: так видно, что
 * рейтинг вообще есть, и понятно, когда он откроется.
 */
export function RatingButton({ slug, isOver }: { slug: string; isOver: boolean }) {
  const [open, setOpen] = useState(false);

  if (isOver) {
    return (
      <Link href={`/contests/${slug}/works`} className={CLASSES}>
        {t.worksCta}
      </Link>
    );
  }

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className={`${CLASSES} cursor-pointer`}>
        {t.worksCta}
      </button>

      {open && (
        <div
          className="fixed inset-0 z-100 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t.worksClosedTitle}
            onClick={(event) => event.stopPropagation()}
            className="cc-enter w-full max-w-[420px] rounded-2xl border border-line-2 bg-surface
                       p-6 text-center sm:p-7"
          >
            <h2 className="mb-2.5 text-lg font-extrabold text-text">{t.worksClosedTitle}</h2>
            <p className="mb-6 text-[14px] leading-relaxed text-muted">{t.worksClosedDesc}</p>
            <Button className="w-full" onClick={() => setOpen(false)}>
              {t.worksClosedOk}
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
