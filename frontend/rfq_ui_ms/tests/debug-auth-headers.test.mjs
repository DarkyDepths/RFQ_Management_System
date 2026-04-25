import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const apiSource = await readFile(
  path.join(process.cwd(), "src", "config", "api.ts"),
  "utf8",
);
const actorSource = await readFile(
  path.join(process.cwd(), "src", "lib", "manager-actor.ts"),
  "utf8",
);

assert.ok(
  apiSource.includes(
    'process.env.NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED === "true"',
  ),
);
assert.ok(
  actorSource.includes("if (!apiConfig.managerDebugHeadersEnabled) {"),
);
assert.ok(actorSource.includes("return {};"));
