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
            className="fixed inset-0 bg-black/60 z-[90]"
            onClick={closeModal}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-x-4 top-1/2 -translate-y-1/2 z-[95] glass rounded-xl p-6 max-w-sm mx-auto"
          >
            <h2 className="text-lg font-semibold text-text-primary mb-3">{modal.title}</h2>
            <div className="text-text-secondary text-sm mb-6">{modal.content}</div>
            <div className="flex gap-3 justify-end">
              <Button variant="ghost" onClick={closeModal}>
                Cancel
              </Button>
              {modal.onConfirm && (
                <Button
                  onClick={() => {
                    modal.onConfirm?.();
                    closeModal();
                  }}
                >
                  Confirm
                </Button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
