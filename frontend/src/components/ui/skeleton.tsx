import { cn } from "@/lib/utils";

/** Скелетон с тем же мерцанием, что в макетах загрузки. */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("cc-skeleton", className)} {...props} />;
}

export { Skeleton };
