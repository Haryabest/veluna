"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";

const navItems = [
  { href: ROUTES.home, label: "Home", icon: "🏠" },
  { href: ROUTES.generate, label: "Generate", icon: "✨" },
  { href: ROUTES.shop, label: "Shop", icon: "💎" },
  { href: ROUTES.profile, label: "Profile", icon: "👤" },
];

export function BottomNav() {
  const pathname = usePathname();

  if (pathname.startsWith("/chat") || pathname.startsWith("/admin")) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 glass border-t border-border safe-area-bottom">
      <div className="flex items-center justify-around py-2 px-4 max-w-lg mx-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-0.5 py-1 px-3 rounded-md transition-colors",
                isActive ? "text-accent" : "text-text-muted hover:text-text-secondary"
              )}
            >
              <motion.span
                animate={isActive ? { scale: 1.1 } : { scale: 1 }}
                className="text-lg"
              >
                {item.icon}
              </motion.span>
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
