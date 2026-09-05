"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { CheckIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { saveReview } from "@/lib/api/admin";
import { ApiRequestError } from "@/lib/api/errors";
import { review as t } from "@/messages/ru";
import type { AdminSubmission } from "@/lib/api/types";

/** Панель оценки справа на экране проверки. */
export function ReviewPanel({ submission }: { submission: AdminSubmission }) {
  const router = useRouter();

  const [score, setScore] = useState(submission.score?.toString() ?? "");
  const [notes, setNotes] = useState(submission.reviewer_notes ?? "");
  const [isWinner, setIsWinner] = useState(submission.is_winner ?? false);
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setState("saving");
    setError(null);
    try {
      await saveReview(submission.id, {
        score: score === "" ? null : Number(score),
        reviewer_notes: notes,
        is_winner: isWinner,
      });
      setState("saved");
      router.refresh();
    } catch (caught) {
      setState("idle");
      setError(caught instanceof ApiRequestError ? caught.message : t.saving);
    }
  }

  return (
    <div
      className="sticky top-21 flex flex-col gap-4.5 rounded-card border border-line-2
                 bg-surface p-5.5"
    >
      <div>
        <Label htmlFor="score">{t.scoreLabel}</Label>
        <Input
          id="score"
          type="number"
          min={0}
          max={100}
          value={score}
          onChange={(event) => {
            setScore(event.target.value);
            setState("idle");
          }}
          className="bg-surface-2 py-2.5 font-mono"
        />
        {/* Бонус за видео начисляется сам, поэтому оценка тут — без него. */}
        <div className="mt-2 flex items-center justify-between text-[12.5px]">
          <span className="text-muted-2">
            {t.totalLabel} · {submission.video_bonus ? t.videoBonusHint : t.noVideoHint}
          </span>
          <span className="font-mono font-bold text-text">
            {score === "" ? "—" : Number(score) + submission.video_bonus}
          </span>
        </div>
      </div>

      <div>
        <Label htmlFor="notes">{t.notesLabel}</Label>
        <Textarea
          id="notes"
          rows={4}
          value={notes}
          onChange={(event) => {
            setNotes(event.target.value);
            setState("idle");
          }}
          placeholder={t.notesPlaceholder}
          className="bg-surface-2 py-2.5 text-[13.5px]"
        />
      </div>

      <label
        className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-green/20
                   bg-green/[0.06] px-3 py-2.5"
      >
        <input
          type="checkbox"
          checked={isWinner}
          onChange={(event) => {
            setIsWinner(event.target.checked);
            setState("idle");
          }}
          className="size-4 accent-green"
        />
        <span className="text-[13.5px] font-semibold text-green-light">{t.markWinner}</span>
      </label>

      {state === "saving" && (
        <Notice tone="blue">
          <Spinner />
          {t.saving}
        </Notice>
      )}
      {state === "saved" && (
        <Notice tone="green">
          <CheckIcon size={14} />
          {t.saved}
        </Notice>
      )}
      {error && <Notice tone="red">{error}</Notice>}

      <Button onClick={save} disabled={state === "saving"}>
        {t.saveReview}
      </Button>
    </div>
  );
}

function Notice({ tone, children }: { tone: "blue" | "green" | "red"; children: React.ReactNode }) {
  const tones = {
    blue: "bg-blue/8 border-blue/20 text-blue-pale",
    green: "bg-green/8 border-green/20 text-green-light",
    red: "bg-red/8 border-red/25 text-red",
  } as const;
  return (
    <div className={`flex items-center gap-2 rounded-lg border px-3 py-3 text-[13px] ${tones[tone]}`}>
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
