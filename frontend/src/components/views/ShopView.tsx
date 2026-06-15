"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
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
import { balanceQueryOptions, shopProductsQueryOptions } from "@/lib/catalog-queries";
import { type ShopProduct, type ShopTab } from "@/lib/shop";
import { BackButton } from "@/components/shared/BackButton";
import { useMounted } from "@/hooks/use-mounted";
import { chatBorderStyle } from "@/lib/theme";
import { formatGems } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/use-translation";
import type { TranslationKey } from "@/lib/i18n/translations";

const TABS: ShopTab[] = ["bundle", "gems", "credits"];

const SHOP_TAB_KEYS: Record<ShopTab, TranslationKey> = {
  bundle: "shop.tab.bundle",
  gems: "shop.tab.gems",
  credits: "shop.tab.credits",
};

export function ShopView() {
  const mounted = useMounted();
  const queryClient = useQueryClient();
  const goBack = useNavStore((s) => s.goBack);
  const { user, setUser } = useUserStore();
  const { gems, credits, setBalance } = usePaymentStore();
  const { toast } = useToast();
  const { t } = useTranslation();
  const [tab, setTab] = useState<ShopTab>("bundle");
  const [selected, setSelected] = useState<ShopProduct | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [paying, setPaying] = useState(false);

  const { data: balance } = useQuery(balanceQueryOptions);

  useEffect(() => {
    if (balance) {
      setBalance(balance.gems, balance.credits);
    }
  }, [balance, setBalance]);

  const gemsDisplay = balance?.gems ?? gems ?? user?.gems ?? 0;
  const creditsDisplay = balance?.credits ?? credits ?? 0;

  const {
    data: apiProducts,
    isLoading,
    isFetching,
    isError,
    refetch: refetchProducts,
  } = useQuery(shopProductsQueryOptions());

  const products: ShopProduct[] = useMemo(() => {
    const list = (Array.isArray(apiProducts) ? apiProducts : []) as ShopProduct[];
    return list.filter((p) => p.is_active !== false);
  }, [apiProducts]);

  const filtered = products.filter((p) => p.product_type === tab);

  const handlePayStars = async (promoCode: string) => {
    if (!selected) return;

    if (!canPayWithTelegramStars()) {
      toast(t("shop.openViaTelegram"), "info");
      return;
    }

    setPaying(true);
    try {
      if (!getTelegramInitData()) {
        toast(t("shop.openViaBot"), "info");
        return;
      }
      await ensureTelegramSession();
      const checkout = await shopService.checkout(selected.id, promoCode || undefined);
      const status = await openTelegramInvoice(checkout.invoice_url);

      if (status === "paid") {
        toast(t("shop.paymentSuccess"), "success");
        setSheetOpen(false);
        setSelected(null);
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.balance });
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.financeStats });
        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.shopProducts });
        try {
          const [me, freshBalance] = await Promise.all([
            authService.getMe(),
            balanceService.get(),
          ]);
          setUser(me);
          setBalance(freshBalance.gems, freshBalance.credits);
        } catch {
          /* ignore */
        }
      } else if (status === "cancelled") {
        toast(t("shop.paymentCancelled"), "info");
      } else {
        toast(t("shop.paymentFailed"), "error");
      }
    } catch (err) {
      toast(getApiError(err).message || t("shop.paymentStartError"), "error");
    } finally {
      setPaying(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 pb-8 pt-4">
      <header className="mb-4 flex items-center gap-3">
        <BackButton onClick={goBack} />
        <div>
          <h1 className="text-xl font-bold">{t("shop.title")}</h1>
          <p className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm text-text-secondary">
            <span className="font-medium text-text-muted">{t("shop.balance")}</span>
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
        {TABS.map((shopTab) => (
          <button
            key={shopTab}
            type="button"
            onClick={() => setTab(shopTab)}
            className={cn(
              "relative flex-1 rounded-xl py-2.5 text-sm font-medium transition-all",
              tab === shopTab ? "text-text-primary" : "text-text-muted hover:text-text-secondary"
            )}
          >
            {tab === shopTab &&
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
            <span className="relative z-[1]">{t(SHOP_TAB_KEYS[shopTab])}</span>
          </button>
        ))}
      </div>

      {isLoading && !apiProducts && (
        <p className="py-8 text-center text-sm text-text-muted">{t("shop.loading")}</p>
      )}

      {isFetching && apiProducts && (
        <p className="py-1 text-center text-xs text-text-muted">{t("shop.refreshing")}</p>
      )}

      {isError && (
        <div className="py-8 text-center">
          <p className="text-sm text-text-muted">{t("shop.loadError")}</p>
          <button
            type="button"
            onClick={() => void refetchProducts()}
            className="mt-3 text-sm font-medium text-accent-light underline"
          >
            {t("shop.retry")}
          </button>
        </div>
      )}

      {!isLoading && !isFetching && !isError && filtered.length === 0 && (
        <p className="py-12 text-center text-sm text-text-muted">{t("shop.empty")}</p>
      )}

      {filtered.length > 0 && (
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
