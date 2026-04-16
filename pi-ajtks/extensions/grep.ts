import type { ExtensionAPI } from '@mariozechner/pi-coding-agent'

export default async function (pi: ExtensionAPI) {
  const result = await pi.exec('which', ['rg'])
  if (result.code !== 0) {
    throw new Error(
      'rg (ripgrep) is required but not found. Install: https://github.com/BurntSushi/ripgrep',
    )
  }

  pi.on('session_start', () => {
    pi.setActiveTools([...pi.getActiveTools(), 'grep'])
  })

  pi.on('before_agent_start', async (event) => {
    return {
      systemPrompt:
        event.systemPrompt +
        `

<grep-preference>
The "grep" tool wraps ripgrep (rg) with output safeguards: head-based truncation (first 100 matches kept), per-line 500-char truncation, and 50KB limit. Running rg via bash uses tail-based truncation (last 2000 lines), which can lose the most relevant early matches in large results.

Always prefer the "grep" tool for file content search. Only use bash for rg when you need pipes (e.g., rg | wc -l) or multi-step command chains.
</grep-preference>`,
    }
  })
}
