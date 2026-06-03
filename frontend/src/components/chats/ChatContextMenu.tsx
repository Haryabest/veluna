"use client";

import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Pin, PinOff, Pencil, Trash2 } from "lucide-react";
import { CHAT_BORDER } from "@/lib/theme";
import { cn } from "@/lib/utils";

const MENU_ICON = "h-5 w-5";
const MENU_ICON_STROKE = 1.75;

export interface ChatMenuAnchor {
  top: number;
  left: number;
  width: number;
}

interface ChatContextMenuProps {
  open: boolean;
  anchor: ChatMenuAnchor | null;
  isPinned: boolean;
  isSystem?: boolean;
  onClose: () => void;
  onPin: () => void;
  onRename: () => void;
  onDelete: () => void;
}

export function ChatContextMenu({
  open,
  anchor,
  isPinned,
  isSystem,
  onClose,
  onPin,
  onRename,
  onDelete,
}: ChatContextMenuProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const menuTop = anchor ? Math.min(anchor.top + 8, window.innerHeight - 200) : 0;
  const menuLeft = anchor
    ? Math.min(Math.max(anchor.left, 12), window.innerWidth - 220)
    : 0;

  return createPortal(
    <AnimatePresence>
      {open && anchor && (
        <>
          <motion.button
            type="button"
            aria-label="Закрыть меню"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[80] bg-black/40"
            onClick={onClose}
          />
          <motion.div
            role="menu"
            initial={{ opacity: 0, scale: 0.92, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: -8 }}
            transition={{ type: "spring", stiffness: 420, damping: 28 }}
            className="fixed z-[85] min-w-[200px] overflow-hidden rounded-2xl bg-bg-elevated/95 py-1 backdrop-blur-xl"
            style={{
              top: menuTop,
              left: menuLeft,
              border: `1px solid ${CHAT_BORDER}`,
            }}
          >
            <MenuItem
              label={isPinned ? "Открепить" : "Закрепить"}
              icon={
                isPinned ? (
                  <PinOff className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />
                ) : (
                  <Pin className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />
                )
              }
              onClick={onPin}
              showBorder
            />
            <MenuItem
              label="Переименовать"
              icon={<Pencil className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onRename}
              disabled={isSystem}
              showBorder
            />
            <MenuItem
              label="Удалить"
              icon={<Trash2 className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onDelete}
              variant="danger"
              disabled={isSystem}
            />
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}

function MenuItem({
  label,
  icon,
  onClick,
  variant = "default",
  disabled,
  showBorder,
}: {
  label: string;
  icon: ReactNode;
  onClick: () => void;
  variant?: "default" | "danger";
  disabled?: boolean;
  showBorder?: boolean;
}) {
  return (
    <motion.button
      type="button"
      role="menuitem"
      disabled={disabled}
      whileTap={disabled ? undefined : { scale: 0.96 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      onClick={() => {
        if (disabled) return;
        onClick();
      }}
      className={cn(
        "flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-medium transition-colors",
        disabled && "cursor-not-allowed opacity-40",
        !disabled && variant === "danger" && "text-red-400 hover:bg-red-500/10",
        !disabled && variant !== "danger" && "text-text-primary hover:bg-bg-elevated/80"
      )}
      style={showBorder ? { borderBottom: `1px solid ${CHAT_BORDER}` } : undefined}
    >
      <span
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl",
          variant === "danger" ? "bg-red-500/15 text-red-400" : "bg-accent/15 text-accent-light"
        )}
      >
        {icon}
      </span>
      {label}
    </motion.button>
  );
}
