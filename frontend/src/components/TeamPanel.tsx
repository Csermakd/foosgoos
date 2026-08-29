import * as React from "react";

import { PixelImg } from "@/components/ui/PixelImg";
import { cn } from "@/lib/utils";

/** A team-coloured card. The header band is the only place the team colour
 *  appears, matching how PlayerCard is built, so the roster picker and the
 *  live game read as the same component family. */
const TeamPanel = ({
  team,
  title,
  icon,
  aside,
  children,
  className,
}: {
  team: "blue" | "red";
  title: string;
  icon?: string;
  /** Right-hand slot in the header - the live score, usually. */
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) => (
  <section
    className={cn(
      "w-full max-w-xs overflow-hidden rounded-base border-2 border-border bg-secondary-background shadow-shadow",
      className
    )}
  >
    <header
      className={cn(
        "flex items-center gap-3 border-b-2 border-border px-4 py-3",
        team === "blue" ? "bg-blue-team-soft" : "bg-red-team-soft"
      )}
    >
      {icon && (
        <PixelImg src={icon} outlined className="h-8 w-8 shrink-0" />
      )}
      <h2 className="font-heading uppercase tracking-wide">{title}</h2>
      {aside && <div className="ml-auto">{aside}</div>}
    </header>
    <div className="flex flex-col gap-4 p-4">{children}</div>
  </section>
);

export default TeamPanel;
