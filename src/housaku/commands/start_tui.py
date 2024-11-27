import click
from housaku.tui import app as tui_app


@click.command(
    name="tui",
    short_help="Starts Textual TUI.",
)
@click.pass_context
def start_tui(ctx: click.Context) -> None:
    settings = ctx.obj["settings"]
    tui_app(settings).run()
