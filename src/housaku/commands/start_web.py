import rich_click as click
from uvicorn import run
from housaku.web import app as web_app


@click.command(
    name="web",
    short_help="Launches Web UI.",
)
@click.option(
    "-p",
    "--port",
    default=4242,
    help="Port.",
)
def start_web(port: int) -> None:
    run(web_app, host="127.0.0.1", port=port)
