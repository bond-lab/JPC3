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

# Injected into the HTML <head>. The key line is `pre { overflow-x: auto }`,
# so long code lines scroll inside their block instead of being clipped.
HTML_CSS = """<style>
body{max-width:52rem;margin:2rem auto;padding:0 1rem;line-height:1.5;
     font-family:"TeX Gyre Pagella",Palatino,Georgia,serif;color:#1a1a1a}
code,pre{font-family:Inconsolata,"DejaVu Sans Mono",monospace}
pre{overflow-x:auto;background:#f6f6f6;padding:.8em 1em;border-radius:6px;font-size:.9em}
pre>code{white-space:pre}
h1,h2{line-height:1.2}
h2{margin-top:2em;border-bottom:1px solid #ddd;padding-bottom:.2em}
a{color:#8b0000}
:not(pre)>code{background:#f0f0f0;padding:.1em .3em;border-radius:3px}
img{max-width:100%}
</style>
"""


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
    # A stylesheet in the head makes long code lines scroll, not clip.
    html_md, figs = preprocess(md, outdir, stem, "svg")
    tmp_html = outdir / f"{stem}.weave.md"
    tmp_html.write_text(html_md, encoding="utf-8")
    css = outdir / f"{stem}.weave-css.html"
    css.write_text(HTML_CSS, encoding="utf-8")
    pandoc([tmp_html.name, "-s", "--embed-resources", "--include-in-header", css.name,
            "--metadata", f"title={stem} (literate)", "-o", f"{stem}.html"], outdir)

    # PDF: PNG diagrams. The HTML above uses vector SVG; for the PDF we embed a
    # raster PNG on purpose. A faithful *vector* PDF of a Mermaid diagram needs a
    # real renderer (inkscape / mermaid-cli / graphviz) -- the pure-Python
    # SVG->PDF converters drop or mis-space Mermaid's labels. PNG stays faithful.
    pdf_md, figs_png = preprocess(md, outdir, stem, "png")
    tmp_pdf = outdir / f"{stem}.weave-pdf.md"
    tmp_pdf.write_text(pdf_md, encoding="utf-8")
    pandoc([tmp_pdf.name, "--pdf-engine=xelatex", "-V", "geometry:margin=2.5cm",
            "-V", "mainfont=TeX Gyre Pagella", "-o", f"{stem}.pdf"], outdir)

    for f in (tmp_html, tmp_pdf, css, *figs, *figs_png):
        f.unlink(missing_ok=True)
    print(f"wove {stem}.html and {stem}.pdf")


if __name__ == "__main__":
    main()
