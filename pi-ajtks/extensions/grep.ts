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
}
