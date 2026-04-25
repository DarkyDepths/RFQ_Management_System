import { existsSync, realpathSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = realpathSync.native(resolve(scriptDir, ".."));
const devDistDir = join(projectRoot, ".next");
const projectNodeModules = join(projectRoot, "node_modules");
const nextCliEntrypoint = join(projectNodeModules, "next", "dist", "bin", "next");

function resetPath(targetPath) {
  if (!existsSync(targetPath)) {
    return;
  }

  rmSync(targetPath, {
    force: true,
    recursive: true,
  });
}

try {
  resetPath(devDistDir);
} catch (error) {
  const message =
    error instanceof Error ? error.message : "Unknown cleanup failure";
  console.error(
    `Unable to prepare the local .next directory for Next. Stop any running dev server and try again.\n${message}`,
  );
  process.exit(1);
}

const child = spawn(
  process.execPath,
  [nextCliEntrypoint, "dev", "--turbo"],
  {
    cwd: projectRoot,
    env: {
      ...process.env,
      NODE_PATH: [
        projectNodeModules,
        process.env.NODE_PATH,
      ]
        .filter(Boolean)
        .join(process.platform === "win32" ? ";" : ":"),
    },
    stdio: "inherit",
  },
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});
