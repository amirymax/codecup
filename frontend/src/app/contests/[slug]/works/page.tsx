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
import { formatRelative, formatScore } from "@/lib/format";
import { contest as t } from "@/messages/ru";

interface Props {
  params: Promise<{ slug: string }>;
}

/**
 * Работы участников контеста — итоговая таблица.
 *
 * Открыта всем, включая гостей: результаты смотрят и те, кто не участвовал,
 * поэтому вход здесь не требуется ни на странице, ни в API.
 */
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
          {isOver ? t.worksResultsTitle : t.worksPageTitle}
        </h1>
        <p className="mb-8 text-sm text-muted-2">
          {contest.title}
          {isOver && works && works.results.length > 0 && ` · ${t.worksResultsHint}`}
        </p>

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
            {works.results.map((work, index) => (
              <WorkCard key={work.id} work={work} place={index + 1} />
            ))}
          </ul>
        )}
      </div>

      <Footer />
    </div>
  );
}

/** ``place`` — позиция в списке: он отсортирован по итогам проверки. */
function WorkCard({ work, place }: { work: ContestWork; place: number }) {
  return (
    <li id={work.username} className="rounded-xl border border-line bg-surface p-5 scroll-mt-24">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <span
          aria-label={`${place} ${t.worksPlace}`}
          className="flex size-7 shrink-0 items-center justify-center rounded-lg border
                     border-line-2 bg-surface-3 font-mono text-[12.5px] font-bold text-muted"
        >
          {place}
        </span>
        <Avatar name={work.display_name} size={30} />
        <Link
          href={`/users/${work.username}`}
          className="text-[15px] font-bold text-text no-underline hover:text-blue-light"
        >
          {work.display_name}
        </Link>
        {work.display_status === "winner" && <StatusBadge status="winner" />}
        <Score work={work} />
      </div>

      {work.submitted_at && (
        <p className="mb-3 text-[12.5px] text-muted-3">
          {t.worksSubmittedAt} {formatRelative(work.submitted_at)}
        </p>
      )}

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

/** Балл справа в шапке карточки; у непроверенной работы его ещё нет. */
function Score({ work }: { work: ContestWork }) {
  if (work.total_score === null) {
    return <span className="ml-auto text-[12.5px] text-muted-3">{t.worksNotScored}</span>;
  }

  return (
    <span
      className="ml-auto text-right font-mono text-[15px] font-bold text-text"
      title={work.video_bonus ? t.worksVideoBonus : undefined}
    >
      {formatScore(work.total_score)}
    </span>
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
