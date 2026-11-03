#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Lint an AI-generated code explainer against its source.

An explainer is generated and can hallucinate. This catches the three failure
modes a reader is least likely to notice by eye:

  1. identifiers quoted in <pre> code blocks that do not appear in the source
     (an invented function or variable name, or a typo);
  2. file:line references that point past the end of the file (the code moved);
  3. links that do not resolve (a wrong or invented URL).

It does not judge the prose — that still needs a human, or a second model. Think
of it as the mechanical half of guarding against a wrong explainer.

Usage:
    uv run explainer_check.py <explainer.html> <source.py> [more sources...]
    uv run explainer_check.py --no-net <explainer.html> <source.py>

Exit status is non-zero if anything is flagged.
"""
import html as html_mod
import re
import sys
from pathlib import Path

import requests

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")      # 3+ char identifiers
PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.DOTALL)
TAG = re.compile(r"<[^>]+>")
LINEREF = re.compile(r"([A-Za-z0-9_./-]+\.py):(\d+)(?:[–—\-](\d+))?")
HREF = re.compile(r'href="(https?://[^"]+)"')

# HTML/markup tokens that are not code claims, so never flag them
STOP = {"span", "code", "pre", "class", "href", "div", "the", "and", "for"}


def text_of(block: str) -> str:
    """Strip tags and unescape entities from an HTML fragment."""
    return html_mod.unescape(TAG.sub("", block))


def check_identifiers(doc: str, source: str) -> list[str]:
    """Identifiers inside <pre> code blocks that are absent from the source."""
    found: set[str] = set()
    for block in PRE.findall(doc):
        found.update(IDENT.findall(text_of(block)))
    return sorted(t for t in found if t not in STOP and t not in source)


def check_linerefs(doc: str, sources: list[Path]) -> list[str]:
    """file:line references that name an unknown file or fall past its end."""
    by_name = {s.name: s for s in sources}
    problems = []
    for m in LINEREF.finditer(doc):
        fname, lo = m.group(1), int(m.group(2))
        hi = int(m.group(3)) if m.group(3) else lo
        src = by_name.get(Path(fname).name)
        if src is None:
            problems.append(f"{fname}:{lo} — source not provided to the checker")
        else:
            n = len(src.read_text(encoding="utf-8").splitlines())
            if lo < 1 or hi > n:
                problems.append(f"{fname}:{lo}-{hi} — out of range ({src.name} has {n} lines)")
    return problems


def check_links(doc: str, timeout: int = 20) -> list[str]:
    """URLs that are genuinely missing (404/410) or unreachable.

    Many good sites (Wikimedia, GitHub) return 401/403/405/429 to bots; those
    mean "reachable but gated", not dead, so we don't flag them. Only a 404/410
    or a connection/DNS failure counts as a bad link.
    """
    ua = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) explainer-check/0.1"}
    dead = []
    for url in sorted(set(HREF.findall(doc))):
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True, headers=ua)
            if r.status_code in (401, 403, 405, 429) or r.status_code >= 500:
                r = requests.get(url, timeout=timeout, allow_redirects=True,
                                 headers=ua, stream=True)
            if r.status_code in (404, 410):
                dead.append(f"{url} -> HTTP {r.status_code}")
        except requests.RequestException as e:
            dead.append(f"{url} -> {type(e).__name__}")
    return dead


def main() -> None:
    net = "--no-net" not in sys.argv
    args = [a for a in sys.argv[1:] if a != "--no-net"]
    if len(args) < 2:
        sys.exit("usage: uv run explainer_check.py [--no-net] "
                 "<explainer.html> <source.py> [more sources...]")

    doc = Path(args[0]).read_text(encoding="utf-8")
    sources = [Path(a) for a in args[1:]]
    source_text = "\n".join(s.read_text(encoding="utf-8") for s in sources)

    sections = [
        ("Identifiers in code blocks not found in the source",
         check_identifiers(doc, source_text),
         "a hallucinated name or a typo — check each against the code"),
        ("Line references out of range",
         check_linerefs(doc, sources),
         "the code moved; fix the ref or regenerate"),
    ]
    if net:
        sections.append(("Links that did not resolve", check_links(doc),
                         "a wrong or invented URL"))

    total = 0
    for title, items, hint in sections:
        if items:
            total += len(items)
            print(f"\n{title} ({len(items)}):")
            for it in items:
                print(f"  - {it}")
            print(f"  => {hint}")

    if total == 0:
        tail = "identifiers and line refs" if not net else "identifiers, line refs, and links"
        print(f"OK: {tail} all check out.")
    else:
        print(f"\n{total} item(s) to review. (Identifier hits can be false "
              "positives — example data in a code block — so read, don't just trust.)")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
