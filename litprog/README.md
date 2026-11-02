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

**Show the output, don't just describe it.** End the document with a "What it
produces" section holding a *real* run — console output and a few output rows —
as a plain ```` ```text ```` block (no chunk label, so it is woven but not
tangled). Seeing the result is part of understanding it. Prefer formats a human
can open — TOML, CSV, JSON — over opaque dumps; the output is there to be read.

## Worked example

[`../wikidata/wikidata.lit.md`](../wikidata/wikidata.lit.md) → tangles to
`wikidata_to_czech.py`, weaves to `wikidata.html` / `wikidata.pdf`. Read it to
see the format in use.

## Using it as a Claude Code skill

A [Claude Code](https://docs.claude.com/en/docs/claude-code) *skill* teaches the
agent when and how to use these tools, so you can ask it to "make this snippet
literate" or "re-tangle and weave" and it follows the same conventions. The
skill is [`SKILL.md`](SKILL.md) in this directory (a readable copy); the repo
also ships it, already active for this project, at
`.claude/skills/literate-programming/SKILL.md`.

**To make it available elsewhere**, copy `SKILL.md` into a `literate-programming/`
folder under a skills directory — Claude Code auto-discovers it:

```bash
# for one project (everyone who clones that repo gets it):
mkdir -p <project>/.claude/skills/literate-programming
cp litprog/SKILL.md <project>/.claude/skills/literate-programming/SKILL.md

# or for yourself, in every project on your machine:
mkdir -p ~/.claude/skills/literate-programming
cp litprog/SKILL.md ~/.claude/skills/literate-programming/SKILL.md
```

Restart Claude Code (or `/doctor` to check) and it will list
`literate-programming` among its skills. The skill assumes `litprog/tangle.py`
and `litprog/weave.py` are reachable, so keep this folder alongside it or adjust
the paths in `SKILL.md`.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) for running the scripts
- `pandoc` and `xelatex` for `weave.py` (the PDF)
- network access for Kroki (diagram rendering)
