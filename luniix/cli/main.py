import logging

import typer
from rich.logging import RichHandler

from luniix.constants import FILE_OFFICIAL_DB
from luniix.databases import download_official_db, load_db
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
    download_official_db()

    db = load_db(FILE_OFFICIAL_DB)

    typer.echo(db)


if __name__ == "__main__":
    app()
