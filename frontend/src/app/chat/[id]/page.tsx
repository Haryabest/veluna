"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { chatService } from "@/services/api";
import { useWebSocket } from "@/hooks/use-websocket";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/shared/Button";
import { MessageSkeleton } from "@/components/shared/Skeleton";
import { QUERY_KEYS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const { id: chatId } = useParams<{ id: string }>();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { isTyping, setIsTyping, addMessage } = useChatStore();

  const { data: messages, isLoading } = useQuery({
    queryKey: QUERY_KEYS.messages(chatId),
    queryFn: () => chatService.getMessages(chatId),
    enabled: !!chatId,
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => chatService.sendMessage(chatId, content),
    onSuccess: (msg) => {
      addMessage(chatId, msg);
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
    },
  });

  const { sendTyping, isConnected } = useWebSocket(`/chat/${chatId}`, {
    onMessage: (data) => {
      if (data.type === "typing") setIsTyping(data.is_typing as boolean);
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || sendMutation.isPending) return;
    sendMutation.mutate(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-screen max-w-lg mx-auto">
      <header className="glass px-4 py-3 flex items-center justify-between border-b border-border">
        <h1 className="font-semibold">Chat</h1>
        <span className={cn("text-xs", isConnected ? "text-green-400" : "text-text-muted")}>
          {isConnected ? "● Live" : "○ Offline"}
        </span>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => <MessageSkeleton key={i} />)
          : messages?.map((msg: { id: string; role: string; content: string }) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                  msg.role === "user"
                    ? "ml-auto bg-accent/20 text-text-primary"
                    : "mr-auto glass text-text-secondary"
                )}
              >
                {msg.content}
              </motion.div>
            ))}
        {isTyping && (
          <div className="text-xs text-text-muted animate-pulse">typing...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="glass px-4 py-3 border-t border-border">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              sendTyping(true);
            }}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type a message..."
            className="flex-1 bg-bg-elevated rounded-md px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted outline-none focus:ring-1 focus:ring-accent/50"
          />
          <Button onClick={handleSend} loading={sendMutation.isPending} disabled={!input.trim()}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
