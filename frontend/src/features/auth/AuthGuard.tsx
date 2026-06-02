"use client";

import { useTelegramAuth } from "@/hooks/use-telegram-auth";
import { Skeleton } from "@/components/shared/Skeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isLoading } = useTelegramAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6">
        <div className="text-4xl animate-pulse-glow">🌙</div>
        <Skeleton className="h-4 w-32" />
        <p className="text-text-muted text-sm">Loading Veluna...</p>
      </div>
    );
  }

  return <>{children}</>;
}
