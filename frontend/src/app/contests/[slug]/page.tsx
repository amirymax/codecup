import Link from "next/link";
import { notFound } from "next/navigation";

import { Countdown } from "@/components/Countdown";
import { Footer } from "@/components/Footer";
import { ArrowLeftIcon, CheckIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { StatusBadge } from "@/components/StatusBadge";
import { RatingButton } from "@/components/contest/RatingButton";
import { ApiRequestError } from "@/lib/api/errors";
import { getContest, getCurrentUser, getParticipation } from "@/lib/api/server";
import {
  EntryFeeRow,
  ParticipationCta,
  PaymentStatusBanner,
} from "@/components/payments/ParticipationCta";
import { formatMoney, formatNumber, formatRelative, formatShortDate } from "@/lib/format";
import { contest as t, statusLabels } from "@/messages/ru";

interface Props {
  params: Promise<{ slug: string }>;
}

export default async function ContestPage({ params }: Props) {
  const { slug } = await params;
  const user = await getCurrentUser();

  const contest = await getContest(slug).catch((error) => {
    // Черновики и архив backend отдаёт как 404 — показываем «не найден»,
    // а не страницу ошибки: для посетителя такого контеста не существует.
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });

  const submission = contest.my_submission;
  const isOver = contest.state === "ended";
  const participation = await getParticipation(slug);

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="contests" />

      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-20 sm:px-10 sm:py-10">
        <Link
          href="/"
          className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                     no-underline hover:text-text-2"
        >
          <ArrowLeftIcon />
          {t.allContests}
        </Link>

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <StatusBadge status={isOver ? "ended" : "live"} />
            <span className="font-mono text-[13px] text-muted-2">{contest.display_number}</span>
          </div>

          <RatingButton slug={contest.slug} isOver={isOver} />
        </div>

        {/* Заголовок и описание — в левой колонке, чтобы карточка со
            взносом и дедлайном стояла рядом с ними, а не ниже. */}
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
          <div className="min-w-0">
            <h1 className="text-3xl font-extrabold tracking-tight text-balance sm:text-[2.6rem]">
              {contest.title}
            </h1>
            <p className="mt-3.5 mb-10 text-[15.5px] leading-[1.7] whitespace-pre-line text-muted">
              {contest.description}
            </p>

            <section className="mb-9">
              <h3 className="mb-4 text-[15px] font-bold tracking-wider text-muted-2 uppercase">
                {t.requirementsTitle}
              </h3>
              <ul className="flex list-none flex-col gap-3 p-0">
                {contest.requirements.map((requirement) => (
                  <li
                    key={requirement}
                    className="flex items-start gap-3 rounded-[10px] border border-line
                               bg-surface px-4 py-3.5"
                  >
                    <CheckIcon className="mt-0.5 shrink-0 text-green-light" />
                    <span className="text-[14.5px] leading-relaxed text-text-2">
                      {requirement}
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            {submission && (
              <section>
                <h3 className="mb-4 text-[15px] font-bold tracking-wider text-muted-2 uppercase">
                  {t.yourSubmission}
                </h3>
                <div
                  className="flex flex-wrap items-center justify-between gap-4 rounded-xl
                             border border-line bg-surface px-5 py-4.5"
                >
                  <div>
                    <div className="mb-1 text-[14.5px] font-semibold text-text">
                      {submission.submitted_at
                        ? `${statusLabels.submitted} ${formatRelative(submission.submitted_at)}`
                        : statusLabels.draft}
                    </div>
                    <div className="text-[13px] text-muted-2">
                      {submission.github_url || "—"}
                    </div>
                  </div>
                  <StatusBadge status={submission.display_status} />
                </div>
              </section>
            )}
          </div>

          <aside className="min-w-0">
            <div
              className="sticky top-21 flex flex-col gap-5.5 rounded-card border border-line-2
                         bg-surface p-6"
            >
              <div>
                <div className="mb-1.5 text-[11.5px] font-semibold tracking-wider text-muted-2 uppercase">
                  {t.prizePool}
                </div>
                <div className="font-mono text-[26px] font-bold text-green-light">
                  {formatMoney(contest.prize_pool, contest.currency)}
                </div>
              </div>

              <div>
                <div className="mb-2 text-[11.5px] font-semibold tracking-wider text-muted-2 uppercase">
                  {isOver ? t.endedOn : t.timeRemaining}
                </div>
                {isOver ? (
                  <div className="font-mono text-[17px] font-bold text-text">
                    {formatShortDate(contest.deadline)}
                  </div>
                ) : (
                  <Countdown secondsLeft={contest.seconds_left} />
                )}
              </div>

              <div className="flex justify-between border-t border-line pt-4 text-[13.5px] text-muted">
                <span>{t.participants}</span>
                <span className="font-mono font-semibold text-text">
                  {formatNumber(contest.participants_count)}
                </span>
              </div>

              <EntryFeeRow participation={participation} />

              <PaymentStatusBanner participation={participation} />

              {isOver ? (
                <div
                  className="flex cursor-not-allowed items-center justify-center rounded-[9px]
                             border border-line-2 bg-surface-3 px-4 py-3.5 text-[14.5px]
                             font-bold text-muted-2"
                >
                  {t.closedCta}
                </div>
              ) : (
                <ParticipationCta
                  slug={contest.slug}
                  participation={participation}
                  isAuthenticated={Boolean(user)}
                  hasSubmission={Boolean(submission)}
                />
              )}
            </div>
          </aside>
        </div>
      </div>

      <Footer />
    </div>
  );
}
