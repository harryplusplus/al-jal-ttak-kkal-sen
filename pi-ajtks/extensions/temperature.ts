import type { ExtensionAPI } from '@mariozechner/pi-coding-agent'

export default function (pi: ExtensionAPI) {
  pi.on('before_provider_request', (event) => {
    const { payload } = event as { payload: { temperature?: number } }
    payload.temperature = 0
  })
}
