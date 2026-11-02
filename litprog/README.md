# Literate programming for JPC3

A *literate program* (Knuth, 1984) is written for a human to read: prose and
code interwoven, explanation before implementation. The code is pulled out
("tangled") to run; the document is rendered ("woven") to read.

Why here: in these projects the extraction is scaffolded and the hard part is
*understanding* what the data says (see the validation lecture — "understanding
is the new bottleneck"). A literate script makes the reasoning the main text and
the code a consequence of it. The report you hand in is itself the literate
layer over your pipeline.

## The two tools

| Tool | Does | Run |
|---|---|---|
| [`tangle.py`](tangle.py) | pulls source files **out** of a `.lit.md` | `uv run tangle.py doc.lit.md` |
| [`weave.py`](weave.py) | renders the `.lit.md` to **HTML + PDF** | `uv run weave.py doc.lit.md` |

Both are short, dependency-light, and run with `uv` — no node, no chromium.
`weave.py` renders Mermaid diagrams through the [Kroki](https://kroki.io) web
service (needs network); the PDF also needs `pandoc` and `xelatex`.

## The `.lit.md` format

Plain Markdown, plus two conventions in fenced code blocks:

- A **file chunk** is written to disk when you tangle:
  ````
  ```python {file=thing.py}
  <<imports>>
  <<main>>
  ```
  ````
- A **named chunk** is defined once and reused:
  ````
  ```python {#imports}
  import sys
  ```
  ````
- Inside any chunk, a line that is only `<<name>>` is replaced by that chunk,
  with its indentation preserved — so Python blocks stay aligned. A name used
  more than once is concatenated in order, which lets prose interleave the
  pieces of one function.
- A ```` ```mermaid ```` block is a diagram; `weave.py` renders it, and GitHub
  shows it inline.

Keep the `.lit.md` as the single source of truth: edit it, then re-tangle so the
`.py` stays in step. The generated script carries a one-line note saying so.

## Worked example

[`../wikidata/wikidata.lit.md`](../wikidata/wikidata.lit.md) → tangles to
`wikidata_to_czech.py`, weaves to `wikidata.html` / `wikidata.pdf`. Read it to
see the format in use.

## Using it as a skill

The Claude Code skill in `.claude/skills/literate-programming/` tells the agent
when and how to use these tools, so you can ask it to "make this snippet
literate" or "re-tangle and weave" and it will follow the same conventions.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) for running the scripts
- `pandoc` and `xelatex` for `weave.py` (the PDF)
- network access for Kroki (diagram rendering)
