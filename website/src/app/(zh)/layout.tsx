import type { Metadata } from "next";

import { metadataFor } from "@/lib/site";

import "../globals.css";

export const metadata: Metadata = metadataFor("zh-TW");

export default function TraditionalChineseLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
