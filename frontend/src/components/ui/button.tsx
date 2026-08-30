import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Кнопка в стилистике CodeCup.
 *
 * Компонент из shadcn/ui переписан на токены проекта: значения по умолчанию
 * (`bg-primary` и подобные) в тёмной палитре макетов не читаются. Структура
 * каталога и утилита cn оставлены как есть, чтобы `npx shadcn add` работал
 * для будущих компонентов на Radix — модалки и тостов.
 */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-[9px] text-sm font-semibold " +
    "whitespace-nowrap transition-colors cursor-pointer disabled:pointer-events-none " +
    "disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 " +
    "focus-visible:ring-blue/60 focus-visible:ring-offset-2 focus-visible:ring-offset-ink " +
    "[&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-green text-green-ink font-bold hover:bg-green-light",
        telegram: "bg-blue text-white font-bold hover:bg-blue-dark",
        outline: "border border-line-2 text-text hover:border-line-3 hover:bg-surface-2",
        ghost: "text-muted hover:bg-surface-3 hover:text-text",
        subtle: "bg-surface-3 border border-line-2 text-text hover:border-line-3",
        danger: "border border-line-2 text-muted hover:border-red-dark hover:text-red",
      },
      size: {
        sm: "h-9 px-3.5 text-[13px]",
        md: "h-11 px-5",
        lg: "h-[50px] px-6 text-[15px]",
        icon: "size-[34px]",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export { Button, buttonVariants };
