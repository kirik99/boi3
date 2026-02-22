import { Link, useLocation } from "wouter";
import { Plus, MessageSquare, Trash2, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Conversation } from "@shared/schema";

interface SidebarProps {
  conversations: Conversation[];
  activeId: number | null;
  onCreate: () => void;
  onDelete: (id: number) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

export function Sidebar({
  conversations,
  activeId,
  onCreate,
  onDelete,
  isMobileOpen,
  setIsMobileOpen
}: SidebarProps) {
  const [location] = useLocation();

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Content */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-72 bg-card/95 backdrop-blur-xl border-r border-white/5 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static",
        isMobileOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-white/5">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
                Nexus AI
              </h1>
            </div>

            <button
              onClick={() => {
                onCreate();
                setIsMobileOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary hover:bg-primary/90 text-white font-medium transition-all duration-200 shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5 active:translate-y-0"
            >
              <Plus className="w-5 h-5" />
              New Chat
            </button>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
            {conversations.length === 0 ? (
              <div className="text-center py-10 px-4">
                <p className="text-muted-foreground text-sm">No conversations yet.</p>
                <p className="text-muted-foreground/60 text-xs mt-1">Start a new chat to begin.</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={cn(
                    "group relative flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 border border-transparent",
                    activeId === conv.id
                      ? "bg-white/10 border-white/10 text-white shadow-lg shadow-black/20"
                      : "text-muted-foreground hover:bg-white/5 hover:text-white"
                  )}
                  onClick={() => {
                    // Navigate handled by parent usually, but we can do it here too if passed nav function
                    // For now assuming parent handles selection via prop, or we use Link
                    window.location.hash = `/chat/${conv.id}`; // Hacky nav for wouter hash routing if used, but usually <Link> is better.
                    // Actually, let's use the Link component to be safe with wouter
                  }}
                >
                  <Link
                    href={`/chat/${conv.id}`}
                    className="absolute inset-0 z-0"
                    onClick={() => setIsMobileOpen(false)}
                  />

                  <MessageSquare className={cn(
                    "w-4 h-4 z-10",
                    activeId === conv.id ? "text-secondary" : "text-muted-foreground group-hover:text-secondary/70"
                  )} />

                  <span className="truncate text-sm font-medium flex-1 z-10 relative">
                    {conv.title}
                  </span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      onDelete(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-destructive/20 hover:text-destructive transition-all z-20"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-white/5">
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 border border-white/5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <span className="text-xs font-medium text-emerald-500">Systems Online</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
