import asyncio
import os
import subprocess
import urllib.parse
from collections import Counter
from pathlib import Path
from time import perf_counter
import aiohttp
import rich_click as click
from rich.status import Status
from rich.table import Table
from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import Session
from housaku.db import init_db
from housaku.feeds import fetch_feed, fetch_post
from housaku.files import list_files, extract_tokens
from housaku.models import Doc, Posting, Word
from housaku.repositories import DocRepository, PostingRepository, WordRepository
from housaku.search import search
from housaku.settings import Settings, config_file_path
from housaku.utils import get_digest, tokenize, console


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
            doc_uri = f"{file}"

            try:
                doc_in_db = doc_repo.get_by_attributes(uri=doc_uri)
                content_hash = get_digest(file)

                if doc_in_db:
                    if doc_in_db.content_hash == content_hash:
                        console.print(
                            f"[yellow][Skip][/] file already indexed: '{doc_uri}'"
                        )
                        return
                    else:
                        # TODO: Clean child pages
                        # TODO: Clean postings per child page
                        # TODO: Update hash
                        pass

                async for page in extract_tokens(file):
                    new_doc = Doc(
                        uri=page.uri,
                        properties=page.properties,
                    )

                    if page.parent_uri:
                        parent_doc = doc_repo.get_by_attributes(uri=page.parent_uri)
                        if not parent_doc:
                            console.print(
                                f"[red][Err][/] something went wrong while reading '{file}': parent '{page.parent_uri}' does not exist"
                            )
                        else:
                            new_doc.parent_id = parent_doc.id
                    else:
                        new_doc.content_hash = content_hash

                    doc_in_db = doc_repo.add(new_doc)

                    count = Counter(page.tokens)
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
                                    tf=count / len(page.tokens),
                                )
                            )

                    console.print(f"[green][Ok][/] indexed '{page.uri}'.")
                session.commit()
            except Exception as e:
                console.print(
                    f"[red][Err][/] something went wrong while reading '{file}': {e}"
                )
                session.rollback()

    for dir in include:
        status.update(
            f"[green]Indexing documents from '{dir.name}'... Please wait, this may take a moment.[/]"
        )
        try:
            files = list_files(dir, exclude)
        except Exception as e:
            console.print(f"[red][Err][/] {e}")
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
                    console.print(f"[yellow][Skip][/] post already indexed: '{uri}'")
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

                console.print(f"[green][Ok][/] indexed '{uri}'.")
                session.commit()
        except Exception as e:
            console.print(f"[red][Err][/] {e}")
            session.rollback()

    status.update(
        "[green]Indexing feeds and posts... Please wait, this may take a moment."
    )
    async with aiohttp.ClientSession() as client:
        tasks = [process_feed(client, feed) for feed in feeds]
        await asyncio.gather(*tasks)


async def _index(
    session: Session, include: list[Path], exclude: list[str], urls: list[str]
):
    """
    Start indexing of files and feeds based on the settings.
    """

    with console.status(
        "[green]Start indexing... Please, wait a moment.",
        spinner="arrow",
    ) as status:
        await _index_files(session, status, include, exclude)
        await _index_feeds(session, status, urls)


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

    engine = ctx.obj["engine"]
    settings = ctx.obj["settings"]

    merged_include = list(
        set(Path(d) for d in settings.files.include) | {Path(d) for d in include}
    )
    merged_exclude = list(set(settings.files.exclude) | set(exclude))
    urls = settings.feeds.urls

    with Session(engine) as session:
        asyncio.run(
            _index(
                session,
                merged_include,
                merged_exclude,
                urls,
            )
        )


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

    start_time = perf_counter()
    tokens = tokenize(query)
    with Session(engine) as session:
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

    engine = ctx.obj["engine"]
    with Session(engine) as session:
        try:
            session.execute(text("VACUUM"))
            session.commit()
            console.print("[green][Ok][/] unused space has been reclaimed!")
        except exc.SQLAlchemyError as e:
            console.print(
                f"[red][Err][/] something went wrong while reclaiming space: {e}"
            )
