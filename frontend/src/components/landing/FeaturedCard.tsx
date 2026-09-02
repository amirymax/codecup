"use client";

import Link from "next/link";

import { InlineCountdown } from "@/components/Countdown";
import { ClockIcon } from "@/components/Icons";
import { firstParagraph, formatMoney, formatNumber, formatShortDate } from "@/lib/format";
import { landing } from "@/messages/ru";
import type { ContestDetail } from "@/lib/api/types";

/** Карточка «Контест недели» на главной. */
export function FeaturedCard({ contest }: { contest: ContestDetail }) {
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
          label={landing.deadline}
          value={formatShortDate(contest.deadline)}
          className="text-text"
        />
      </div>
    </Link>
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
