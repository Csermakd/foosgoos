import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Icons drawn on a pixel grid.
 *
 * The app is pixel art, so a set of smooth 1.5px-stroke Lucide glyphs sitting
 * next to the sprites read as borrowed from a different program. These are
 * literal grids: one `#` is one square, rendered with `shapeRendering:
 * crispEdges` and filled with `currentColor`, so they inherit text colour and
 * stay hard-edged at any size.
 *
 * Add a glyph by drawing it. That is the entire authoring process.
 */
const GLYPHS = {
  arrowLeft: [
    "...#...",
    "..##...",
    ".###...",
    "#######",
    ".###...",
    "..##...",
    "...#...",
  ],
  chevronDown: ["#.....#", "##...##", ".##.##.", "..###..", "...#..."],
  chevronUp: ["...#...", "..###..", ".##.##.", "##...##", "#.....#"],
  search: [
    ".###....",
    "#...#...",
    "#...#...",
    "#...#...",
    ".###....",
    "....##..",
    ".....##.",
    "......##",
  ],
  swap: [
    ".#.....",
    "###....",
    ".#...#.",
    ".#...#.",
    ".#...#.",
    ".#..###",
    ".....#.",
  ],
  chart: [
    "........",
    "......##",
    "......##",
    "...##.##",
    "...##.##",
    "##.##.##",
    "##.##.##",
    "########",
  ],
  check: [
    "......#",
    ".....##",
    "#...##.",
    "##.##..",
    ".###...",
    "..#....",
    ".......",
  ],
  cross: [
    "#.....#",
    "##...##",
    ".##.##.",
    "..###..",
    ".##.##.",
    "##...##",
    "#.....#",
  ],
} as const;

export type PixelIconName = keyof typeof GLYPHS;

function PixelIcon({
  name,
  className,
  title,
  ...props
}: { name: PixelIconName; title?: string } & React.ComponentProps<"svg">) {
  const grid = GLYPHS[name];
  const rows = grid.length;
  const cols = grid[0].length;

  return (
    <svg
      viewBox={`0 0 ${cols} ${rows}`}
      shapeRendering="crispEdges"
      fill="currentColor"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      className={cn("size-4", className)}
      {...props}
    >
      {title && <title>{title}</title>}
      {grid.flatMap((row, y) =>
        [...row].map((cell, x) =>
          cell === "#" ? (
            <rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" />
          ) : null
        )
      )}
    </svg>
  );
}

export { PixelIcon };
