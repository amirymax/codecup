import * as React from "react";

import { cn } from "@/lib/utils";

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "w-full rounded-[9px] border border-line-2 bg-surface px-3.5 py-3 text-[14.5px]",
        "text-text transition-colors",
        "aria-[invalid=true]:border-red-dark",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
