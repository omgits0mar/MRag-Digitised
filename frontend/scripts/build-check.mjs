import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const distDir = path.join(projectRoot, "dist");
const entryBudgetBytes = 200 * 1024;
const forbiddenTokens = ["mockServiceWorker", "@mswjs", 'from "msw"', "from 'msw'"];

function fail(message) {
  console.error(`build-check: ${message}`);
  process.exitCode = 1;
}

function walkFiles(directory) {
  return fs.readdirSync(directory, {
    withFileTypes: true,
  }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      return walkFiles(fullPath);
    }

    return [fullPath];
  });
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function gzipSize(filePath) {
  const contents = fs.readFileSync(filePath);
  return zlib.gzipSync(contents).byteLength;
}

if (!fs.existsSync(distDir)) {
  fail("dist/ is missing. Run `npm run build` first.");
} else {
  const builtFiles = walkFiles(distDir);
  const textFiles = builtFiles.filter((filePath) => /\.(?:html|js|css|json|txt)$/.test(filePath));
  const mockWorkerPath = path.join(distDir, "mockServiceWorker.js");

  if (fs.existsSync(mockWorkerPath)) {
    fail("dist/mockServiceWorker.js should not be present in production output.");
  }

  for (const filePath of textFiles) {
    const contents = readText(filePath);

    for (const token of forbiddenTokens) {
      if (contents.includes(token)) {
        fail(`Found forbidden token "${token}" in ${path.relative(projectRoot, filePath)}.`);
      }
    }
  }

  const indexHtmlPath = path.join(distDir, "index.html");
  if (!fs.existsSync(indexHtmlPath)) {
    fail("dist/index.html is missing.");
  } else {
    const indexHtml = readText(indexHtmlPath);
    const entryMatch = indexHtml.match(/<script[^>]+src="([^"]+\.js)"/);

    if (entryMatch === null) {
      fail("Could not determine the main entry chunk from dist/index.html.");
    } else {
      const entryScriptPath = path.join(distDir, entryMatch[1].replace(/^\//, ""));
      const entryGzipBytes = gzipSize(entryScriptPath);

      console.log(
        `build-check: main entry gzip size ${(entryGzipBytes / 1024).toFixed(2)} KB (${path.relative(projectRoot, entryScriptPath)})`,
      );

      if (entryGzipBytes > entryBudgetBytes) {
        fail(
          `Main entry chunk exceeds ${(entryBudgetBytes / 1024).toFixed(0)} KB gzip budget.`,
        );
      }
    }
  }

  if (process.exitCode !== 1) {
    console.log("build-check: production bundle passed mock-isolation and budget checks.");
  }
}
