import click
from housaku.db import init_db, clear_db
from housaku.utils import console


@click.command(
    name="purge",
    help="Purges all data from the database.",
)
@click.pass_context
def purge(ctx: click.Context) -> None:
    settings = ctx.obj["settings"]

    try:
        clear_db(settings.sqlite_url)
        init_db(settings.sqlite_url)
        console.print("[green][Ok][/] database purged correctly!")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while purging database: {e}")
