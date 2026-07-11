import type { Metadata } from "next";

import { metadataFor } from "@/lib/site";

import "../globals.css";

export const metadata: Metadata = metadataFor("en");

export default function EnglishLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
