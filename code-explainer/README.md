# code-explainer

A repeatable recipe (and Claude Code skill) for turning a finished script into a
self-contained, interactive HTML explainer — background, intuition, a code tour,
and a quiz — in the style of Geoffrey Litt's *explain-diff*. It is generated
*from* the code, so the script stays a normal file with nothing to keep in sync.

- **The skill:** [`SKILL.md`](SKILL.md) — a readable copy. The repo also ships it,
  active for this project, at `.claude/skills/code-explainer/SKILL.md`.
- **Worked examples:** every starter script in the repo has one — seven in
  all, published on the course site under *Explainers*. The Wikidata one,
  [`../wikidata/wikidata_explainer.html`](../wikidata/wikidata_explainer.html),
  was built up interactively over `v0` → `v4` (the prompts are in
  [`../wikidata/README.md`](../wikidata/README.md)).

## The recipe

Point at a script → ask for background / intuition / code / quiz → read it → ask
for the next fix → keep each version (`…v0.html`, `…v1.html`, …) with a symlink
to the latest → publish and share one stable link.

## Checking an explainer

[`explainer_check.py`](explainer_check.py) lints a generated explainer against
its source — the mechanical half of the trust problem:

```bash
uv run explainer_check.py wikidata/wikidata_explainer.html wikidata/wikidata_to_czech.py
# add --no-net to skip the link check
```

It flags three things: identifiers quoted in `<pre>` code blocks that are absent
from the source (an invented name), `file:line` references past the end of the
file (the code moved), and links that return 404/410 or fail to connect. A clean
run is not a guarantee — read the prose too — but it catches the errors a reader
is least likely to spot. Put example output in
`<pre class="data">` and the checker skips it; remaining identifier hits can
still be false positives, so read them rather than trusting the exit code blindly.

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
