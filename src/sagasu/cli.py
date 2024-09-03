import asyncio
from pathlib import Path
from itertools import batched
from collections import Counter
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from rich.console import Console
from sagasu.db import init_db
from sagasu.files import list_files_in_dir, read_file
from sagasu.models import Doc, Posting, Word
from sagasu.repositories import DocRepository, PostingRepository, WordRepository
from sagasu.settings import Settings

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx) -> None:
    """
    A personal search engine.
    """
    ctx.ensure_object(dict)

    # Load settings
    settings = Settings()
    ctx.obj["settings"] = settings

    # Setup SQLite database
    engine = create_engine(settings.sqlite_url)
    init_db(engine)

    ctx.obj["engine"] = engine

    # If no subcommand, exit
    if ctx.invoked_subcommand is None:
        print(ctx.obj["settings"])


async def _index_file(session: Session, file: Path) -> None:
    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    result = await read_file(file)
    if not result:
        print(f"Error while reading file: {file}")
        return

    uri = file.resolve()
    uri_str = f"{uri}"
    doc_in_db = doc_repo.get_by_attributes(uri=uri_str)
    if doc_in_db:
        return

    content, tokens, metadata = result
    doc_in_db = doc_repo.add(
        Doc(
            uri=uri_str,
            content=content,
            properties=metadata,
        )
    )

    tokens = Counter(tokens)
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
                )
            )

    session.commit()


async def _index_files(session: Session, files: list[Path]) -> None:
    number_of_tasks = 20

    with console.status(
        "Indexing documents... This may take a moment", spinner="earth"
    ):
        for batch in batched(files, number_of_tasks):
            tasks = []
            for file in batch:
                tasks.append(asyncio.ensure_future(_index_file(session, file)))

            await asyncio.gather(*tasks)


@cli.command(name="index", help="")
@click.pass_context
def index(ctx) -> None:
    engine = ctx.obj["engine"]
    settings = ctx.obj["settings"]

    files = []
    for dir in settings.directories:
        files_in_dir = list_files_in_dir(settings.directories[dir])
        if files_in_dir:
            files.extend(files_in_dir)

    with Session(engine) as session:
        asyncio.run(_index_files(session, files))
