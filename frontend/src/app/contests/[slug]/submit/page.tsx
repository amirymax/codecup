import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { ArrowLeftIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { ApiRequestError } from "@/lib/api/errors";
import { getContest, getCurrentUser, getMySubmission } from "@/lib/api/server";
import { contest as contestText } from "@/messages/ru";

import { SubmitForm } from "./SubmitForm";

interface Props {
  params: Promise<{ slug: string }>;
}

export default async function SubmitPage({ params }: Props) {
  const { slug } = await params;
  const user = await getCurrentUser();

  // Отправлять решение может только вошедший — возвращаем сюда же после входа.
  if (!user) redirect(`/login?next=/contests/${slug}/submit`);

  const contest = await getContest(slug).catch((error) => {
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });

  const submission = await getMySubmission(slug);

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} />

      <div className="mx-auto max-w-[720px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <Link
          href={`/contests/${slug}`}
          className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                     no-underline hover:text-text-2"
        >
          <ArrowLeftIcon />
          {contest.title}
        </Link>

        {contest.accepts_submissions ? (
          <SubmitForm slug={slug} contestTitle={contest.title} existing={submission} />
        ) : (
          <ClosedNotice slug={slug} />
        )}
      </div>
    </div>
  );
}

/** Приём закрыт — форму не показываем вовсе, а не даём отправить и получить отказ. */
function ClosedNotice({ slug }: { slug: string }) {
  return (
    <div className="rounded-card border border-line-2 bg-surface px-6 py-15 text-center">
      <h2 className="mb-2 text-[19px] font-bold">{contestText.closedCta}</h2>
      <p className="mb-6 text-sm text-muted">{contestText.notFoundDesc}</p>
      <Button variant="subtle" asChild>
        <Link href={`/contests/${slug}`}>{contestText.allContests}</Link>
      </Button>
    </div>
  );
}
