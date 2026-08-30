import Link from "next/link";

import { Avatar } from "@/components/Avatar";
import { ExternalIcon } from "@/components/Icons";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { formatMonthYear, formatRelative } from "@/lib/format";
import { profile as t } from "@/messages/ru";
import type { ProfileSubmission } from "@/lib/api/types";

interface Props {
  username: string;
  joinedAt: string;
  submissionsCount: number;
  winsCount: number;
  submissions: ProfileSubmission[];
  /** Свой профиль или чужой: от этого зависят заголовок и пустое состояние. */
  isOwn?: boolean;
}

/** Профиль: используется и для своей страницы, и для чужой. */
export function ProfileView({
  username,
  joinedAt,
  submissionsCount,
  winsCount,
  submissions,
  isOwn = false,
}: Props) {
  return (
    <div className="mx-auto max-w-[880px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
      <header className="mb-10 flex flex-wrap items-center gap-5">
        <Avatar name={username} size={72} />
        <div className="min-w-[200px] flex-1">
          <h1 className="mb-1 text-[22px] font-extrabold tracking-tight">{username}</h1>
          <p className="text-[13.5px] text-muted-2">
            {t.joinedVia} · {formatMonthYear(joinedAt)}
          </p>
        </div>
        <dl className="flex gap-6">
          <Stat value={submissionsCount} label={t.submissionsLabel} />
          <Stat value={winsCount} label={t.winsLabel} accent />
        </dl>
      </header>

      <h2 className="mb-4 text-[15px] font-bold tracking-wider text-muted-2 uppercase">
        {isOwn ? t.mySubmissions : t.theirSubmissions}
      </h2>

      {submissions.length === 0 ? (
        <EmptyState isOwn={isOwn} />
      ) : (
        <ul className="flex list-none flex-col gap-3 p-0">
          {submissions.map((submission) => (
            <li
              key={submission.id}
              className="flex flex-wrap items-center justify-between gap-4 rounded-xl
                         border border-line bg-surface px-5 py-4.5"
            >
              <div className="min-w-0">
                <Link
                  href={`/contests/${submission.contest_slug}`}
                  className="mb-1 block text-[14.5px] font-bold text-text no-underline
                             hover:text-blue-light"
                >
                  {submission.contest_title}
                </Link>
                <div className="font-mono text-[13px] text-muted-2">
                  {formatRelative(submission.submitted_at ?? submission.created_at)}
                  {submission.repo_name ? ` · ${submission.repo_name}` : ""}
                </div>
              </div>
              <StatusBadge status={submission.display_status} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Stat({ value, label, accent }: { value: number; label: string; accent?: boolean }) {
  return (
    <div className="text-center">
      <dd
        className={`font-mono text-[19px] font-bold ${accent ? "text-green-light" : "text-text"}`}
      >
        {value}
      </dd>
      <dt className="mt-0.5 text-[11.5px] text-muted-2">{label}</dt>
    </div>
  );
}

function EmptyState({ isOwn }: { isOwn: boolean }) {
  return (
    <div className="rounded-2xl border border-dashed border-line-2 bg-surface px-6 py-14 text-center">
      <div
        className="mx-auto mb-4 flex size-12 items-center justify-center rounded-[10px]
                   border border-line-2 bg-surface-3"
      >
        <ExternalIcon size={20} className="text-muted-2" />
      </div>
      <h3 className="mb-2 text-base font-bold">{t.emptyTitle}</h3>
      {isOwn && (
        <>
          <p className="mb-6 text-sm text-muted-2">{t.emptyDesc}</p>
          <Button asChild>
            <Link href="/">{t.browseContests}</Link>
          </Button>
        </>
      )}
    </div>
  );
}
