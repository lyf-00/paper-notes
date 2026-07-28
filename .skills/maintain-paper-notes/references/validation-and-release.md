# Validation and Release

## Preflight

Run these before editing or staging:

```bash
git status --short --branch
git diff --stat
```

Record unrelated modified and untracked files. Never use destructive cleanup to obtain a clean tree.

## Validation Matrix

| Change | Minimum checks | Strong finish |
|---|---|---|
| Wiki/news/front matter | `bundle exec jekyll build` | `npm run build` and inspect rendered page |
| One paper note | note-specific figure check, visual audit, Jekyll build | `npm run check:figures:gate`, then `npm run build` |
| Layout/include/CSS/JS | `bundle exec jekyll build` | `npm run build` plus desktop/mobile browser inspection |
| Navigation/profile/data | `bundle exec jekyll build` | inspect navbar, homepage, and links |
| Search behavior | `npm run build` | serve `_site` and test Pagefind queries |
| Build/deploy workflow | exact affected command | full `npm run build`, then inspect workflow diff |

Useful commands:

```bash
# Jekyll only
bundle exec jekyll build

# Full local release gate: figure gate + Jekyll + Pagefind
npm run build

# Paper-note hard gate
python3 scripts/check_paper_reading_figures.py "paper-reading/Note.md"

# Paper-note visual quality audit
python3 scripts/audit_paper_reading_visuals.py "paper-reading/Note.md"

# Whole-repo paper gate with grandfathered legacy debt
npm run check:figures:gate

# Optional local server for visual inspection
bundle exec jekyll serve
```

With the configured baseurl, expect the served site under `/paper-notes/` rather than assuming `/`.

## Interpreting Paper Checks

- The hard figure checker returns nonzero for a new note below three original images or one generated diagram.
- The gate allows existing entries in `scripts/paper_reading_figure_debt.json` only if they do not regress.
- Do not add a new note to the debt baseline to make CI green.
- The visual audit reports `POLISH` without failing. Resolve obvious early-image, density, and explanation issues for newly edited notes.
- If a baseline entry now passes, remove that entry in the same focused change when safe.

## Browser QA

For visual changes, inspect at least:

- Home navigation and search modal
- `/wiki/` and one long wiki note
- `/paper-reading/`, including filters, sort, pagination, and one note
- Desktop width and a mobile width
- Table overflow, KaTeX, heading TOC, image zoom/source badges, and reading progress

Use the in-app browser or Chrome control skill when available. Do not claim visual verification from a build alone.

## Dependency Discipline

- Use `Gemfile.lock` and `package-lock.json` as the source of truth.
- Do not run broad dependency upgrades during unrelated content work.
- If dependencies are missing, install from the existing lockfiles without changing versions when authorized.
- Review any lockfile change as a product change, not incidental noise.

## Commit and Deploy

- Stage only files belonging to the requested change.
- Exclude Obsidian workspace state unless explicitly requested.
- Do not commit `_site/`, Pagefind output, `node_modules/`, `vendor/`, or preview screenshots.
- Do not edit or push `gh-pages` manually.
- Push to `main` only when the user asks. Relevant source changes trigger `.github/workflows/deploy-site.yml`.
- CI runs `npm ci`, the paper figure gate, Jekyll, Pagefind, adds `.nojekyll`, and force-pushes the generated site to `gh-pages`.
- Report the commit, push, or deployment result separately from local build success.
