import { cn } from "@/lib/utils";

/** Круглый градиентный аватар с первой буквой — как в макетах. */
export function Avatar({
  name,
  size = 26,
  className,
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full font-mono font-bold text-ink",
        className,
      )}
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.42),
        background: "linear-gradient(135deg, #3b82f6, #22c55e)",
      }}
    >
      {(name[0] ?? "?").toUpperCase()}
    </span>
  );
}
