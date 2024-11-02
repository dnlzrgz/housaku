import asyncio
import concurrent.futures
import os
import subprocess
import textwrap
import urllib.parse
from functools import partial
from multiprocessing import cpu_count
from time import perf_counter
import rich_click as click
from uvicorn import run
from housaku.web import app as web_app
from housaku.tui import app as tui_app
from housaku.db import init_db, with_db, clear_db, rebuild_fts
from housaku.feeds import index_feed
from housaku.files import list_files, index_file, SUPPORTED_MIME_TYPES
from housaku.settings import Settings, config_file_path
from housaku.search import search
from housaku.utils import console

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
def cli() -> None:
    pass


@cli.command(
    name="index",
    short_help="Start indexing documents and posts.",
)
@click.option(
    "-t",
    "--max-threads",
    type=click.IntRange(min=1),
    default=cpu_count() // 2,
    help="Maximum number of threads to use for indexing (default: half of CPU cores).",
)
def index(max_threads) -> None:
    with console.status(
        "[green]Start indexing... Please, wait a moment.",
        spinner="arrow",
    ) as status:
        include_files = set(settings.files.include)
        exclude_files = set(settings.files.exclude)
        urls = settings.feeds.urls

        partial_function = partial(index_file, settings.sqlite_url)
        try:
            for dir in include_files:
                status.update(
                    f"[green]Indexing documents from '{dir.name}'... Please wait, this may take a moment.[/]"
                )
                files = list_files(dir, exclude_files)

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_threads
                ) as executor:
                    executor.map(partial_function, files)

            status.update(
                "[green]Indexing feeds and posts... Please wait, this may take a moment."
            )
            asyncio.run(index_feed(settings.sqlite_url, urls))

            status.update("[green]Wrapping things up...")
            rebuild_fts(settings.sqlite_url)
        except Exception as e:
            console.print(
                f"[red][Err][/] something went wrong while rebuilding the fts5 table: {e}"
            )


@cli.command(
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


@cli.command(
    name="tui",
    short_help="Starts Textual TUI.",
)
def start_tui() -> None:
    tui_app(settings).run()


@cli.command(
    name="search",
    short_help="Search for documents and posts.",
)
@click.option(
    "-q",
    "--query",
    prompt="Search terms",
    help="Search terms to find relevant documents.",
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=10,
    help="Limit the number of documents returned.",
)
def search_documents(query: str, limit: int) -> None:
    start_time = perf_counter()

    try:
        results = search(settings.sqlite_url, query, limit)
    except Exception as e:
        console.print(f"[red][Err][/] Something went wrong with your query: {e}")
        return

    if not results:
        console.print("[yellow]No results found.[/]")
        return

    end_time = perf_counter()
    elapsed_time = end_time - start_time

    for uri, title, doc_type, content in results:
        encoded_uri = urllib.parse.quote(uri, safe=":/")
        doc_title = title if title else uri

        truncated_content = textwrap.shorten(content, width=280, placeholder="...")
        emoji = ":globe_with_meridians:"
        link = f"[link={uri}]{doc_title}[/]"
        if doc_type in SUPPORTED_MIME_TYPES:
            link = f"[link=file://{encoded_uri}]{doc_title}[/]"
            emoji = ":scroll:"

        console.print(
            f"{emoji} [bold underline]{link}[/]\n{truncated_content}",
            emoji=True,
            justify="left",
            highlight=False,
            end="\n\n",
        )

    console.print(
        f"Search completed in {elapsed_time:.3f}s",
        highlight=False,
    )


@cli.command(
    name="config",
    help="Opens the configuration file.",
)
def config() -> None:
    editor = os.environ.get("EDITOR", None)
    try:
        if editor:
            subprocess.run([editor, str(config_file_path)], check=True)
        else:
            subprocess.run(["open", str(config_file_path)], check=True)
    except Exception as e:
        console.print(f"[red][Err][/] Failed to open the configuration file: {e}")


@cli.command(
    name="purge",
    help="Purges all data from the database.",
)
def purge() -> None:
    try:
        clear_db(settings.sqlite_url)
        init_db(settings.sqlite_url)
        console.print("[green][Ok][/] database purged correctly!")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while purging database: {e}")


@cli.command(
    name="vacuum",
    help="Reclaims unused spaced in the database.",
)
def vacuum() -> None:
    try:
        with with_db(settings.sqlite_url) as conn:
            conn.execute("VACUUM")
            console.print("[green][Ok][/] unused space has been reclaimed!")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while reclaiming space: {e}")
