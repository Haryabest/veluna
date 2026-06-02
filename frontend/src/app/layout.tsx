import type { Metadata, Viewport } from "next";
import { Manrope } from "next/font/google";
import { AppBackground } from "@/components/layout/AppBackground";
import { Providers } from "@/components/shared/Providers";
import { AuthGuard } from "@/features/auth/AuthGuard";
import "@/styles/globals.css";

const manrope = Manrope({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-manrope",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Veluna — AI-компаньон",
  description: "Твоя AI waifu в Telegram",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0c0812",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={manrope.variable}>
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js" async />
      </head>
      <body className="font-sans antialiased">
        <Providers>
          <AuthGuard>
            <AppBackground />
            <main className="relative z-[1] min-h-screen">{children}</main>
          </AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
