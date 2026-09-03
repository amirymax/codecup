"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { deleteSubmission } from "@/lib/api/admin";
import { ApiRequestError } from "@/lib/api/errors";
import { review as t } from "@/messages/ru";

/** Удаление заявки с экрана проверки: спам и дубли. */
export function DeleteSubmissionButton({ id, contestSlug }: { id: number; contestSlug: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    // Вернуть заявку нельзя, поэтому спрашиваем прямо.
    if (!window.confirm(t.deleteConfirm)) return;

    setBusy(true);
    setError(null);
    try {
      await deleteSubmission(id);
      router.replace(`/admin/submissions?contest=${contestSlug}`);
      router.refresh();
    } catch (caught) {
      setBusy(false);
      setError(caught instanceof ApiRequestError ? caught.message : t.deleteFailed);
    }
  }

  return (
    <div className="mt-4">
      <button
        type="button"
        onClick={remove}
        disabled={busy}
        className="w-full cursor-pointer rounded-lg border border-red/30 bg-transparent px-4 py-2.5
                   text-[13px] font-semibold text-red transition-colors hover:bg-red/10
                   disabled:opacity-50"
      >
        {busy ? t.deleting : t.deleteCta}
      </button>
      {error && <p className="mt-2 text-[12.5px] text-red">{error}</p>}
    </div>
  );
}
