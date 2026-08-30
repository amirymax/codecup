"use client";

import { CompactCountdown } from "@/components/Countdown";
import { formatMoney, formatNumber } from "@/lib/format";
import { landing } from "@/messages/ru";
import type { ContestDetail } from "@/lib/api/types";

/** Три плитки под заголовком главной. */
export function HeroStats({ contest }: { contest: ContestDetail }) {
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
        value={<CompactCountdown secondsLeft={contest.seconds_left} />}
        label={landing.timeLeftHero}
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
