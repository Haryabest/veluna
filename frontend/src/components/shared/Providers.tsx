"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ModalProvider } from "@/hooks/use-modal";
import { ToastProvider } from "@/hooks/use-toast";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { GlobalModal } from "@/components/widgets/GlobalModal";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 2 * 60 * 1000,
            gcTime: 10 * 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
            refetchOnReconnect: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ModalProvider>
          <ErrorBoundary>
            {children}
            <GlobalModal />
          </ErrorBoundary>
        </ModalProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
