import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl bg-bg-elevated/80",
        "before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent",
        className
      )}
    />
  );
}

export function CharacterCardSkeleton() {
  return (
    <div className="glass aspect-[3/4] overflow-hidden rounded-2xl">
      <Skeleton className="h-full w-full rounded-none" />
    </div>
  );
}

export function MessageSkeleton() {
  return (
    <div className="mb-3 flex gap-2">
      <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
      <Skeleton className="h-12 flex-1 rounded-2xl" />
    </div>
  );
}

export function ChatRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-3.5">
      <Skeleton className="h-12 w-12 shrink-0 rounded-full" />
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  );
}

export function ScenarioRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-3.5">
      <Skeleton className="h-14 w-[4.5rem] shrink-0 rounded-xl" />
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
    </div>
  );
}

export function HistoryRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <Skeleton className="h-10 w-10 shrink-0 rounded-full" />
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-3/5" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-4 w-10 shrink-0" />
    </div>
  );
}
