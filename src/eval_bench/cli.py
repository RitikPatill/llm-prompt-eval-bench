import typer

app = typer.Typer(help="LLM prompt evaluation harness.")


@app.command()
def run(suite: str = typer.Argument(..., help="Path to the eval suite YAML file.")):
    """Run an evaluation suite against configured models."""
    print("not yet implemented")


@app.command()
def report(target: str = typer.Argument("last", help="Report to open (use 'last').")):
    """Open a previously generated evaluation report."""
    print("not yet implemented")


if __name__ == "__main__":
    app()
