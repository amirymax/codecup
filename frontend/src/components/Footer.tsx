import Link from "next/link";

import { landing } from "@/messages/ru";

export function Footer() {
  return (
    <footer
      className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-4
                 border-t border-line px-5 py-7 sm:px-10"
    >
      <span className="text-[13px] text-muted-2">{landing.footerCopy}</span>
      <div className="flex gap-5">
        <Link href="/login" className="text-[13px] text-muted no-underline hover:text-text">
          {landing.footerLogin}
        </Link>
        <Link href="/" className="text-[13px] text-muted no-underline hover:text-text">
          {landing.footerContest}
        </Link>
      </div>
    </footer>
  );
}
