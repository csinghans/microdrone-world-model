import type { Metadata } from "next";

import type { Locale } from "@/content/site-copy";

export const SITE_ORIGIN = "https://csinghans.github.io";
export const SITE_BASE_PATH = "/microdrone-world-model";
export const GITHUB_URL =
  "https://github.com/csinghans/microdrone-world-model";

export function sitePath(path = ""): string {
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${basePath}${normalizedPath}`;
}

export function publicUrl(path = ""): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${SITE_ORIGIN}${SITE_BASE_PATH}${normalizedPath}`;
}

export function metadataFor(locale: Locale): Metadata {
  const isZh = locale === "zh-TW";
  const title = isZh
    ? "microdrone-world-model｜512 KB 裡，可以買到多少預判？"
    : "microdrone-world-model | How much anticipation can 512 KB buy?";
  const description = isZh
    ? "為 27 g 微型無人機打造的 tiny latent world model：在嵌入式限制下預測動作的未來，以可重跑的模擬閘門驗證每一個主張。"
    : "A tiny latent world model for 27 g micro-drones, measuring how much action-conditioned anticipation fits inside embedded constraints.";
  const canonical = publicUrl(isZh ? "/zh/" : "/");
  const ogImage = publicUrl("/og.png");

  return {
    title,
    description,
    metadataBase: new URL(`${SITE_ORIGIN}${SITE_BASE_PATH}/`),
    alternates: {
      canonical,
      languages: {
        "zh-Hant": publicUrl("/zh/"),
        en: publicUrl("/"),
        "x-default": publicUrl("/"),
      },
    },
    icons: {
      icon: [
        {
          url: publicUrl("/icon.png"),
          type: "image/png",
          sizes: "64x64",
        },
      ],
    },
    openGraph: {
      type: "website",
      url: canonical,
      siteName: "microdrone-world-model",
      title,
      description,
      locale: isZh ? "zh_TW" : "en_US",
      alternateLocale: isZh ? ["en_US"] : ["zh_TW"],
      images: [
        {
          url: ogImage,
          width: 1734,
          height: 907,
          alt: "microdrone-world-model flight recorder social card",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImage],
    },
    robots: {
      index: true,
      follow: true,
    },
  };
}
