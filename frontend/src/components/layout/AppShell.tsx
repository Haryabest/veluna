"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useNavStore } from "@/store/nav-store";
import { BottomNav } from "@/components/widgets/BottomNav";
import { HomeView } from "@/components/views/HomeView";
import { ChatsView } from "@/components/views/ChatsView";
import { StudioView } from "@/components/views/StudioView";
import { ProfileView } from "@/components/views/ProfileView";
import { CharacterDetailView } from "@/components/views/CharacterDetailView";
import { ScenarioSelectView } from "@/components/views/ScenarioSelectView";
import { ChatDialogView } from "@/components/views/ChatDialogView";
import { ShopView } from "@/components/views/ShopView";

const tabVariants = {
  initial: { opacity: 0, x: 12 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -12 },
};

export function AppShell() {
  const screen = useNavStore((s) => s.screen);
  const showNav = screen === "home" || screen === "studio" || screen === "chats" || screen === "profile";

  return (
    <>
      <div className={showNav ? "pb-32" : "pb-0"}>
        <AnimatePresence mode="wait">
          {screen === "home" && (
            <motion.div key="home" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.2 }}>
              <HomeView />
            </motion.div>
          )}
          {screen === "chats" && (
            <motion.div key="chats" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.2 }}>
              <ChatsView />
            </motion.div>
          )}
          {screen === "studio" && (
            <motion.div key="studio" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.2 }}>
              <StudioView />
            </motion.div>
          )}
          {screen === "profile" && (
            <motion.div key="profile" variants={tabVariants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.2 }}>
              <ProfileView />
            </motion.div>
          )}
          {screen === "character" && (
            <motion.div key="character" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <CharacterDetailView />
            </motion.div>
          )}
          {screen === "scenarios" && (
            <motion.div key="scenarios" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <ScenarioSelectView />
            </motion.div>
          )}
          {screen === "chat" && (
            <motion.div key="chat" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}>
              <ChatDialogView />
            </motion.div>
          )}
          {screen === "shop" && (
            <motion.div key="shop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <ShopView />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {showNav && <BottomNav />}
    </>
  );
}
