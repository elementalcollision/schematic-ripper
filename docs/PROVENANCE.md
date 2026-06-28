# First-pass provenance — specimen amplifier

A manual read of the nine chassis photographs (`source_images/IMG_0983–0992`)
against the two Fender factory documents (`sample_schematics/`). This is the
human baseline the automated pipeline is built to reproduce and extend.

## Verdict (preliminary)

> **A genuine Fender "Bassman" 6G6-C (the last of the blonde-piggyback series),
> built ~1964 and since serviced. The power and output transformers are non-OE
> replacements and the filter caps have been redone — but the original Schumacher
> choke (125C1A, dated 1964 week 20) survives and pins both the model and the year.**

Confidence: **genuine — high; revision — 6G6-C, now positively evidenced by the
original choke (was "6G6 family" on the first nine photos alone).**

## Evidence

**Construction → genuine vintage Fender, not a modern clone.**
- Eyelet-board point-to-point on a steel chassis (IMG_0985).
- Cloth-covered push-back hookup wire in yellow/tan, green, white/red — correct
  for the era (IMG_0985, IMG_0989, IMG_0991).
- Period-correct **molded paper caps** stamped *"MOLDED .1mfd / .047mfd / .25mfd
  400 vdc — Made in U.S."* with *"OUTSIDE FOIL"* banding, plus a **Good-All TYPE
  N-503 .1 MFD 400 V.D.C.** (IMG_0986, IMG_0987, IMG_0988, IMG_0989).
- **Carbon-composition resistors** throughout (IMG_0987, IMG_0988).
- **Octal power-tube sockets** (IMG_0983) consistent with the 6G6's twin 5881s;
  nine-pin preamp sockets consistent with the 7025 (low-noise 12AX7) complement.

**Service history → the amp is *modified*, not original-spec.**
- Filter bank rebuilt with **4× Sprague Atom 20 µF 500 VDC (TVA1906)** and a
  **Nichicon 80 µF** can (IMG_0983) — both standard re-cap replacements.
- Small **modern Vishay 22 µF 50 V** electrolytics on cathode-bypass duty
  (IMG_0986, IMG_0987).
- **The transformers are non-OE replacements** — their part-number stamps are
  therefore excluded from the provenance analysis (a re-transformer is service
  history, not origin).
- These do not affect the circuit *identity*; they flag a recap + re-transformer,
  which is normal maintenance for a 60-year-old amp.

**Reference match → 6G6 family confirmed.**
- The `6G6-B` layout and `6G6-C` schematic both specify **2× 5881 + 4× 7025**, a
  **solid-state (silicon-diode) rectifier**, a two-channel **Normal + Bass** front
  end with a shared **Presence** control, and pot values **25K presence / 250K
  bass / 250K(70K-tap) treble / 1M volume** — all consistent with the chassis.
- The `6G6-C` schematic additionally names the iron: **TR1 125P7A** (power),
  **TR2 125C1A** (choke), **TR3 125A13A** (output), with a **+430 V** plate rail.

## Update — chassis & iron codes (enhanced reads)

Four further photos (IMG_0971/0972/0981/0982) were enhanced with `vision/enhance.py`
(crop → upscale → contrast/threshold → de-rotate) to read stamped and inked codes:

| Code | Reading | Bearing on provenance |
|---|---|---|
| Choke (olive) | **125C1A · EIA 606-4-20** | **original** Schumacher choke; `125C1A` is the 6G6-C's choke P/N, dated **1964 wk 20** |
| Chassis (stamped) | **BP11840** | Fender serial — **BP = Bassman Piggyback** prefix; independently confirms a piggyback Bassman |
| Transformer (chrome) | **W022798 / 1279 / 0537** | non-OE replacement |
| Transformer (black) | **W018343** | non-OE replacement |
| Chassis (inked) | **83 3369** (tentative) | inked production / inspector mark; low-confidence read (ink corroded into the metal) |

**Effect on the verdict.** Re-running the matcher with these reads flips the
identification from "6G6 family / 6G6-B" to **6G6-C (38%, genuine/modified)** — the
`125C1A` choke is listed by the 6G6-C signature but not 6G6-B, and its 1964 date
code sits squarely in the 6G6-C window. Authenticity holds on the *original* choke
while the two replaced transformers are flagged as modification, not as a clone
(`sripper analyze --bom tests/fixtures/sample_bom_with_codes.json`). The stamped
serial **BP11840** independently corroborates the model — `BP` is Fender's prefix
for the **B**assman **P**iggyback — though the build year stays pinned by the choke
(Fender serials aren't sequential enough to date on their own).

**Still open:** the inked chassis stamp (a date/inspector mark) is too degraded in
this frame to read; a low-angle raking-light photo would likely recover it. The
6G6-B↔6G6-C residual circuit differences (bias network, a few coupling-cap values)
remain a nice-to-have confirmation but are no longer needed for the model call.

The pipeline's `extract` → human-confirm → `analyze` loop is designed to ingest
exactly these follow-up photos and tighten the verdict.
