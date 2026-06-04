"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type ModalType = "confirm" | "info" | "custom";

interface ModalState {
  isOpen: boolean;
  type: ModalType;
  title: string;
  content: ReactNode;
  onConfirm?: () => void | Promise<void>;
}

interface ModalContextValue {
  modal: ModalState;
  openModal: (config: Omit<ModalState, "isOpen">) => void;
  closeModal: () => void;
}

const defaultModal: ModalState = {
  isOpen: false,
  type: "info",
  title: "",
  content: null,
};

const ModalContext = createContext<ModalContextValue | null>(null);

export function ModalProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<ModalState>(defaultModal);

  const openModal = useCallback((config: Omit<ModalState, "isOpen">) => {
    setModal({ ...config, isOpen: true });
  }, []);

  const closeModal = useCallback(() => {
    setModal(defaultModal);
  }, []);

  return (
    <ModalContext.Provider value={{ modal, openModal, closeModal }}>
      {children}
    </ModalContext.Provider>
  );
}

export function useModal() {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error("useModal must be used within ModalProvider");
  return ctx;
}
