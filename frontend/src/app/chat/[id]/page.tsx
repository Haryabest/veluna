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
import { useTranslation } from "@/hooks/use-translation";

export default function ChatPage() {
  const { id: chatId } = useParams<{ id: string }>();
  const { t } = useTranslation();
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
    onSuccess: (data) => {
      addMessage(chatId, {
        ...data.user_message,
        role: data.user_message.role as "user" | "assistant" | "system",
        tokens_used: 0,
        is_regenerated: false,
      });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(chatId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.chat(chatId) });
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
    <div className="mx-auto flex h-screen max-w-lg flex-col">
      <header className="glass flex items-center justify-between border-b border-border px-4 py-3">
        <h1 className="font-semibold">{t("chat.legacy.title")}</h1>
        <span className={cn("text-xs", isConnected ? "text-green-400" : "text-text-muted")}>
          {isConnected ? t("chat.legacy.online") : t("chat.legacy.offline")}
        </span>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => <MessageSkeleton key={i} />)
          : messages?.map((msg: { id: string; role: string; content: string }) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "max-w-[85%] rounded-2xl px-3 py-2 text-sm",
                  msg.role === "user"
                    ? "ml-auto bg-accent/20 text-text-primary"
                    : "mr-auto glass text-text-secondary"
                )}
              >
                {msg.content}
              </motion.div>
            ))}
        {isTyping && (
          <div className="animate-pulse text-xs text-text-muted">{t("chat.legacy.typing")}</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="glass border-t border-border px-4 py-3 pb-24">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              sendTyping(true);
            }}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={t("chat.legacy.placeholder")}
            className="flex-1 rounded-xl bg-bg-elevated px-3 py-2.5 text-sm text-text-primary outline-none placeholder:text-text-muted focus:ring-1 focus:ring-accent/50"
          />
          <Button onClick={handleSend} loading={sendMutation.isPending} disabled={!input.trim()}>
            {t("chat.send")}
          </Button>
        </div>
      </div>
    </div>
  );
}
