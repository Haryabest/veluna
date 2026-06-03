"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useMounted } from "@/hooks/use-mounted";
import { useNavStore, type AppTab } from "@/store/nav-store";

const navItems: { tab: AppTab; label: string; Icon: React.FC<IconProps> }[] = [
  { tab: "home", label: "Главная", Icon: HomeIcon },
  { tab: "chats", label: "Чаты", Icon: ChatsIcon },
  { tab: "studio", label: "Студия", Icon: StudioIcon },
  { tab: "profile", label: "Профиль", Icon: UserIcon },
];

export function BottomNav() {
  const mounted = useMounted();
  const tab = useNavStore((s) => s.tab);
  const setTab = useNavStore((s) => s.setTab);

  return (
    <nav className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex justify-center px-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <div className="glass-strong pointer-events-auto flex w-full max-w-lg items-end justify-around rounded-3xl px-2 py-2.5 shadow-glow">
        {navItems.map(({ tab: itemTab, label, Icon }) => {
          const isActive = tab === itemTab;
          const isCenter = itemTab === "chats";

          return (
            <button
              key={itemTab}
              type="button"
              onClick={() => setTab(itemTab)}
              aria-label={label}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "relative flex flex-col items-center justify-end gap-0.5 transition-all",
                isCenter ? "min-w-[72px] -mt-3" : "min-w-[56px]"
              )}
            >
              {isActive && mounted && (
                <motion.div
                  layoutId="nav-indicator"
                  className="-top-0.5 absolute h-0.5 w-6 rounded-full bg-gradient-to-r from-accent-light via-accent to-accent-deep"
                  style={{ boxShadow: "0 0 12px rgba(199,125,255,0.8)" }}
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
              {isActive && !mounted && (
                <div
                  className="-top-0.5 absolute h-0.5 w-6 rounded-full bg-gradient-to-r from-accent-light via-accent to-accent-deep"
                  style={{ boxShadow: "0 0 12px rgba(199,125,255,0.8)" }}
                />
              )}

              <motion.div
                animate={isActive ? { scale: 1.05, y: -1 } : { scale: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className={cn(
                  "flex items-center justify-center rounded-2xl transition-shadow duration-300",
                  isCenter ? "h-[52px] w-[52px]" : "h-11 w-11",
                  isActive && "shadow-[0_0_20px_rgba(160,32,240,0.55)]"
                )}
              >
                <Icon
                  className={cn(
                    "transition-all duration-300",
                    isCenter ? "h-7 w-7" : "h-6 w-6",
                    isActive
                      ? "text-accent-light drop-shadow-[0_0_8px_rgba(199,125,255,0.9)]"
                      : "text-text-muted"
                  )}
                  filled={isActive}
                />
              </motion.div>

              <span
                className={cn(
                  "font-medium leading-none",
                  isCenter ? "text-[11px]" : "text-[10px]",
                  isActive ? "text-accent-light" : "text-text-muted"
                )}
              >
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

type IconProps = { className?: string; filled?: boolean };

function HomeIcon({ className, filled }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} aria-hidden>
      <path
        d="M4 10.5L12 4l8 6.5V19a1.5 1.5 0 01-1.5 1.5H15v-5.5H9V20.5H5.5A1.5 1.5 0 014 19v-8.5z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChatsIcon({ className, filled }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} aria-hidden>
      <path
        d="M8 10h8M8 14h5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M5 5h14a2 2 0 012 2v8a2 2 0 01-2 2H9l-4 3V7a2 2 0 012-2z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StudioIcon({ className, filled }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} aria-hidden>
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M12 8v4l2.5 2.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M8 4l1 2M16 4l-1 2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function UserIcon({ className, filled }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} aria-hidden>
      <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
