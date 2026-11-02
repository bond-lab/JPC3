# Project 5 — Wikidata → ILI → Czech

Find concepts that Wikidata links to a wordnet synset, carry a Czech label, and
ask whether the Czech wordnet already has them. The ones it doesn't are ranked
candidates — either a missing lemma on an existing synset, or a missing synset.

## The bridge

Two Wikidata properties get you to an ILI; we use both and prefer the first:

| Property | Meaning | Value | Items | …with `cs` label |
|---|---|---|---|---|
| `P5063` | Interlingual Index ID | `i46360` (an ILI) | ~19.6k | ~14.2k |
| `P8814` | WordNet 3.1 Synset ID | `02086723-n` | ~34.9k | ~25.6k |

`P5063` is the ILI directly. `P8814` is a WordNet **3.1** offset, mapped to an
ILI via the Collaborative Interlingual Index table
[`ili-map-pwn31.tab`](https://github.com/globalwordnet/cili). Do **not** map
through `omw-en:2.0` — that is WordNet 3.0 and the offsets don't line up (every
lookup misses). The Czech NTU-MC synsets expose ILIs
(`cs.synsets(ili="i46360")`), so ILI is the common key.

## Literate version

This project doubles as the worked example for *literate programming* (the
explainers idea from the validation lecture; see [`../litprog/`](../litprog/)).
The real source is [`wikidata.lit.md`](wikidata.lit.md) — prose and a diagram
first, code in named chunks. The tooling lives in `../litprog/`:

```bash
uv run ../litprog/tangle.py wikidata.lit.md   # -> wikidata_to_czech.py (code)
uv run ../litprog/weave.py  wikidata.lit.md   # -> wikidata.html + wikidata.pdf (doc)
```

So `wikidata_to_czech.py` is **generated**; edit the `.lit.md` and re-tangle.
`weave.py` renders the Mermaid diagram via [Kroki](https://kroki.io) and builds a
self-contained HTML and a PDF. GitHub also renders the `.lit.md` with the diagram
inline.

## Run

```bash
uv run wikidata_to_czech.py            # demo, LIMIT 500
uv run wikidata_to_czech.py 5000 candidates.tsv
```

It writes `kind, qid, wn31, ili, wikidata_cs, czech_lemmas`, where `kind` is:
`present`, `missing-lemma` (candidate lemma), `missing-synset` (candidate
synset), or `no-ili`.

## Error-analysis / explainability notes

- A first sweep is dominated by **named entities** — countries, cities, people
  (*Lesotho*, *Boston*, *Mahátma Gándhí*). Many are legitimately absent from a
  general wordnet. Filter them out (e.g. drop synsets reached by
  `instance_hypernym`, or English `noun.person`/`noun.location` proper-noun
  synsets) to surface genuine **common-noun** gaps, and report how many you
  dropped and why.
- `missing-lemma` is the richer vein for this course: *Nizozemsko* vs the Czech
  synset's *Holandsko* (a synonym to add), *pes domácí* vs *pes* (a variant).
- Verify a random 100 by hand: is the Wikidata Czech label really a synonym for
  that sense, or has Wikidata linked a near-neighbour? That precision number,
  broken down by `kind`, is your headline result.

## Scale it up

`LIMIT 5000` is a demo. For the whole set, page with `LIMIT`/`OFFSET`, or add a
`VALUES` clause to restrict to common nouns. Always send a real `User-Agent`
(WDQS rejects anonymous bulk traffic).
