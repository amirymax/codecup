"use client";

import { AlertIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { common } from "@/messages/ru";

export default function ContestError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto max-w-[480px] px-5 py-30 text-center">
      <div
        className="mx-auto mb-6 flex size-14 items-center justify-center rounded-xl
                   border border-red/25 bg-red/10"
      >
        <AlertIcon className="text-red" />
      </div>
      <h2 className="mb-2 text-[19px] font-bold">{common.error}</h2>
      <p className="mb-6 text-sm text-muted">{common.errorDesc}</p>
      <Button variant="subtle" onClick={reset}>
        {common.retry}
      </Button>
    </div>
  );
}
