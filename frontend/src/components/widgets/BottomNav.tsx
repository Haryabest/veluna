"use client";

import { motion } from "framer-motion";
import { Home, MessageCircle, Palette, User, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMounted } from "@/hooks/use-mounted";
import { useSetTab } from "@/hooks/use-catalog-navigation";
import { useNavStore, type AppTab } from "@/store/nav-store";
import { useTranslation } from "@/hooks/use-translation";
import type { TranslationKey } from "@/lib/i18n/translations";

const navItems: { tab: AppTab; labelKey: TranslationKey; Icon: LucideIcon }[] = [
  { tab: "home", labelKey: "nav.home", Icon: Home },
  { tab: "chats", labelKey: "nav.chats", Icon: MessageCircle },
  { tab: "studio", labelKey: "nav.studio", Icon: Palette },
  { tab: "profile", labelKey: "nav.profile", Icon: User },
];

export function BottomNav() {
  const mounted = useMounted();
  const tab = useNavStore((s) => s.tab);
  const setTab = useSetTab();
  const { t } = useTranslation();

  return (
    <nav className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex justify-center px-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <div className="glass-strong pointer-events-auto flex w-full max-w-lg items-end justify-around rounded-3xl px-2 py-2.5 shadow-glow">
        {navItems.map(({ tab: itemTab, labelKey, Icon }) => {
          const isActive = tab === itemTab;
          const label = t(labelKey);

          return (
            <button
              key={itemTab}
              type="button"
              onClick={() => setTab(itemTab)}
              aria-label={label}
              aria-current={isActive ? "page" : undefined}
              className="relative flex min-w-[56px] flex-col items-center justify-end gap-0.5 transition-all"
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
                  "flex h-11 w-11 items-center justify-center rounded-2xl transition-shadow duration-300",
                  isActive && "bg-accent/15 shadow-[0_0_20px_rgba(160,32,240,0.55)]"
                )}
              >
                <Icon
                  className={cn(
                    "h-6 w-6 transition-all duration-300",
                    isActive
                      ? "text-accent-light drop-shadow-[0_0_8px_rgba(199,125,255,0.9)]"
                      : "text-text-muted"
                  )}
                  strokeWidth={isActive ? 2.25 : 1.75}
                  aria-hidden
                />
              </motion.div>

              <span
                className={cn(
                  "text-[10px] font-medium leading-none",
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
