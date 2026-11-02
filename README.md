# JPC3 — Improving the Czech Wordnet / Open Multilingual Wordnet

Project course, based on the JPS3 task *Improve the Czech wordnet / Open
Multilingual Wordnet*. Teams of 1–2 pick one project and carry it through a
semester: roughly **2–3 months at 5–6 hours a week** (≈ 50–70 hours a team).

## What every project delivers

Whatever the topic, the report has the same four-part spine. It is baked into
the template in `docs/template/`:

1. **Extend** — produce the new data *semi-automatically*: an automatic step
   plus a human in the loop. Report how much you made against your numerical
   goal.
2. **Error analysis** — hand-check a random sample of ≥ 100 items, report
   precision, and (if two of you annotate) inter-annotator agreement. **Group
   the mistakes into types** — the categories matter more than the single
   number.
3. **Visualise & explain** — one figure that makes the change *and its errors*
   legible to someone who was not in the room.
4. **Release** — valid LMF that loads with the [`wn`](https://github.com/goodmami/wn)
   library, with a one-line data statement and a licence.

Write the report with `docs/template/report.tex` (Overleaf: upload the whole
`docs/template/` folder and press Recompile). It already has the Czech-diacritic
setup, Leipzig-style glosses, and the four sections stubbed.

## The projects

Numerical goals are **targets to size the work**, not pass/fail thresholds —
adjust once you see the data, and say in the report if you changed them.

### 1. Semi-automatic expansion of Czech-specific patterns (přechylování)

Add feminine / motion variants (*učitel → učitelka*) and other productive
Czech patterns the English-derived wordnet does not encode. The gender-bias
work on Open English Wordnet is the obvious comparison point.

- **Goal:** add variants to ≥ 500 animate/personal nouns; validate a
  100-item sample at ≥ 90 % precision.
- **Readings:** McCrae et al. (2025) *Remedying Gender Bias in Open English
  Wordnet* `[mccrae-etal2025gender]`; Pala & Smrž (2004) *Building Czech
  WordNet* `[palasmrz2004]`.

### 2. Adding derivational relations

Add derivational / morphosemantic links in the spirit of Pala & Hlaváčková,
drawing candidates from a word-formation resource such as DeriNet and
validating a sample.

- **Goal:** add ≥ 1000 derivational links across ≥ 3 relation types
  (e.g. agentive, diminutive, feminine-motion); validate 100 at ≥ 90 %.
- **Readings:** Stoyanova et al. (2025) *Expanding and Enhancing Derivational
  and Morphosemantic Relations in Princeton WordNet* `[stoyanova-etal2025derivational]`;
  Pala & Hlaváčková (2007) *Derivational Relations in Czech WordNet*
  `[pala-hlavackova2007]`. (See also DeriNet 2.0 `[derinet2019]`.)

### 3. Merging the PDT wordnet sense tags

The Prague Dependency Treebank is annotated with wordnet senses, but against an
**older version**. Map those sense tags onto the current synset inventory. The
real deliverable is the **residue**: the tags that don't map, categorised
(synset split / merged / renumbered / deleted / genuinely missing).

- **Goal:** attempt the full set of PDT wordnet tags; target ≥ 95 %
  automatically mapped; hand-categorise 100 of the unmapped residue.
- **Readings:** Daudé, Padró & Rigau (2000) *Mapping WordNets Using Structural
  Information* `[daude-etal2000]`; Bond et al. (2016) *CILI: the Collaborative
  Interlingual Index* `[bond-etal2016cili]`. (PDT 3.0: `[bejcek-etal2013pdt]`.)

### 4. Better links to ARASAAC and Global Symbols

Improve pictograph coverage for AAC: add colour variants, match more synsets,
and bring in sets from other countries (e.g. the Bulgarian and Croatian sets on
[Global Symbols](https://globalsymbols.com/)). Watch the per-set licences —
they differ — and report them.

- **Goal:** add images to ≥ 1000 (ideally high-frequency) synsets from ≥ 3
  symbol sets; validate appropriateness on a 100-item sample.
- **Readings:** Sevens (2018) *Words Divide, Pictographs Unite* `[sevens2018]`;
  Bond & Foster (2013) *Linking and Extending an Open Multilingual Wordnet*
  `[bond-foster2013]`. Resources: ARASAAC `[arasaac]`, Global Symbols
  `[globalsymbols]`.

## Further options (a fifth project, or swaps)

### 5. Wikidata → CILI → Czech

Start from Wikidata items that already carry an ILI/PWN mapping, pull their
Czech labels, project them onto the Czech wordnet, and verify. The residue —
Czech labels with no matching synset — is a ranked list of candidate gaps.

- **Goal:** project ≥ 2000 labels; verify a 100-item sample.
- **Readings:** Vrandečić & Krötzsch (2014) *Wikidata* `[vrandecic-krotzsch2014]`;
  Bond et al. (2016) `[bond-etal2016cili]`.

### 6. LLM-assisted quality estimation, grounded in Wikidata

Have an LLM flag suspicious synset members / glosses **with a rationale**, using
the Wikidata label and description (from project 5) as evidence rather than
free generation. Then verify a sample and report the LLM's precision. Pairs
well with project 5.

- **Goal:** score ≥ 1000 synsets; verify a 100-item sample; report precision
  of the flag against human judgement.
- **Readings:** as for project 5, plus a paper you find on LLMs for lexical
  resource curation.

## Layout

```
docs/template/     report.tex, report.bib — the shared report skeleton
```
