import asyncio
from pathlib import Path
from collections import Counter
import aiohttp
import click
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import Session
from rich.console import Console
from sagasu.db import init_db
from sagasu.feeds import fetch_feed, fetch_post
from sagasu.files import list_files, extract_tokens
from sagasu.models import Doc, Posting, Word
from sagasu.repositories import DocRepository, PostingRepository, WordRepository
from sagasu.search import search
from sagasu.settings import Settings
from sagasu.utils import tokenize

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx) -> None:
    """
    A minimalistic personal search engine.
    """

    ctx.ensure_object(dict)

    # Load settings
    settings = Settings()
    ctx.obj["settings"] = settings

    # Setup SQLite database
    engine = create_engine(settings.sqlite_url)
    init_db(engine)

    ctx.obj["engine"] = engine

    if ctx.invoked_subcommand is None:
        ctx.forward(search)


async def _index_files(
    session: Session, include: list[Path], exclude: list[str]
) -> None:
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
                        f"[bold yellow]SKIP:[/] skipping already indexed file: '{uri}'"
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

                console.print(f"[bold green]SUCCESS:[/] successfully indexed '{file}'.")
                session.commit()
            except Exception as e:
                console.print(
                    f"[bold red]ERROR:[/] something went wrong while reading '{file}': {e}"
                )

    with console.status(
        "Indexing documents... This may take a moment", spinner="earth"
    ):
        for dir in include:
            try:
                files = list_files(dir, exclude)
            except Exception as e:
                console.print(f"[bold red]ERROR:[/] {e}")
                continue

            tasks = [process_file(file) for file in files]
            await asyncio.gather(*tasks)


async def _index_feeds(session: Session, feeds: list[str]) -> None:
    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    async def process_feed(client: aiohttp.ClientSession, feed_url: str):
        try:
            entries = await fetch_feed(client, feed_url)
            for entry in entries:
                uri = f"{entry}"

                doc_in_db = doc_repo.get_by_attributes(uri=uri)
                if doc_in_db:
                    console.print(
                        f"[bold yellow]SKIP:[/] skipping already indexed post: '{uri}'"
                    )
                    return

                content = await fetch_post(client, entry)
                result = tokenize(content)
                doc_in_db = doc_repo.add(Doc(uri=uri))
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

                console.print(f"[bold green]SUCCESS:[/] successfully indexed '{uri}'.")
                session.commit()
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] {e}")

    with console.status(
        "Fetching feeds and indexing content ... This may take a moment",
        spinner="earth",
    ):
        async with aiohttp.ClientSession() as client:
            tasks = [process_feed(client, feed) for feed in feeds]
            await asyncio.gather(*tasks)


async def _index(session: Session, settings: Settings):
    await _index_files(session, settings.files.include, settings.files.exclude)
    await _index_feeds(session, settings.feeds.urls)


@cli.command(
    name="index",
    help="Index document for the specified directories.",
)
@click.pass_context
def index(ctx) -> None:
    engine = ctx.obj["engine"]
    settings = ctx.obj["settings"]

    with Session(engine) as session:
        asyncio.run(_index(session, settings))


@cli.command(
    name="search",
    help="Search for documents.",
)
@click.option(
    "--query",
    help="Search query",
)
@click.pass_context
def search_documents(ctx, query: str) -> None:
    engine = ctx.obj["engine"]

    if not query:
        query = click.prompt("Search query")

    tokens = tokenize(query)

    with Session(engine) as session:
        results = search(session, tokens)
        if not results:
            console.print("[yellow]No results found.[/]")
            return

        console.print(f"[green]Found {len(results)} results:[/]")
        for result in results:
            console.print(f"'{result.uri}'")


@cli.command(
    name="vacuum",
    help="Reclaim unused spaced in the database.",
)
@click.pass_context
def vacuum(ctx) -> None:
    engine = ctx.obj["engine"]
    with Session(engine) as session:
        try:
            session.execute(text("VACUUM"))
            session.commit()
            console.print("[bold green]SUCCESS:[/] unused space has been reclaimed!")
        except exc.SQLAlchemyError as e:
            console.print(
                f"[bold red]ERROR:[/] something went wrong while reclaiming space: {e}"
            )
