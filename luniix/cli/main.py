import logging

import typer
from rich.logging import RichHandler

from luniix.databases import DatabaseManager
from luniix.devices import list_devices

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def list():
    devices = list_devices()
    for device in devices:
        typer.echo(device)


@app.command()
def db():
    db = DatabaseManager()

    db = DatabaseManager()
    typer.echo(len(db._db))


if __name__ == "__main__":
    app()
