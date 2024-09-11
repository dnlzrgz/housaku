import asyncio
import os
import subprocess
from collections import Counter
from pathlib import Path
import aiohttp
import rich_click as click
from rich.console import Console
from rich.status import Status
from rich.table import Table
from sqlalchemy import create_engine, exc, except_, text
from sqlalchemy.orm import Session
from housaku.db import init_db
from housaku.feeds import fetch_feed, fetch_post
from housaku.files import list_files, extract_tokens
from housaku.models import Doc, Posting, Word
from housaku.repositories import DocRepository, PostingRepository, WordRepository
from housaku.search import search
from housaku.settings import Settings, config_file_path
from housaku.utils import tokenize

console = Console()


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
    engine = create_engine(settings.sqlite_url)
    init_db(engine)

    ctx.obj["engine"] = engine


async def _index_files(
    session: Session,
    status: Status,
    include: list[Path],
    exclude: list[str],
) -> None:
    """
    Index files from the specified list of directories.
    """

    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    sempahore = asyncio.Semaphore(10)

    async def process_file(file: Path):
        async with sempahore:
            uri = f"{file}"

            try:
                doc_in_db = doc_repo.get_by_attributes(uri=uri)
                if doc_in_db:
                    console.print(
                        f"[bold yellow]SKIP:[/] file already indexed: '{uri}'"
                    )
                    return

                tokens, metadata = await extract_tokens(file)
                doc_in_db = doc_repo.add(Doc(uri=uri, properties=metadata))
                count = Counter(tokens)

                for token, count in count.items():
                    word_in_db = word_repo.get_by_attributes(word=token)
                    if not word_in_db:
                        word_in_db = word_repo.add(Word(word=token))

                    posting_in_db = posting_repo.get_by_attributes(
                        word_id=word_in_db.id,
                        doc_id=doc_in_db.id,
                    )

                    if not posting_in_db:
                        posting_in_db = posting_repo.add(
                            Posting(
                                word=word_in_db,
                                doc=doc_in_db,
                                count=count,
                                tf=count / len(tokens),
                            )
                        )

                console.print(f"[bold green]OK:[/] indexed '{file}'.")
                session.commit()
            except Exception as e:
                console.print(
                    f"[bold red]ERROR:[/] something went wrong while reading '{file}': {e}"
                )

    for dir in include:
        status.update(
            f"[bold green]Indexing documents from '{dir.name}'... Please wait, this may take a moment."
        )
        try:
            files = list_files(dir, exclude)
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] {e}")
            continue

        tasks = [process_file(file) for file in files]
        await asyncio.gather(*tasks)


async def _index_feeds(session: Session, status: Status, feeds: list[str]) -> None:
    """
    Index content from the specified RSS feeds' posts.
    """

    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    async def process_feed(client: aiohttp.ClientSession, feed_url: str):
        try:
            entries = await fetch_feed(client, feed_url)
            for entry in entries:
                entry_link = entry.link
                uri = f"{entry_link}"

                doc_in_db = doc_repo.get_by_attributes(uri=uri)
                if doc_in_db:
                    console.print(
                        f"[bold yellow]SKIP:[/] post already indexed: '{uri}'"
                    )
                    return

                content = await fetch_post(client, entry_link)
                result = tokenize(content)
                metadata = {
                    "title": entry.get("title", ""),
                    "link": entry_link,
                    "published": entry.get("published", ""),
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", ""),
                    "categories": [
                        category.term for category in entry.get("categories", [])
                    ],
                }

                doc_in_db = doc_repo.add(Doc(uri=uri, properties=metadata))
                tokens = Counter(result)

                for token, count in tokens.items():
                    word_in_db = word_repo.get_by_attributes(word=token)
                    if not word_in_db:
                        word_in_db = word_repo.add(Word(word=token))

                    posting_in_db = posting_repo.get_by_attributes(
                        word_id=word_in_db.id,
                        doc_id=doc_in_db.id,
                    )

                    if not posting_in_db:
                        posting_in_db = posting_repo.add(
                            Posting(
                                word=word_in_db,
                                doc=doc_in_db,
                                count=count,
                                tf=count / len(result),
                            )
                        )

                console.print(f"[bold green]OK:[/] indexed '{uri}'.")
                session.commit()
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] {e}")

    status.update(
        "[bold green]Indexing feeds and posts... Please wait, this may take a moment."
    )
    async with aiohttp.ClientSession() as client:
        tasks = [process_feed(client, feed) for feed in feeds]
        await asyncio.gather(*tasks)


async def _index(session: Session, settings: Settings):
    """
    Start indexing of files and feeds based on the settings.
    """

    with console.status(
        "[bold green]Start indexing... Please, wait a moment.",
        spinner="arrow",
    ) as status:
        await _index_files(
            session,
            status,
            settings.files.include,
            settings.files.exclude,
        )
        await _index_feeds(session, status, settings.feeds.urls)


@cli.command(
    name="index",
    short_help="Start indexing documents and posts.",
)
@click.pass_context
def index(ctx) -> None:
    """
    Index documents and posts from the specified sources in the
    config.toml file.
    """

    engine = ctx.obj["engine"]
    settings = ctx.obj["settings"]

    with Session(engine) as session:
        asyncio.run(_index(session, settings))


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

    engine = ctx.obj["engine"]

    tokens = tokenize(query)
    with Session(engine) as session:
        results = search(session, tokens, limit)
        if not results:
            console.print("[yellow]No results found.[/]")
            return

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
                table.add_row(
                    ":scroll:",
                    file_name,
                    f"[link=file://{result.uri}]{result.uri}[/]",
                )
            else:
                title = result.properties.get("title", result.uri)
                table.add_row(
                    ":globe_with_meridians:",
                    title,
                    f"[link={result.uri}]{result.uri}[/]",
                )

        console.print(table)


@cli.command(name="config", help="Open the configuration file.")
def config() -> None:
    user_editor = os.environ.get("EDITOR", None)
    try:
        if user_editor:
            subprocess.run([user_editor, str(config_file_path)], check=True)
        else:
            subprocess.run(["open", str(config_file_path)], check=True)
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to open the configuration file: {e}")


@cli.command(
    name="vacuum",
    help="Reclaim unused spaced in the database.",
)
@click.pass_context
def vacuum(ctx) -> None:
    """
    Reclaims unused space in the database.
    """

    engine = ctx.obj["engine"]
    with Session(engine) as session:
        try:
            session.execute(text("VACUUM"))
            session.commit()
            console.print("[bold green]OK:[/] unused space has been reclaimed!")
        except exc.SQLAlchemyError as e:
            console.print(
                f"[bold red]ERROR:[/] something went wrong while reclaiming space: {e}"
            )
