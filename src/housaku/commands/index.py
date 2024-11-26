import asyncio
import concurrent.futures
from functools import partial
from multiprocessing import cpu_count
import rich_click as click
from housaku.db import rebuild_fts
from housaku.feeds import index_feed
from housaku.files import list_files, index_file
from housaku.utils import console


@click.command(
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
@click.pass_context
def index(ctx: click.Context, max_threads: int) -> None:
    settings = ctx.obj["settings"]

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
