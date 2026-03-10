"use client";

import { Client as LangGraphClient } from "@langchain/langgraph-sdk/client";

import { getLangGraphBaseURL } from "../config";

import { sanitizeRunStreamOptions } from "./stream-mode";

function createCompatibleClient(isMock?: boolean): LangGraphClient {
  const client = new LangGraphClient({
    apiUrl: getLangGraphBaseURL(isMock),
  });

  const originalRunStream = client.runs.stream.bind(client.runs);
  client.runs.stream = ((threadId, assistantId, payload) =>
    originalRunStream(
      threadId,
      assistantId,
      sanitizeRunStreamOptions(payload),
    )) as typeof client.runs.stream;

  const originalJoinStream = client.runs.joinStream.bind(client.runs);
  client.runs.joinStream = ((threadId, runId, options) =>
    originalJoinStream(
      threadId,
      runId,
      sanitizeRunStreamOptions(options),
    )) as typeof client.runs.joinStream;

  return client;
}

// Keep separate singletons for mock vs real — prevents the bug where opening
// a case study (?mock=true) first locks the singleton to the mock API and
// breaks all subsequent real-chat sessions in the same browser tab.
let _realClient: LangGraphClient | null = null;
let _mockClient: LangGraphClient | null = null;

export function getAPIClient(isMock?: boolean): LangGraphClient {
  if (isMock) {
    _mockClient ??= createCompatibleClient(true);
    return _mockClient;
  }
  _realClient ??= createCompatibleClient(false);
  return _realClient;
}
