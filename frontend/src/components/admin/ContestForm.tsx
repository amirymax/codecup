"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { FieldError } from "@/components/FieldError";
import { ArrowLeftIcon, CheckIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createContest, publishContest, updateContest } from "@/lib/api/admin";
import { ApiRequestError } from "@/lib/api/errors";
import { formatMoney } from "@/lib/format";
import { admin, createContest as t } from "@/messages/ru";
import type { AdminContest } from "@/lib/api/types";

type Busy = "idle" | "saving" | "publishing";

/** Форма создания и правки контеста с предпросмотром карточки справа. */
export function ContestForm({ existing }: { existing?: AdminContest }) {
  const router = useRouter();

  const [title, setTitle] = useState(existing?.title ?? "");
  const [description, setDescription] = useState(existing?.description ?? "");
  const [requirements, setRequirements] = useState<string[]>(
    existing?.requirements?.length ? existing.requirements : ["", ""],
  );
  const [prize, setPrize] = useState(existing?.prize_pool ?? "");
  const [deadline, setDeadline] = useState(toLocalInput(existing?.deadline));

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<Busy>("idle");
  const [saved, setSaved] = useState<"draft" | "published" | null>(null);

  function payload() {
    return {
      title,
      description,
      // Пустые строки backend отвергнет, поэтому чистим их здесь.
      requirements: requirements.map((item) => item.trim()).filter(Boolean),
      prize_pool: prize || "0",
      deadline: deadline ? new Date(deadline).toISOString() : "",
    };
  }

  async function run(action: () => Promise<AdminContest>, done: "draft" | "published") {
    setErrors({});
    setSaved(null);
    setBusy(done === "published" ? "publishing" : "saving");
    try {
      const contest = await action();
      setSaved(done);
      router.refresh();
      if (!existing) router.replace(`/admin/contests/${contest.id}`);
    } catch (error) {
      if (error instanceof ApiRequestError) {
        const fields = error.fieldErrors;
        setErrors(Object.keys(fields).length ? fields : { title: error.message });
      }
    } finally {
      setBusy("idle");
    }
  }

  const saveDraft = () =>
    run(
      () =>
        existing
          ? updateContest(existing.id, payload())
          : createContest({ ...payload(), status: "draft" }),
      "draft",
    );

  /**
   * Публикация идёт в два запроса: сначала сохраняем правки, затем меняем
   * статус. Так на backend остаётся одно место, отвечающее за публикацию.
   */
  const publish = () =>
    run(async () => {
      const contest = existing
        ? await updateContest(existing.id, payload())
        : await createContest({ ...payload(), status: "draft" });
      return publishContest(contest.id);
    }, "published");

  return (
    <>
      <Link
        href="/admin"
        className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                   no-underline hover:text-text-2"
      >
        <ArrowLeftIcon />
        {admin.dashboard}
      </Link>
      <h1 className="mb-8 text-2xl font-extrabold tracking-tight sm:text-[1.9rem]">
        {existing ? t.editHeading : t.heading}
      </h1>

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex min-w-0 flex-col gap-6">
          <div>
            <Label htmlFor="title">{t.titleLabel}</Label>
            <Input
              id="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder={t.titlePlaceholder}
              aria-invalid={Boolean(errors.title)}
            />
            <FieldError message={errors.title} />
          </div>

          <div>
            <Label htmlFor="description">{t.descriptionLabel}</Label>
            <Textarea
              id="description"
              rows={4}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder={t.descriptionPlaceholder}
            />
            <FieldError message={errors.description} />
          </div>

          <div>
            <Label>{t.requirementsLabel}</Label>
            <div className="flex flex-col gap-2">
              {requirements.map((requirement, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Input
                    value={requirement}
                    onChange={(event) =>
                      setRequirements((current) =>
                        current.map((item, i) => (i === index ? event.target.value : item)),
                      )
                    }
                    className="flex-1 py-2.5"
                  />
                  <button
                    type="button"
                    aria-label="Удалить требование"
                    onClick={() =>
                      setRequirements((current) => current.filter((_, i) => i !== index))
                    }
                    className="size-9 shrink-0 cursor-pointer rounded-lg border border-line-2
                               bg-transparent text-muted-2 hover:border-red-dark hover:text-red"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={() => setRequirements((current) => [...current, ""])}
              className="mt-2.5 cursor-pointer border-none bg-transparent text-[13.5px]
                         font-semibold text-blue-light"
            >
              {t.addRequirement}
            </button>
            <FieldError message={errors.requirements} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="prize">{t.prizeLabel}</Label>
              <Input
                id="prize"
                value={prize}
                onChange={(event) => setPrize(event.target.value)}
                placeholder="5000"
                className="font-mono"
                aria-invalid={Boolean(errors.prize_pool)}
              />
              <FieldError message={errors.prize_pool} />
            </div>
            <div>
              <Label htmlFor="deadline">{t.deadlineLabel}</Label>
              <Input
                id="deadline"
                type="datetime-local"
                value={deadline}
                onChange={(event) => setDeadline(event.target.value)}
                className="font-mono [color-scheme:dark]"
                aria-invalid={Boolean(errors.deadline)}
              />
              <FieldError message={errors.deadline} />
            </div>
          </div>

          {busy !== "idle" && (
            <Notice tone="blue">
              <Spinner />
              {t.publishing}
            </Notice>
          )}
          {saved && busy === "idle" && (
            <Notice tone="green">
              <CheckIcon size={16} />
              {saved === "published" ? t.publishedMsg : t.savedMsg}
            </Notice>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button
              variant="outline"
              className="min-w-[140px] flex-1"
              onClick={saveDraft}
              disabled={busy !== "idle"}
            >
              {t.saveDraft}
            </Button>
            <Button className="min-w-[140px] flex-1" onClick={publish} disabled={busy !== "idle"}>
              {t.publish}
            </Button>
          </div>
        </div>

        <aside className="min-w-0">
          <div className="mb-3 text-xs font-bold tracking-wide text-muted-2 uppercase">
            {t.livePreview}
          </div>
          <div
            className="sticky top-21 rounded-card border border-line-2 bg-gradient-to-b
                       from-[#101012] to-[#0b0b0d] p-6"
          >
            <span
              className="mb-3.5 inline-block rounded-full border border-green/30 bg-green/10
                         px-2.5 py-1 text-[11px] font-bold text-green-light"
            >
              {t.live}
            </span>
            <h3 className="mb-2 text-[17px] font-extrabold text-text">
              {title || t.defaultTitle}
            </h3>
            <p className="mb-4 text-[13px] leading-relaxed text-muted">
              {description || t.defaultDesc}
            </p>
            <div className="flex gap-5">
              <div>
                <div className="mb-1 text-[10.5px] text-muted-2 uppercase">{t.prizeWord}</div>
                <div className="font-mono text-[15px] font-bold text-green-light">
                  {formatMoney(prize || "0")}
                </div>
              </div>
              <div>
                <div className="mb-1 text-[10.5px] text-muted-2 uppercase">{t.deadlineLabel}</div>
                <div className="font-mono text-[15px] font-bold text-text">
                  {deadline ? deadline.split("T")[0] : "—"}
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}

/** ISO с сервера → значение для input[type=datetime-local] в местном времени. */
function toLocalInput(iso: string | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function Notice({ tone, children }: { tone: "blue" | "green"; children: React.ReactNode }) {
  const tones = {
    blue: "bg-blue/8 border-blue/20 text-blue-pale",
    green: "bg-green/8 border-green/25 text-green-light",
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
