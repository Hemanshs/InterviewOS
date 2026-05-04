import type { Metadata } from "next";
import { DM_Mono, DM_Sans } from "next/font/google";

import { SupabaseSessionProvider } from "@/lib/supabaseClient";

import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-dm-mono",
});

export const metadata: Metadata = {
  title: "InterviewOS — AI Voice Interview Coach",
  description:
    "Practice realistic software engineering interviews with AI voice coaching",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${dmSans.variable} ${dmMono.variable} bg-[#0a0a0a] text-[#f5f5f5] antialiased`}
      >
        <SupabaseSessionProvider>{children}</SupabaseSessionProvider>
      </body>
    </html>
  );
}
