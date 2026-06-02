import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-2xl bg-bg-elevated/80", className)} />
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
