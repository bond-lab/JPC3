# Project 2 — Derivational relations

Add derivational / morphosemantic links (agentive, diminutive, feminine-motion,
…) in the spirit of Pala & Hlaváčková, drawing candidates from a word-formation
resource and **validating** them — the validation is the project.

## Candidates are cheap; judging them is the work

[DeriNet](https://ufal.mff.cuni.cz/derinet) already encodes Czech word-formation
families, so generating candidate links is mostly a join: for each DeriNet
parent→child edge where both lemmas appear in the Czech wordnet, propose a
derivational relation between their synsets. A string-suffix heuristic (below)
is a quick stand-in to see the shape of the data before you wire in DeriNet.

The heuristic is in [`feminine_candidates.py`](feminine_candidates.py):

```bash
uv run feminine_candidates.py 40      # the first 40 base -> feminine pairs
```

This over-generates wildly (*pes* → *peska*? no; *past* → *pastka*? different
sense) — which is the point: the candidate list is trivial, so the deliverable
is how well you can **tell the real derivations from the coincidences**.

## The validation is the deliverable

- Judge a random sample (aim for ≥ 200, not just 100) by hand: is this a genuine
  derivational relation, and is the relation *type* right?
- Two annotators → report Cohen's κ and how you resolved disagreements.
- **Group the errors into types** with counts and one real example each
  (wrong type, false friend / coincidental suffix, cross-sense, non-derived
  compound). That taxonomy is what the next team builds on.
- Report precision **per relation type** and per candidate source (DeriNet vs
  heuristic) — they will differ, and saying how is the interesting result.

## Readings

Stoyanova et al. (2025); Pala & Hlaváčková (2007); DeriNet 2.3. Keys in the
top-level `README.md`.
