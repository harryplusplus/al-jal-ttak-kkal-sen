import type { Plugin } from "@opencode-ai/plugin";
import { HindsightClient } from "@vectorize-io/hindsight-client";

export const AjtksPlugin: Plugin = async ({ client: opencode }, options) => {
  const fetchMessageText = async (sessionId: SessionId, messageId: string) => {
    const message = await opencode.session.message({
      path: { id: sessionId, messageID: messageId },
    });
    if (message.error) return null;
    const part = message.data.parts.at(0);
    if (!part) return null;
    if (part.type !== "text") return null;
    return part.text;
  };

  const {
    enabled,
    autoRetain,
    bankId,
    baseUrl,
    apiKey,
    autoRecall,
    agentAllowList,
  } = fillOptions(options);
  const sessionCache = new SessionCache();
  const hindsight = enabled ? new HindsightClient({ baseUrl, apiKey }) : null;

  return {
    event: async ({ event }) => {
      if (event.type === "message.updated") {
        const { info: message } = event.properties;
        if (message.role !== "assistant") return;

        const sessionId = message.sessionID;
        sessionCache.setAssistantMessageId(sessionId, message.id);
        sessionCache.setUserMessageId(sessionId, message.parentID);
      } else if (event.type === "session.idle") {
        const sessionId = event.properties.sessionID;
        const userMessageId = sessionCache.takeUserMessageId(sessionId);
        const assistantMessageId =
          sessionCache.takeAssistantMessageId(sessionId);

        if (!enabled) return;
        if (!autoRetain) return;
        if (!userMessageId) return;
        if (!assistantMessageId) return;

        const userText = await fetchMessageText(sessionId, userMessageId);
        if (!userText) return;

        const assistantText = await fetchMessageText(
          sessionId,
          assistantMessageId,
        );
        if (!assistantText) return;

        // TODO: Wrap with tag.
        const content = `${userText}\n\n${assistantText}`;

        // TODO: Add retain options.
        await hindsight?.retain(bankId, content, {
          timestamp: new Date(),
          documentId: sessionId,
          async: true,
          updateMode: "append",
          metadata: {
            harness: "opencode",
            sessionId,
            userMessageId,
            assistantMessageId,
          },
        });
      } else if (event.type === "session.deleted") {
        if (!enabled) return;

        const sessionId = event.properties.info.id;
        sessionCache.delete(sessionId);
      }
    },
    "chat.params": async (input) => {
      if (!enabled) return;

      const sessionId = input.sessionID;
      sessionCache.setUserMessageId(sessionId, input.message.id);
      sessionCache.setAgent(sessionId, input.agent);
    },
    "experimental.chat.system.transform": async (input, output) => {
      const sessionId = input.sessionID;
      if (!sessionId) return;

      const userMessageId = sessionCache.takeUserMessageId(sessionId);
      const agent = sessionCache.takeAgent(sessionId);

      if (!enabled) return;
      if (!autoRecall) return;
      if (!userMessageId) return;
      if (!agent) return;
      if (!agentAllowList.includes(agent)) return;

      const userText = await fetchMessageText(sessionId, userMessageId);
      if (!userText) return;

      // TODO: Add recall options.
      const res = await hindsight?.recall(bankId, userText);
      const text = res?.results.at(0)?.text;
      if (!text) return;

      // TODO: Wrap with tag.
      output.system.push(text);
    },
  };
};

function fillOptions(options?: Record<string, unknown>): FilledOptions {
  const defaultOptions: FilledOptions = {
    enabled: true,
    baseUrl: "http://localhost:8888",
    bankId: "openclaw",
    apiKey: undefined,
    autoRecall: true,
    autoRetain: true,
    agentAllowList: ["build"],
  };
  return { ...defaultOptions, ...options };
}

type FilledOptions = {
  enabled: boolean;
  baseUrl: string;
  apiKey: string | undefined;
  bankId: string;
  agentAllowList: string[];
  autoRecall: boolean;
  autoRetain: boolean;
};

type SessionId = string;
type SessionData = {
  assistantMessageId: string | null;
  userMessageId: string | null;
  agent: string | null;
};

class SessionCache {
  private map = new Map<SessionId, SessionData>();

  setAssistantMessageId(sessionId: SessionId, assistantMessageId: string) {
    this.setData(sessionId).assistantMessageId = assistantMessageId;
  }

  takeAssistantMessageId(sessionId: SessionId): string | null {
    const data = this.map.get(sessionId);
    if (!data) return null;

    const assistantMessageId = data.assistantMessageId;
    data.assistantMessageId = null;
    return assistantMessageId;
  }

  setUserMessageId(sessionId: SessionId, userMessageId: string) {
    this.setData(sessionId).userMessageId = userMessageId;
  }

  takeUserMessageId(sessionId: SessionId): string | null {
    const data = this.map.get(sessionId);
    if (!data) return null;

    const userMessageId = data.userMessageId;
    data.userMessageId = null;
    return userMessageId;
  }

  setAgent(sessionId: SessionId, agent: string) {
    this.setData(sessionId).agent = agent;
  }

  takeAgent(sessionId: SessionId): string | null {
    const data = this.map.get(sessionId);
    if (!data) return null;

    const agent = data.agent;
    data.agent = null;
    return agent;
  }

  delete(sessionId: SessionId) {
    this.map.delete(sessionId);
  }

  private setData(sessionId: SessionId): SessionData {
    if (!this.map.has(sessionId)) {
      this.map.set(sessionId, {
        assistantMessageId: null,
        userMessageId: null,
        agent: null,
      });
    }

    return this.map.get(sessionId)!;
  }
}
