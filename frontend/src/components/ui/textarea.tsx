import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "w-full resize-y rounded-[9px] border border-line-2 bg-surface px-3.5 py-3",
        "text-[14.5px] leading-relaxed text-text transition-colors",
        "aria-[invalid=true]:border-red-dark",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
