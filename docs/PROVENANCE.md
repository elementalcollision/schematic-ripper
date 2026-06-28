# First-pass provenance — specimen amplifier

A manual read of the nine chassis photographs (`source_images/IMG_0983–0992`)
against the two Fender factory documents (`sample_schematics/`). This is the
human baseline the automated pipeline is built to reproduce and extend.

## Verdict (preliminary)

> **A genuine early-1960s Fender "Bassman" of the 6G6 family (6G6-B / 6G6-C,
> blonde piggyback era, ~1962–1964), since serviced — the filter caps, several
> electrolytics, and the transformers have been replaced. Distinguishing 6G6-B
> from 6G6-C cannot be done from these nine frames alone, and the non-OE
> transformers don't help; it needs the bias/coupling-cap values and the tube chart.**

Confidence: **family — high; exact revision — low (B vs C unresolved).**

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

## What's needed to resolve 6G6-B vs 6G6-C

The two revisions are electrically near-identical, and **the transformers here are
non-OE (replaced), so their stamps carry no provenance weight** — they're excluded.
That leaves the circuit itself and the surviving original parts. To close the gap:
1. **Bias circuit + a few coupling-cap values** — the residual electrical
   differences between 6G6-B and 6G6-C live here; transcribe them from the board.
2. **Tube chart / preamp tube layout** — confirm the 5881 × 2 / 7025 × 4 count
   directly rather than inferring from sockets.
3. **Pot date codes** (EIA, e.g. `137-YYWW` CTS) — to pin the build year against
   the 1962–64 window; pots are usually original even when the iron is not.
4. **Chassis & original-part stamps** — the Fender chassis ink-stamp and any
   surviving original component date codes.

The pipeline's `extract` → human-confirm → `analyze` loop is designed to ingest
exactly these follow-up photos and tighten the verdict.
