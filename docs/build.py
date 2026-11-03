#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Build the docs/ GitHub Pages site.

The explainer HTML files in the project directories are body fragments (written
for the Artifact host, which supplies the <head>). For GitHub Pages they need a
real <head> — charset so Czech renders, a viewport, a title — so we wrap them
here. We also copy the compiled slide PDFs from latex/ into docs/pdf/.

Run after editing an explainer or rebuilding the slides:

    uv run docs/build.py

(Compile the LaTeX in latex/ first if you want fresh PDFs; missing PDFs are
skipped, leaving whatever is already committed in docs/pdf/.)
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# (fragment source, published name) — fragments follow symlinks to the latest
EXPLAINERS = [
    (ROOT / "wikidata" / "wikidata_explainer.html", "wikidata.html"),
    (ROOT / "patterns" / "patterns_explainer.html", "patterns.html"),
    (ROOT / "derivations" / "derivations_explainer.html", "derivations.html"),
    (ROOT / "sensebank" / "sensebank_explainer.html", "sensebank.html"),
    (ROOT / "images" / "arasaac_explainer.html", "arasaac.html"),
    (ROOT / "images" / "swatch_explainer.html", "swatch.html"),
    (ROOT / "LLM" / "llm_explainer.html", "llm.html"),
]
PDFS = [
    ROOT / "latex" / "slides" / "validation.pdf",
    ROOT / "latex" / "slides" / "literate.pdf",
    ROOT / "latex" / "report" / "report.pdf",
]

SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def title_of(fragment: str, fallback: str) -> str:
    """Use the fragment's <h1> text as the page <title>."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", fragment, re.DOTALL)
    text = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else fallback
    return f"{text} — JPC3 explainer"


def main() -> None:
    (DOCS / "explanations").mkdir(parents=True, exist_ok=True)
    (DOCS / "pdf").mkdir(parents=True, exist_ok=True)

    for src, dest in EXPLAINERS:
        body = src.read_text(encoding="utf-8")
        (DOCS / "explanations" / dest).write_text(
            SKELETON.format(title=title_of(body, dest), body=body), encoding="utf-8")
        print(f"wrote explanations/{dest}")

    for pdf in PDFS:
        if pdf.exists():
            shutil.copy2(pdf, DOCS / "pdf" / pdf.name)
            print(f"copied pdf/{pdf.name}")
        else:
            print(f"skip {pdf.name} (not built — compile the LaTeX first)")


if __name__ == "__main__":
    main()
