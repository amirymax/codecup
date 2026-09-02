"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { savePaymentRequisites } from "@/lib/api/admin";
import { payments as t } from "@/messages/ru";

type State = "idle" | "saving" | "saved" | "error";

/**
 * Реквизиты для оплаты.
 *
 * Их видит каждый участник платного контеста, а меняются они чаще, чем
 * выкатывается код, — поэтому правятся отсюда, а не в .env на сервере.
 */
export function RequisitesForm({ initial }: { initial: string }) {
  const router = useRouter();
  const [value, setValue] = useState(initial);
  const [state, setState] = useState<State>("idle");

  async function save() {
    setState("saving");
    try {
      await savePaymentRequisites(value);
      setState("saved");
      // Страница серверная: без refresh она осталась бы со старым текстом.
      router.refresh();
    } catch {
      setState("error");
    }
  }

  return (
    <section className="mb-8 rounded-xl border border-line bg-surface p-5">
      <h2 className="mb-1 text-[15px] font-bold text-text">{t.requisitesTitle}</h2>
      <p className="mb-4 text-[13px] text-muted-2">{t.requisitesHint}</p>

      <Textarea
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
          setState("idle");
        }}
        rows={5}
        placeholder={t.requisitesPlaceholder}
        className="mb-4 font-mono text-[13px]"
      />

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={state === "saving" || value === initial}>
          {state === "saving" ? t.saving : t.requisitesSave}
        </Button>
        {state === "saved" && <span className="text-[13px] text-green-light">{t.requisitesSaved}</span>}
        {state === "error" && <span className="text-[13px] text-red">{t.requisitesFailed}</span>}
      </div>
    </section>
  );
}
