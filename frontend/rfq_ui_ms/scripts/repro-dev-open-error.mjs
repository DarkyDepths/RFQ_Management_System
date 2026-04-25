import http from "node:http";
import { spawn } from "node:child_process";
import { resolve } from "node:path";

const projectRoot = resolve("d:/PFE/rfq_ui_ms");
const port = process.env.REPRO_PORT || "3103";
const childArgs = process.argv.slice(2);
const commandArgs =
  childArgs.length > 0 ? childArgs : [resolve(projectRoot, "scripts/dev.mjs")];

const child = spawn(process.execPath, commandArgs, {
  cwd: projectRoot,
  env: {
    ...process.env,
    PORT: port,
  },
  stdio: ["ignore", "pipe", "pipe"],
});

let output = "";
let requested = false;
let finished = false;

function shutdown(code) {
  if (finished) {
    return;
  }
  finished = true;
  child.kill("SIGTERM");
  process.exit(code);
}

function get(url) {
  return new Promise((resolveRequest, rejectRequest) => {
    const req = http.get(url, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        resolveRequest({
          statusCode: res.statusCode ?? 0,
          body,
        });
      });
    });

    req.on("error", rejectRequest);
    req.setTimeout(5000, () => {
      req.destroy(new Error(`Timed out fetching ${url}`));
    });
  });
}

async function probe() {
  if (requested) {
    return;
  }
  requested = true;

  try {
    const page = await get(`http://127.0.0.1:${port}/`);
    console.log(`[probe] GET / -> ${page.statusCode}`);
    const chunkMatches = [...page.body.matchAll(/\/_next\/static\/chunks\/[^"' )]+/g)].map((match) => match[0]);
    console.log(`[probe] HTML chunk refs -> ${chunkMatches.join(", ")}`);

    for (let attempt = 1; attempt <= 3; attempt += 1) {
      const chunk = await get(`http://127.0.0.1:${port}/_next/static/chunks/app/layout.js`);
      console.log(`[probe] GET layout.js #${attempt} -> ${chunk.statusCode}`);
    }

    setTimeout(() => shutdown(0), 3000);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[probe-error] ${message}`);
    shutdown(2);
  }
}

function onChunk(chunk) {
  const text = chunk.toString();
  process.stdout.write(text);
  output += text;

  if (text.includes("UNKNOWN: unknown error, open")) {
    console.error("[repro-found] layout chunk open failure detected");
    setTimeout(() => shutdown(3), 1000);
    return;
  }

  if (output.includes("Ready in")) {
    setTimeout(probe, 1000);
  }
}

child.stdout.on("data", onChunk);
child.stderr.on("data", onChunk);

child.on("exit", (code) => {
  if (!finished) {
    console.log(`[child-exit] ${code ?? 0}`);
    shutdown(code ?? 0);
  }
});

setTimeout(() => {
  console.error("[timeout] repro timed out");
  shutdown(4);
}, 30000);
