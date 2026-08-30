import { Skeleton } from "@/components/ui/skeleton";

/** Состояние загрузки главной — скелетоны из макета. */
export default function LandingLoading() {
  return (
    <div className="min-h-screen bg-ink">
      <div className="h-16 border-b border-line" />
      <div className="mx-auto max-w-[1180px] px-5 pt-24 text-center sm:px-10">
        <Skeleton className="mx-auto mb-7 h-6.5 w-[200px] rounded-full" />
        <Skeleton className="mx-auto mb-4 h-14 w-full max-w-[680px]" />
        <Skeleton className="mx-auto mb-10 h-14 w-full max-w-[520px]" />
        <div className="mx-auto grid max-w-[700px] gap-px overflow-hidden rounded-xl bg-line sm:grid-cols-3">
          {[0, 1, 2].map((slot) => (
            <div key={slot} className="bg-surface px-4 py-6">
              <Skeleton className="mb-2.5 h-6 w-3/5" />
              <Skeleton className="h-3 w-4/5" />
            </div>
          ))}
        </div>
        <Skeleton className="mt-14 h-[280px] rounded-2xl" />
      </div>
    </div>
  );
}
