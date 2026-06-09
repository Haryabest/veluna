"use client";

/** Day badge between message groups — like Telegram */
export function ChatDaySeparator({ label }: { label: string }) {
  return (
    <div className="my-3 flex w-full justify-center">
      <span className="inline-flex items-center rounded-full bg-black/55 px-3 py-1 text-[13px] font-semibold leading-none text-white shadow-[0_2px_8px_rgba(0,0,0,0.45)] ring-1 ring-white/15 backdrop-blur-sm">
        {label}
      </span>
    </div>
  );
}
