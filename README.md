# JPC3 — Improving the Czech Wordnet / Open Multilingual Wordnet

Project course, our overall goal will be to  *Improve the Czech wordnet*. Teams of 1–2 pick one project and carry it through a
semester: roughly **2–3 months at 5–6 hours a week** (≈ 50–70 hours a team).

We start with this wordnet: <https://github.com/bond-lab/NTUMC/releases/download/2026.08/wn-ntumc-ces.xml>

New here? See [`docs/setup.md`](docs/setup.md) to install `uv` and prime the
wordnet database once.

## What every project delivers

Whatever the topic, the report has the same four-part spine. It is baked into
the template in `docs/template/`:

1. **Extend** — produce the new data *semi-automatically*: an automatic step
   plus a human in the loop.
2. **Validate** — this is the heart of the project and where the marks are.
   Hand-check a random sample (aim for ≥ 200), report precision, and — since
   you work in pairs — inter-annotator agreement (Cohen's κ) with a sentence on
   how you resolved disagreements. **Group the mistakes into types**, with
   counts and one real example each: the error taxonomy matters more than the
   single number, because it is what the next team acts on.
3. **Visualise & explain** — one figure that makes the change *and its errors*
   legible to someone who was not in the room.
4. **Release** — valid LMF that loads with the [`wn`](https://github.com/goodmami/wn)
   library, with a one-line data statement and a licence.

Each project directory ships starter code that does most of the **Extend**
mechanics (candidate generation, the ILI bridge, API calls). That is
deliberate: extraction is the easy part now, so the weight of the work — and of
the grade — sits on **validation and error analysis**. A big pile of unchecked
candidates is not a result; a carefully judged sample with an honest error
taxonomy is.

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
- **Stretch:** add national/adjectives/language adverbials (Česko/český/česky)
- **Readings:** McCrae et al. (2025) *Remedying Gender Bias in Open English
  Wordnet* `[mccrae-etal2025gender]`; Pala & Smrž (2004) *Building Czech
  WordNet* `[palasmrz2004]`.
- **Code:** [`patterns/`](patterns/)

**Scale of the task.** Counting *role nouns* (nouns denoting a person by their
role) in the starting wordnet, two ways — synsets in the `noun.person`
lexicographer file, and transitive hyponyms of *person* `00007846-n`:

| Measure | Czech synsets | Distinct Czech lemmas |
|---|---|---|
| `noun.person` lexfile | 1919 | 2585 |
| person-hyponym closure | 1849 | 2489 |

So ~1900 role-noun synsets / ~2500 lemmas, against 11 087 `noun.person`
synsets on the English side (≈ 17 % coverage). `noun.person` is an upper bound
— it also holds nationalities, kinship terms, and named individuals, so the
motion-eligible subset is smaller; narrowing it is part of the work. The
≥ 500-noun goal is ~20–25 % of this pool. Reproduce with
[`patterns/count_role_nouns.py`](patterns/count_role_nouns.py).

### 2. Adding derivational relations

Add derivational / morphosemantic links in the spirit of Pala & Hlaváčková,
drawing candidates from a word-formation resource such as DeriNet and
validating a sample.

- **Goal:** add ≥ 1000 derivational links across ≥ 3 relation types
  (e.g. agentive, diminutive, feminine-motion); validate 100 at ≥ 90 %.
- **Stretch:** add a different language as well, ...
- **Readings:** Stoyanova et al. (2025) *Expanding and Enhancing Derivational
  and Morphosemantic Relations in Princeton WordNet* `[stoyanova-etal2025derivational]`;
  Pala & Hlaváčková (2007) *Derivational Relations in Czech WordNet*
  `[pala-hlavackova2007]`. (See also DeriNet 2.3 <https://ufal.mff.cuni.cz/derinet>)
- **Code:** [`derivations/`](derivations/)

### 3. Merging the PDT wordnet sense tags

The Prague Dependency Treebank is annotated with wordnet senses, but against an
**older version** (PWN 1.5). Map those sense tags onto the current synset inventory. The
real deliverable is the **residue**: the tags that don't map, categorised
(synset split / merged / renumbered / deleted / genuinely missing).

- **Goal:** attempt the full set of PDT wordnet tags; target ≥ 95 %
  automatically mapped; hand-categorise 100 of the unmapped residue.
- **Stretch:** handle **all* of the residue
- **Readings:** Daudé, Padró & Rigau (2000) *Mapping WordNets Using Structural
  Information* `[daude-etal2000]`; Bond et al. (2016) *CILI: the Collaborative
  Interlingual Index* `[bond-etal2016cili]`. (PDT 3.0: `[bejcek-etal2013pdt]`.)
- **Code:** [`sensebank/`](sensebank/)

### 4. Better links to ARASAAC and Global Symbols

Improve pictograph coverage for AAC: add colour variants, match more synsets,
and bring in sets from other countries (e.g. the Bulgarian and Croatian sets on
[Global Symbols](https://globalsymbols.com/)). Watch the per-set licences —
they differ — and report them.

- **Goal:** add images to ≥ 1000 (ideally high-frequency) synsets from ≥ 3
  symbol sets; validate appropriateness on a 100-item sample.
- **Stretch:** validate them **all**
- **Readings:** Sevens (2018) *Words Divide, Pictographs Unite* `[sevens2018]`;
  Bond & Foster (2013) *Linking and Extending an Open Multilingual Wordnet*
  `[bond-foster2013]`. Resources: ARASAAC `[arasaac]`, Global Symbols
  `[globalsymbols]`, and the existing ARASAAC wordnet **ARAWN**
  <https://github.com/omwn/arawn> — the base this project extends.
- **Code:** [`images/`](images/)

## Further options (a fifth project, or swaps)

### 5. Wikidata → CILI → Czech

Start from Wikidata items that already carry an ILI/PWN mapping, pull their
Czech labels, project them onto the Czech wordnet, and verify. The residue —
Czech labels with no matching synset — is a ranked list of candidate gaps.

- **Goal:** project ≥ 2000 labels; verify a 100-item sample.
- **Readings:** Vrandečić & Krötzsch (2014) *Wikidata* `[vrandecic-krotzsch2014]`;
  Bond et al. (2016) `[bond-etal2016cili]`.
- **Code:** [`wikidata/`](wikidata/)

### 6. LLM-assisted quality estimation, grounded in Wikidata

Have an LLM flag suspicious synset members / glosses **with a rationale**, using
the Wikidata label and description (from project 5) as evidence rather than
free generation. Then verify a sample and report the LLM's precision. Pairs
well with project 5.

- **Goal:** score ≥ 1000 synsets; verify a 100-item sample; report precision
  of the flag against human judgement.
- **Readings:** as for project 5, plus a paper you find on LLMs for lexical
  resource curation.
- **Code:** [`LLM/`](LLM/)

## Layout

```
docs/setup.md      one-time setup (uv, priming the wn database)
docs/template/     report.tex, report.bib — the shared report skeleton
docs/slides/       validation.tex, literate.tex — the two lectures
patterns/          project 1 — Czech-specific patterns / přechylování
derivations/       project 2 — derivational relations
sensebank/         project 3 — PDT sense-tag remapping
images/            project 4 — ARASAAC / Global Symbols pictographs
wikidata/          project 5 — Wikidata → CILI → Czech
LLM/               project 6 — LLM-assisted quality estimation
litprog/           literate-programming tools (tangle.py, weave.py)
```

Each project directory has its own `README.md` with a starting snippet. Python
code uses [`uv`](https://docs.astral.sh/uv/) inline-script headers — run any
script with `uv run <script>.py`; it fetches its own dependencies.
