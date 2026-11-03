# Setup

One-time setup shared by all six projects. You need Python ≥ 3.10 and
[`uv`](https://docs.astral.sh/uv/); the LaTeX parts need XeLaTeX.

## 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # macOS / Linux
# Windows: see https://docs.astral.sh/uv/getting-started/installation/
```

Every script carries its own dependency header, so you never `pip install`
anything — `uv run some_script.py` fetches `wn`, `requests`, etc. into a
throwaway environment on first run.

## 2. Prime the wordnet database (once)

The projects share one `wn` database under `patterns/.wn_data`. Build it once by
running the role-noun counter, which downloads `omw-en:2.0` and the Czech
wordnet and leaves them cached for everyone else:

```bash
cd patterns
uv run count_role_nouns.py
```

You should see ~1900 role-noun synsets. After this, the `sensebank/`,
`images/`, and `wikidata/` scripts reuse the same `.wn_data` and start fast.

- The starting wordnet is
  [`wn-ntumc-ces.xml`](https://github.com/bond-lab/NTUMC/releases/download/2026.08/wn-ntumc-ces.xml);
  the scripts fetch it for you.
- `.wn_data/`, the downloaded `*.xml`, and the CILI `*.tab` maps are
  git-ignored — they are inputs, not results. Don't commit them.

## 3. Run a project's starter

Each project directory has a `README.md` and a starter script or snippet:

| Dir | Start with |
|---|---|
| `patterns/` | `uv run count_role_nouns.py` |
| `wikidata/` | `uv run wikidata_to_czech.py 500` |
| `sensebank/`, `images/`, `derivations/`, `LLM/` | the snippet in the README |

## 4. Build the report and the slides

```bash
# report (pdfLaTeX is fine)
cd latex/report && pdflatex report && bibtex report && pdflatex report && pdflatex report

# lecture slides (XeLaTeX — uses system fonts)
cd latex/slides && xelatex validation && xelatex validation
```

On Overleaf, upload the folder and press Recompile; set the compiler to XeLaTeX
for the slides.

## 5. The course website (`docs/`)

`docs/` is the GitHub Pages site: `index.html`, the slide PDFs under `pdf/`, and
the interactive explainers under `explanations/`. The LaTeX sources live in
`latex/` (not published); the compiled PDFs are copied into `docs/pdf/`.

Rebuild the site after editing an explainer or the slides:

```bash
# build the PDFs in latex/ first (see §4), then:
uv run docs/build.py     # wraps the explainer fragments, copies the PDFs in
```

Publish it once under **Settings → Pages → Branch `master`, folder `/docs`**. The
`.nojekyll` file tells GitHub to serve the HTML as-is.

## Keep out of git

Already in `.gitignore`: `.wn_data/`, `*.xml`, `*.tab`, `*.tsv`, LaTeX build
artifacts, and editor lock files. Commit source and results (counts, a sample
TSV you want to keep as a result goes in the report, not the repo).
