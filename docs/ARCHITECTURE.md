# Architecture

## Principle: identity before topology

The provenance question — *which revision, genuine or clone, what era* — is
answerable from **local, enumerable features**: tube complement, rectifier type,
transformer part numbers, a few diagnostic RC values, and date codes. None of
these require a reconstructed net graph. So the critical path is a **weighted
discriminator scorecard**, not graph matching.

This is also why automatic photo→netlist extraction is explicitly **out of v1**:
the discriminators that decide provenance are readable on individual parts;
connectivity is not recoverable from these photos and isn't needed to answer the
question.

## Pipeline

1. **Ingest** (`ingest.py`) — discover images + reference PDFs, hash, apply EXIF
   orientation.
2. **Vision extraction** (`vision/`) — Claude multimodal (`claude_extractor.py`)
   emits a structured component list per photo via a forced tool call
   (`prompts.py`). Tesseract/OpenCV (`ocr.py`) optionally deskew + crop label
   regions to feed cleaner inputs. **Identity only — never connectivity.**
2a. **Value normalization** (`values.py`) — raw reads are decoded deterministically:
   vintage cap/resistor notation (".1mfd" → 100 nF, "MFD" == µF), resistor
   **colour-band decoding**, and SI canonicalization (ohms/farads) into
   `value_si` so the matcher compares values, not strings. The model reports
   colour bands and verbatim markings; the parser — not the model — decodes them,
   so a misremembered decode can't corrupt a value.
3. **Human confirmation** — the merged BOM is written to JSON, reviewed/edited by
   a human, and reloaded. Vision can misread a value; nothing unconfirmed drives a
   verdict.
4. **Match** (`matching/discriminators.py`) — score the BOM against each
   `CircuitSignature`. Each feature votes match (+w) / unknown (0) / mismatch (−w);
   hard discriminators (rectifier, transformers) outweigh soft ones (a resistor).
5. **Provenance** (`matching/provenance.py`) — two axes: *which revision* (top of
   ranking) and *genuine/clone/modified* (transformer + date-code coherence; a
   recap flags **modified**, not fake).
6. **Generate** (`generate/schematic.py`) — render the identified circuit with
   schemdraw (pure-Python SVG).
7. **Report** (`report/dossier.py`) — Markdown dossier; every row cites its source
   image. Traceability *is* the product.

## Key decisions

- **Deterministic value parsing over model-decoded values.** Vision reports
  colour bands + verbatim markings; `values.py` decodes them with fixed tables and
  regex. SI-normalized values let the matcher treat `100k`, `0.1M`, and `100kΩ` as
  equal within tolerance.
- **Scorecard, not graph-edit-distance.** GED is NP-hard and `networkx`'s optimal
  solver can fail to terminate; it would buy nothing against a tiny known library
  whose members differ by local features. VF2 subgraph isomorphism
  (`matching/graph_match.py`) is kept as a **v2 confirmation** of the scorecard's
  top pick, never the ranker.
- **One representation, two fill levels.** `Netlist`/`BOM` serve both fully-wired
  references and BOM-only extractions; `nets` is optional.
- **schemdraw over KiCad/SKiDL for v1.** Pure-Python, zero system deps, renders
  clean schematics. KiCad export and PySpice verification are deferred (heavy
  system deps for little provenance value).
- **Data-driven knowledge base.** Revisions are YAML `CircuitSignature` fixtures;
  adding AA864 / AB165 is data entry, not code.

## Roadmap

- **v1** (this slice): identity extraction → scorecard → dossier + generated
  schematic.
- **v2**: human-assisted net tracing → `Netlist` → VF2 topology confirmation;
  eyelet-board layout diagram; Qdrant fingerprint index once >10 references.
- **v3**: assisted multi-view connectivity; PySpice frequency-response check;
  KiCad `.kicad_sch` export.
