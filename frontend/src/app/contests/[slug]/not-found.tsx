import Link from "next/link";

import { AlertIcon } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { contest as t } from "@/messages/ru";

export default function ContestNotFound() {
  return (
    <div className="mx-auto max-w-[480px] px-5 py-30 text-center">
      <div
        className="mx-auto mb-6 flex size-14 items-center justify-center rounded-xl
                   border border-red/25 bg-red/10"
      >
        <AlertIcon className="text-red" />
      </div>
      <h2 className="mb-2 text-[19px] font-bold">{t.notFoundTitle}</h2>
      <p className="mb-6 text-sm text-muted">{t.notFoundDesc}</p>
      <Button variant="subtle" asChild>
        <Link href="/">{t.backHome}</Link>
      </Button>
    </div>
  );
}
