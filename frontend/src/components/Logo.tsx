import Link from "next/link";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex shrink-0 items-center gap-2 no-underline">
      <span
        className="flex size-[26px] items-center justify-center rounded-[7px] font-mono
                   text-[13px] font-bold text-ink"
        style={{ background: "linear-gradient(135deg, #22c55e, #3b82f6)" }}
      >
        C
      </span>
      <span className="text-base font-bold tracking-tight text-text">
        CodeCup<span className="text-green">.</span>tech
      </span>
    </Link>
  );
}
