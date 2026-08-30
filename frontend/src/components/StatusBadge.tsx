import { statusLabels } from "@/messages/ru";
import { cn } from "@/lib/utils";

type Status = keyof typeof statusLabels;

/** Цвета бейджей повторяют макеты: победа и «идёт» зелёные, отправлено синее. */
const STYLES: Record<Status, string> = {
  draft: "bg-surface-3 border-line-2 text-muted",
  submitted: "bg-blue/10 border-blue/30 text-blue-light",
  reviewed: "bg-amber/10 border-amber/30 text-amber",
  winner: "bg-green/10 border-green/30 text-green-light",
  live: "bg-green/10 border-green/30 text-green-light",
  ended: "bg-surface-3 border-line-2 text-muted",
  archived: "bg-surface-3 border-line-2 text-muted",
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-full border px-3 py-[5px]",
        "text-xs font-semibold whitespace-nowrap",
        STYLES[status],
        className,
      )}
    >
      {statusLabels[status]}
    </span>
  );
}
