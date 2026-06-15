"use client";

import { ChevronLeft } from "lucide-react";
import { useTranslation } from "@/hooks/use-translation";
import { cn } from "@/lib/utils";

interface BackButtonProps {
  onClick: () => void;
  className?: string;
  iconClassName?: string;
}

export function BackButton({ onClick, className, iconClassName }: BackButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={t("common.back")}
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-text-primary transition-transform active:scale-90",
        className
      )}
    >
      <ChevronLeft className={cn("h-5 w-5", iconClassName)} strokeWidth={2.2} aria-hidden />
    </button>
  );
}
