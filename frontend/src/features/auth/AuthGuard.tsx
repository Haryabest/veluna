"use client";

import { useTelegramAuth } from "@/hooks/use-telegram-auth";
import { Skeleton } from "@/components/shared/Skeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isLoading } = useTelegramAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
        <div className="flex h-14 w-14 items-center justify-center rounded-full glass-strong shadow-glow-sm">
          <span className="text-2xl text-gradient font-bold">V</span>
        </div>
        <Skeleton className="h-3 w-28" />
        <p className="text-sm text-text-muted">Загрузка Veluna...</p>
      </div>
    );
  }

  return <>{children}</>;
}
