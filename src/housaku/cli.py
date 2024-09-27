import asyncio
import concurrent.futures
import os
import subprocess
import urllib.parse
from pathlib import Path
from functools import partial
from time import perf_counter
import rich_click as click
from rich.table import Table
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import scoped_session, sessionmaker
from housaku.db import init_db
from housaku.feeds import index_feeds
from housaku.files import list_files, index_file
from housaku.search import search
from housaku.settings import Settings, config_file_path
from housaku.utils import tokenize, console


@click.group()
@click.pass_context
def cli(ctx) -> None:
    """
    A minimalist personal search engine.
    """

    ctx.ensure_object(dict)

    # Load settings
    settings = Settings()
    ctx.obj["settings"] = settings

    # Setup SQLite database
    engine = create_engine(
        settings.sqlite_url,
        connect_args={"check_same_thread": False},
    )
    init_db(engine)

    # Setup scoped session
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    ctx.obj["session"] = session


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
@click.pass_context
def index(ctx, include, exclude) -> None:
    """
    Index documents and posts from the specified sources in the
    config.toml file.
    """
    settings = ctx.obj["settings"]
    session = ctx.obj["session"]

    for dir in include:
        path = Path(dir)
        if not path.is_dir():
            console.print(f"[red][Err][/] Path '{path.resolve()}' is not a directory")
            return

    merged_include = list(
        set(Path(d) for d in settings.files.include) | {Path(d) for d in include}
    )
    merged_exclude = list(set(settings.files.exclude) | set(exclude))
    urls = settings.feeds.urls

    with console.status(
        "[green]Start indexing... Please, wait a moment.",
        spinner="arrow",
    ) as status:
        partial_function = partial(index_file, session)

        for dir in merged_include:
            status.update(
                f"[green]Indexing documents from '{dir.name}'... Please wait, this may take a moment.[/]"
            )
            files = list_files(dir, merged_exclude)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                executor.map(partial_function, files)

        asyncio.run(index_feeds(session, status, urls))


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
    default=None,
    help="Limit the number of documents returned.",
)
@click.pass_context
def search_documents(ctx, query: str, limit: int) -> None:
    """
    Search for documents and posts based on the provided query.
    """

    session = ctx.obj["session"]

    start_time = perf_counter()
    tokens = tokenize(query)
    results = search(session, tokens, limit)

    if not results:
        console.print("[yellow]No results found.[/]")
        return

    end_time = perf_counter()
    elapsed_time = end_time - start_time

    table = Table(
        show_header=True,
        header_style="bold",
        show_lines=True,
    )
    table.add_column("Type", width=5, justify="center")
    table.add_column("Name")
    table.add_column("URI")

    for result in results:
        if result.properties.get("name", None):
            file_name = result.properties.get("name", result.uri)
            encoded_uri = urllib.parse.quote(result.uri, safe=":/")
            table.add_row(
                ":scroll:", file_name, f"[link=file://{encoded_uri}]{result.uri}[/]"
            )
        else:
            title = result.properties.get("title", result.uri)
            table.add_row(
                ":globe_with_meridians:",
                title,
                f"[link={result.uri}]{result.uri}[/]",
            )

    console.print(table)
    console.print(
        f"Search completed in {elapsed_time:.2f}s",
        highlight=False,
        justify="center",
    )


@cli.command(
    name="config",
    help="Open the configuration file.",
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
    name="vacuum",
    help="Reclaim unused spaced in the database.",
)
@click.pass_context
def vacuum(ctx) -> None:
    """
    Reclaims unused space in the database.
    """

    session = ctx.obj["session"]
    try:
        session.execute(text("VACUUM"))
        session.commit()
        console.print("[green][Ok][/] unused space has been reclaimed!")
    except exc.SQLAlchemyError as e:
        console.print(f"[red][Err][/] something went wrong while reclaiming space: {e}")
