import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Blue | table | red.
 *
 * Both match screens draw this arrangement, and both used to do it with their
 * own `flex ... gap-8` incantation - one of them stretching edge to edge with
 * `w-screen`, which meant the columns collapsed into the table on a tablet.
 * A grid that stacks below `lg` fixes both at once.
 */
const MatchLayout = ({
  blue,
  center,
  red,
  className,
}: {
  blue: React.ReactNode;
  center: React.ReactNode;
  red: React.ReactNode;
  className?: string;
}) => (
  <div
    className={cn(
      "grid grid-cols-1 items-stretch gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)_minmax(0,1fr)] lg:gap-8",
      className
    )}
  >
    <div className="order-2 flex flex-col items-center justify-center gap-6 lg:order-1">
      {blue}
    </div>
    <div className="order-1 flex flex-col items-center justify-center gap-6 lg:order-2">
      {center}
    </div>
    <div className="order-3 flex flex-col items-center justify-center gap-6">{red}</div>
  </div>
);

export default MatchLayout;
