import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const websiteRoot = fileURLToPath(new URL("../", import.meta.url));
const outRoot = path.join(websiteRoot, "out");
const basePath = "/microdrone-world-model";
const siteOrigin = "https://csinghans.github.io";
const siteUrl = `${siteOrigin}${basePath}`;

const pages = {
  zh: {
    file: "index.html",
    canonical: `${siteUrl}/`,
    headline: "512 KB 裡，可以買到多少預判？",
  },
  en: {
    file: "en/index.html",
    canonical: `${siteUrl}/en/`,
    headline: "How much anticipation can 512 KB buy?",
  },
};

function parseAttributes(tag) {
  const attributes = {};
  const pattern = /([^\s=/>]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;

  for (const match of tag.matchAll(pattern)) {
    attributes[match[1].toLowerCase()] = match[2] ?? match[3];
  }

  return attributes;
}

function tags(html, tagName) {
  return [...html.matchAll(new RegExp(`<${tagName}\\b[^>]*>`, "gi"))].map(
    (match) => parseAttributes(match[0]),
  );
}

function linkByRel(html, rel) {
  return tags(html, "link").find((tag) =>
    (tag.rel ?? "").toLowerCase().split(/\s+/).includes(rel),
  );
}

function metaBy(html, attribute, value) {
  return tags(html, "meta").find(
    (tag) => (tag[attribute] ?? "").toLowerCase() === value.toLowerCase(),
  );
}

function allAssetReferences(html) {
  const references = [];
  const pattern = /\b(?:href|src|poster)\s*=\s*(?:"([^"]+)"|'([^']+)')/gi;

  for (const match of html.matchAll(pattern)) {
    references.push(match[1] ?? match[2]);
  }

  return references;
}

async function assertExportedAsset(reference, label) {
  const url = new URL(reference, siteOrigin);
  assert.equal(url.origin, siteOrigin, `${label} must use the GitHub Pages origin`);
  assert.ok(
    url.pathname.startsWith(`${basePath}/`),
    `${label} must be under ${basePath}`,
  );

  const relativePath = decodeURIComponent(url.pathname.slice(basePath.length + 1));
  await access(path.join(outRoot, relativePath));
}

test("static export contains direct-loadable Traditional Chinese and English pages", async () => {
  const [zhHtml, enHtml] = await Promise.all([
    readFile(path.join(outRoot, pages.zh.file), "utf8"),
    readFile(path.join(outRoot, pages.en.file), "utf8"),
  ]);

  assert.match(zhHtml, /<html\b[^>]*\blang=["']zh-(?:Hant|TW)["']/i);
  assert.match(enHtml, /<html\b[^>]*\blang=["']en["']/i);
  assert.ok(zhHtml.includes(pages.zh.headline), "Traditional Chinese headline is missing");
  assert.ok(enHtml.includes(pages.en.headline), "English headline is missing");
  assert.match(zhHtml, /模擬/);
  assert.match(zhHtml, /(?:推算|估算)/);
  assert.match(enHtml, /simulation/i);
  assert.match(enHtml, /estimated/i);
});

test("both locales export complete canonical, alternate, and Open Graph metadata", async () => {
  const exportedPages = await Promise.all(
    Object.values(pages).map(async (page) => ({
      ...page,
      html: await readFile(path.join(outRoot, page.file), "utf8"),
    })),
  );
  const ogImages = [];

  for (const page of exportedPages) {
    assert.match(page.html, /<title>[^<]*microdrone[^<]*<\/title>/i);
    assert.ok(metaBy(page.html, "name", "description")?.content);
    assert.equal(linkByRel(page.html, "canonical")?.href, page.canonical);

    const alternates = tags(page.html, "link").filter(
      (tag) => (tag.rel ?? "").toLowerCase() === "alternate",
    );
    const zhAlternate = alternates.find((tag) =>
      /^zh-(?:hant|tw)$/i.test(tag.hreflang ?? ""),
    );
    const enAlternate = alternates.find(
      (tag) => (tag.hreflang ?? "").toLowerCase() === "en",
    );
    assert.equal(zhAlternate?.href, pages.zh.canonical);
    assert.equal(enAlternate?.href, pages.en.canonical);

    assert.ok(metaBy(page.html, "property", "og:title")?.content);
    assert.ok(metaBy(page.html, "property", "og:description")?.content);
    const ogImage = metaBy(page.html, "property", "og:image")?.content;
    assert.ok(ogImage, `${page.file} is missing og:image`);
    await assertExportedAsset(ogImage, `${page.file} og:image`);
    ogImages.push(ogImage);
  }

  assert.equal(new Set(ogImages).size, 1, "both locales must share one bilingual OG card");
});

test("all internal URLs honor the repository base path", async () => {
  const [zhHtml, enHtml] = await Promise.all([
    readFile(path.join(outRoot, pages.zh.file), "utf8"),
    readFile(path.join(outRoot, pages.en.file), "utf8"),
  ]);

  for (const [locale, html] of [
    ["zh", zhHtml],
    ["en", enHtml],
  ]) {
    assert.ok(html.includes(`${basePath}/_next/`), `${locale} assets lack basePath`);

    for (const reference of allAssetReferences(html)) {
      if (reference.startsWith("/") && !reference.startsWith("//")) {
        assert.ok(
          reference === basePath || reference.startsWith(`${basePath}/`),
          `${locale} export has an unprefixed root-relative URL: ${reference}`,
        );
      }
    }
  }

  assert.ok(zhHtml.includes(`href="${basePath}/en/"`));
  assert.ok(enHtml.includes(`href="${basePath}/"`));
});

test("referenced videos, posters, gate image, icon, and static assets exist", async () => {
  const [zhHtml, enHtml] = await Promise.all([
    readFile(path.join(outRoot, pages.zh.file), "utf8"),
    readFile(path.join(outRoot, pages.en.file), "utf8"),
  ]);
  const combinedHtml = `${zhHtml}\n${enHtml}`;
  const requiredMedia = [
    "hero-course.mp4",
    "hero-course.webp",
    "transit.mp4",
    "transit.webp",
    "indoor.mp4",
    "indoor.webp",
    "integration-climb.png",
  ];

  for (const filename of requiredMedia) {
    const reference = `${basePath}/media/${filename}`;
    assert.ok(combinedHtml.includes(reference), `export does not reference ${filename}`);
    await access(path.join(outRoot, "media", filename));
  }

  const icon = linkByRel(zhHtml, "icon");
  assert.ok(icon?.href, "export is missing a favicon link");
  await assertExportedAsset(icon.href, "favicon");

  const localStaticReferences = new Set(
    [...allAssetReferences(zhHtml), ...allAssetReferences(enHtml)].filter(
      (reference) =>
        reference.startsWith(`${basePath}/`) &&
        !reference.includes("#") &&
        !reference.endsWith("/"),
    ),
  );

  for (const reference of localStaticReferences) {
    await assertExportedAsset(reference, reference);
  }
});
