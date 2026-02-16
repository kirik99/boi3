import { useState, useRef, useEffect } from "react";
import { Send, Image as ImageIcon, X, Mic } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (content: string, imageUrl?: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadFile = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("image", file);
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("Upload failed");
    const data = await res.json();
    return data.url;
  };

  const handleSubmit = async () => {
    if ((!input.trim() && !selectedFile) || isLoading) return;
    
    let imageUrl: string | undefined;
    if (selectedFile) {
      try {
        imageUrl = await uploadFile(selectedFile);
      } catch (error) {
        console.error("Upload error:", error);
        // Should show toast error here
        return;
      }
    }

    onSend(input, imageUrl);
    setInput("");
    removeFile();
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative max-w-3xl mx-auto p-4">
      <div className="relative group rounded-2xl bg-secondary/5 border border-white/10 focus-within:border-primary/50 focus-within:bg-secondary/10 transition-all duration-300 shadow-xl shadow-black/20">
        
        {previewUrl && (
          <div className="p-4 pb-0">
            <div className="relative inline-block">
              <img src={previewUrl} alt="Preview" className="h-20 w-auto rounded-lg object-cover border border-white/10" />
              <button 
                onClick={removeFile}
                className="absolute -top-2 -right-2 bg-destructive text-white rounded-full p-1 hover:bg-destructive/90 shadow-md"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          rows={1}
          className="w-full px-4 py-4 md:py-5 bg-transparent border-0 focus:ring-0 resize-none text-base md:text-lg placeholder:text-muted-foreground/50 text-white max-h-[200px] scrollbar-hide"
          style={{ minHeight: "60px" }}
        />

        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept="image/*" 
          onChange={handleFileChange} 
        />

        <div className="flex items-center justify-between px-3 pb-3">
          <div className="flex items-center gap-1">
            <button 
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "p-2 rounded-xl text-muted-foreground hover:text-white hover:bg-white/10 transition-colors",
                selectedFile && "text-primary bg-primary/10"
              )}
              title="Upload image"
            >
              <ImageIcon className="w-5 h-5" />
            </button>
            <button 
              className="p-2 rounded-xl text-muted-foreground hover:text-white hover:bg-white/10 transition-colors"
              title="Voice input (coming soon)"
            >
              <Mic className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className={cn(
              "p-2.5 rounded-xl transition-all duration-200 flex items-center justify-center",
              input.trim() && !isLoading
                ? "bg-primary text-white shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-105 active:scale-95"
                : "bg-white/5 text-muted-foreground cursor-not-allowed"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      <div className="text-center mt-3">
        <p className="text-[10px] md:text-xs text-muted-foreground/40 font-medium">
          Nexus AI can make mistakes. Consider checking important information.
        </p>
      </div>
    </div>
  );
}
