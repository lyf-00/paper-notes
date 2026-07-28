# Repository Map

## Stack and Data Flow

The repository combines an Obsidian-authored Markdown vault with a Jekyll 3.9 site. Jekyll renders the source into `_site/`, then Pagefind indexes the rendered HTML. A GitHub Actions workflow repeats that process on `main` and force-pushes the output to `gh-pages`.

```text
Markdown + YAML + Liquid + assets
  -> bundle exec jekyll build
  -> _site/
  -> pagefind --site _site
  -> GitHub Pages from gh-pages
```

Pinned tooling:

- Ruby/Jekyll: `Gemfile`, `Gemfile.lock`, Jekyll `~> 3.9`
- Node/Pagefind: `package.json`, `package-lock.json`, Pagefind `1.5.2`
- CI: Ruby `3.2`, Bundler `2.4.22`, Node `20`
- Site URL before custom-domain setup: `https://lyf-00.github.io/paper-notes`
- Language/timezone: `zh-CN`, `Asia/Shanghai`

## Path Ownership

| Path | Responsibility |
|---|---|
| `index.md` | Homepage body using the `home` layout |
| `_data/profile.yml` | Name, GitHub identity, bio, portrait, positions |
| `_data/navigation.yml` | Navbar pages and URLs |
| `_data/display.yml` | Homepage display toggles and counts |
| `_news/` | Dated homepage announcements |
| `wiki/` | Public topic notes, essays, and sharing notes |
| `paper-reading/` | Public paper and technical-source reading notes |
| `_layouts/` | Page skeletons and note rendering |
| `_includes/` | Shared navbar, footer, and homepage widgets |
| `assets/css/global.css` | Shared site and index-page styling |
| `assets/css/blog.css` | Long-form note typography, figures, TOC, math, tables |
| `assets/js/common.js` | Lazy loading and Masonry behavior |
| `assets/js/blog.js` | Heading IDs, TOC, anchors, image labels/zoom, progress, tables |
| `assets/paper-reading/` | Paper-note visual assets, grouped by note slug |
| `assets/wiki/` | General wiki-note visual assets, grouped by note slug |
| `scripts/publish_paper_note.py` | Generates paper-note front matter and runs a note-level figure check |
| `scripts/check_paper_reading_figures.py` | Enforces 3 original images plus 1 generated diagram |
| `scripts/audit_paper_reading_visuals.py` | Reports figure placement, density, and explanation quality |
| `scripts/paper_reading_figure_debt.json` | Grandfathers legacy visual debt; do not add new debt casually |
| `.github/workflows/deploy-site.yml` | Builds source and replaces the generated `gh-pages` branch |

## Rendering Contracts

- `_config.yml` assigns `wiki_note` to pages under both `wiki/` and `paper-reading/`.
- `wiki_note.html` adds the reading progress bar, table of contents, Pagefind body marker, and back link.
- `wiki_note.html` rewrites rendered `src="assets/` and `href="assets/` to `../assets/`; preserve this convention when writing notes.
- `default.html` loads KaTeX, Pagefind, Bootstrap, and global assets. It conditionally loads Prism, Tocbot, AnchorJS, Medium Zoom, `blog.css`, and `blog.js` for `wiki_note` pages.
- Use `relative_url` for internal URLs because the deployed site has a non-empty baseurl.
- Pagefind output exists only after `npm run build` or `npm run build:search`; a plain Jekyll build does not create the search bundle.

## Skill Composition

Use an available research or paper-analysis skill for source reading when appropriate. Keep site architecture, front matter rules, asset paths, validation, and release behavior in `maintain-paper-notes`.
