import rich_click as click
from housaku.commands import (
    config,
    index,
    purge,
    search_documents,
    start_tui,
    start_web,
    vacuum,
)
from housaku.db import init_db
from housaku.settings import Settings

settings = Settings()
init_db(settings.sqlite_url)


@click.group(
    help=settings.description,
    epilog="Check out https://github.com/dnlzrgz/housaku for more details",
    context_settings=dict(
        help_option_names=["-h", "--help"],
    ),
)
@click.version_option(version=settings.version)
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


cli.add_command(index)
cli.add_command(start_web)
cli.add_command(start_tui)
cli.add_command(search_documents)
cli.add_command(config)
cli.add_command(purge)
cli.add_command(vacuum)
