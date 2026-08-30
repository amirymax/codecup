"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { FieldError } from "@/components/FieldError";
import { CheckIcon, ExternalIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiRequestError } from "@/lib/api/errors";
import { saveDraft, submitSolution, type SubmissionDraft } from "@/lib/api/submissions";
import { submit as t } from "@/messages/ru";
import type { MySubmission } from "@/lib/api/types";

const MIN_DESCRIPTION = 100;
const MAX_DESCRIPTION = 500;

type View = "form" | "success";
type Busy = "idle" | "saving" | "submitting";

export function SubmitForm({
  slug,
  contestTitle,
  existing,
}: {
  slug: string;
  contestTitle: string;
  existing: MySubmission | null;
}) {
  const router = useRouter();

  const [fields, setFields] = useState<SubmissionDraft>({
    github_url: existing?.github_url ?? "",
    live_url: existing?.live_url ?? "",
    video_url: existing?.video_url ?? "",
    description: existing?.description ?? "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState<Busy>("idle");
  const [view, setView] = useState<View>("form");
  const [draftSaved, setDraftSaved] = useState(false);

  // Пробелы по краям не считаются — так же, как на сервере.
  const descriptionLength = fields.description.trim().length;

  function update(field: keyof SubmissionDraft) {
    return (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setFields((current) => ({ ...current, [field]: event.target.value }));
      setDraftSaved(false);
    };
  }

  /**
   * Проверять поля здесь заново не нужно: те же правила уже действуют на
   * сервере, и его ответ — единственный источник истины. Так сообщения
   * не разъезжаются между формой и API.
   */
  async function run(action: () => Promise<MySubmission>, onDone: () => void) {
    setErrors({});
    setFormError(null);
    try {
      await action();
      onDone();
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.isUnauthorized) {
          router.push(`/login?next=/contests/${slug}/submit`);
          return;
        }
        setErrors(error.fieldErrors);
        // Ошибка правила (закрытый приём) приходит без привязки к полю.
        if (Object.keys(error.fieldErrors).length === 0) setFormError(error.message);
      } else {
        setFormError(t.githubRequired);
      }
    } finally {
      setBusy("idle");
    }
  }

  async function onSaveDraft() {
    setBusy("saving");
    await run(
      () => saveDraft(slug, fields),
      () => setDraftSaved(true),
    );
  }

  async function onSubmit() {
    setBusy("submitting");
    await run(
      () => submitSolution(slug, fields),
      () => setView("success"),
    );
  }

  if (view === "success") {
    return <SuccessView onEdit={() => setView("form")} />;
  }

  return (
    <>
      <h1 className="mb-2 text-2xl font-extrabold tracking-tight sm:text-[2rem]">{t.heading}</h1>
      <p className="mb-8 text-[14.5px] text-muted">{t.subheading}</p>

      <div className="flex flex-col gap-5.5">
        <div>
          <Label htmlFor="github_url">
            <GithubIcon />
            {t.githubLabel}
          </Label>
          <Input
            id="github_url"
            value={fields.github_url}
            onChange={update("github_url")}
            placeholder="https://github.com/username/project"
            aria-invalid={Boolean(errors.github_url)}
          />
          <FieldError message={errors.github_url} />
        </div>

        <div>
          <Label htmlFor="live_url">
            <ExternalIcon />
            {t.liveLabel}
          </Label>
          <Input
            id="live_url"
            value={fields.live_url}
            onChange={update("live_url")}
            placeholder="https://your-project.vercel.app"
            aria-invalid={Boolean(errors.live_url)}
          />
          <FieldError message={errors.live_url} />
        </div>

        <div>
          <Label htmlFor="video_url">
            <VideoIcon />
            {t.videoLabel}
          </Label>
          <Input
            id="video_url"
            value={fields.video_url}
            onChange={update("video_url")}
            placeholder="https://youtube.com/watch?v=..."
            aria-invalid={Boolean(errors.video_url)}
          />
          <FieldError message={errors.video_url} />
        </div>

        <div>
          <Label htmlFor="description">{t.descLabel}</Label>
          <Textarea
            id="description"
            rows={5}
            value={fields.description}
            onChange={update("description")}
            placeholder={t.descPlaceholder}
            maxLength={MAX_DESCRIPTION}
            aria-invalid={Boolean(errors.description)}
          />
          {/* Нижняя граница показывается заранее: узнать о ней только из
              отказа при отправке — неприятный сюрприз. */}
          <div className="mt-1 flex justify-between font-mono text-[11.5px]">
            <span className="text-muted-3">
              {descriptionLength < MIN_DESCRIPTION && `минимум ${MIN_DESCRIPTION}`}
            </span>
            <span
              className={
                descriptionLength >= MAX_DESCRIPTION
                  ? "text-red"
                  : descriptionLength < MIN_DESCRIPTION
                    ? "text-amber"
                    : "text-muted-3"
              }
            >
              {descriptionLength}/{MAX_DESCRIPTION}
            </span>
          </div>
          <FieldError message={errors.description} />
        </div>

        {busy !== "idle" && (
          <Notice tone="blue">
            <Spinner />
            {busy === "saving" ? t.savingDraft : t.submitting}
          </Notice>
        )}

        {draftSaved && busy === "idle" && (
          <Notice tone="green">
            <CheckIcon size={16} />
            {t.draftSaved}
          </Notice>
        )}

        {formError && <Notice tone="red">{formError}</Notice>}

        <div className="flex flex-wrap gap-3 pt-2">
          <Button
            variant="outline"
            className="min-w-[140px] flex-1"
            onClick={onSaveDraft}
            disabled={busy !== "idle"}
          >
            {t.saveDraft}
          </Button>
          <Button
            className="min-w-[140px] flex-1"
            onClick={onSubmit}
            disabled={busy !== "idle"}
          >
            {t.submitBtn}
          </Button>
        </div>
      </div>

      <p className="mt-6 text-center text-[13px] text-muted-2">
        <Link href={`/contests/${slug}`} className="text-muted underline hover:text-text">
          {contestTitle}
        </Link>
      </p>
    </>
  );
}

function SuccessView({ onEdit }: { onEdit: () => void }) {
  return (
    <div className="cc-enter px-5 py-15 text-center">
      <div
        className="mx-auto mb-6 flex size-15 items-center justify-center rounded-full border
                   border-green/30 bg-green/10"
      >
        <CheckIcon size={26} className="text-green-light" />
      </div>
      <h2 className="mb-2 text-[21px] font-extrabold">{t.successTitle}</h2>
      <p className="mb-7 text-[14.5px] text-muted">{t.successDesc}</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button variant="outline" onClick={onEdit}>
          {t.editSubmission}
        </Button>
        <Button variant="subtle" asChild>
          <Link href="/profile">{t.viewProfile}</Link>
        </Button>
      </div>
    </div>
  );
}

function Notice({ tone, children }: { tone: "blue" | "green" | "red"; children: React.ReactNode }) {
  const tones = {
    blue: "bg-blue/8 border-blue/20 text-blue-pale",
    green: "bg-green/8 border-green/25 text-green-light",
    red: "bg-red/8 border-red/25 text-red",
  } as const;

  return (
    <div
      className={`flex items-center gap-2.5 rounded-[9px] border px-3.5 py-3.5
                  text-[13.5px] ${tones[tone]}`}
    >
      {children}
    </div>
  );
}

function Spinner() {
  return (
    <span
      className="inline-block size-3.5 shrink-0 rounded-full border-2 border-blue-pale/30
                 border-t-blue-pale"
      style={{ animation: "cc-spin 0.8s linear infinite" }}
    />
  );
}

function GithubIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 0C5.37 0 0 5.5 0 12.3c0 5.44 3.44 10.05 8.2 11.68.6.12.82-.27.82-.6v-2.1c-3.34.75-4.04-1.65-4.04-1.65-.55-1.44-1.33-1.82-1.33-1.82-1.09-.77.08-.75.08-.75 1.2.09 1.84 1.27 1.84 1.27 1.07 1.87 2.8 1.33 3.49 1.02.1-.79.42-1.33.76-1.64-2.66-.31-5.47-1.37-5.47-6.1 0-1.35.46-2.45 1.23-3.31-.12-.31-.53-1.57.12-3.28 0 0 1-.33 3.3 1.27a11 11 0 0 1 6 0c2.3-1.6 3.3-1.27 3.3-1.27.65 1.71.24 2.97.12 3.28.77.86 1.23 1.96 1.23 3.31 0 4.74-2.82 5.78-5.5 6.09.43.38.81 1.13.81 2.29v3.39c0 .33.22.72.83.6A12.3 12.3 0 0 0 24 12.3C24 5.5 18.63 0 12 0z" />
    </svg>
  );
}

function VideoIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M23 7l-7 5 7 5V7z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}
