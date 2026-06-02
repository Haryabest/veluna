"use client";

import { useModal } from "@/hooks/use-modal";
import { Button } from "@/components/shared/Button";
import { motion, AnimatePresence } from "framer-motion";

export function GlobalModal() {
  const { modal, closeModal } = useModal();

  return (
    <AnimatePresence>
      {modal.isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[90] bg-black/60"
            onClick={closeModal}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="glass fixed inset-x-4 top-1/2 z-[95] mx-auto max-w-sm -translate-y-1/2 rounded-2xl p-6"
          >
            <h2 className="mb-3 text-lg font-semibold text-text-primary">{modal.title}</h2>
            <div className="mb-6 text-sm text-text-secondary">{modal.content}</div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={closeModal}>
                Отмена
              </Button>
              {modal.onConfirm && (
                <Button
                  onClick={() => {
                    modal.onConfirm?.();
                    closeModal();
                  }}
                >
                  Подтвердить
                </Button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
