import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/** Small flat chip. Same border and weight as every other surface so a
 *  "BLUE WON" pill reads as part of the app, not as a stray Bootstrap label. */
const badgeVariants = cva(
  "inline-flex items-center gap-1 whitespace-nowrap rounded-base border-2 border-border px-2 py-0.5 text-sm font-heading uppercase tracking-wide",
  {
    variants: {
      variant: {
        neutral: "bg-secondary-background text-foreground",
        muted: "bg-sunken text-muted-foreground",
        blue: "bg-blue-team text-main-foreground",
        red: "bg-red-team text-main-foreground",
        success: "bg-success text-main-foreground",
        gold: "bg-gold text-main-foreground",
        silver: "bg-silver text-main-foreground",
        bronze: "bg-bronze text-main-foreground",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };
