# microdrone-world-model website

The bilingual, static project introduction site for
`microdrone-world-model`. English is the default route and Traditional Chinese
is available at `/zh/`.

## Local development

```bash
npm ci
npm run dev
```

## Verification

```bash
npm run lint
npm test
```

`npm test` checks the published evidence against the repository's committed
gate records, builds with the GitHub Pages base path, and verifies both static
HTML exports and their assets.

## GitHub Pages

The repository workflow builds this directory with
`/microdrone-world-model` as its base path and deploys `out/` after the relevant
source reaches `main`. GitHub Pages must use **GitHub Actions** as its publishing
source.
