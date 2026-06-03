"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ShopCheckoutSheet } from "@/components/shop/ShopCheckoutSheet";
import { ShopProductCard } from "@/components/shop/ShopProductCard";
import { ListPanel } from "@/components/shared/ListPanel";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { useToast } from "@/hooks/use-toast";
import { openTelegramInvoice } from "@/hooks/use-telegram-payment";
import { ensureTelegramSession, getApiError } from "@/lib/api-client";
import { QUERY_KEYS } from "@/lib/constants";
import { canPayWithTelegramStars, getTelegramInitData } from "@/lib/telegram-webapp";
import { useNavStore } from "@/store/nav-store";
import { usePaymentStore } from "@/store/payment-store";
import { useUserStore } from "@/store/user-store";
import { shopService, authService, balanceService } from "@/services/api";
import {
  MOCK_SHOP_PRODUCTS,
  SHOP_TAB_LABELS,
  type ShopProduct,
  type ShopTab,
} from "@/lib/shop";
import { BackButton } from "@/components/shared/BackButton";
import { useMounted } from "@/hooks/use-mounted";
import { chatBorderStyle } from "@/lib/theme";
import { formatGems } from "@/lib/utils";
import { cn } from "@/lib/utils";

const TABS: ShopTab[] = ["bundle", "gems", "credits"];

export function ShopView() {
  const mounted = useMounted();
  const goBack = useNavStore((s) => s.goBack);
  const { user, setUser } = useUserStore();
  const { gems, credits, setBalance } = usePaymentStore();
  const { toast } = useToast();
  const [tab, setTab] = useState<ShopTab>("bundle");
  const [selected, setSelected] = useState<ShopProduct | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [paying, setPaying] = useState(false);

  const { data: balance } = useQuery({
    queryKey: QUERY_KEYS.balance,
    queryFn: () => balanceService.get(),
  });

  useEffect(() => {
    if (balance) {
      setBalance(balance.gems, balance.credits);
    }
  }, [balance, setBalance]);

  const gemsDisplay = balance?.gems ?? gems ?? user?.gems ?? 0;
  const creditsDisplay = balance?.credits ?? credits ?? 0;

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
      if (!getTelegramInitData()) {
        toast("Откройте магазин через кнопку бота в Telegram", "info");
        return;
      }
      await ensureTelegramSession();
      const checkout = await shopService.checkout(selected.id, promoCode || undefined);
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
        toast(
          "Оплата не открылась. Откройте Mini App с телефона (не ПК) и убедитесь, что есть Stars ⭐",
          "error"
        );
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
        <BackButton onClick={goBack} />
        <div>
          <h1 className="text-xl font-bold">Магазин</h1>
          <p className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm text-text-secondary">
            <span className="font-medium text-text-muted">Баланс:</span>
            <span className="inline-flex items-center gap-1 font-semibold text-text-primary">
              <AnimeGemIcon className="h-4 w-4" />
              {formatGems(gemsDisplay)}
            </span>
            <span className="inline-flex items-center gap-1 font-semibold text-text-primary">
              <AnimeHeartIcon className="h-4 w-4" />
              {formatGems(creditsDisplay)}
            </span>
          </p>
        </div>
      </header>

      <div className="mb-4 flex gap-1 rounded-2xl bg-bg-elevated/60 p-1" style={chatBorderStyle}>
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              "relative flex-1 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === t ? "text-text-primary" : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab === t &&
              (mounted ? (
                <motion.div
                  layoutId="shop-tab"
                  className="absolute inset-0 rounded-xl bg-bg-elevated"
                  style={chatBorderStyle}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              ) : (
                <div
                  className="absolute inset-0 rounded-xl bg-bg-elevated"
                  style={chatBorderStyle}
                />
              ))}
            <span className="relative z-[1]">{SHOP_TAB_LABELS[t]}</span>
          </button>
        ))}
      </div>

      {isLoading && (
        <p className="py-8 text-center text-sm text-text-muted">Загрузка…</p>
      )}

      {!isLoading && filtered.length === 0 && (
        <p className="py-12 text-center text-sm text-text-muted">Товаров пока нет</p>
      )}

      {!isLoading && filtered.length > 0 && (
        <ListPanel>
          {filtered.map((product, i) => (
            <ShopProductCard
              key={product.id}
              product={product}
              index={i}
              showSeparator={i < filtered.length - 1}
              onSelect={() => {
                setSelected(product);
                setSheetOpen(true);
              }}
            />
          ))}
        </ListPanel>
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
