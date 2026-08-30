import { Skeleton } from "@/components/ui/skeleton";

export default function ContestLoading() {
  return (
    <div className="min-h-screen bg-ink">
      <div className="h-16 border-b border-line" />
      <div className="mx-auto max-w-[1180px] px-5 py-10 sm:px-10">
        <Skeleton className="mb-6 h-5.5 w-[140px]" />
        <Skeleton className="mb-4 h-10 w-[70%]" />
        <Skeleton className="mb-10 h-4.5 w-1/2" />
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
          <Skeleton className="h-[320px]" />
          <Skeleton className="h-[320px]" />
        </div>
      </div>
    </div>
  );
}
