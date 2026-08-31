import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { requireAdmin } from "@/lib/adminGuard";
import { getAdminContests, getAdminStats, getAdminSubmissions } from "@/lib/api/server";
import { formatMoney, formatNumber, formatShortDate } from "@/lib/format";
import { admin as t, payments as paymentsText } from "@/messages/ru";

export default async function AdminDashboardPage() {
  const user = await requireAdmin("/admin");
  const [stats, contests, submissions] = await Promise.all([
    getAdminStats(),
    getAdminContests(),
    getAdminSubmissions(),
  ]);

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />

      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="mb-1.5 text-2xl font-extrabold tracking-tight sm:text-[1.8rem]">
              {t.title}
            </h1>
            <p className="text-sm text-muted-2">{t.subtitle}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" asChild>
              <Link href="/admin/payments">{paymentsText.title}</Link>
            </Button>
            <Button asChild>
              <Link href="/admin/contests/new">
                <PlusIcon />
                {t.createContest}
              </Link>
            </Button>
          </div>
        </header>

        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Tile label={t.totalUsers} value={stats.total_users} dot="bg-blue" />
          <Tile
            label={t.activeContests}
            value={stats.active_contests}
            dot="bg-green"
            tone="text-green-light"
          />
          <Tile label={t.submissionsWord} value={stats.submissions} dot="bg-blue" />
          <Tile
            label={t.pendingReview}
            value={stats.pending_review}
            dot="bg-amber"
            tone="text-amber"
          />
        </div>

        <section className="mb-10">
          <h2 className="mb-4 text-[15px] font-bold tracking-wider text-muted-2 uppercase">
            {t.contestsTitle}
          </h2>

          {contests.results.length === 0 ? (
            <div className="rounded-card border border-dashed border-line-2 bg-surface px-6 py-12 text-center">
              <h3 className="mb-2 text-base font-bold">{t.noContestsTitle}</h3>
              <p className="mb-5 text-sm text-muted-2">{t.noContestsDesc}</p>
              <Button size="sm" asChild>
                <Link href="/admin/contests/new">{t.createContest}</Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-line bg-surface">
              {contests.results.map((contest) => (
                <div
                  key={contest.id}
                  className="flex flex-wrap items-center gap-4 border-b border-[#1a1a1d]
                             px-5 py-4 last:border-b-0 hover:bg-surface-2"
                >
                  <div className="min-w-[180px] flex-1">
                    <div className="text-[14.5px] font-bold text-text">{contest.title}</div>
                    <div className="mt-0.5 font-mono text-[12.5px] text-muted-2">
                      {formatMoney(contest.prize_pool ?? "0", contest.currency)} {t.prizeWord}
                    </div>
                  </div>
                  <StatusBadge status={contest.state} />
                  <div className="w-[90px] font-mono text-[13px] text-muted-2">
                    {formatShortDate(contest.deadline)}
                  </div>
                  <Link
                    href={`/admin/contests/${contest.id}`}
                    className="rounded-[7px] border border-line-2 px-3.5 py-1.5 text-[12.5px]
                               font-semibold text-text-2 no-underline hover:border-line-3"
                  >
                    {t.edit}
                  </Link>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-4 text-[15px] font-bold tracking-wider text-muted-2 uppercase">
            {t.recentSubmissions}
          </h2>
          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            {submissions.results.map((submission) => (
              <div
                key={submission.id}
                className="flex flex-wrap items-center gap-4 border-b border-[#1a1a1d] px-5 py-3.5
                           last:border-b-0 hover:bg-surface-2"
              >
                <Avatar name={submission.username} size={30} />
                <div className="min-w-[160px] flex-1">
                  <div className="text-sm font-semibold text-text">{submission.username}</div>
                  <div className="text-[12.5px] text-muted-2">{submission.repo_name}</div>
                </div>
                {submission.score !== null && (
                  <span className="font-mono text-[13px] text-muted">{submission.score}</span>
                )}
                <StatusBadge status={submission.display_status} />
                <Link
                  href={`/admin/submissions/${submission.id}`}
                  className="rounded-[7px] border border-line-2 bg-surface-3 px-3.5 py-1.5
                             text-[12.5px] font-semibold text-text no-underline
                             hover:border-blue"
                >
                  {t.review}
                </Link>
              </div>
            ))}
            {submissions.results.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-muted-2">{t.noContestsDesc}</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function Tile({
  label,
  value,
  dot,
  tone = "text-text",
}: {
  label: string;
  value: number;
  dot: string;
  tone?: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-semibold tracking-wide text-muted-2 uppercase">
          {label}
        </span>
        <span className={`size-2 rounded-full ${dot}`} />
      </div>
      <div className={`font-mono text-2xl font-bold ${tone}`}>{formatNumber(value)}</div>
    </div>
  );
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 5v14m-7-7h14" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
