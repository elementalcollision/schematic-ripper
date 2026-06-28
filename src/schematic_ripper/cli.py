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


if __name__ == "__main__":
    app()
