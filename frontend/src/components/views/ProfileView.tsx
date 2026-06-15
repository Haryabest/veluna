"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { History } from "lucide-react";
import { useNavStore } from "@/store/nav-store";
import { useUserStore } from "@/store/user-store";
import { usePaymentStore } from "@/store/payment-store";
import { useSettingsStore } from "@/store/settings-store";
import { balanceQueryOptions } from "@/lib/catalog-queries";
import { QUERY_KEYS } from "@/lib/constants";
import { authService, userService } from "@/services/api";
import { AnimeGemIcon, AnimeHeartIcon } from "@/components/icons/CurrencyIcons";
import { ListPanel } from "@/components/shared/ListPanel";
import { formatGems } from "@/lib/utils";
import { useTelegramUser } from "@/hooks/use-telegram-user";
import { ProfileAvatar } from "@/components/shared/ProfileAvatar";
import { chatSeparatorVerticalStyle } from "@/lib/theme";
import { useTranslation } from "@/hooks/use-translation";
import { useToast } from "@/hooks/use-toast";
import { onLocaleChanged } from "@/lib/locale-sync";
import type { AppLocale } from "@/lib/i18n/translations";

import { resolveProfileAvatarUrl } from "@/lib/profile-avatar";

export function ProfileView() {
  const { t, locale } = useTranslation();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { user, setUser } = useUserStore();
  const setLanguage = useSettingsStore((s) => s.setLanguage);
  const openHistory = useNavStore((s) => s.openHistory);
  const { gems, credits, setBalance } = usePaymentStore();
  const { displayName: tgName, username: tgUsername, photoUrl: tgPhoto } = useTelegramUser();

  const { data: profile } = useQuery({
    queryKey: QUERY_KEYS.user,
    queryFn: () => authService.getMe(),
    staleTime: 0,
    refetchOnMount: "always",
  });

  useEffect(() => {
    if (profile) setUser(profile);
  }, [profile, setUser]);

  const localeMutation = useMutation({
    mutationFn: (next: AppLocale) => userService.updateLocale(next),
    onSuccess: (updated) => {
      setUser(updated);
      setLanguage(updated.language_code);
      onLocaleChanged(queryClient, updated.language_code as AppLocale);
      toast(t("locale.saved"), "success");
    },
  });

  const guestLabel = t("profile.guest");
  const displayName =
    tgName !== guestLabel
      ? tgName
      : profile
        ? `${profile.first_name ?? ""}${profile.last_name ? ` ${profile.last_name}` : ""}`.trim() || guestLabel
        : user
          ? `${user.first_name ?? ""}${user.last_name ? ` ${user.last_name}` : ""}`.trim() || guestLabel
          : guestLabel;
  const username = tgUsername ?? profile?.username ?? user?.username;
  const photoUrl = resolveProfileAvatarUrl(tgPhoto, profile?.photo_url, user?.photo_url);

  const { data: balance } = useQuery(balanceQueryOptions);

  const { data: finance } = useQuery({
    queryKey: QUERY_KEYS.financeStats,
    queryFn: () => userService.getFinanceStats(),
    staleTime: 0,
    refetchOnMount: "always",
    refetchOnWindowFocus: true,
  });

  useEffect(() => {
    if (balance) {
      setBalance(balance.gems, balance.credits);
    }
  }, [balance, setBalance]);

  const gemsDisplay = balance?.gems ?? gems;
  const creditsDisplay = balance?.credits ?? credits;
  const currentLocale = (profile?.language_code ?? user?.language_code ?? locale) as AppLocale;

  return (
    <div className="mx-auto max-w-lg space-y-4 px-4 pt-6">
      <header className="flex items-center gap-4">
        <ProfileAvatar photoUrl={photoUrl} name={displayName || guestLabel} />
        <div>
          <h1 className="text-xl font-bold">{displayName || guestLabel}</h1>
          {username && <p className="text-sm text-text-muted">@{username}</p>}
        </div>
      </header>

      <ListPanel>
        <div className="grid grid-cols-2">
          <BalanceCell
            icon={<AnimeGemIcon className="h-[22px] w-[22px]" />}
            label={t("profile.gems")}
            value={formatGems(gemsDisplay)}
          />
          <div style={chatSeparatorVerticalStyle}>
            <BalanceCell
              icon={<AnimeHeartIcon className="h-[22px] w-[22px]" />}
              label={t("profile.hearts")}
              value={formatGems(creditsDisplay)}
            />
          </div>
        </div>
      </ListPanel>

      {finance ? (
        <ListPanel>
          <div className="grid grid-cols-2 divide-x divide-white/5">
            <div className="px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">{t("profile.spent")}</p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-rose-400">
                <span className="inline-flex items-center gap-1">
                  −{formatGems(finance.spent.gems)}
                  <AnimeGemIcon className="h-3.5 w-3.5" />
                </span>
                <span className="inline-flex items-center gap-1">
                  −{formatGems(finance.spent.credits)}
                  <AnimeHeartIcon className="h-3.5 w-3.5" />
                </span>
              </p>
            </div>
            <div className="px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-text-muted">{t("profile.deposited")}</p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-emerald-400">
                <span className="inline-flex items-center gap-1">
                  +{formatGems(finance.deposited.gems)}
                  <AnimeGemIcon className="h-3.5 w-3.5" />
                </span>
                <span className="inline-flex items-center gap-1">
                  +{formatGems(finance.deposited.credits)}
                  <AnimeHeartIcon className="h-3.5 w-3.5" />
                </span>
              </p>
            </div>
          </div>
        </ListPanel>
      ) : null}

      <ListPanel>
        <div className="px-4 py-3.5" style={chatSeparatorStyle}>
          <p className="text-sm text-text-secondary">{t("profile.language")}</p>
          <div className="mt-3 flex gap-2">
            {(["ru", "en"] as const).map((code) => (
              <button
                key={code}
                type="button"
                disabled={localeMutation.isPending}
                onClick={() => localeMutation.mutate(code)}
                className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition-colors ${
                  currentLocale === code
                    ? "bg-accent text-white shadow-glow"
                    : "bg-bg-elevated text-text-secondary"
                }`}
              >
                {code === "ru" ? t("profile.languageRu") : t("profile.languageEn")}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={openHistory}
          className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-bg-elevated/60"
        >
          <History className="h-5 w-5 text-accent-light" strokeWidth={1.75} />
          <span className="text-sm font-medium">{t("profile.history")}</span>
        </button>
      </ListPanel>
    </div>
  );
}

const chatSeparatorStyle = { borderBottom: "1px solid rgba(255,255,255,0.06)" } as const;

function BalanceCell({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-3">
      <span className="flex items-center gap-2">
        <span className="drop-shadow-[0_0_6px_rgba(199,125,255,0.5)]">{icon}</span>
        <span className="text-[10px] font-medium uppercase tracking-wide text-text-muted">
          {label}
        </span>
      </span>
      <p className="text-lg font-bold leading-tight text-text-primary">{value}</p>
    </div>
  );
}
