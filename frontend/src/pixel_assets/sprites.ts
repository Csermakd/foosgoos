/**
 * Every sprite in the app, named once.
 *
 * Pages import from here rather than reaching into `../pixel_assets/...`
 * themselves, so a sprite can be swapped in one place and nothing ends up
 * half-migrated - which is how `trophy.png` sat in the repo unreferenced
 * while the leaderboard header held an empty flex wrapper where it belonged.
 */
import trophy from "./trophy.png";
import bluePlayer from "./characters/blue_player.png";
import redPlayer from "./characters/red_player.png";
import bluePlayerTorso from "./characters/blue_player_torso.png";
import redPlayerTorso from "./characters/red_player_torso.png";
import fiveBar from "./characters/5bar.png";
import table from "./table/table1.png";

export const sprites = {
  trophy,
  bluePlayer,
  redPlayer,
  bluePlayerTorso,
  redPlayerTorso,
  fiveBar,
  table,
} as const;

export type SpriteName = keyof typeof sprites;
