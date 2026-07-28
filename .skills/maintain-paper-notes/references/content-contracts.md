# Content Contracts

## Public Wiki Notes

Create long-lived topic notes under `wiki/` with this minimum front matter:

```yaml
---
title: "Readable title"
public: true
description: "One-line list-page summary."
date: 2026-07-16
---
```

Add `type` only when it carries meaning, for example `paper-sharing`. Do not use `type: paper-reading` for ordinary wiki notes.

Important listing behavior:

- `wiki/index.md` searches all `site.pages`, not only files under `wiki/`.
- Every page with `public: true` appears there unless its type is exactly `paper-reading`.
- The list sorts by `date` descending.
- Avoid adding `public: true` to utility or index pages unless they should be discoverable as notes.

## Paper-Reading Notes

Prefer the `paper-auto-reading` skill and `scripts/publish_paper_note.py`. A normal public note uses:

```yaml
---
title: "Site-facing title"
public: true
description: "Decision-oriented one-line summary."
type: paper-reading
date: 2026-07-16
created_at: 2026-07-16T12:00:00+08:00
paper_title: "Original title"
authors: "Verified authors"
venue: "Verified venue or source"
year: "2026"
status: "reading"
category: "Agent Systems"
tags:
  - agent-systems
source_url: "https://primary-source.example"
---
```

Rules:

- Verify bibliographic metadata from a primary source; omit uncertain fields.
- Keep `type: paper-reading` exact so the correct index and back link work.
- Use one display `category` and a compact tag vocabulary for filters.
- Use an ISO `created_at` timestamp with the local offset; the index sorts on it before falling back to `date`.
- Store visuals in `assets/paper-reading/<slug>/`, even though older generic instructions may mention `assets/<slug>/`.
- Meet the hard gate: at least three original raster figures/screenshots plus one generated diagram.
- Treat SVG as generated and PNG/JPEG/WebP/GIF as original unless explicit `figure-generated`, `figure-original`, or `data-source` attributes override detection.
- Follow every important figure with a real explanation; the visual audit treats unexplained images as polish debt.

## News

Create short announcements in `_news/YYYY-MM-DD-slug.md`:

```yaml
---
title: A short announcement.
date: 2026-07-16
---

One short paragraph.
```

The homepage shows news only when `_data/display.yml` has `homepage.show_news: true`; it currently shows the newest five items.

## Homepage, Identity, and Navigation

- Edit homepage prose in `index.md`.
- Edit name, bio, portrait, GitHub handle, and positions in `_data/profile.yml`.
- Edit navbar pages in `_data/navigation.yml`.
- Keep navbar URLs site-relative, such as `/wiki/`; templates apply `relative_url`.
- Set `navbar_title` on index pages so the active navbar state matches the navigation item name.

## Assets and Links

- Store general note assets in `assets/wiki/<slug>/`.
- Store paper-note assets in `assets/paper-reading/<slug>/`.
- In note Markdown, reference assets as `assets/...`, not as a filesystem path and not as a raw `_site` path.
- In Liquid templates, wrap internal paths with `relative_url`.
- Keep original screenshots and generated diagrams distinguishable; `blog.js` displays a source badge based on file type or explicit attributes.
- Use descriptive alt text and add prose explaining why each important image matters.
- Do not edit, link to, or commit generated `_site/pagefind/` output.

## Markdown and Math

- Jekyll uses Kramdown with GFM input; browser-side KaTeX renders `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`.
- Keep inline math on one line.
- Prefer `\lbrace` and `\rbrace` over escaped curly delimiters that GitHub Markdown may damage.
- Inspect rendered tables, code blocks, headings, and math after substantial edits; the note layout adds wrappers and heading IDs in JavaScript.

## Cross-Linking and Backlinks

- To cross-link another note, use `[label]({{ '/<dir>/<fully-percent-encoded-filename>.html' | relative_url }})`. Encode spaces as `%20` and CJK characters as their UTF-8 percent-encoding so the link text matches the target's `page.url` exactly — `_layouts/wiki_note.html` builds the automatic "引用了本文的笔记" backlinks section by searching other pages' source for the encoded filename.
