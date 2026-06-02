import type { Metadata, Viewport } from "next";
import { Providers } from "@/components/shared/Providers";
import { AuthGuard } from "@/features/auth/AuthGuard";
import { BottomNav } from "@/components/widgets/BottomNav";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Veluna — AI Waifu Companion",
  description: "Your AI anime companion in Telegram",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0a0a0f",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js" async />
      </head>
      <body>
        <Providers>
          <AuthGuard>
            <main className="min-h-screen pb-20">{children}</main>
            <BottomNav />
          </AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
