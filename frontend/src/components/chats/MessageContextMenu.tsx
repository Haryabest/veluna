"use client";

import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Reply, Trash2, UserX, Users } from "lucide-react";
import { CHAT_BORDER } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";

const MENU_ICON = "h-5 w-5";
const MENU_ICON_STROKE = 1.75;

export interface MessageMenuAnchor {
  top: number;
  left: number;
}

interface MessageContextMenuProps {
  open: boolean;
  anchor: MessageMenuAnchor | null;
  canDelete?: boolean;
  onClose: () => void;
  onCopy: () => void;
  onReply: () => void;
  onDeleteSelf: () => void;
  onDeleteAll: () => void;
}

export function MessageContextMenu({
  open,
  anchor,
  canDelete = true,
  onClose,
  onCopy,
  onReply,
  onDeleteSelf,
  onDeleteAll,
}: MessageContextMenuProps) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  const menuTop = anchor ? Math.min(anchor.top, window.innerHeight - 280) : 0;
  const menuLeft = anchor ? Math.min(Math.max(anchor.left - 100, 12), window.innerWidth - 220) : 0;

  return createPortal(
    <AnimatePresence>
      {open && anchor && (
        <>
          <motion.button
            type="button"
            aria-label={t("common.closeMenu")}
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
            className="fixed z-[85] min-w-[210px] overflow-hidden rounded-2xl bg-bg-elevated/95 py-1 backdrop-blur-xl"
            style={{
              top: menuTop,
              left: menuLeft,
              border: `1px solid ${CHAT_BORDER}`,
            }}
          >
            <MenuItem
              label={t("chat.copy")}
              icon={<Copy className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onCopy}
              showBorder
            />
            <MenuItem
              label={t("chat.replyAction")}
              icon={<Reply className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onReply}
              showBorder
            />
            <MenuItem
              label={t("chat.deleteForMe")}
              icon={<UserX className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onDeleteSelf}
              disabled={!canDelete}
              showBorder
            />
            <MenuItem
              label={t("chat.deleteForAll")}
              icon={<Users className={MENU_ICON} strokeWidth={MENU_ICON_STROKE} />}
              onClick={onDeleteAll}
              variant="danger"
              disabled={!canDelete}
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
