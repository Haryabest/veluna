"use client";

import { canPayWithTelegramStars, getTelegramWebApp } from "@/lib/telegram-webapp";

export type InvoiceStatus = "paid" | "cancelled" | "failed" | "pending";

export function openTelegramInvoice(invoiceUrl: string): Promise<InvoiceStatus> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve("failed");
      return;
    }

    if (!canPayWithTelegramStars()) {
      resolve("failed");
      return;
    }

    const tg = getTelegramWebApp();
    tg!.openInvoice!(invoiceUrl, (status) => {
      resolve((status as InvoiceStatus) ?? "failed");
    });
  });
}