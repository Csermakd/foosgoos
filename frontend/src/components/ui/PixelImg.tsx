import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * A sprite from `pixel_assets`.
 *
 * Exists so `image-rendering: pixelated` is never forgotten - the sprites are
 * small (135px tall for a full player) and get scaled up, and without this the
 * browser smooths them into mush, which is the single fastest way to make
 * pixel art stop looking like pixel art.
 *
 * Decorative by default: pass `alt` only when the sprite carries meaning the
 * surrounding text does not already state.
 */
function PixelImg({
  alt,
  outlined,
  className,
  ...props
}: React.ComponentProps<"img"> & {
  /** Trace the sprite's silhouette. Needed for any sprite containing white
   *  pixels that would otherwise dissolve into the page. */
  outlined?: boolean;
}) {
  return (
    <img
      {...props}
      alt={alt ?? ""}
      aria-hidden={alt ? undefined : true}
      data-pixel
      className={cn(
        "[image-rendering:pixelated] select-none",
        outlined && "pixel-outline",
        className
      )}
      draggable={false}
    />
  );
}

export { PixelImg };
