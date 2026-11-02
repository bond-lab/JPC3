---
name: literate-programming
description: Write and maintain literate programs (.lit.md) for the JPC3 course — tangle code out, weave HTML/PDF docs. Use when creating or editing a project's .lit.md, when its generated script needs regenerating, or when turning a plain snippet into a literate one.
---

# Literate programming (JPC3)

The repo keeps some project code as **literate programs**: a `.lit.md` with prose
and code interwoven is the source of truth. Code is tangled out of it; the
readable document is woven from it. Tools live in `litprog/`.

## When to use

- The user asks to make a snippet literate, or to edit a `.lit.md`.
- A `.lit.md` changed and its generated `.py` must be regenerated.
- The user wants an HTML/PDF explainer of a script.

## The format

Fenced code blocks carry labels in their info string:

- `` ```python {file=thing.py} `` — a chunk tangled to that path.
- `` ```python {#name} `` — a named chunk, reused elsewhere.
- Inside a chunk, a line that is only `<<name>>` expands that chunk, with its
  indentation prepended to every line (so Python stays aligned). A name used
  twice is concatenated in order.
- A `` ```mermaid `` block is a diagram.

Write the explanation *before* each chunk. Prefer many small named chunks over
one big block, so prose can interleave.

## Commands

```bash
uv run litprog/tangle.py <doc>.lit.md    # write the source file(s)
uv run litprog/weave.py  <doc>.lit.md    # write <doc>.html and <doc>.pdf
```

(From inside a project dir, use `../litprog/tangle.py` etc.)

## Rules

- The `.lit.md` is the single source of truth. After editing it, **re-tangle**
  so the `.py` matches, and **re-run** the script to confirm it still works.
- Never hand-edit a generated `.py` (it carries a note saying so); edit the
  `.lit.md` and tangle.
- Keep the tangled code passing `ruff` — the tangler preserves whatever spacing
  the chunks and root layout give, so put blank lines between top-level chunks.
- `weave.py` needs `pandoc`, `xelatex`, and network (Kroki for diagrams).

## Worked example

`wikidata/wikidata.lit.md` → `wikidata_to_czech.py` (+ `.html`/`.pdf`). Follow its
structure: intro, a Mermaid diagram of the pipeline, an assembly chunk that lists
`<<references>>`, then one named chunk per piece with prose above it.
