import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { getCurrentUser, getFeaturedContest } from "@/lib/api/server";
import { formatMoney, formatNumber } from "@/lib/format";
import { landing } from "@/messages/ru";

/**
 * Временная главная: шаг 6 закладывает основу, полноценные экраны —
 * следующий шаг. Здесь проверяется, что стек собран целиком: серверная
 * загрузка данных с пробросом кук, токены оформления и шапка.
 */
export default async function HomePage() {
  const [user, featured] = await Promise.all([getCurrentUser(), getFeaturedContest()]);
  const contest = featured.contest;

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="contests" />

      <main className="mx-auto max-w-[1180px] px-5 py-16 sm:px-10">
        <h1 className="text-4xl font-extrabold tracking-tight text-balance sm:text-6xl">
          {landing.h1Line1}
          <br />
          <span className="bg-gradient-to-br from-green to-blue bg-clip-text text-transparent">
            {landing.h1Line2}
          </span>
        </h1>

        <p className="mt-5 max-w-[620px] text-base leading-relaxed text-pretty text-muted">
          {landing.subhead}
        </p>

        {contest ? (
          <section className="mt-12 rounded-card border border-line-2 bg-surface p-8">
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <StatusBadge status={contest.state} />
              <span className="font-mono text-[13px] text-muted-2">
                {contest.display_number}
              </span>
            </div>
            <h2 className="text-2xl font-extrabold">{contest.title}</h2>
            <p className="mt-3 max-w-[640px] leading-relaxed text-muted">{contest.description}</p>

            <dl className="mt-6 flex flex-wrap gap-8">
              <Stat label={landing.prizePool} value={formatMoney(contest.prize_pool)} accent />
              <Stat
                label={landing.participants}
                value={formatNumber(contest.participants_count)}
              />
            </dl>

            <Button className="mt-7" asChild>
              <a href={`/contests/${contest.slug}`}>{landing.ctaViewContest}</a>
            </Button>
          </section>
        ) : (
          <section
            className="mt-12 rounded-card border border-dashed border-line-2 bg-surface
                       px-6 py-16 text-center"
          >
            <h2 className="text-lg font-bold">{landing.emptyStateTitle}</h2>
            <p className="mx-auto mt-2 max-w-[380px] text-[14.5px] text-muted-2">
              {landing.emptyStateDesc}
            </p>
          </section>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <dt className="text-[11.5px] font-semibold tracking-wide text-muted-2 uppercase">
        {label}
      </dt>
      <dd
        className={`mt-1 font-mono text-xl font-bold ${accent ? "text-green-light" : "text-text"}`}
      >
        {value}
      </dd>
    </div>
  );
}
