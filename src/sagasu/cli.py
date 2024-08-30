from sqlalchemy import create_engine
import typer

from sagasu.db import init_db

app = typer.Typer(name="sagasu")


@app.command()
def hello() -> None:
    sqlite_url = "sqlite:///sagasu.db"
    engine = create_engine(sqlite_url)
    init_db(engine)
