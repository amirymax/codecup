import { Skeleton } from "@/components/ui/skeleton";

export default function ProfileLoading() {
  return (
    <div className="min-h-screen bg-ink">
      <div className="h-16 border-b border-line" />
      <div className="mx-auto max-w-[880px] px-5 py-10 sm:px-10">
        <div className="mb-10 flex items-center gap-5">
          <Skeleton className="size-18 rounded-full" />
          <div className="flex-1">
            <Skeleton className="mb-2.5 h-5.5 w-[180px]" />
            <Skeleton className="h-3.5 w-[240px]" />
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {[0, 1, 2].map((slot) => (
            <Skeleton key={slot} className="h-19" />
          ))}
        </div>
      </div>
    </div>
  );
}
