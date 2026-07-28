#!/usr/bin/env python3
"""Audit whether paper-reading notes feel visually rich enough."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

from check_paper_reading_figures import (
    MIN_GENERATED,
    MIN_ORIGINAL,
    HTML_IMG_RE,
    MARKDOWN_IMAGE_RE,
    ImageRef,
    iter_note_paths,
    rel,
    source_kind,
)


ROOT = Path(__file__).resolve().parents[1]
EARLY_IMAGE_OFFSET = 2600
EARLY_IMAGE_RATIO = 0.32
MAX_CHARS_PER_FIGURE = 2200
MIN_EXPLAINED_RATIO = 0.7


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class LocatedImage:
    ref: ImageRef
    start: int
    end: int
    kind: str


@dataclass(frozen=True)
class VisualAudit:
    path: Path
    body_chars: int
    original: int
    generated: int
    unknown: int
    total: int
    first_image_offset: int | None
    first_image_ratio: float | None
    chars_per_figure: float | None
    explained_ratio: float
    issues: tuple[str, ...]

    @property
    def status(self) -> str:
        if any(issue.startswith("missing-") for issue in self.issues):
            return "COUNT_DEBT"
        if self.issues:
            return "POLISH"
        return "OK"


def strip_frontmatter(markdown: str) -> str:
    if markdown.startswith("---"):
        end = markdown.find("\n---", 3)
        if end != -1:
            return markdown[end + 4 :]
    return markdown


def body_char_count(markdown: str) -> int:
    text = strip_frontmatter(markdown)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = MARKDOWN_IMAGE_RE.sub("", text)
    text = HTML_IMG_RE.sub("", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return len(re.sub(r"\s+", "", text))


def parse_markdown_attr(markdown: str, image_end_offset: int) -> str:
    line_end = image_end_offset
    while line_end < len(markdown) and markdown[line_end] not in "\n\r":
        line_end += 1
    next_start = line_end
    while next_start < len(markdown) and markdown[next_start] in "\n\r":
        next_start += 1
    next_end = next_start
    while next_end < len(markdown) and markdown[next_end] not in "\n\r":
        next_end += 1
    next_line = markdown[next_start:next_end]
    match = re.match(r"^\s*\{:\s*([^}]+)\}\s*$", next_line)
    return match.group(1) if match else ""


def parse_html_attrs(tag: str) -> dict[str, str]:
    return {
        match.group(1).lower(): match.group(3)
        for match in re.finditer(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(['\"])(.*?)\2", tag, re.DOTALL)
    }


def located_images(markdown: str) -> list[LocatedImage]:
    images: list[LocatedImage] = []
    for match in MARKDOWN_IMAGE_RE.finditer(markdown):
        ref = ImageRef(match.group(1).strip(), parse_markdown_attr(markdown, match.end()))
        images.append(LocatedImage(ref=ref, start=match.start(), end=match.end(), kind=source_kind(ref)))

    for match in HTML_IMG_RE.finditer(markdown):
        attrs = parse_html_attrs(match.group(0))
        src = attrs.get("src", "").strip()
        if not src:
            continue
        ref = ImageRef(src, " ".join(f"{key}={value}" for key, value in attrs.items()))
        images.append(LocatedImage(ref=ref, start=match.start(), end=match.end(), kind=source_kind(ref)))

    return sorted(images, key=lambda image: image.start)


def image_has_explanation(markdown: str, image: LocatedImage, next_start: int | None) -> bool:
    window_end = min(len(markdown), image.end + 900)
    if next_start is not None:
        window_end = min(window_end, next_start)
    after = markdown[image.end:window_end]
    after = re.sub(r"^\s*\{:\s*[^}]+\}\s*", "", after)
    after = re.sub(r"```[\s\S]*?```", "", after)
    after = re.sub(r"<[^>]+>", "", after)
    after = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", after)
    compact = re.sub(r"\s+", "", after)
    return len(compact) >= 60


def audit_note(path: Path) -> VisualAudit:
    markdown = path.read_text(encoding="utf-8")
    images = located_images(markdown)
    body_chars = body_char_count(markdown)
    original = sum(1 for image in images if image.kind == "original")
    generated = sum(1 for image in images if image.kind == "generated")
    unknown = sum(1 for image in images if image.kind == "unknown")
    total = len(images)
    first_offset = images[0].start if images else None
    first_ratio = first_offset / max(len(markdown), 1) if first_offset is not None else None
    chars_per_figure = body_chars / total if total else None

    explained = 0
    for index, image in enumerate(images):
        next_start = images[index + 1].start if index + 1 < len(images) else None
        if image_has_explanation(markdown, image, next_start):
            explained += 1
    explained_ratio = explained / total if total else 0.0

    issues: list[str] = []
    if original < MIN_ORIGINAL:
        issues.append(f"missing-original:{MIN_ORIGINAL - original}")
    if generated < MIN_GENERATED:
        issues.append(f"missing-generated:{MIN_GENERATED - generated}")
    if total == 0:
        issues.append("no-figures")
    elif first_offset is not None and first_ratio is not None:
        if first_offset > EARLY_IMAGE_OFFSET and first_ratio > EARLY_IMAGE_RATIO:
            issues.append("first-figure-too-late")
    if chars_per_figure is not None and chars_per_figure > MAX_CHARS_PER_FIGURE:
        issues.append("low-visual-density")
    if total and explained_ratio < MIN_EXPLAINED_RATIO:
        issues.append("weak-figure-explanations")
    if unknown:
        issues.append(f"unknown-source:{unknown}")

    return VisualAudit(
        path=path,
        body_chars=body_chars,
        original=original,
        generated=generated,
        unknown=unknown,
        total=total,
        first_image_offset=first_offset,
        first_image_ratio=first_ratio,
        chars_per_figure=chars_per_figure,
        explained_ratio=explained_ratio,
        issues=tuple(issues),
    )


def format_optional_number(value: float | int | None, precision: int = 1) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{precision}f}"
    return str(value)


def write_markdown_report(audits: list[VisualAudit], output: Path) -> None:
    status_order = {"COUNT_DEBT": 0, "POLISH": 1, "OK": 2}
    sorted_audits = sorted(audits, key=lambda audit: (status_order[audit.status], rel(audit.path)))
    lines = [
        "# Paper Reading Visual Audit",
        "",
        f"- Generated: {dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Hard rule: at least {MIN_ORIGINAL} original figures/screenshots + {MIN_GENERATED} generated/self-made diagram.",
        f"- Polish checks: first figure before {EARLY_IMAGE_OFFSET} chars or {EARLY_IMAGE_RATIO:.0%} of the note, "
        f"<= {MAX_CHARS_PER_FIGURE} body chars per figure, >= {MIN_EXPLAINED_RATIO:.0%} figures followed by explanation.",
        "",
        "| Status | Note | Original | Generated | Total | Chars/Fig | Explained | Issues |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for audit in sorted_audits:
        issues = ", ".join(audit.issues) if audit.issues else "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    audit.status,
                    rel(audit.path),
                    str(audit.original),
                    str(audit.generated),
                    str(audit.total),
                    format_optional_number(audit.chars_per_figure, 0),
                    f"{audit.explained_ratio:.0%}",
                    issues,
                ]
            )
            + " |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(audits: list[VisualAudit]) -> None:
    counts = {"OK": 0, "POLISH": 0, "COUNT_DEBT": 0}
    for audit in audits:
        counts[audit.status] += 1

    print(
        f"OK={counts['OK']} POLISH={counts['POLISH']} COUNT_DEBT={counts['COUNT_DEBT']} "
        f"TOTAL={len(audits)}"
    )
    for audit in sorted(audits, key=lambda item: (item.status != "COUNT_DEBT", item.status, rel(item.path))):
        if audit.status == "OK":
            continue
        print(
            f"{audit.status:10} original={audit.original} generated={audit.generated} "
            f"total={audit.total} chars/fig={format_optional_number(audit.chars_per_figure, 0)} "
            f"explained={audit.explained_ratio:.0%} {rel(audit.path)} "
            f"[{', '.join(audit.issues)}]"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Markdown files to audit. Defaults to paper-reading/*.md.")
    parser.add_argument("--report", help="Optional Markdown report path.")
    args = parser.parse_args()

    audits = [audit_note(path) for path in iter_note_paths(args.paths)]
    print_summary(audits)

    if args.report:
        output = Path(args.report)
        if not output.is_absolute():
            output = ROOT / output
        write_markdown_report(audits, output)
        print(f"Wrote {display_path(output)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
