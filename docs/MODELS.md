# Models & external help

Which model/service does which job, and when to reach for it.

## Primary

| Model | Role | Where |
|---|---|---|
| **Claude Opus 4.8** (`claude-opus-4-8`) | Component/marking extraction from photos; provenance reasoning; schematic-transcription assist. The v1 vision workhorse. | `vision/claude_extractor.py` via Anthropic SDK |
| **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) | Cheap bulk first-pass OCR over many crops before an Opus consolidation pass. | `config.BULK_OCR_MODEL` |
| **Tesseract 5.5** | Local OCR of deskewed label crops — an *assist*, not the primary reader. | `vision/ocr.py` |

Auth: the Anthropic SDK reads `ANTHROPIC_API_KEY` from the environment. The
offline path (`analyze --bom`) needs no key.

## Optional / later phases

| Model | Role | Phase |
|---|---|---|
| **YOLO** (ultralytics) fine-tuned on electronic components | Dense-board component localization when Claude vision needs help on cluttered shots. | v3 |
| **Specialized OCR** (transformers) | Hard hand-stamped date codes. | v3 |

## Research aids (MCP / tools — corroborate provenance)

- **EPO / patent search** — Fender-era amplifier circuit patents to corroborate
  lineage.
- **Academic / arXiv search** — circuit-recognition and netlist-extraction
  literature for the v2/v3 topology work.
- **Web search / Firecrawl** — pull known schematics, transformer EIA date-code
  charts, serial-number dating references.
- **Context7** — current docs for schemdraw / networkx / PySpice during build.
- **PDF tools** — render/region-extract the reference schematic scans.

## Calibration

Vision output is advisory. Every `Component` carries a `Provenance.confidence`;
the human-confirmation gate sits between extraction and matching; the dossier
cites the source image for every discriminator. The system is built to **decline
to over-call** when evidence is thin (e.g. 6G6-B vs 6G6-C without a transformer
stamp read) rather than guess.
