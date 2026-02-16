import { Bot, User, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { motion } from "framer-motion";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  imageUrl?: string | null;
  isStreaming?: boolean;
}

export function ChatMessage({ role, content, imageUrl, isStreaming }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isBot = role === "assistant";

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={cn(
        "group flex gap-4 md:gap-6 mx-auto w-full max-w-3xl p-4 md:p-6 rounded-2xl transition-colors",
        isBot ? "bg-white/5 hover:bg-white/[0.07] border border-white/5" : "bg-transparent"
      )}
    >
      <div className={cn(
        "flex-shrink-0 w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center shadow-lg",
        isBot 
          ? "bg-gradient-to-br from-primary to-purple-600 text-white shadow-primary/20" 
          : "bg-gradient-to-br from-slate-700 to-slate-600 text-slate-200"
      )}>
        {isBot ? <Bot className="w-5 h-5 md:w-6 md:h-6" /> : <User className="w-5 h-5 md:w-6 md:h-6" />}
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80">
            {isBot ? "Nexus AI" : "You"}
          </span>
          
          {isBot && (
            <button
              onClick={handleCopy}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-white/10 text-muted-foreground hover:text-white"
              title="Copy to clipboard"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
        </div>

        <div className={cn(
          "prose prose-invert prose-p:leading-relaxed prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 max-w-none break-words",
          isBot ? "text-slate-200" : "text-white text-lg font-medium leading-relaxed"
        )}>
          {imageUrl && (
            <img 
              src={imageUrl} 
              alt="Uploaded content" 
              className="rounded-lg max-h-60 mb-4 border border-white/10 object-contain bg-black/20"
            />
          )}
          {isStreaming ? (
            <div>
              {content}
              <span className="inline-block w-2 h-4 ml-1 align-middle bg-primary animate-pulse" />
            </div>
          ) : (
            <ReactMarkdown>{content}</ReactMarkdown>
          )}
        </div>
      </div>
    </motion.div>
  );
}
