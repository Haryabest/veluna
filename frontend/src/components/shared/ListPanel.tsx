"use client";

import { chatBorderStyle } from "@/lib/theme";
import { cn } from "@/lib/utils";
import type { HTMLAttributes, ReactNode } from "react";

interface ListPanelProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

/** Прямоугольный блок-список с тёмной обводкой (как чаты) */
export function ListPanel({ children, className, ...props }: ListPanelProps) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl bg-bg-elevated/40 backdrop-blur-md",
        className
      )}
      style={chatBorderStyle}
      {...props}
    >
      {children}
    </div>
  );
}
