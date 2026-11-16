"""Fetch and read the PDT lexico-semantic annotation and the wordnet it used.

Shared by pdt_wordnet_vs_wncze.py and pdt_frequencies.py. Three downloads,
all from LINDAT, all CC BY-NC-SA 3.0 (not the CC BY-SA of the Czech
WordNet release), cached in ./data and never committed:

  cwn      Czech WordNet 1.9 PDT: the wordnet the annotators chose from
           (nas_anotacni_slovnik.xml, "our annotation dictionary")
  ann      Lexico-Semantic Annotation of PDT: stand-off tags, one per word
  pdt      Prague Dependency Treebank 3.0, read only for the lemma and the
           morphological tag of each annotated word (128 MB)

The tags are synset ids of the annotation wordnet. Those ids are Princeton
WordNet 1.5 offsets, written without the leading zeros or the part of
speech (1307561 for 01307561-v), or ids of synsets added to this copy
without a Princeton counterpart, by ÚFAL or in Brno (NAS-430683854,
1448862335). Small numbers are exceptions;
"-" means the word has no agreed tag.
"""
import gzip
import re
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PML = "{http://ufal.mff.cuni.cz/pdt/pml/}"
LINDAT = "https://lindat.mff.cuni.cz/repository/server/api/core/bitstreams/"
SOURCES = {
    "cwn": (LINDAT + "a0bd7658-eaf3-49f0-9a60-e6fc06aa284f/content", "Czech_WordNet_1.9_PDT.zip"),
    "ann": (LINDAT + "57842d3d-246b-45bb-a2ea-7c0123cb2605/content", "pdt-wsd-annotation.zip"),
    "pdt": (LINDAT + "d0a1771e-816a-4475-8a23-54f0ebafce3c/content", "PDT_3.0.zip"),
}
CILI_URL = ("https://raw.githubusercontent.com/globalwordnet/cili/master/"
            "older-wn-mappings/ili-map-pwn15.tab")
CILI_TAB = HERE / "ili-map-pwn15.tab"

# The exception codes, as the 2011 data numbers them. The papers list the
# exceptions in order (Hajič et al. 2004, Table 1) but not their codes. Codes
# 2 and 4 are tested against the data (a reflexive se/si beside 68% of code-2
# verbs; 99.7% of code-4 words negated), 5-7 read off their lemmas, 8 and 10
# from the counts Bejček et al. (2006) give. Codes 0 and 1 are guesses.
EXCEPTIONS = {
    "0": "other problem (guess)",
    "1": "missing sense (guess)",
    "2": "incorrect reflexivity",
    "3": "missing positive sense",
    "4": "missing negative sense",
    "5": "incorrect lemma",
    "6": "figurative use",
    "7": "proper name",
    "8": "unclear word meaning in the text",
    "9": "unclear CWN sense",
    "10": "missing more general sense",
}
UNTAGGED = "-"


@dataclass
class NasSynset:
    """A synset of the annotation wordnet."""

    id: str
    pos: str
    literals: list[str]
    definitions: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    hypernyms: list[str] = field(default_factory=list)
    stamp: str = ""

    @property
    def pwn15(self) -> str | None:
        """The Princeton 1.5 offset, e.g. 00003711-n, or None for a new synset.

        Returns:
            The offset with 'r' for adverbs (the file writes 'b'), or None
        """
        m = re.fullmatch(r"(\d{8})-([nvab])", self.id)
        return f"{m[1]}-{'r' if m[2] == 'b' else m[2]}" if m else None


@dataclass
class Token:
    """One annotated word: its tag and, when PDT is read, its lemma and sentence."""

    doc: str
    mid: str
    tag: str
    lemma: str = ""
    mtag: str = ""
    form: str = ""
    sentence: str = ""


def fetch(name: str) -> Path:
    """Download a source once into ./data.

    Args:
        name: a key of SOURCES ('cwn', 'ann' or 'pdt')

    Returns:
        The path of the downloaded file

    Raises:
        requests.HTTPError: if LINDAT refuses the download
    """
    url, filename = SOURCES[name]
    path = DATA / filename
    if not path.exists():
        DATA.mkdir(exist_ok=True)
        print(f"downloading {filename} ...")
        with requests.get(url, stream=True, timeout=120,
                          headers={"User-Agent": "JPC3-course"}) as r:
            r.raise_for_status()
            with path.open("wb") as fh:
                for chunk in r.iter_content(1 << 20):
                    fh.write(chunk)
    return path


def literal(text: str) -> str:
    """A literal of the annotation wordnet as a lemma.

    Args:
        text: the literal, e.g. 'vypadat ^2'

    Returns:
        The lemma without the homonym mark, e.g. 'vypadat'
    """
    return re.sub(r"\s*\^\d+$", "", text.strip())


def read_nas() -> dict[str, NasSynset]:
    """Read the annotation wordnet.

    The file is ISO-8859-2 and has no root element, so it is wrapped in one.

    Returns:
        Every synset, keyed by its id
    """
    with zipfile.ZipFile(fetch("cwn")) as z:
        raw = z.read("nas_anotacni_slovnik.xml").decode("iso-8859-2")
    body = re.sub(r"^<\?xml[^>]*\?>", "", raw)
    root = ET.fromstring(f"<wn>{body}</wn>")
    out = {}
    for s in root.iter("SYNSET"):
        sid = s.findtext("ID").strip()
        out[sid] = NasSynset(
            id=sid,
            pos=(s.findtext("POS") or "").strip(),
            literals=[literal(lit.text or "") for lit in s.iter("LITERAL")],
            definitions=[d.text.strip() for d in s.iter("DEF") if d.text],
            examples=[u.text.strip() for u in s.iter("USAGE") if u.text],
            hypernyms=[r.text.strip() for r in s.iter("ILR")
                       if r.findtext("TYPE") == "hypernym" and r.text],
            stamp=(s.findtext("STAMP") or "").strip(),
        )
    return out


def tag_index(nas: dict[str, NasSynset]) -> dict[str, str]:
    """Map a tag as written in the annotation to a synset id.

    PWN offsets lose their zeros and part of speech in the tags (1307561).
    A few numbers name a synset in two parts of speech; they go to the
    first one in the file.

    Args:
        nas: the annotation wordnet

    Returns:
        tag -> synset id
    """
    index: dict[str, str] = {}
    for sid in nas:
        index.setdefault(sid.split("-")[0].lstrip("0") if sid[0].isdigit() and "-" in sid
                         else sid, sid)
    return index


def pwn15_ili() -> dict[str, tuple[str, float]]:
    """Read the CILI map from Princeton WordNet 1.5, downloading it once.

    Returns:
        offset -> (ILI, confidence of the mapping, 0 to 1)
    """
    if not CILI_TAB.exists():
        CILI_TAB.write_bytes(requests.get(CILI_URL, timeout=60).content)
    out = {}
    for line in CILI_TAB.read_text().splitlines():
        ili, off, conf = line.split("\t")
        out[off] = (ili, float(conf))
    return out


def ili_of(syn: NasSynset, cili: dict[str, tuple[str, float]]) -> tuple[str, float] | None:
    """The ILI of an annotation synset.

    Args:
        syn: the synset
        cili: the map from pwn15_ili()

    Returns:
        (ILI, confidence), or None for a new synset or one the map lacks.
        An adjective is also looked up as a satellite, as 1.5 may have it.
    """
    off = syn.pwn15
    if off is None:
        return None
    return cili.get(off) or (cili.get(off[:-1] + "s") if off.endswith("-a") else None)


def read_tags() -> Iterator[Token]:
    """Read the stand-off annotation.

    Returns:
        Every annotated word with its tag, in document order, without lemma
    """
    with zipfile.ZipFile(fetch("ann")) as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".s")):
            doc = Path(name).stem
            root = ET.fromstring(z.read(name))
            for st in root.iter(PML + "st"):
                yield Token(doc, st.findtext(PML + "a.rf").strip(),
                            st.findtext(PML + "lexicon-id").strip())


def read_tokens() -> Iterator[Token]:
    """Read the annotation together with the PDT 3.0 morphological layer.

    Returns:
        Every annotated word with its lemma and morphological tag; a word
        whose document is not in PDT 3.0 has an empty lemma
    """
    with zipfile.ZipFile(fetch("pdt")) as pdt:
        mfiles = {Path(n).name.removesuffix(".m.gz"): n
                  for n in pdt.namelist() if n.endswith(".m.gz")}
        doc, morph = None, {}
        for tok in read_tags():
            if tok.doc != doc:
                doc = tok.doc
                morph = read_morph(pdt.read(mfiles[doc])) if doc in mfiles else {}
            if tok.mid in morph:
                tok.lemma, tok.mtag, tok.form, words, i = morph[tok.mid]
                tok.sentence = detokenise([*words[:i], f"«{tok.form}»", *words[i + 1:]])
            yield tok


def read_morph(gz: bytes) -> dict[str, tuple[str, str, str, list[str], int]]:
    """Read one gzipped PDT m-layer file.

    Args:
        gz: the file's bytes

    Returns:
        m-id -> (lemma, tag, form, the forms of its sentence, its position)
    """
    out = {}
    for s in ET.fromstring(gzip.decompress(gz)).iter(PML + "s"):
        ms = list(s.iter(PML + "m"))
        words = [m.findtext(PML + "form") for m in ms]
        for i, m in enumerate(ms):
            out[m.get("id")] = (m.findtext(PML + "lemma"), m.findtext(PML + "tag"),
                                words[i], words, i)
    return out


def detokenise(words: list[str]) -> str:
    """Join tokens into readable text, without spaces before punctuation.

    Args:
        words: the tokens of a sentence

    Returns:
        The sentence as a string
    """
    text = " ".join(words)
    text = re.sub(r" ([,.;:!?)%])", r"\1", text)
    return re.sub(r"([(„]) ", r"\1", text)


def base_lemma(lemma: str) -> str:
    """A PDT m-lemma without its technical suffixes.

    Args:
        lemma: the m-layer lemma, e.g. 'stát-2_^(státní_útvar)'

    Returns:
        The bare lemma, e.g. 'stát'
    """
    head = re.split(r"(?<=.)[_`]", lemma, maxsplit=1)[0]
    return re.sub(r"(?<=.)-\d+$", "", head)
