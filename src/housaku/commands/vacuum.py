import click
from housaku.db import with_db
from housaku.utils import console


@click.command(
    name="vacuum",
    help="Reclaims unused spaced in the database.",
)
@click.pass_context
def vacuum(ctx: click.Context) -> None:
    settings = ctx.obj["settings"]

    try:
        with with_db(settings.sqlite_url) as conn:
            conn.execute("VACUUM")
            console.print("[green][Ok][/] unused space has been reclaimed!")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while reclaiming space: {e}")
