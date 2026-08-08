import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BIP-110 Dashboard",
  description: "Self-hosted BIP-110 monitoring from your own nodes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
