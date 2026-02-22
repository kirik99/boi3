import { useEffect, useState, useRef } from "react";
import { useRoute, useLocation } from "wouter";
import { Menu, Bot } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import {
  useConversations,
  useConversation,
  useCreateConversation,
  useDeleteConversation,
  useChatStream
} from "@/hooks/use-chat";

export default function ChatPage() {
  const [match, params] = useRoute("/chat/:id");
  const conversationId = match && params?.id ? parseInt(params.id) : null;
  const [location, setLocation] = useLocation();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Queries & Mutations
  const { data: conversations = [], isLoading: isLoadingConvs } = useConversations();
  const { data: conversationData, isLoading: isLoadingMessages } = useConversation(conversationId);
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();
  const { sendMessage, isStreaming, streamedContent } = useChatStream(conversationId);

  // Auto-scroll to bottom
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [conversationData?.messages, streamedContent]);

  const handleCreateChat = () => {
    createConversation.mutate("New Chat", {
      onSuccess: (newConv) => {
        setLocation(`/chat/${newConv.id}`);
      }
    });
  };

  const handleDeleteChat = (id: number) => {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (conversationId === id) {
          setLocation("/");
        }
      }
    });
  };

  const [pendingMessage, setPendingMessage] = useState<{ content: string, imageUrl?: string } | null>(null);

  // Auto-send pending message when chat ID becomes available
  useEffect(() => {
    if (conversationId && pendingMessage) {
      sendMessage(pendingMessage.content, pendingMessage.imageUrl);
      setPendingMessage(null);
    }
  }, [conversationId, pendingMessage, sendMessage]);

  const handleSend = (content: string, imageUrl?: string) => {
    if (conversationId) {
      sendMessage(content, imageUrl);
    } else {
      // Create chat first if sending from home
      setPendingMessage({ content, imageUrl });
      createConversation.mutate(content.slice(0, 30) + "...", {
        onSuccess: (newConv) => {
          setLocation(`/chat/${newConv.id}`);
        }
      });
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground font-sans">
      <Sidebar
        conversations={conversations}
        activeId={conversationId}
        onCreate={handleCreateChat}
        onDelete={handleDeleteChat}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      <main className="flex-1 flex flex-col relative w-full h-full min-w-0">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center p-4 border-b border-white/5 bg-background/80 backdrop-blur-md z-10 sticky top-0">
          <button
            onClick={() => setIsMobileOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-white/10 text-muted-foreground"
          >
            <Menu className="w-6 h-6" />
          </button>
          <span className="ml-3 font-semibold text-lg truncate">
            {conversationData?.title || "Nexus AI"}
          </span>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto scrollbar-hide">
          {!conversationId ? (
            // Empty State / Home
            <div className="h-full flex flex-col items-center justify-center p-8 text-center animate-in-up">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-2xl shadow-primary/30 mb-8">
                <Bot className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                How can I help you today?
              </h2>
              <p className="text-xl text-muted-foreground max-w-lg mb-10">
                I'm Nexus, your advanced AI assistant. I can help you with coding, writing, analysis, and more.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full">
                {["Explain quantum computing", "Write a Python script", "Draft a professional email", "Analyze this data"].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-primary/30 transition-all text-left group"
                  >
                    <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                      {prompt}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Messages List
            <div className="flex flex-col gap-6 p-4 md:p-8 pb-32 min-h-full">
              {isLoadingMessages ? (
                <div className="flex items-center justify-center h-full">
                  <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <>
                  {conversationData?.messages.map((msg) => (
                    <ChatMessage
                      key={msg.id}
                      role={msg.role as "user" | "assistant"}
                      content={msg.content}
                      imageUrl={msg.imageUrl}
                    />
                  ))}

                  {isStreaming && (
                    <ChatMessage
                      role="assistant"
                      content={streamedContent}
                      isStreaming={true}
                    />
                  )}

                  <div ref={scrollRef} className="h-px" />
                </>
              )}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background/95 to-transparent pb-6 pt-10 px-4">
          <ChatInput onSend={handleSend} isLoading={isStreaming} />
        </div>
      </main>
    </div>
  );
}
