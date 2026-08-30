import * as React from "react";

import { cn } from "@/lib/utils";

function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      className={cn(
        "mb-2 flex items-center gap-2 text-[13.5px] font-semibold text-text-2",
        className,
      )}
      {...props}
    />
  );
}

export { Label };
