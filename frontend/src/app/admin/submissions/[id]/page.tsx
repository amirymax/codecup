import Link from "next/link";
import { notFound } from "next/navigation";

import { Avatar } from "@/components/Avatar";
import { ArrowLeftIcon, ExternalIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { ReviewPanel } from "@/components/admin/ReviewPanel";
import { ScreeningPanel } from "@/components/admin/ScreeningPanel";
import { requireAdmin } from "@/lib/adminGuard";
import { ApiRequestError } from "@/lib/api/errors";
import { getAdminSubmission } from "@/lib/api/server";
import { formatRelative } from "@/lib/format";
import { admin, review as t } from "@/messages/ru";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ReviewSubmissionPage({ params }: Props) {
  const { id } = await params;
  const user = await requireAdmin(`/admin/submissions/${id}`);

  const data = await getAdminSubmission(id).catch((error) => {
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });

  const { submission, navigation, screening } = data;

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />

      <div className="mx-auto max-w-[1000px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/admin"
            className="inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                       no-underline hover:text-text-2"
          >
            <ArrowLeftIcon />
            {admin.dashboard}
          </Link>

          {/* Стрелки и счётчик приходят с сервера — там же задан порядок очереди. */}
          <div className="flex items-center gap-2">
            <NavArrow href={navigation.previous_id} label="←" />
            <span className="px-2.5 font-mono text-[12.5px] text-muted-2">
              {navigation.position ?? "—"} / {navigation.total}
            </span>
            <NavArrow href={navigation.next_id} label="→" />
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0">
            <div className="mb-6 flex items-center gap-3">
              <Avatar name={submission.username} size={44} />
              <div>
                <div className="text-base font-bold">{submission.username}</div>
                <div className="text-[13px] text-muted-2">
                  {submission.contest_title} · {formatRelative(submission.submitted_at ?? null)}
                </div>
              </div>
              <StatusBadge status={submission.display_status} className="ml-auto" />
            </div>

            <ScreeningPanel submissionId={submission.id} screening={screening ?? null} />

            <div className="mb-7 flex flex-col gap-3">
              <ResourceLink href={submission.github_url} label={submission.repo_name} />
              <ResourceLink href={submission.live_url} label={submission.live_url} accent />
              {submission.video_url && (
                <ResourceLink href={submission.video_url} label={t.demoVideo} accent />
              )}
            </div>

            <div>
              <h3 className="mb-2.5 text-[13px] font-bold tracking-wide text-muted-2 uppercase">
                {t.description}
              </h3>
              <p className="text-[14.5px] leading-[1.7] whitespace-pre-line text-text-2">
                {submission.description || "—"}
              </p>
            </div>
          </div>

          <aside className="min-w-0">
            <ReviewPanel submission={submission} />
          </aside>
        </div>
      </div>
    </div>
  );
}

function NavArrow({ href, label }: { href: number | null; label: string }) {
  const classes =
    "flex size-8.5 items-center justify-center rounded-lg border border-line-2 text-muted";

  if (href === null) {
    return <span className={`${classes} cursor-not-allowed opacity-40`}>{label}</span>;
  }
  return (
    <Link
      href={`/admin/submissions/${href}`}
      className={`${classes} no-underline hover:border-line-3 hover:text-text`}
    >
      {label}
    </Link>
  );
}

function ResourceLink({
  href,
  label,
  accent,
}: {
  href: string | undefined;
  label: string | undefined;
  accent?: boolean;
}) {
  if (!href) return null;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-between gap-3 rounded-[10px] border border-line
                 bg-surface px-4 py-3.5 no-underline hover:border-line-3"
    >
      <span className="min-w-0 truncate text-sm text-text-2">{label}</span>
      <ExternalIcon className={accent ? "text-blue-light" : "text-muted-2"} />
    </a>
  );
}
