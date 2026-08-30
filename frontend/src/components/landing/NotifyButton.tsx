"use client";

import { useState } from "react";

import { CheckIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";
import { ApiRequestError } from "@/lib/api/errors";
import { landing } from "@/messages/ru";

/** «Уведомить меня» — гостя сначала отправляем на вход. */
export function NotifyButton({ isAuthenticated }: { isAuthenticated: boolean }) {
  const [state, setState] = useState<"idle" | "saving" | "done">("idle");

  async function subscribe() {
    setState("saving");
    try {
      await api.post("/api/me/notify/");
      setState("done");
    } catch (error) {
      // Единственный ожидаемый отказ — истёкшая сессия; тогда на вход.
      if (error instanceof ApiRequestError && error.isUnauthorized) {
        window.location.href = "/login?next=/";
        return;
      }
      setState("idle");
    }
  }

  if (!isAuthenticated) {
    return (
      <Button variant="subtle" size="sm" asChild>
        <a href="/login?next=/">{landing.notifyMe}</a>
      </Button>
    );
  }

  if (state === "done") {
    return (
      <span className="inline-flex items-center gap-2 text-[14px] font-semibold text-green-light">
        <CheckIcon size={16} />
        {landing.notifyDone}
      </span>
    );
  }

  return (
    <Button variant="subtle" size="sm" onClick={subscribe} disabled={state === "saving"}>
      {landing.notifyMe}
    </Button>
  );
}
