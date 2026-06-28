"""`sripper` command-line interface.

    sripper ingest                 # list discovered input assets
    sripper references             # list loaded reference signatures
    sripper extract                # vision pass -> writes a human-editable BOM
    sripper analyze --bom run.json # match a confirmed BOM -> provenance dossier
    sripper generate 6G6-C         # render the identified circuit (schemdraw)
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import config, ingest, pipeline
from .reference import loader

app = typer.Typer(add_completion=False, help="Photo-to-provenance for tube amplifiers.")
console = Console()


@app.command("ingest")
def ingest_cmd(
    images: Path = typer.Option(None, "--images", help="Override source images dir."),
) -> None:
    """List discovered input assets (images + reference PDFs)."""
    table = Table("Kind", "File", "Dims", "SHA-256")
    for a in ingest.discover(images_dir=images):
        dims = f"{a.width}×{a.height}" if a.width else "—"
        table.add_row(a.kind, a.path.name, dims, a.sha256[:12])
    console.print(table)


@app.command()
def references(refs: Path = typer.Option(None, "--refs")) -> None:
    """List the reference circuit signatures available to the matcher."""
    table = Table("Model", "Rectifier", "Tubes", "Transformers")
    for sig in loader.load_all_signatures(refs):
        table.add_row(
            sig.model,
            sig.rectifier_type,
            ", ".join(sig.required_tubes),
            ", ".join(sig.transformer_part_numbers) or "—",
        )
    console.print(table)


@app.command()
def extract(
    images: Path = typer.Option(None, "--images"),
    out: Path = typer.Option(config.RUNS_DIR / "bom.json", "--out"),
    model: str = typer.Option(None, "--model"),
) -> None:
    """Run the Claude vision pass and write a human-editable BOM for review."""
    console.print("[bold]Running vision extraction…[/bold] (requires ANTHROPIC_API_KEY)")
    bom = pipeline.extract_bom(images_dir=images, model=model)
    pipeline.save_bom(bom, out)
    console.print(f"Wrote {len(bom.items)} components to [cyan]{out}[/cyan]. Review, then `analyze --bom`.")


@app.command()
def analyze(
    bom: Path = typer.Option(None, "--bom", help="Confirmed BOM JSON; omit to run live vision."),
    refs: Path = typer.Option(None, "--refs"),
    out: Path = typer.Option(config.RUNS_DIR, "--out"),
) -> None:
    """Match a BOM against the reference library and write a provenance dossier."""
    loaded = pipeline.load_bom(bom) if bom else None
    report = pipeline.analyze(bom=loaded, references_dir=refs)
    path = pipeline.write_dossier(report, out_dir=out)
    console.print(
        f"[bold green]{report.identified_model}[/bold green] "
        f"({report.confidence:.0%}, {report.genuine_vs_clone}) → [cyan]{path}[/cyan]"
    )


@app.command()
def generate(
    model_name: str = typer.Argument(..., help="Reference model to render, e.g. 6G6-C."),
    refs: Path = typer.Option(None, "--refs"),
    out: Path = typer.Option(config.RUNS_DIR, "--out"),
) -> None:
    """Render the identified circuit as a clean schematic (requires `eda` extra)."""
    from .generate import schematic

    sig = next((s for s in loader.load_all_signatures(refs) if s.model == model_name), None)
    if sig is None:
        raise typer.BadParameter(f"unknown model {model_name!r}")
    out.mkdir(parents=True, exist_ok=True)
    block = schematic.render_block_diagram(sig, out / f"{model_name}_block.svg")
    stage = schematic.render_gain_stage(out / f"{model_name}_gainstage.svg")
    console.print(f"Wrote [cyan]{block}[/cyan] and [cyan]{stage}[/cyan]")


@app.command()
def decode(
    marking: str = typer.Argument(None, help="A printed marking, e.g. '.1mfd 400vdc' or '220k'."),
    bands: str = typer.Option(None, "--bands", help="Resistor colour bands, space-separated."),
) -> None:
    """Parse a component marking or resistor colour bands into a normalized value."""
    from . import values

    if bands:
        rv = values.decode_resistor_bands(bands.split())
        if rv:
            console.print(f"resistor: [bold]{values.format_ohms(rv[0])}[/bold] ±{rv[1]}  ({rv[0]:g} Ω)")
        else:
            console.print("[red]could not decode those bands[/red]")
        return
    if not marking:
        raise typer.BadParameter("provide a MARKING argument or --bands")
    farads, volts = values.parse_capacitor(marking)
    if farads is not None:
        v = f" @ {volts}" if volts else ""
        console.print(f"capacitor: [bold]{values.format_farads(farads)}[/bold]{v}  ({farads:g} F)")
        return
    ohms = values.parse_resistor(marking)
    if ohms is not None:
        console.print(f"resistor: [bold]{values.format_ohms(ohms)}[/bold]  ({ohms:g} Ω)")
        return
    console.print("[yellow]no value parsed[/yellow]")


@app.command()
def enhance(
    src: Path = typer.Argument(..., help="Source image."),
    out: Path = typer.Option(..., "--out", help="Output PNG path."),
    box: str = typer.Option(None, "--box", help="Relative crop 'x0,y0,x1,y1' in 0..1."),
    scale: int = typer.Option(3, "--scale"),
    rotate: int = typer.Option(0, "--rotate", help="Rotate degrees CCW (90/-90/180)."),
    equalize: bool = typer.Option(False, "--equalize"),
    invert: bool = typer.Option(False, "--invert"),
    flip: bool = typer.Option(False, "--flip", help="Mirror horizontally (chrome bells)."),
    threshold: int = typer.Option(None, "--threshold", help="Binarize at 0..255."),
) -> None:
    """Enhance a crop of an image to read a faint stamped/inked code."""
    from .vision import enhance as enh

    b = tuple(float(x) for x in box.split(",")) if box else None
    p, size = enh.enhance(
        src, out, box=b, scale=scale, rotate=rotate,
        equalize=equalize, invert=invert, flip_h=flip, threshold=threshold,
    )
    console.print(f"wrote [cyan]{p}[/cyan] ({size[0]}×{size[1]})")


if __name__ == "__main__":
    app()
