import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelAI — Secure Enterprise AI Workspace",
  description: "MCP-powered enterprise AI platform for knowledge, code, email, calendar, and operational tools",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
