/**
 * web-fetch — Fetch and extract text content from a web page via Ollama's local API.
 *
 * Usage:
 *   node web-fetch.ts "https://example.com"
 *   node web-fetch.ts "https://example.com" --max-links 20
 *   node web-fetch.ts "https://example.com" --no-content
 *   node web-fetch.ts "https://example.com" --json
 *
 * Options:
 *   --max-links <n>    Maximum number of links to show (default: 10, 0 to hide)
 *   --no-content       Omit page content, show only title and link count
 *   --json             Output raw JSON instead of formatted text
 *   --host <url>       Ollama host (default: http://localhost:11434)
 *
 * Environment:
 *   OLLAMA_HOST          Override default Ollama host URL
 *
 * Requires:
 *   - Ollama running locally with web fetch enabled
 *   - Node.js 24+ (uses fetch, --experimental-strip-types)
 */

interface FetchResponse {
  title: string;
  content: string;
  links: string[];
}

function parseArgs(argv: string[]): {
  url: string;
  maxLinks: number;
  noContent: boolean;
  jsonOutput: boolean;
  host: string;
} {
  const args = argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.error(`Usage: node web-fetch.ts "https://example.com" [options]

Options:
  --max-links <n>    Maximum links to show (default: 10, 0 to hide)
  --no-content       Omit page content, show only title and link count
  --json             Output raw JSON
  --host <url>       Ollama host (default: http://localhost:11434)

Environment:
  OLLAMA_HOST          Override default Ollama host URL`);
    process.exit(1);
  }

  let url = "";
  let maxLinks = 10;
  let noContent = false;
  let jsonOutput = false;
  let host = process.env.OLLAMA_HOST ?? "http://localhost:11434";

  let i = 0;
  const positional: string[] = [];
  while (i < args.length) {
    if (args[i] === "--max-links") {
      const n = parseInt(args[++i], 10);
      maxLinks = Number.isNaN(n) ? 10 : Math.max(0, n);
    } else if (args[i] === "--no-content") {
      noContent = true;
    } else if (args[i] === "--json") {
      jsonOutput = true;
    } else if (args[i] === "--host") {
      host = args[++i] ?? host;
    } else {
      positional.push(args[i]);
    }
    i++;
  }

  url = positional[0]?.trim() ?? "";
  if (!url) {
    console.error("Error: URL is required");
    process.exit(1);
  }

  // Allow bare domain like "example.com"
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }

  return { url, maxLinks, noContent, jsonOutput, host };
}

function formatResult(data: FetchResponse, maxLinks: number, noContent: boolean): string {
  const lines: string[] = [];

  lines.push(data.title || "(no title)");

  if (!noContent && data.content) {
    lines.push("");
    lines.push(data.content);
  }

  if (data.links?.length) {
    if (maxLinks > 0) {
      lines.push("");
      lines.push(`Links: ${data.links.length}`);
      const shown = data.links.slice(0, maxLinks);
      for (const link of shown) {
        lines.push(`  - ${link}`);
      }
      if (data.links.length > maxLinks) {
        lines.push(`  ... and ${data.links.length - maxLinks} more`);
      }
    } else {
      lines.push("");
      lines.push(`Links: ${data.links.length}`);
    }
  }

  return lines.join("\n");
}

async function main(): Promise<void> {
  const { url, maxLinks, noContent, jsonOutput, host } = parseArgs(process.argv);
  const api = `${host}/api/experimental/web_fetch`;

  let response: Response;
  try {
    response = await fetch(api, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`Error: Cannot connect to Ollama at ${host}\n${msg}`);
    console.error("Make sure Ollama is running: ollama serve");
    process.exit(1);
  }

  if (!response.ok) {
    if (response.status === 401) {
      console.error("Error: Unauthorized. Run: ollama signin");
    } else {
      const text = await response.text().catch(() => response.statusText);
      console.error(`Error: Fetch API returned ${response.status}: ${text}`);
    }
    process.exit(1);
  }

  const data: FetchResponse = await response.json();

  if (jsonOutput) {
    console.log(JSON.stringify(data, null, 2));
  } else {
    console.log(formatResult(data, maxLinks, noContent));
  }
}

main();