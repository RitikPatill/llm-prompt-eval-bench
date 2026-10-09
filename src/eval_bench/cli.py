import asyncio

import typer
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich import print as rprint

from eval_bench.loader import load_suite
from eval_bench.runner import RunResult, run_suite

app = typer.Typer(help="LLM prompt evaluation harness.")


def _print_summary(results: list[RunResult]) -> None:
    table = Table(title="Run Summary", show_lines=True)
    table.add_column("case_id", style="cyan")
    table.add_column("model", style="magenta")
    table.add_column("latency_ms", justify="right")
    table.add_column("status", justify="center")

    for r in results:
        status = "[red]error[/red]" if r.error else "[green]ok[/green]"
        table.add_row(r.case_id, r.model, f"{r.latency_ms:.0f}", status)

    rprint(table)


@app.command()
def run(suite_path: str = typer.Argument(..., help="Path to the eval suite YAML.")):
    """Run an evaluation suite against configured models."""
    suite = load_suite(suite_path)
    pairs_count = sum(len(c.models) for c in suite.cases)

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"Running {suite.name}", total=pairs_count)
        results = asyncio.run(run_suite(suite, progress=progress, task_id=task))

    _print_summary(results)


@app.command()
def report(target: str = typer.Argument("last", help="Report to open (use 'last').")):
    """Open a previously generated evaluation report."""
    print("not yet implemented")


if __name__ == "__main__":
    app()
