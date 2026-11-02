#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Weave a `.lit.md` into HTML and PDF -- the readable half of litprog.

`tangle.py` pulls the *code* out of a literate document; `weave.py` makes the
*document* a human reads. Mermaid diagrams are rendered to images by the Kroki
web service (https://kroki.io) -- pure Python + requests, no node or chromium.

Needs `pandoc` on the PATH, and `xelatex` for the PDF.

Run:  uv run weave.py wikidata.lit.md     # -> wikidata.html and wikidata.pdf
"""
import subprocess
import sys
from pathlib import Path

import requests

KROKI = "https://kroki.io/mermaid"


def render(code: str, path: Path, fmt: str) -> None:
    """Render mermaid source to an image via Kroki (fmt: 'svg' or 'png')."""
    r = requests.post(f"{KROKI}/{fmt}", data=code.encode(), timeout=60)
    r.raise_for_status()
    path.write_bytes(r.content)


def preprocess(md: str, outdir: Path, stem: str, fmt: str) -> tuple[str, list[Path]]:
    """Replace each ```mermaid block with an image include, rendering it."""
    lines = md.splitlines()
    out: list[str] = []
    figs: list[Path] = []
    i = n = 0
    while i < len(lines):
        if lines[i].strip() == "```mermaid":
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence
            fig = outdir / f"{stem}-fig{n}.{fmt}"
            render("\n".join(body), fig, fmt)
            figs.append(fig)
            out.append(f"![diagram]({fig.name})")
            n += 1
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out), figs


def pandoc(args: list[str], cwd: Path) -> None:
    subprocess.run(["pandoc", *args], cwd=cwd, check=True)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run weave.py <document.lit.md>")
    doc = Path(sys.argv[1]).resolve()
    outdir = doc.parent
    stem = doc.name.replace(".lit.md", "") if doc.name.endswith(".lit.md") else doc.stem
    md = doc.read_text(encoding="utf-8")

    # HTML: SVG diagrams, embedded as data URIs -> one self-contained file.
    html_md, figs = preprocess(md, outdir, stem, "svg")
    tmp_html = outdir / f"{stem}.weave.md"
    tmp_html.write_text(html_md, encoding="utf-8")
    pandoc([tmp_html.name, "-s", "--embed-resources",
            "--metadata", f"title={stem} (literate)", "-o", f"{stem}.html"], outdir)

    # PDF: PNG diagrams (xelatex cannot embed SVG directly).
    pdf_md, figs_png = preprocess(md, outdir, stem, "png")
    tmp_pdf = outdir / f"{stem}.weave-pdf.md"
    tmp_pdf.write_text(pdf_md, encoding="utf-8")
    pandoc([tmp_pdf.name, "--pdf-engine=xelatex", "-V", "geometry:margin=2.5cm",
            "-V", "mainfont=TeX Gyre Pagella", "-o", f"{stem}.pdf"], outdir)

    for f in (tmp_html, tmp_pdf, *figs, *figs_png):
        f.unlink(missing_ok=True)
    print(f"wove {stem}.html and {stem}.pdf")


if __name__ == "__main__":
    main()
