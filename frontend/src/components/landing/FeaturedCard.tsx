"use client";

import Link from "next/link";

import { InlineCountdown } from "@/components/Countdown";
import { ArrowRightIcon, ClockIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { firstParagraph, formatMoney, formatNumber, formatShortDate } from "@/lib/format";
import { landing } from "@/messages/ru";
import type { ContestDetail } from "@/lib/api/types";

/**
 * Карточка контеста на главной.
 *
 * Пока контест идёт — «Контест недели» с обратным отсчётом, вся карточка
 * ведёт на контест. Когда он окончен — та же карточка с пометкой «Окончен»
 * и кнопкой к результатам. Ссылку в этом случае вешаем на заголовок, а не
 * на всю карточку: кнопка внутри ссылки — вложенный `a`, так нельзя.
 */
export function FeaturedCard({ contest }: { contest: ContestDetail }) {
  if (contest.state === "ended") {
    return <EndedCard contest={contest} />;
  }

  return (
    <Link
      href={`/contests/${contest.slug}`}
      className="block rounded-card border border-line-2 bg-gradient-to-b from-[#101012]
                 to-[#0b0b0d] p-6 no-underline transition-colors hover:border-blue sm:p-10"
    >
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <span className="text-[12.5px] font-bold tracking-wider text-blue-light uppercase">
          {landing.featuredLabel}
        </span>
        <span className="flex items-center gap-2 font-mono text-[13px] text-muted">
          <ClockIcon className="text-muted-2" />
          {landing.endsIn} <InlineCountdown secondsLeft={contest.seconds_left} />
        </span>
      </div>

      <h3 className="text-2xl font-extrabold tracking-tight text-text sm:text-[1.9rem]">
        {contest.title}
      </h3>
      {/* На главной — только первый абзац: полный текст ждёт на странице
          контеста, а карточка должна оставаться карточкой. */}
      <p className="mt-3 mb-6 max-w-[640px] text-[15px] leading-relaxed whitespace-pre-line text-muted">
        {firstParagraph(contest.description)}
      </p>

      <Metrics contest={contest} />
    </Link>
  );
}

function EndedCard({ contest }: { contest: ContestDetail }) {
  return (
    <div
      className="rounded-card border border-line-2 bg-gradient-to-b from-[#101012] to-[#0b0b0d]
                 p-6 sm:p-10"
    >
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <span className="text-[12.5px] font-bold tracking-wider text-muted-2 uppercase">
          {landing.endedLabel}
        </span>
        <span
          className="rounded-full border border-line-2 bg-surface-3 px-3 py-1 text-[12.5px]
                     font-semibold text-muted"
        >
          {landing.endedChip}
        </span>
      </div>

      <h3 className="text-2xl font-extrabold tracking-tight sm:text-[1.9rem]">
        <Link
          href={`/contests/${contest.slug}`}
          className="text-text no-underline hover:text-blue-light"
        >
          {contest.title}
        </Link>
      </h3>
      <p className="mt-3 mb-6 max-w-[640px] text-[15px] leading-relaxed whitespace-pre-line text-muted">
        {firstParagraph(contest.description)}
      </p>

      <Metrics contest={contest} />

      <Button className="mt-8" asChild>
        <Link href={`/contests/${contest.slug}/works`}>
          {landing.ctaViewResults}
          <ArrowRightIcon />
        </Link>
      </Button>
    </div>
  );
}

/** Три числа под описанием: у завершённого вместо дедлайна — дата конца. */
function Metrics({ contest }: { contest: ContestDetail }) {
  const isEnded = contest.state === "ended";

  return (
    <div className="flex flex-wrap gap-7">
      <Metric
        label={landing.prizePool}
        value={formatMoney(contest.prize_pool, contest.currency)}
        className="text-green-light"
      />
      <Metric
        label={landing.participants}
        value={formatNumber(contest.participants_count)}
        className="text-text"
      />
      <Metric
        label={isEnded ? landing.endedOn : landing.deadline}
        value={formatShortDate(contest.deadline)}
        className="text-text"
      />
    </div>
  );
}

function Metric({ label, value, className }: { label: string; value: string; className: string }) {
  return (
    <div>
      <div className="mb-1 text-[11.5px] font-semibold tracking-wider text-muted-2 uppercase">
        {label}
      </div>
      <div className={`font-mono text-xl font-bold ${className}`}>{value}</div>
    </div>
  );
}
