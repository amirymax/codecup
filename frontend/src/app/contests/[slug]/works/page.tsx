import Link from "next/link";
import { notFound } from "next/navigation";

import { Avatar } from "@/components/Avatar";
import { Footer } from "@/components/Footer";
import { ArrowLeftIcon, ExternalIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiRequestError } from "@/lib/api/errors";
import { getContest, getContestWorks, getCurrentUser } from "@/lib/api/server";
import type { ContestWork } from "@/lib/api/types";
import { formatRelative } from "@/lib/format";
import { contest as t } from "@/messages/ru";

interface Props {
  params: Promise<{ slug: string }>;
}

/** Работы участников контеста. Открыты всем, включая гостей. */
export default async function ContestWorksPage({ params }: Props) {
  const { slug } = await params;
  const user = await getCurrentUser();

  const contest = await getContest(slug).catch((error) => {
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });
  // Пока контест идёт, работы закрыты и на сервере: сюда можно прийти по
  // прямой ссылке, поэтому состояние проверяем, а не полагаемся на кнопку.
  const isOver = contest.state === "ended";
  const works = isOver ? await getContestWorks(slug) : null;

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="contests" />

      <div className="mx-auto max-w-[900px] px-5 py-6 pb-20 sm:px-10 sm:py-10">
        <Link
          href={`/contests/${slug}`}
          className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                     no-underline hover:text-text-2"
        >
          <ArrowLeftIcon />
          {t.worksBackToContest}
        </Link>

        <h1 className="mb-1.5 text-2xl font-extrabold tracking-tight sm:text-[2rem]">
          {t.worksPageTitle}
        </h1>
        <p className="mb-8 text-sm text-muted-2">{contest.title}</p>

        {!works ? (
          <p
            className="rounded-xl border border-dashed border-line-2 bg-surface px-5 py-12
                       text-center text-sm text-muted-2"
          >
            {t.worksClosedDesc}
          </p>
        ) : works.results.length === 0 ? (
          <p
            className="rounded-xl border border-dashed border-line-2 bg-surface px-5 py-12
                       text-center text-sm text-muted-2"
          >
            {t.worksEmpty}
          </p>
        ) : (
          <ul className="flex list-none flex-col gap-4 p-0">
            {works.results.map((work) => (
              <WorkCard key={work.id} work={work} />
            ))}
          </ul>
        )}
      </div>

      <Footer />
    </div>
  );
}

function WorkCard({ work }: { work: ContestWork }) {
  return (
    <li id={work.username} className="rounded-xl border border-line bg-surface p-5 scroll-mt-24">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <Avatar name={work.display_name} size={30} />
        <Link
          href={`/users/${work.username}`}
          className="text-[15px] font-bold text-text no-underline hover:text-blue-light"
        >
          {work.display_name}
        </Link>
        {work.display_status === "winner" && <StatusBadge status="winner" />}
        {work.submitted_at && (
          <span className="ml-auto text-[12.5px] text-muted-3">
            {t.worksSubmittedAt} {formatRelative(work.submitted_at)}
          </span>
        )}
      </div>

      {work.description && (
        <p className="mb-4 text-[14px] leading-relaxed whitespace-pre-line text-muted">
          {work.description}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <WorkLink href={work.github_url} label={t.worksRepo} />
        <WorkLink href={work.live_url} label={t.worksDemo} />
        <WorkLink href={work.video_url} label={t.worksVideo} />
      </div>
    </li>
  );
}

function WorkLink({ href, label }: { href: string; label: string }) {
  if (!href) return null;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="flex items-center gap-1.5 rounded-[7px] border border-line-2 px-3 py-1.5
                 text-[12.5px] font-semibold text-text-2 no-underline hover:border-line-3
                 hover:bg-surface-3"
    >
      {label}
      <ExternalIcon size={13} />
    </a>
  );
}
