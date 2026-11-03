---
name: code-explainer
description: Generate and interactively refine a self-contained, interactive HTML explainer for a code file — background, intuition, a code walkthrough, and a quiz — versioned v0/v1/… with a symlink to the latest and published as an Artifact. Use when asked to explain a script, build a code walkthrough, or refine an existing explainer.
---

# Code explainer (JPC3)

Turn a finished script into an HTML document a human can learn from. The
explainer is generated *from* the code, so the `.py` stays a normal file with
nothing to keep in sync — a lighter-weight answer to "make it understandable"
than literate programming. Modelled on Geoffrey Litt's *explain-diff*.

Worked example in this repo: `wikidata/wikidata_explainer.html` (and its
`.v0`/`.v1`/`.v2` snapshots).

## When to use

- "explain this script", "build a walkthrough", "make a code explainer".
- "refine the explainer" / a follow-up that changes an existing one.

## Structure

One continuous page with a table of contents:

1. **Background** — the domain, from beginner overview to the specifics this code
   needs. Define the terms.
2. **Intuition** — the core idea on concrete toy data, with a diagram (semantic
   HTML/CSS, never ASCII) and a small worked table.
3. **Code** — a walkthrough grouped by execution flow, each part with a
   `file:line` reference and the few lines that matter.
4. **Quiz** — ~5 medium multiple-choice questions on the substance (not wording).
   Shuffle the options on load; vary their length; show the reason either way.

Add appendices as asked (a SPARQL primer, a glossary, …).

## Build it

- Load the **`artifact-design`** skill before writing the page.
- Write a **self-contained** HTML file: inline CSS and JS, no external fonts,
  CDNs, or images. Light *and* dark via CSS-custom-property tokens
  (`prefers-color-scheme` + `:root[data-theme=…]`). Responsive. Code in `<pre>`
  with `overflow-x:auto; white-space:pre`.
- Ground every claim in the real code; use real examples and real numbers.
- The file is body content only (no `<!doctype>`/`<html>`/`<head>`/`<body>`) so
  the Artifact wrapper can host it; it still opens fine in a browser.

## Version it

Keep the history visible so readers see how it changed:

```
<name>.v0.html   <name>.v1.html   <name>.v2.html   ...
<name>.html  ->  symlink to the latest version
```

Each refinement is a **new** `vN` file; repoint the symlink; the live URL tracks
the symlink. Save a short note of the prompt that produced each version.

## Publish and refine

- Publish the symlink path as an Artifact. Re-publishing the **same file path**
  keeps the **same URL**, so you share the link once and keep improving behind it.
- To refine: read the feedback, edit into a new `vN`, repoint the symlink,
  re-publish. Repeat.

## Caveats (required)

An explainer is AI-generated and can be wrong — a misread line, an invented
detail, a stale number. Guard against it, in the page and in the process:

- Ground every claim in the real file; give `file:line` references the reader can
  open.
- Pin numbers to an actual run, or label them illustrative — never invent counts.
- Put a visible caveat near the top ("generated from the code; verify against the
  source; run it") and a short "How much to trust this" section.
- The quiz answers must follow from the code; where one disagrees, the code wins.
- Have a second reader — a person or another model — check it against the source
  before it is shared.
- Run `explainer_check.py` (in this skill's folder) after each revision — it
  flags identifiers, `file:line` refs, and links in the page that do not check
  out against the source. It is the mechanical half; the reader is the other.
- Stamp provenance in the page: the date it was generated, the model, and the
  source file's version (a commit hash or mtime), so staleness is visible.

## The recipe, in one line

Point at a script → ask for background/intuition/code/quiz → read it → ask for
the next fix → keep each version → link the latest.
