"use client";

import { chatSeparatorStyle } from "@/lib/theme";
import { cn } from "@/lib/utils";

interface SeparatorProps {
  className?: string;
}

/** Горизонтальный разделитель как в списке чатов */
export function Separator({ className }: SeparatorProps) {
  return <div role="separator" className={cn("w-full", className)} style={chatSeparatorStyle} />;
}
