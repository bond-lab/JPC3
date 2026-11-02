#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""A tiny noweb-style tangler: extract source files from a `.lit.md`.

A literate document weaves prose and code. This pulls the code back out.

Code chunks are fenced blocks tagged in their info string:

    ```python {file=wikidata_to_czech.py}   # a chunk written to this path
    ```python {#load-the-cili-map}          # a named chunk, reused by others

Inside any chunk, a line that is only `<<name>>` (at any indentation) is
replaced by the named chunk, with the indentation prepended to every line --
so Python blocks stay aligned. A name used more than once is concatenated in
order of appearance, which lets prose interleave the pieces of one function.

Run:  uv run tangle.py wikidata.lit.md
"""
import re
import stat
import sys
from pathlib import Path

HEADER = re.compile(r"^```[\w-]*\s*\{(#|file=)([^}]*)\}\s*$")
REF = re.compile(r"^(\s*)<<([^>]+)>>\s*$")


def parse(md: str) -> tuple[dict[str, list[str]], list[str]]:
    """Return (chunks by name, list of file paths), from a literate document."""
    chunks: dict[str, list[str]] = {}
    files: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        m = HEADER.match(lines[i])
        if not m:
            i += 1
            continue
        kind, label = m.group(1), m.group(2).strip()
        i += 1
        body: list[str] = []
        while i < len(lines) and not lines[i].startswith("```"):
            body.append(lines[i])
            i += 1
        i += 1  # skip the closing fence
        chunks.setdefault(label, []).extend(body)
        if kind == "file=" and label not in files:
            files.append(label)
    return chunks, files


def expand(name: str, chunks: dict[str, list[str]], seen: tuple = ()) -> list[str]:
    """Recursively expand a chunk, preserving indentation at <<ref>> sites."""
    if name in seen:
        raise ValueError(f"recursive chunk <<{name}>>")
    if name not in chunks:
        raise KeyError(f"undefined chunk <<{name}>>")
    out: list[str] = []
    for line in chunks[name]:
        ref = REF.match(line)
        if ref:
            indent, target = ref.group(1), ref.group(2).strip()
            for sub in expand(target, chunks, seen + (name,)):
                out.append(indent + sub if sub else sub)
        else:
            out.append(line)
    return out


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run tangle.py <document.lit.md>")
    doc = Path(sys.argv[1])
    chunks, files = parse(doc.read_text(encoding="utf-8"))
    if not files:
        sys.exit("no {file=...} chunks found")
    for path in files:
        text = "\n".join(expand(path, chunks)) + "\n"
        dest = doc.parent / path
        dest.write_text(text, encoding="utf-8")
        if text.startswith("#!"):          # make shebang scripts executable
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"tangled {path} ({text.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
