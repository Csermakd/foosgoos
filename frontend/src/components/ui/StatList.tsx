import * as React from "react";

import { cn } from "@/lib/utils";

export type Stat = {
  label: string;
  value: React.ReactNode;
  /** Draws the row in the danger colour - own goals, and nothing else so far. */
  tone?: "default" | "danger";
};

/** A label/value block. Shared by the profile page and the in-game player
 *  cards, which previously drew the same thing two different ways. */
function StatList({
  stats,
  className,
}: {
  stats: Stat[];
  className?: string;
}) {
  return (
    <dl
      className={cn(
        "divide-y-2 divide-border overflow-hidden rounded-base border-2 border-border bg-sunken",
        className
      )}
    >
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex items-center justify-between gap-4 px-4 py-2.5"
        >
          <dt
            className={cn(
              "text-sm",
              stat.tone === "danger" ? "text-danger" : "text-muted-foreground"
            )}
          >
            {stat.label}
          </dt>
          <dd
            className={cn(
              "font-heading tabular-nums",
              stat.tone === "danger" && "text-danger"
            )}
          >
            {stat.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export { StatList };
