import Link from "next/link";

import { ArrowLeftIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { requireAdmin } from "@/lib/adminGuard";
import { getAnalytics } from "@/lib/api/server";
import type { AnalyticsSummary } from "@/lib/api/types";
import { formatNumber, formatShortDate } from "@/lib/format";
import { admin, analytics as t, eventLabels } from "@/messages/ru";

const RANGES = [7, 30, 90];
const DEFAULT_DAYS = 30;

interface Props {
  searchParams: Promise<{ days?: string }>;
}

export default async function AdminAnalyticsPage({ searchParams }: Props) {
  const { days } = await searchParams;
  const period = RANGES.includes(Number(days)) ? Number(days) : DEFAULT_DAYS;

  const user = await requireAdmin(`/admin/analytics?days=${period}`);
  const data = await getAnalytics(period);
  const actions = data.events.reduce((sum, row) => sum + row.count, 0);

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />

      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <Link
          href="/admin"
          className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                     no-underline hover:text-text-2"
        >
          <ArrowLeftIcon />
          {admin.dashboard}
        </Link>

        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="mb-1.5 text-2xl font-extrabold tracking-tight">{t.title}</h1>
            <p className="text-sm text-muted-2">{t.subtitle}</p>
          </div>
          <div className="flex gap-2">
            {RANGES.map((range) => (
              <Range key={range} current={period} value={range} />
            ))}
          </div>
        </div>

        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Tile label={t.views} value={data.views} dot="bg-blue" />
          <Tile
            label={t.visitors}
            value={data.visitors}
            dot="bg-green"
            tone="text-green-light"
          />
          <Tile label={t.loggedIn} value={data.logged_in} dot="bg-amber" tone="text-amber" />
          <Tile label={t.clicksTotal} value={actions} dot="bg-blue" />
        </div>

        {data.views === 0 ? (
          <p className="rounded-xl border border-dashed border-line-2 bg-surface px-5 py-12 text-center text-sm text-muted-2">
            {t.empty}
          </p>
        ) : (
          <>
            <DailyChart daily={data.daily} />

            <div className="grid gap-6 lg:grid-cols-2">
              <Panel title={t.pages}>
                <Table
                  head={[t.pageColumn, t.viewsColumn, t.visitorsColumn]}
                  rows={data.pages.map((row) => [
                    row.path || "/",
                    formatNumber(row.views),
                    formatNumber(row.visitors),
                  ])}
                />
              </Panel>

              <Panel title={t.events} hint={t.visitorsHint}>
                {data.events.length === 0 ? (
                  <p className="px-4 py-8 text-center text-[13px] text-muted-2">{t.noEvents}</p>
                ) : (
                  <Table
                    head={[t.actionColumn, t.countColumn, t.visitorsColumn]}
                    rows={data.events.map((row) => [
                      eventLabels[row.name] ?? row.name,
                      formatNumber(row.count),
                      formatNumber(row.visitors),
                    ])}
                  />
                )}
              </Panel>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/** Столбики по дням. Своими руками, потому что одной библиотеке тут не место. */
function DailyChart({ daily }: { daily: AnalyticsSummary["daily"] }) {
  const peak = Math.max(...daily.map((point) => point.views), 1);

  return (
    <section className="mb-6 rounded-xl border border-line bg-surface p-5">
      <h2 className="mb-5 text-[15px] font-bold text-text">{t.perDay}</h2>
      <div className="flex h-40 items-end gap-1 overflow-x-auto">
        {daily.map((point) => (
          <div
            key={point.day}
            className="flex min-w-2.5 flex-1 flex-col items-center justify-end gap-1.5"
            title={`${formatShortDate(point.day)}: ${point.views} / ${point.visitors}`}
          >
            <span className="font-mono text-[10px] text-muted-2">{point.views}</span>
            <div
              className="w-full rounded-t-[3px] bg-blue"
              style={{ height: `${Math.max(3, (point.views / peak) * 100)}%` }}
            />
          </div>
        ))}
      </div>
      <p className="mt-3 text-[12px] text-muted-2">{t.visitorsHint}</p>
    </section>
  );
}

function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-line bg-surface">
      <header className="border-b border-line px-5 py-4">
        <h2 className="text-[15px] font-bold text-text">{title}</h2>
        {hint && <p className="mt-0.5 text-[12px] text-muted-2">{hint}</p>}
      </header>
      {children}
    </section>
  );
}

function Table({ head, rows }: { head: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-[13.5px]">
        <thead>
          <tr className="border-b border-line">
            {head.map((cell, index) => (
              <th
                key={cell}
                className={`px-5 py-2.5 text-[11.5px] font-bold tracking-wide text-muted-2 uppercase ${
                  index === 0 ? "text-left" : "text-right"
                }`}
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[0]} className="border-b border-line last:border-0">
              {row.map((cell, index) => (
                <td
                  key={index}
                  className={`px-5 py-2.5 ${
                    index === 0
                      ? "max-w-[280px] truncate font-mono text-text-2"
                      : "text-right font-mono text-muted"
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
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
    <div className="rounded-xl border border-line bg-surface px-5 py-4">
      <div className="mb-2 flex items-center gap-2">
        <span className={`size-1.5 rounded-full ${dot}`} />
        <span className="text-[12px] font-semibold tracking-wide text-muted-2 uppercase">
          {label}
        </span>
      </div>
      <div className={`font-mono text-[26px] font-bold ${tone}`}>{formatNumber(value)}</div>
    </div>
  );
}

function Range({ current, value }: { current: number; value: number }) {
  const labels: Record<number, string> = { 7: t.days7, 30: t.days30, 90: t.days90 };
  const active = current === value;
  return (
    <Link
      href={`/admin/analytics?days=${value}`}
      className={`rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold no-underline ${
        active ? "bg-surface-4 text-text" : "text-muted-2 hover:text-text"
      }`}
    >
      {labels[value]}
    </Link>
  );
}
