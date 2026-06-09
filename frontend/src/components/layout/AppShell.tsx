"use client";

import { useNavStore, isMainTab, type AppScreen } from "@/store/nav-store";
import { BottomNav } from "@/components/widgets/BottomNav";
import { HomeView } from "@/components/views/HomeView";
import { ChatsView } from "@/components/views/ChatsView";
import { StudioView } from "@/components/views/StudioView";
import { ProfileView } from "@/components/views/ProfileView";
import { CharacterDetailView } from "@/components/views/CharacterDetailView";
import { ScenarioSelectView } from "@/components/views/ScenarioSelectView";
import { NarratorSelectView } from "@/components/views/NarratorSelectView";
import { ChatDialogView } from "@/components/views/ChatDialogView";
import { ShopView } from "@/components/views/ShopView";
import { HistoryView } from "@/components/views/HistoryView";
import { TopUpBalanceView } from "@/components/views/TopUpBalanceView";
import { StudioCreateView } from "@/components/views/StudioCreateView";
import { StudioGeneratingView } from "@/components/views/StudioGeneratingView";
import { StudioResultView } from "@/components/views/StudioResultView";
import { StudioAllModelsView } from "@/components/views/StudioAllModelsView";
import { cn } from "@/lib/utils";
import { useCatalogRefresh } from "@/hooks/use-catalog-refresh";
import { useCatalogVersionCheck } from "@/hooks/use-catalog-version-check";

function ScreenContent({ screen }: { screen: AppScreen }) {
  switch (screen) {
    case "home":
      return <HomeView />;
    case "chats":
      return <ChatsView />;
    case "studio":
      return <StudioView />;
    case "profile":
      return <ProfileView />;
    case "character":
      return <CharacterDetailView />;
    case "scenarios":
      return <ScenarioSelectView />;
    case "narrators":
      return <NarratorSelectView />;
    case "chat":
      return <ChatDialogView />;
    case "shop":
      return <ShopView />;
    case "history":
      return <HistoryView />;
    case "topup":
      return <TopUpBalanceView />;
    case "studio-create":
      return <StudioCreateView />;
    case "studio-generating":
      return <StudioGeneratingView />;
    case "studio-result":
      return <StudioResultView />;
    case "studio-all-models":
      return <StudioAllModelsView />;
    default:
      return null;
  }
}

export function AppShell() {
  const screen = useNavStore((s) => s.screen);
  const showNav = isMainTab(screen);
  useCatalogRefresh();
  useCatalogVersionCheck();

  return (
    <>
      <div className={cn("relative min-h-screen", showNav ? "pb-32" : "pb-0")}>
        <ScreenContent screen={screen} />
      </div>
      {showNav && <BottomNav />}
    </>
  );
}
