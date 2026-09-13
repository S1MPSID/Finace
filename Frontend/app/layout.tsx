import type { Metadata } from "next";
import { Instrument_Sans, Manrope } from "next/font/google";

import { StoreProvider } from "@/components/providers/StoreProvider";
import { AuthHydrator } from "@/components/dashboard/auth-hydrator";
import { ChatSessionsHydrator } from "@/components/dashboard/chat-sessions-hydrator";
import "./globals.css";

const heading = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-heading",
});

const body = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Finace Compliance UI",
  description: "Autonomous compliance engine interface for fintech and crypto startups.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${heading.variable} ${body.variable} bg-ink font-[var(--font-body)] text-white antialiased`}
      >
        <StoreProvider>
          <AuthHydrator />
          <ChatSessionsHydrator />
          {children}
        </StoreProvider>
      </body>
    </html>
  );
}
