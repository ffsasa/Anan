import typer

app = typer.Typer()


@app.command()
def run(source: str) -> None:
    typer.echo(f"Input: {source}")