#!/usr/bin/env python3
"""Validate visual evidence requirements for paper-reading notes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PAPER_READING_DIR = ROOT / "paper-reading"
MIN_ORIGINAL = 3
MIN_GENERATED = 1


MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\n]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(['\"])(.*?)\2", re.DOTALL)
CLASS_ATTR_RE = re.compile(r"^\s*\{:\s*([^}]+)\}\s*$")


@dataclass(frozen=True)
class ImageRef:
    src: str
    attrs: str = ""


@dataclass(frozen=True)
class FigureCounts:
    original: int
    generated: int
    unknown: int
    total: int

    @property
    def passes(self) -> bool:
        return self.original >= MIN_ORIGINAL and self.generated >= MIN_GENERATED


def iter_note_paths(paths: list[str]) -> list[Path]:
    if paths:
        candidates = [Path(path) for path in paths]
    else:
        candidates = sorted(PAPER_READING_DIR.glob("*.md"))

    note_paths: list[Path] = []
    for path in candidates:
        path = path if path.is_absolute() else ROOT / path
        if path.name == "index.md":
            continue
        if path.suffix != ".md":
            continue
        note_paths.append(path)
    return note_paths


def parse_attr_line(lines: list[str], image_end_offset: int) -> str:
    line_end = image_end_offset
    while line_end < len(lines) and lines[line_end] not in "\n\r":
        line_end += 1
    next_start = line_end
    while next_start < len(lines) and lines[next_start] in "\n\r":
        next_start += 1
    next_end = next_start
    while next_end < len(lines) and lines[next_end] not in "\n\r":
        next_end += 1
    next_line = lines[next_start:next_end]
    match = CLASS_ATTR_RE.match(next_line)
    return match.group(1) if match else ""


def extract_html_attrs(tag: str) -> dict[str, str]:
    return {match.group(1).lower(): match.group(3) for match in ATTR_RE.finditer(tag)}


def extract_images(markdown: str) -> list[ImageRef]:
    images: list[ImageRef] = []

    for match in MARKDOWN_IMAGE_RE.finditer(markdown):
        raw_src = match.group(1).strip()
        images.append(ImageRef(src=raw_src, attrs=parse_attr_line(markdown, match.end())))

    for match in HTML_IMG_RE.finditer(markdown):
        attrs = extract_html_attrs(match.group(0))
        src = attrs.get("src", "").strip()
        if src:
            attr_text = " ".join(f"{key}={value}" for key, value in attrs.items())
            images.append(ImageRef(src=src, attrs=attr_text))

    return images


def source_kind(image: ImageRef) -> str:
    attrs = image.attrs.lower()
    src = image.src.lower().strip("<>").strip()

    if "figure-generated" in attrs or "data-source=generated" in attrs or 'data-source="generated"' in attrs:
        return "generated"
    if "figure-original" in attrs or "data-source=original" in attrs or 'data-source="original"' in attrs:
        return "original"

    if re.search(r"\.svg(?:$|[\s'\"}|?#)])", src):
        return "generated"
    if re.search(r"\.(?:png|jpe?g|webp|gif)(?:$|[\s'\"}|?#)])", src):
        return "original"
    return "unknown"


def count_figures(path: Path) -> FigureCounts:
    images = extract_images(path.read_text(encoding="utf-8"))
    kinds = [source_kind(image) for image in images]
    return FigureCounts(
        original=kinds.count("original"),
        generated=kinds.count("generated"),
        unknown=kinds.count("unknown"),
        total=len(kinds),
    )


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_baseline(path: Path | None) -> dict[str, dict[str, int]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("allowed_debt", {})


def write_baseline(path: Path, counts_by_path: dict[str, FigureCounts]) -> None:
    allowed_debt = {
        note: {
            "original": counts.original,
            "generated": counts.generated,
            "unknown": counts.unknown,
            "total": counts.total,
        }
        for note, counts in sorted(counts_by_path.items())
        if not counts.passes
    }
    data = {
        "description": (
            "Temporary baseline for legacy paper-reading notes that predate the "
            "3 original figures + 1 generated diagram requirement. New notes or "
            "regressions must not be added here; remove entries as notes are backfilled."
        ),
        "min_original": MIN_ORIGINAL,
        "min_generated": MIN_GENERATED,
        "allowed_debt": allowed_debt,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_counts(counts: FigureCounts) -> str:
    return (
        f"original={counts.original}/{MIN_ORIGINAL}, "
        f"generated={counts.generated}/{MIN_GENERATED}, "
        f"unknown={counts.unknown}, total={counts.total}"
    )


def validate(paths: Iterable[Path], baseline: dict[str, dict[str, int]]) -> tuple[int, dict[str, FigureCounts]]:
    failures: list[str] = []
    legacy_debt: list[str] = []
    resolved_debt: list[str] = []
    counts_by_path: dict[str, FigureCounts] = {}

    for path in paths:
        note = rel(path)
        counts = count_figures(path)
        counts_by_path[note] = counts

        if counts.passes:
            if note in baseline:
                resolved_debt.append(note)
            continue

        if note in baseline:
            previous = baseline[note]
            regressed = (
                counts.original < int(previous.get("original", 0))
                or counts.generated < int(previous.get("generated", 0))
                or counts.total < int(previous.get("total", 0))
            )
            if regressed:
                failures.append(f"{note}: regressed from baseline; {format_counts(counts)}")
            else:
                legacy_debt.append(f"{note}: {format_counts(counts)}")
            continue

        failures.append(f"{note}: {format_counts(counts)}")

    if failures:
        print("Paper-reading figure requirement failed:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        print(
            f"Requirement: at least {MIN_ORIGINAL} original figures/screenshots and "
            f"{MIN_GENERATED} generated/self-made diagram per paper-reading note.",
            file=sys.stderr,
        )

    if legacy_debt:
        print("Legacy figure debt still allowed by baseline:")
        for item in legacy_debt:
            print(f"  - {item}")

    if resolved_debt:
        print("These notes now pass; remove them from the figure debt baseline:")
        for item in resolved_debt:
            print(f"  - {item}")

    return (1 if failures else 0), counts_by_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Markdown files to check. Defaults to paper-reading/*.md.")
    parser.add_argument("--baseline", help="JSON baseline of existing allowed figure debt.")
    parser.add_argument("--write-baseline", help="Write a baseline JSON file from current failures.")
    args = parser.parse_args()

    paths = iter_note_paths(args.paths)
    baseline_path = Path(args.baseline) if args.baseline else None
    if baseline_path and not baseline_path.is_absolute():
        baseline_path = ROOT / baseline_path
    baseline = load_baseline(baseline_path)

    exit_code, counts_by_path = validate(paths, baseline)

    if args.write_baseline:
        output = Path(args.write_baseline)
        if not output.is_absolute():
            output = ROOT / output
        write_baseline(output, counts_by_path)
        print(f"Wrote {output.relative_to(ROOT)}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
