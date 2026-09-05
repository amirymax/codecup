import Link from "next/link";

import { Footer } from "@/components/Footer";
import { ArrowRightIcon, ChartIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { FeaturedCard } from "@/components/landing/FeaturedCard";
import { HeroStats } from "@/components/landing/HeroStats";
import { NotifyButton } from "@/components/landing/NotifyButton";
import { Button } from "@/components/ui/button";
import { getCurrentUser, getFeaturedContest } from "@/lib/api/server";
import { landing } from "@/messages/ru";

/**
 * Главная страница.
 *
 * Два состояния из макета — с активным контестом и без него — выбираются по
 * ответу backend: featured отдаёт contest: null, когда ничего не идёт.
 * Состояние загрузки живёт в loading.tsx.
 */
export default async function HomePage() {
  const [user, featured] = await Promise.all([getCurrentUser(), getFeaturedContest()]);
  const contest = featured.contest;
  // Завершённый контест приходит сюда, пока не начался следующий: главная
  // показывает его итоги, а не заглушку «активного контеста нет».
  const isEnded = contest?.state === "ended";

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="contests" />

      <section className="mx-auto max-w-[1180px] px-5 pt-12 pb-8 text-center sm:px-10 sm:pt-24">
        {contest && !isEnded ? (
          <span
            className="mb-7 inline-flex items-center gap-2 rounded-full border border-green/25
                       bg-green/10 px-3.5 py-1.5 text-[13px] font-semibold text-green-light"
          >
            <span
              className="size-1.5 rounded-full bg-green shadow-[0_0_0_3px_rgb(34_197_94/0.2)]"
              style={{ animation: "cc-pulse 2s infinite" }}
            />
            {landing.liveBadge}
          </span>
        ) : (
          <span
            className="mb-7 inline-flex items-center gap-2 rounded-full border border-line-2
                       bg-surface-3 px-3.5 py-1.5 text-[13px] font-semibold text-muted"
          >
            {isEnded ? landing.endedBadge : landing.emptyBadge}
          </span>
        )}

        <h1
          className="text-[2.1rem] leading-[1.08] font-extrabold tracking-tighter text-balance
                     sm:text-[4.25rem] sm:leading-[1.05]"
        >
          {landing.h1Line1}
          <br />
          <span className="bg-gradient-to-br from-green to-blue bg-clip-text text-transparent">
            {landing.h1Line2}
          </span>
        </h1>

        <p className="mx-auto mt-5 mb-10 max-w-[620px] text-base leading-relaxed text-pretty text-muted sm:text-[1.2rem]">
          {landing.subhead}
        </p>

        {/* Кнопку входа показываем только гостю: предлагать «Войти через
            Telegram» тому, кто уже вошёл, бессмысленно. Вошедшему без
            активного контеста остаётся «Уведомить меня» в карточке ниже. */}
        <div className="mb-16 flex flex-wrap items-center justify-center gap-3">
          {contest && (
            <Button asChild>
              <Link href={isEnded ? `/contests/${contest.slug}/works` : `/contests/${contest.slug}`}>
                {isEnded ? landing.ctaViewResults : landing.ctaViewContest}
                <ArrowRightIcon />
              </Link>
            </Button>
          )}

          {!user && (
            <Button variant={contest ? "outline" : "primary"} asChild>
              <Link href="/login">{landing.ctaLoginTelegram}</Link>
            </Button>
          )}
        </div>

        {contest && <HeroStats contest={contest} />}
      </section>

      <section className="mx-auto max-w-[1180px] px-5 pb-14 sm:px-10 sm:pb-24">
        {contest ? (
          <>
            <FeaturedCard contest={contest} />
            {isEnded && (
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-center">
                <span className="text-[14px] text-muted-2">{landing.endedNotifyHint}</span>
                <NotifyButton isAuthenticated={Boolean(user)} />
              </div>
            )}
          </>
        ) : (
          <div
            className="rounded-2xl border border-dashed border-line-2 bg-surface px-6 py-10
                       text-center sm:py-18"
          >
            <div
              className="mx-auto mb-5 flex size-13 items-center justify-center rounded-xl
                         border border-line-2 bg-surface-3"
            >
              <ChartIcon className="text-muted-2" />
            </div>
            <h3 className="mb-2 text-[19px] font-bold text-text">{landing.emptyStateTitle}</h3>
            <p className="mx-auto mb-6 max-w-[380px] text-[14.5px] text-muted-2">
              {landing.emptyStateDesc}
            </p>
            <NotifyButton isAuthenticated={Boolean(user)} />
          </div>
        )}
      </section>

      <section className="mx-auto max-w-[1180px] px-5 pb-16 sm:px-10 sm:pb-28">
        <h2 className="mb-10 text-center text-2xl font-bold tracking-tight sm:text-[2rem]">
          {landing.howItWorks}
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.n} className="rounded-2xl border border-line bg-surface px-6 py-7">
              <div
                className={`mb-4.5 flex size-10 items-center justify-center rounded-[10px]
                            font-mono font-bold ${step.tone}`}
              >
                {step.n}
              </div>
              <h4 className="mb-2 text-base font-bold text-text">{step.title}</h4>
              <p className="text-sm leading-relaxed text-muted">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}

const STEPS = [
  {
    n: "01",
    title: landing.step1Title,
    desc: landing.step1Desc,
    tone: "bg-blue/10 text-blue-light",
  },
  {
    n: "02",
    title: landing.step2Title,
    desc: landing.step2Desc,
    tone: "bg-green/10 text-green-light",
  },
  {
    n: "03",
    title: landing.step3Title,
    desc: landing.step3Desc,
    tone: "bg-amber/10 text-amber",
  },
];
