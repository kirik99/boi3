import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Conversation, Message } from "@shared/schema";

// Using the routes provided by the Replit AI integration
const API_BASE = "/api";

export function useConversations() {
  return useQuery<Conversation[]>({
    queryKey: [`${API_BASE}/conversations`],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/conversations`);
      if (!res.ok) throw new Error("Failed to fetch conversations");
      return res.json();
    },
  });
}

export function useConversation(id: number | null) {
  return useQuery<Conversation & { messages: Message[] }>({
    queryKey: [`${API_BASE}/conversations`, id],
    enabled: !!id,
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/conversations/${id}`);
      if (!res.ok) throw new Error("Failed to fetch conversation");
      return res.json();
    },
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (title: string) => {
      const res = await fetch(`${API_BASE}/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (!res.ok) throw new Error("Failed to create conversation");
      return res.json() as Promise<Conversation>;
    },
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: [`${API_BASE}/conversations`] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${API_BASE}/conversations/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete conversation");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [`${API_BASE}/conversations`] });
    },
  });
}

// NOTE: Sending messages uses SSE (Server-Sent Events) for streaming responses.
// This is handled directly in the component to manage the stream state,
// but we can provide a mutation for non-streaming updates if needed.
// For this app, we'll implement a custom hook for the streaming interaction.

import { useState, useCallback, useRef } from "react";

export function useChatStream(conversationId: number | null) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState("");
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string, imageUrl?: string) => {
    if (!conversationId) return;

    setIsStreaming(true);
    setStreamedContent("");

    // Optimistically update UI could happen here, but we'll rely on the parent component
    // to show the user's message immediately.

    abortControllerRef.current = new AbortController();

    try {
      const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, imageUrl }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) throw new Error("Failed to send message");

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let accumulatedResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                accumulatedResponse += data.content;
                setStreamedContent((prev) => prev + data.content);
              }
              if (data.done) {
                // Stream finished
              }
              if (data.error) {
                console.error("Stream error:", data.error);
              }
            } catch (e) {
              // Ignore parse errors for incomplete lines
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error("Chat stream error:", error);
      }
    } finally {
      setIsStreaming(false);
      setStreamedContent("");
      // Invalidate query to fetch the full saved message from DB
      queryClient.invalidateQueries({
        queryKey: [`${API_BASE}/conversations`, conversationId]
      });
    }
  }, [conversationId, queryClient]);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  return { sendMessage, isStreaming, streamedContent, stopStream };
}
