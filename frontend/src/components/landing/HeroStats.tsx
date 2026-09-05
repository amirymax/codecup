"use client";

import { CompactCountdown } from "@/components/Countdown";
import { formatMoney, formatNumber, formatShortDate } from "@/lib/format";
import { landing } from "@/messages/ru";
import type { ContestDetail } from "@/lib/api/types";

/**
 * Три плитки под заголовком главной.
 *
 * У завершённого контеста обратный отсчёт заменяется датой окончания:
 * «00:00:00» выглядело бы как контест, который вот-вот начнётся.
 */
export function HeroStats({ contest }: { contest: ContestDetail }) {
  const isEnded = contest.state === "ended";

  return (
    <div
      className="mx-auto grid max-w-[700px] gap-px overflow-hidden rounded-xl border
                 border-line bg-line sm:grid-cols-3"
    >
      <Tile
        value={formatMoney(contest.prize_pool, contest.currency)}
        label={landing.prizePoolLabelHero}
        className="text-green-light"
      />
      <Tile
        value={formatNumber(contest.participants_count)}
        label={landing.participantsLabelHero}
        className="text-blue-light"
      />
      <Tile
        value={
          isEnded ? (
            formatShortDate(contest.deadline)
          ) : (
            <CompactCountdown secondsLeft={contest.seconds_left} />
          )
        }
        label={isEnded ? landing.endedOn : landing.timeLeftHero}
        className="text-text"
      />
    </div>
  );
}

function Tile({
  value,
  label,
  className,
}: {
  value: React.ReactNode;
  label: string;
  className: string;
}) {
  return (
    <div className="bg-surface px-4 py-6">
      <div className={`font-mono text-2xl font-bold ${className}`}>{value}</div>
      <div className="mt-1 text-[12.5px] font-medium text-muted-2">{label}</div>
    </div>
  );
}
