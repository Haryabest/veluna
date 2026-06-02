import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-bg-elevated",
        className
      )}
    />
  );
}

export function CharacterCardSkeleton() {
  return (
    <div className="glass rounded-lg overflow-hidden">
      <Skeleton className="aspect-[3/4] w-full rounded-none" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-full" />
      </div>
    </div>
  );
}

export function MessageSkeleton() {
  return (
    <div className="flex gap-2 mb-3">
      <Skeleton className="h-8 w-8 rounded-full shrink-0" />
      <Skeleton className="h-12 flex-1 rounded-lg" />
    </div>
  );
}
