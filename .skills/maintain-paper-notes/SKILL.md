---
name: maintain-paper-notes
description: Maintain and publish this repository-scoped Jekyll paper-reading website. Use when Codex needs to add or revise paper notes, update bibliographic metadata and visual evidence, change site navigation or styling, validate Jekyll and Pagefind output, or prepare the paper-notes GitHub Pages project for release.
---

# Maintain Paper Notes

Maintain this repository as the source of truth for the owner's public paper-reading site. Preserve URL behavior, evidence quality, attribution, and the deployment contract while keeping changes narrowly scoped.

## Load the Right Context

1. Read [references/repo-map.md](references/repo-map.md) before changing site structure, templates, styling, search, build tooling, or deployment.
2. Read [references/content-contracts.md](references/content-contracts.md) before adding or editing public Markdown, front matter, navigation, news, or assets.
3. Read [references/validation-and-release.md](references/validation-and-release.md) before running final checks, committing, pushing, or diagnosing deployment.

## Route Specialized Work

- For reading a paper and publishing it into `paper-reading/`, compose with an available paper-analysis or research skill. Keep this repository's asset convention: `assets/paper-reading/<slug>/`.
- For an inline Heilmeier-style paper critique that is not being published, use `paper-reader-heilmeier` when requested.
- For normal topic notes, essays, sharing notes, homepage content, news, site UI, or publishing infrastructure, stay in this skill.
- Do not copy the existing global paper skills into `.skills`; compose with them and keep repo-specific rules here.

## Workflow

### 1. Establish Scope

- Work from the repository root containing this `.skills/maintain-paper-notes/` directory.
- Run `git status --short --branch` before editing.
- Treat all pre-existing changes as user-owned. Do not revert, reformat, stage, or include unrelated files.
- Inspect the target content, its index page, and the rendering path before changing behavior.

### 2. Select the Content Surface

- Put paper or technical-source reading notes in `paper-reading/` with `type: paper-reading`.
- Put optional long-lived synthesis or methodology notes in `wiki/`.
- Put short dated homepage announcements in `_news/`.
- Change homepage identity and navigation through `index.md` and `_data/`.
- Change shared rendering through `_layouts/`, `_includes/`, `assets/css/`, and `assets/js/`.

### 3. Implement Conservatively

- Reuse existing layouts, helpers, front matter fields, CSS classes, and asset conventions.
- Keep links baseurl-safe with Liquid's `relative_url` in templates.
- Never edit generated `_site/`, installed `node_modules/`, `vendor/`, or deployment output on `gh-pages`.
- Do not change Obsidian workspace state unless the user explicitly asks. In particular, avoid `.obsidian/appearance.json`, `.obsidian/core-plugins.json`, workspace files, graph state, and plugin bundles.
- Do not alter lockfiles unless the task actually changes dependencies.

### 4. Validate in Proportion to Risk

- Use targeted checks while iterating.
- Use `npm run build` as the full release gate; it runs the paper figure gate, Jekyll build, and Pagefind indexing.
- For paper notes, run the note-specific figure check and visual audit before the full build.
- For layout, style, JavaScript, or responsive changes, inspect the rendered site in a browser when available.
- If a failure predates the current task, record the baseline evidence and do not silently absorb it into the change.

### 5. Hand Off Safely

- Summarize changed files and checks run.
- Mention any validation not run and why.
- Commit or push only when explicitly requested.
- Push source changes to `main`; allow the GitHub Action to regenerate `gh-pages`.

## Repository Invariants

- The deployed project site uses `baseurl: /paper-notes`; keep it synchronized with the GitHub repository name and avoid hard-coded root paths in templates.
- `wiki/index.md` lists every public page except `type: paper-reading`; set `public: true` deliberately.
- `paper-reading/index.md` lists only public pages whose type is exactly `paper-reading` and sorts primarily by `created_at`.
- Paper notes require at least three original raster figures/screenshots and one generated diagram under the current gate.
- Markdown note assets should use repository-relative `assets/...` paths because `wiki_note.html` rewrites them for nested rendered pages.
- `main` is the authored branch. `gh-pages` is generated and force-pushed by CI.
- Keep `README.md` minimal unless the user specifically asks to turn it into documentation.
