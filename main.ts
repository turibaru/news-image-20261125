// news-image-20261125 — variant B (poster-grid) entrypoint.
// Copy-only: copies the pre-rendered entry.png sitting next to this file
// into MAKEFUN_OUTPUT_DIR. Node 22, standard library only, no network,
// no rendering, no writes to the repo. Exits non-zero if the copy fails,
// so a missing or unreadable entry.png can never silently pass.
import { copyFileSync } from "node:fs";
import { join } from "node:path";

const src = new URL("./entry.png", import.meta.url);
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const dest = join(outDir, "entry.png");

try {
  copyFileSync(src, dest);
} catch (err) {
  console.error(`failed to copy entry.png to ${dest}: ${err}`);
  process.exit(1);
}
