"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ShopCheckoutSheet } from "@/components/shop/ShopCheckoutSheet";
import { ShopProductCard } from "@/components/shop/ShopProductCard";
import { useToast } from "@/hooks/use-toast";
import { openTelegramInvoice } from "@/hooks/use-telegram-payment";
import { getApiError } from "@/lib/api-client";
import { canPayWithTelegramStars } from "@/lib/telegram-webapp";
import { useNavStore } from "@/store/nav-store";
import { useUserStore } from "@/store/user-store";
import { shopService, authService } from "@/services/api";
import {
  MOCK_SHOP_PRODUCTS,
  SHOP_TAB_LABELS,
  type ShopProduct,
  type ShopTab,
} from "@/lib/shop";
import { BackButton } from "@/components/shared/BackButton";
import { CHAT_BORDER } from "@/lib/theme";
import { formatGems } from "@/lib/utils";
import { cn } from "@/lib/utils";

const TABS: ShopTab[] = ["bundle", "gems", "credits"];

export function ShopView() {
  const goBack = useNavStore((s) => s.goBack);
  const { user, setUser } = useUserStore();
  const { toast } = useToast();
  const [tab, setTab] = useState<ShopTab>("bundle");
  const [selected, setSelected] = useState<ShopProduct | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [paying, setPaying] = useState(false);

  const { data: apiProducts, isLoading } = useQuery({
    queryKey: ["shop", "products"],
    queryFn: () => shopService.listProducts(),
    retry: false,
  });

  const products: ShopProduct[] = useMemo(() => {
    const list = (apiProducts?.length ? apiProducts : MOCK_SHOP_PRODUCTS) as ShopProduct[];
    return list.filter((p) => p.is_active !== false);
  }, [apiProducts]);

  const filtered = products.filter((p) => p.product_type === tab);

  const handlePayStars = async (promoCode: string) => {
    if (!selected) return;

    if (!canPayWithTelegramStars()) {
      toast("Откройте магазин через Telegram (кнопка бота)", "info");
      return;
    }

    if (selected.id.startsWith("mock-")) {
      toast("Запустите backend и миграции для реальной оплаты", "info");
      return;
    }

    setPaying(true);
    try {
      const checkout = await shopService.checkout(
        selected.id,
        promoCode || undefined,
        "stars"
      );
      const status = await openTelegramInvoice(checkout.invoice_url);

      if (status === "paid") {
        toast("Оплата прошла! Гемы зачислены 💎", "success");
        setSheetOpen(false);
        setSelected(null);
        try {
          const me = await authService.getMe();
          setUser(me);
        } catch {
          /* ignore */
        }
      } else if (status === "cancelled") {
        toast("Оплата отменена", "info");
      } else {
        toast("Оплата не завершена", "error");
      }
    } catch (err) {
      toast(getApiError(err).message || "Не удалось начать оплату", "error");
    } finally {
      setPaying(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-4 flex items-center gap-3">
        <BackButton onClick={goBack} className="h-10 w-10 glass-strong active:scale-95" />
        <div>
          <h1 className="text-xl font-bold">Магазин</h1>
          <p className="text-sm text-text-secondary">
            Баланс: <span className="font-semibold text-accent">💎 {formatGems(user?.gems ?? 0)}</span>
          </p>
        </div>
      </header>

      <div
        className="mb-4 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1"
        style={{ border: `1px solid ${CHAT_BORDER}` }}
      >
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              "flex-1 rounded-xl py-2.5 text-sm font-semibold transition-all",
              tab === t
                ? "bg-accent/25 text-accent-light shadow-[0_0_12px_rgba(160,32,240,0.35)]"
                : "text-text-muted hover:text-text-secondary"
            )}
          >
            {SHOP_TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {isLoading && (
        <p className="py-8 text-center text-sm text-text-muted">Загрузка…</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((product, i) => (
          <ShopProductCard
            key={product.id}
            product={product}
            index={i}
            onSelect={() => {
              setSelected(product);
              setSheetOpen(true);
            }}
          />
        ))}
      </div>

      {!isLoading && filtered.length === 0 && (
        <p className="py-12 text-center text-sm text-text-muted">Товаров пока нет</p>
      )}

      <ShopCheckoutSheet
        product={selected}
        open={sheetOpen}
        onClose={() => {
          setSheetOpen(false);
          setSelected(null);
        }}
        onPayStars={handlePayStars}
        loading={paying}
      />
    </div>
  );
}
