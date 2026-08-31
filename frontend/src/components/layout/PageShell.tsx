import * as React from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { PixelImg } from "@/components/ui/PixelImg";
import { cn } from "@/lib/utils";

/** How wide the content column is allowed to get. Named rather than passed as
 *  a class so screens can't each invent their own measure. */
const WIDTHS = {
  narrow: "max-w-md",
  regular: "max-w-2xl",
  wide: "max-w-4xl",
  full: "max-w-7xl",
} as const;

type PageShellProps = {
  title: string;
  subtitle?: string;
  /** Sprite shown beside the title. Every screen gets one, so the pixel art
   *  is part of the furniture rather than a decoration on one page. */
  icon?: string;
  /** Sits to the LEFT of the Home button - it does not replace it. Making
   *  this a replacement is what stranded the profile page with no way back. */
  action?: React.ReactNode;
  width?: keyof typeof WIDTHS;
  className?: string;
  children: React.ReactNode;
};

/**
 * The frame every screen sits in.
 *
 * Before this, each page positioned its own "Return Home" button - top left
 * absolutely positioned on one, top right inside a flex row on another - and
 * picked its own background and page padding. The result was that moving
 * between screens felt like moving between apps. Everything routable except
 * the home menu goes through here.
 */
const PageShell = ({
  title,
  subtitle,
  icon,
  action,
  width = "wide",
  className,
  children,
}: PageShellProps) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen w-full bg-background px-4 py-6 sm:px-8 sm:py-10">
      <div className={cn("mx-auto w-full", WIDTHS[width])}>
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b-2 border-border pb-4">
          <div className="flex items-center gap-3 sm:gap-4">
            {icon && <PixelImg src={icon} className="h-12 w-auto sm:h-14" />}
            <div>
              <h1 className="font-display text-lg sm:text-2xl">{title}</h1>
              {subtitle && (
                <p className="mt-1.5 text-sm text-muted-foreground">
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {action}
            <Button variant="neutral" onClick={() => navigate("/")}>
              <PixelIcon name="arrowLeft" />
              Home
            </Button>
          </div>
        </header>

        <main className={className}>{children}</main>
      </div>
    </div>
  );
};

export default PageShell;
