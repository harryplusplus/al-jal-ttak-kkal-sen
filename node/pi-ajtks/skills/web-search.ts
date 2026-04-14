/**
 * web-search — Search the web via Ollama's local experimental API.
 *
 * Usage:
 *   node web-search.ts "search query"
 *   node web-search.ts "search query" --max-results 3
 *   node web-search.ts "search query" --max-results 5 --json
 *
 * Options:
 *   --max-results <n>   Maximum number of results (1-10, default: 5)
 *   --json              Output raw JSON instead of formatted text
 *   --host <url>        Ollama host (default: http://localhost:11434)
 *
 * Environment:
 *   OLLAMA_HOST          Override default Ollama host URL
 *
 * Requires:
 *   - Ollama running locally with web search enabled
 *   - Node.js 24+ (uses fetch, --experimental-strip-types)
 */

interface SearchResult {
  title: string;
  url: string;
  content: string;
}

interface SearchResponse {
  results: SearchResult[];
}

function parseArgs(argv: string[]): {
  query: string;
  maxResults: number;
  jsonOutput: boolean;
  host: string;
} {
  const args = argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.error(`Usage: node web-search.ts "search query" [options]

Options:
  --max-results <n>   Maximum results (1-10, default: 5)
  --json              Output raw JSON
  --host <url>        Ollama host (default: http://localhost:11434)

Environment:
  OLLAMA_HOST          Override default Ollama host URL`);
    process.exit(1);
  }

  let query = "";
  let maxResults = 5;
  let jsonOutput = false;
  let host = process.env.OLLAMA_HOST ?? "http://localhost:11434";

  let i = 0;
  const positional: string[] = [];
  while (i < args.length) {
    if (args[i] === "--max-results" || args[i] === "-n") {
      const n = parseInt(args[++i], 10);
      maxResults = Number.isNaN(n) ? 5 : Math.max(1, Math.min(10, n));
    } else if (args[i] === "--json") {
      jsonOutput = true;
    } else if (args[i] === "--host") {
      host = args[++i] ?? host;
    } else {
      positional.push(args[i]);
    }
    i++;
  }

  query = positional.join(" ").trim();
  if (!query) {
    console.error("Error: search query is required");
    process.exit(1);
  }

  return { query, maxResults, jsonOutput, host };
}

function formatResults(results: SearchResult[]): string {
  if (results.length === 0) {
    return "No results found.";
  }
  return results
    .map((r, i) => `${i + 1}. ${r.title}\n   URL: ${r.url}\n   ${r.content}`)
    .join("\n\n");
}

async function main(): Promise<void> {
  const { query, maxResults, jsonOutput, host } = parseArgs(process.argv);
  const url = `${host}/api/experimental/web_search`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, max_results: maxResults }),
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
      console.error(`Error: Search API returned ${response.status}: ${text}`);
    }
    process.exit(1);
  }

  const data: SearchResponse = await response.json();

  if (jsonOutput) {
    console.log(JSON.stringify(data, null, 2));
  } else {
    console.log(formatResults(data.results));
  }
}

main();