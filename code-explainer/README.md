# code-explainer

A repeatable recipe (and Claude Code skill) for turning a finished script into a
self-contained, interactive HTML explainer — background, intuition, a code tour,
and a quiz — in the style of Geoffrey Litt's *explain-diff*. It is generated
*from* the code, so the script stays a normal file with nothing to keep in sync.

- **The skill:** [`SKILL.md`](SKILL.md) — a readable copy. The repo also ships it,
  active for this project, at `.claude/skills/code-explainer/SKILL.md`.
- **Worked example:**
  [`../wikidata/wikidata_explainer.html`](../wikidata/wikidata_explainer.html),
  built up interactively over `v0` → `v1` → `v2` (the prompts are in
  [`../wikidata/README.md`](../wikidata/README.md)).

## The recipe

Point at a script → ask for background / intuition / code / quiz → read it → ask
for the next fix → keep each version (`…v0.html`, `…v1.html`, …) with a symlink
to the latest → publish and share one stable link.

## Make it available elsewhere

Claude Code auto-discovers skills under a skills directory:

```bash
# one project (everyone who clones it gets the skill):
mkdir -p <project>/.claude/skills/code-explainer
cp code-explainer/SKILL.md <project>/.claude/skills/code-explainer/SKILL.md

# or for yourself, in every project:
mkdir -p ~/.claude/skills/code-explainer
cp code-explainer/SKILL.md ~/.claude/skills/code-explainer/SKILL.md
```

Then ask: "explain this script", or "refine the explainer".
