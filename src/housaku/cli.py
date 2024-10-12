import asyncio
import concurrent.futures
import os
import subprocess
import textwrap
import urllib.parse
from functools import partial
from multiprocessing import cpu_count
from pathlib import Path
from time import perf_counter
import rich_click as click
from uvicorn import run
from housaku.web import app as web_app
from housaku.tui import app as tui_app
from housaku.db import init_db, db_connection, purge_db, rebuilt_fts_table
from housaku.feeds import index_feeds
from housaku.files import (
    list_files,
    index_file,
    COMPLEX_DOCUMENT_FILETYPES,
    PLAIN_TEXT_FILETYPES,
    FILETYPES_SET,
)
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
    "-i",
    "--include",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    multiple=True,
    help="Directory to include for indexing.",
)
@click.option(
    "-e",
    "--exclude",
    multiple=True,
    help="Directory or pattern to exclude from indexing.",
)
@click.option(
    "-t",
    "--max-threads",
    type=click.IntRange(min=1),
    default=cpu_count() // 2,
    help="Maximum number of threads to use for indexing (default: half of CPU cores).",
)
@click.option(
    "--purge",
    is_flag=True,
    show_default=True,
    default=False,
    help="Purge all data from the database before indexing.",
)
def index(include, exclude, max_threads, purge) -> None:
    """
    Index documents and posts from the specified sources in the
    config.toml file.
    """
    with console.status(
        "[green]Start indexing... Please, wait a moment.",
        spinner="arrow",
    ) as status:
        merged_include = list(
            set(Path(d) for d in settings.files.include) | {Path(d) for d in include}
        )
        merged_exclude = list(set(settings.files.exclude) | set(exclude))
        urls = settings.feeds.urls

        partial_function = partial(index_file, settings.sqlite_url)

        if purge:
            try:
                status.update("[green]Purging previous data...")
                purge_db(settings.sqlite_url)
                init_db(settings.sqlite_url)
            except Exception as e:
                console.print(
                    f"[red][Err][/] something went wrong while purging database: {e}"
                )

        for dir in merged_include:
            status.update(
                f"[green]Indexing documents from '{dir.name}'... Please wait, this may take a moment.[/]"
            )
            files = list_files(dir, merged_exclude)

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_threads
            ) as executor:
                executor.map(partial_function, files)

        status.update(
            "[green]Indexing feeds and posts... Please wait, this may take a moment."
        )
        asyncio.run(index_feeds(settings.sqlite_url, urls))

        try:
            status.update("[green]Wrapping things up...")
            rebuilt_fts_table(settings.sqlite_url)
        except Exception as e:
            console.print(
                f"[red][Err][/] something went wrong while rebuilding the fts5 table: {e}"
            )


@cli.command(
    name="web",
    short_help="Launchs Web UI.",
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
    default=20,
    help="Limit the number of documents returned.",
)
def search_documents(query: str, limit: int) -> None:
    """
    Search for documents and posts based on the provided query.
    """

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
        if doc_type in FILETYPES_SET:
            link = f"[link=file://{encoded_uri}]{doc_title}[/]"

        if doc_type in PLAIN_TEXT_FILETYPES:
            emoji = ":page_facing_up:"
        elif doc_type == "application/pdf":
            emoji = ":scroll:"
        elif doc_type == "application/epub+zip":
            emoji = ":green_book:"
        elif doc_type in COMPLEX_DOCUMENT_FILETYPES:
            emoji = ":bookmark_tabs:"

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
    help="Open the configuration file.",
)
def config() -> None:
    """
    Open the configuration file in the default text editor.
    """

    editor = os.environ.get("EDITOR", None)
    try:
        if editor:
            subprocess.run([editor, str(config_file_path)], check=True)
        else:
            subprocess.run(["open", str(config_file_path)], check=True)
    except Exception as e:
        console.print(f"[red][Err][/] Failed to open the configuration file: {e}")


@cli.command(
    name="vacuum",
    help="Reclaim unused spaced in the database.",
)
def vacuum() -> None:
    """
    Reclaims unused space in the database.
    """

    try:
        with db_connection(settings.sqlite_url) as conn:
            conn.execute("VACUUM")
            console.print("[green][Ok][/] unused space has been reclaimed!")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while reclaiming space: {e}")
